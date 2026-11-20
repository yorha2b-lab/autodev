from sklearn.preprocessing import StandardScaler
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process.kernels import RBF, ExpSineSquared, WhiteKernel, ConstantKernel as C
from sklearn.gaussian_process import GaussianProcessRegressor
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import linkage, dendrogram, cophenet, set_link_color_palette
from scipy.stats import rankdata, lognorm, gamma, weibull_min, lomax, kstest
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import os
import warnings

import matplotlib
matplotlib.use('Agg')


OUTPUT_IMAGE = 'plots/bunker_astral_genesis.png'

plt.style.use('dark_background')


def load_bunker_data():
    c_path = 'ghrs-data/clones_ledger.csv'
    if not os.path.exists(c_path):
        raise FileNotFoundError(f'Missing required ledger: {c_path}')

    df = pd.read_csv(c_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').drop_duplicates('date', keep='last')

    full_idx = pd.date_range(df['date'].min(), df['date'].max(), freq='D')
    df = df.set_index('date').reindex(full_idx).fillna(0.0)
    df.index.name = 'date'

    v_path = 'ghrs-data/views_ledger.csv'
    if os.path.exists(v_path):
        v_df = pd.read_csv(v_path)
        v_df['date'] = pd.to_datetime(v_df['date'])
        v_df = v_df.sort_values('date').drop_duplicates('date', keep='last')
        v_df = v_df.set_index('date').reindex(full_idx).fillna(0.0)
        df['views'] = v_df['views'].values
        df['views_uniques'] = v_df['uniques'].values
    else:
        df['views'] = 0.0
        df['views_uniques'] = 0.0

    return df


# ==============================================================================
# 1. Apollo Control: 2D State-Space Kalman Filter & Innovation Radar
# ==============================================================================
def plot_kalman_filter(ax, dates, y):
    z = np.log1p(y)
    n = len(z)
    var_z = max(float(np.var(z)), 0.05)

    x_est = np.array([z[0], 0.0])
    P = np.eye(2) * var_z
    F = np.array([[1.0, 1.0], [0.0, 0.85]])
    H = np.array([[1.0, 0.0]])
    Q = np.diag([0.08 * var_z, 0.015 * var_z])
    R = np.array([[0.35 * var_z]])
    I2 = np.eye(2)

    levels = np.zeros(n)
    vels = np.zeros(n)
    level_std = np.zeros(n)
    innov_z = np.zeros(n)
    gains = np.zeros(n)

    for t in range(n):
        x_pred = F @ x_est
        P_pred = F @ P @ F.T + Q

        innov = float(z[t] - (H @ x_pred)[0])
        S = max(float((H @ P_pred @ H.T + R)[0, 0]), 1e-12)
        K = (P_pred @ H.T) / S

        x_est = x_pred + K[:, 0] * innov
        # Joseph 形式保证协方差矩阵严格对称正定
        IKH = I2 - K @ H
        P = IKH @ P_pred @ IKH.T + K @ R @ K.T

        levels[t] = x_est[0]
        vels[t] = x_est[1]
        level_std[t] = np.sqrt(max(P[0, 0], 1e-12))
        innov_z[t] = innov / np.sqrt(S)
        gains[t] = float(K[0, 0])

    ax.scatter(dates, z, color='#4cc9f0', s=12,
               alpha=0.4, label='Observed Log(Clones+1)')
    ax.plot(dates, levels, color='#00f5d4', lw=2.2,
            label='Kalman Filtered Level ℓ_t')
    ax.fill_between(dates, levels - 2.0 * level_std, levels + 2.0 * level_std,
                    color='#00f5d4', alpha=0.16, label='Kalman ±2σ State Band')

    ax2 = ax.twinx()
    ax2.bar(dates, innov_z, width=0.9, color='#ff4d6d',
            alpha=0.45, label='Innovation Surprise (Z)')
    ax2.axhline(3.0, color='#ffbe0b', ls=':', lw=1.0, alpha=0.7)
    ax2.set_ylabel('Radar Innovation Surprise (σ)', color='#ff4d6d')
    ax2.tick_params(axis='y', colors='#ff4d6d')

    breach_idx = int(np.argmax(innov_z))
    ax2.annotate(
        f"Breach: +{innov_z[breach_idx]:.1f}σ ({dates[breach_idx].strftime('%m-%d')})",
        xy=(dates[breach_idx], innov_z[breach_idx]),
        xytext=(dates[min(n - 1, breach_idx + 14)],
                innov_z[breach_idx] * 0.88),
        color='#ffea00', fontsize=8.5, fontweight='bold',
        arrowprops=dict(arrowstyle='->', color='#ffea00', lw=1.2)
    )

    ax.set_title('Apollo 2D Kalman Filter & Radar Innovation Lock',
                 color='#00f5d4', fontweight='bold')
    ax.set_ylabel('Log(Clones + 1)', color='#00f5d4')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=25)
    ax.grid(alpha=0.15)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2,
              loc='upper right', fontsize=7.8, framealpha=0.84)

    info = (
        f"Steady Kalman Gain K₀: {gains[-1]:.3f}\n"
        f"Current Latent Vel:    {vels[-1]:+.4f}/d\n"
        f"Max Radar Breach:      +{innov_z[breach_idx]:.2f}σ"
    )
    ax.text(0.02, 0.96, info, transform=ax.transAxes, va='top', fontsize=8.3,
            color='#00f5d4', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#00f5d4', alpha=0.88))


# ==============================================================================
# 2. Bayesian Non-Parametric ML: Gaussian Process (Periodic 7d + RBF Kernel)
# ==============================================================================
def plot_gaussian_process(ax, dates, y):
    n_fit = min(120, len(y))
    sub_dates = dates[-n_fit:]
    z_fit = np.log1p(y[-n_fit:])

    X_train = np.arange(n_fit, dtype=float)[:, None]
    horizon = 21
    X_all = np.arange(n_fit + horizon, dtype=float)[:, None]
    all_dates = pd.date_range(sub_dates[0], periods=n_fit + horizon, freq='D')

    kernel = (
        C(1.0, (0.05, 10.0)) * RBF(length_scale=30.0,
                                   length_scale_bounds=(5.0, 160.0))
        + C(0.4, (0.01, 5.0)) * ExpSineSquared(
            length_scale=1.5, periodicity=7.0,
            length_scale_bounds=(0.3, 12.0), periodicity_bounds='fixed'
        )
        + WhiteKernel(noise_level=0.35, noise_level_bounds=(1e-3, 5.0))
    )

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        gpr = GaussianProcessRegressor(
            kernel=kernel, normalize_y=True, n_restarts_optimizer=2, random_state=42
        )
        gpr.fit(X_train, z_fit)

    mean_pred, std_pred = gpr.predict(X_all, return_std=True)
    lml = float(gpr.log_marginal_likelihood_value_)

    ax.scatter(sub_dates, z_fit, color='#4cc9f0', s=18,
               alpha=0.65, label=f'Last {n_fit}d Observed')
    ax.plot(all_dates[:n_fit], mean_pred[:n_fit],
            color='#39ff14', lw=2.0, label='GP Posterior Mean')
    ax.plot(all_dates[n_fit - 1:], mean_pred[n_fit - 1:], color='#ffea00', lw=2.3, ls='--',
            label=f'+{horizon}d Periodic Wave Forecast')

    ax.fill_between(all_dates, mean_pred - 1.96 * std_pred, mean_pred + 1.96 * std_pred,
                    color='#39ff14', alpha=0.14, label='95% GP Confidence Tube')
    ax.fill_between(all_dates[n_fit - 1:], mean_pred[n_fit - 1:] - std_pred[n_fit - 1:],
                    mean_pred[n_fit - 1:] + std_pred[n_fit - 1:],
                    color='#ffea00', alpha=0.22)

    ax.axvline(sub_dates[-1], color='#ff00ff', ls=':', lw=1.4, alpha=0.8)

    # 找到未来 21 天内峰值预测（大概率又是某天周五）
    fut_mean = mean_pred[n_fit:]
    fut_dates = all_dates[n_fit:]
    best_i = int(np.argmax(fut_mean))
    next_peak_clones = np.expm1(fut_mean[best_i])

    ax.set_title('Gaussian Process Forecast (RBF + 7d ExpSineSquared Kernel)',
                 color='#39ff14', fontweight='bold')
    ax.set_ylabel('Log(Clones + 1)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=25)
    ax.legend(loc='upper left', fontsize=7.8, framealpha=0.85)
    ax.grid(alpha=0.15)

    info = (
        f"Log-Marginal-Lik: {lml:.1f}\n"
        f"Next Wave Crest:  {fut_dates[best_i].strftime('%m-%d')} ({fut_dates[best_i].strftime('%a')})\n"
        f"Predicted Crest:  ~{next_peak_clones:.1f} clones/d"
    )
    ax.text(0.02, 0.05, info, transform=ax.transAxes, va='bottom', fontsize=8.3,
            color='#39ff14', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#39ff14', alpha=0.88))


# ==============================================================================
# 3. ML Feature Attribution: Random Forest + OOS Permutation Importance
# ==============================================================================
def plot_rf_permutation_importance(ax, df):
    y_log = np.log1p(df['clones'].values.astype(float))
    v_log = np.log1p(df['views'].values.astype(float))
    dow = df.index.dayofweek.values

    feat_df = pd.DataFrame({
        'Lag-1 (Yesterday)': pd.Series(y_log).shift(1),
        'Lag-2 (2d Ago)': pd.Series(y_log).shift(2),
        'Lag-3 (3d Ago)': pd.Series(y_log).shift(3),
        'Lag-7 (Last Week)': pd.Series(y_log).shift(7),
        'Lag-14 (2w Ago)': pd.Series(y_log).shift(14),
        '7D Rolling Vol': pd.Series(y_log).shift(1).rolling(7).std(),
        'Is Friday': (dow == 4).astype(float),
        'Is Weekend': (dow >= 5).astype(float),
        'Web Views (Lag-1)': pd.Series(v_log).shift(1),
        'target': y_log,
    }).dropna()

    X = feat_df.drop(columns=['target']).values
    y_target = feat_df['target'].values
    names = list(feat_df.drop(columns=['target']).columns)

    split = max(int(len(X) * 0.72), 30)
    X_tr, X_te = X[:split], X[split:]
    y_tr, y_te = y_target[:split], y_target[split:]

    rf = RandomForestRegressor(
        n_estimators=220, max_depth=6, min_samples_leaf=3, random_state=42)
    rf.fit(X_tr, y_tr)

    train_r2 = float(rf.score(X_tr, y_tr))
    test_r2 = float(rf.score(X_te, y_te))

    perm = permutation_importance(
        rf, X_te, y_te, n_repeats=30, random_state=42)
    means = perm.importances_mean
    stds = perm.importances_std

    order = np.argsort(means)
    sorted_names = [names[i] for i in order]
    sorted_means = means[order]
    sorted_stds = stds[order]
    bar_colors = ['#00f5d4' if m > 0 else '#ff4d6d' for m in sorted_means]

    y_pos = np.arange(len(sorted_names))
    ax.barh(y_pos, sorted_means, xerr=sorted_stds, color=bar_colors, alpha=0.85,
            edgecolor='white', linewidth=0.5, ecolor='#adb5bd', capsize=3)
    ax.axvline(0.0, color='#adb5bd', ls='--', lw=1.0)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(sorted_names, fontsize=8.5)
    ax.set_xlabel('OOS Permutation Importance (ΔR² When Shuffled)')
    ax.set_title('Random Forest Lag Attribution (OOS Permutation Importance)',
                 color='#ffbe0b', fontweight='bold')
    ax.grid(alpha=0.15, axis='x')

    top_feat = sorted_names[-1]
    info = (
        f"Train R² / OOS Test R²: {train_r2:.2f} / {test_r2:.2f}\n"
        f"#1 Predictive Driver:   {top_feat}"
    )
    ax.text(0.98, 0.05, info, transform=ax.transAxes, ha='right', va='bottom', fontsize=8.3,
            color='#ffbe0b', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#ffbe0b', alpha=0.88))


# ==============================================================================
# 4. Phylogenetics: Ward Hierarchical Dendrogram of Weekly Civilizations
# ==============================================================================
def plot_weekly_dendrogram(ax, df):
    rows = []
    labels = []
    for p, grp in df.groupby(df.index.to_period('W')):
        if len(grp) < 5:
            continue
        c_log = np.log1p(grp['clones'].values)
        u_log = np.log1p(grp['uniques'].values)
        v_log = np.log1p(grp['views'].values)
        rep = float(grp['clones'].sum()) / \
            max(float(grp['uniques'].sum()), 1.0)
        rows.append([
            float(np.mean(c_log)),
            float(np.std(c_log)),
            float(np.max(c_log)),
            float(np.mean(u_log)),
            rep,
            float(np.mean(v_log)),
        ])
        iso_w = p.start_time.isocalendar().week
        labels.append(f'W{iso_w:02d}')

    X_w = StandardScaler().fit_transform(np.array(rows))
    Z = linkage(X_w, method='ward')
    coph_r, _ = cophenet(Z, pdist(X_w))

    set_link_color_palette(['#00f5d4', '#ff00ff', '#ffbe0b', '#39ff14'])
    dendrogram(
        Z, labels=labels, ax=ax, leaf_rotation=70, leaf_font_size=8,
        color_threshold=0.52 * Z[-1, 2], above_threshold_color='#adb5bd'
    )
    set_link_color_palette(None)

    ax.set_title('Phylogenetic Taxonomy: Weekly Ward Clustering Tree',
                 color='#ff00ff', fontweight='bold')
    ax.set_xlabel('ISO Week Species')
    ax.set_ylabel('Ward Evolutionary Distance')
    ax.grid(alpha=0.14, axis='y')

    info = (
        f"Weekly Species: {len(labels)}\n"
        f"Cophenetic Fit: r = {coph_r:.3f}\n"
        f"Max Clade Split: {Z[-1, 2]:.2f}"
    )
    ax.text(0.98, 0.96, info, transform=ax.transAxes, ha='right', va='top', fontsize=8.4,
            color='#ff00ff', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#ff00ff', alpha=0.88))


# ==============================================================================
# 5. Fractal Bioinformatics: DNA Chaos Game Representation (CGR)
# ==============================================================================
def plot_dna_cgr(ax, y):
    n = len(y)
    pcts = rankdata(y, method='average') / float(n)
    bases = []
    for p in pcts:
        if p <= 0.25:
            bases.append('A')
        elif p <= 0.50:
            bases.append('T')
        elif p <= 0.75:
            bases.append('C')
        else:
            bases.append('G')

    corners = {
        'A': np.array([0.0, 0.0]),
        'T': np.array([0.0, 1.0]),
        'C': np.array([1.0, 1.0]),
        'G': np.array([1.0, 0.0]),
    }

    pts = np.zeros((n, 2))
    cur = np.array([0.5, 0.5])
    for i, b in enumerate(bases):
        cur = 0.5 * (cur + corners[b])
        pts[i] = cur

    # 4x4 二核苷酸密度热图打底
    hist, _, _ = np.histogram2d(pts[:, 0], pts[:, 1], bins=4, range=[
                                [0.0, 1.0], [0.0, 1.0]])
    ax.imshow(hist.T, origin='lower', extent=[
              0, 1, 0, 1], cmap='inferno', alpha=0.58)

    t_norm = np.linspace(0.0, 1.0, n)
    ax.plot(pts[:, 0], pts[:, 1], color='#00f5d4', lw=0.45, alpha=0.28)
    ax.scatter(pts[:, 0], pts[:, 1], c=t_norm, cmap='cool',
               s=22, edgecolors='white', lw=0.25, zorder=4)

    # 子象限辅助网格
    for v in (0.25, 0.5, 0.75):
        ls = '-' if v == 0.5 else ':'
        lw = 1.2 if v == 0.5 else 0.7
        ax.axvline(v, color='#adb5bd', ls=ls, lw=lw, alpha=0.45)
        ax.axhline(v, color='#adb5bd', ls=ls, lw=lw, alpha=0.45)

    # 统计最密集的二核苷酸组合
    dinuc = {}
    for i in range(n - 1):
        pair = bases[i] + bases[i + 1]
        dinuc[pair] = dinuc.get(pair, 0) + 1
    top_pair, top_cnt = max(dinuc.items(), key=lambda kv: kv[1])

    ax.text(0.02, 0.02, 'A (Q1 Quiet)', color='#39ff14',
            fontsize=8.5, fontweight='bold', ha='left', va='bottom')
    ax.text(0.02, 0.98, 'T (Q2 Low-Mid)', color='#00bbf9',
            fontsize=8.5, fontweight='bold', ha='left', va='top')
    ax.text(0.98, 0.98, 'C (Q3 High-Mid)', color='#ffbe0b',
            fontsize=8.5, fontweight='bold', ha='right', va='top')
    ax.text(0.98, 0.02, 'G (Q4 Blitz)', color='#ff006e',
            fontsize=8.5, fontweight='bold', ha='right', va='bottom')

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_aspect('equal', adjustable='box')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f'DNA Chaos Game Representation (Top Dinucleotide: {top_pair} ×{top_cnt})',
                 color='#00bbf9', fontweight='bold')


# ==============================================================================
# 6. Statistical Law Pageant: Log-Normal vs Gamma vs Weibull vs Lomax (AIC + KS)
# ==============================================================================
def plot_distribution_pageant(ax, y):
    y_pos = np.sort(y[y > 0].astype(float))
    n_p = len(y_pos)
    ccdf_emp = 1.0 - (np.arange(1, n_p + 1) / (n_p + 1.0))

    ax.scatter(y_pos, ccdf_emp, color='#ffffff', s=16, alpha=0.75,
               zorder=5, label='Empirical CCDF P(X≥x)')

    candidates = [
        ('Log-Normal', lognorm, '#39ff14', '-'),
        ('Gamma', gamma, '#00bbf9', '--'),
        ('Weibull', weibull_min, '#ffbe0b', '-.'),
        ('Lomax (Power)', lomax, '#ff00ff', ':'),
    ]

    x_grid = np.logspace(np.log10(max(y_pos.min(), 0.8)),
                         np.log10(y_pos.max() * 1.1), 220)
    results = []

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for name, dist, color, ls in candidates:
            try:
                params = dist.fit(y_pos, floc=0.0)
                ll = float(np.sum(dist.logpdf(y_pos, *params)))
                k_params = len(params) - 1  # floc 固定了 1 个参数
                aic = 2.0 * k_params - 2.0 * ll
                ks_stat, ks_p = kstest(y_pos, dist.cdf, args=params)
                sf = np.maximum(dist.sf(x_grid, *params), 1e-6)
                ax.plot(x_grid, sf, color=color, ls=ls, lw=2.1,
                        label=f'{name} (AIC={aic:.0f})')
                results.append((aic, name, ks_stat, ks_p))
            except Exception:
                continue

    results.sort(key=lambda r: r[0])

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_ylim(1.0 / (n_p * 2.5), 1.35)
    ax.set_title('Cosmic Law Contest: Log-Log CCDF & AIC Ranking',
                 color='#ff4d6d', fontweight='bold')
    ax.set_xlabel('Daily Clones (Log Scale)')
    ax.set_ylabel('Survival Tail P(Clones ≥ x) [Log Scale]')
    ax.legend(loc='lower left', fontsize=8, framealpha=0.85)
    ax.grid(alpha=0.16, which='both')

    if results:
        lines = ['AIC Leaderboard (Lower = Better):']
        for rank, (aic, name, ks_d, ks_p) in enumerate(results, start=1):
            lines.append(f'#{rank} {name:<13} AIC={aic:6.1f} (p={ks_p:.2f})')
        info = '\n'.join(lines)
        ax.text(0.98, 0.96, info, transform=ax.transAxes, ha='right', va='top', fontsize=8.0,
                color='#00f5d4', family='monospace',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#00f5d4', alpha=0.88))


def main():
    print('🛸 Pod 042: Executing Astral ML & Genesis Laws (v12.0)...')
    df = load_bunker_data()
    dates = df.index
    y = df['clones'].values.astype(float)

    fig, axes = plt.subplots(3, 2, figsize=(20, 18), facecolor='#04060a')
    for ax in axes.flat:
        ax.set_facecolor('#080c14')

    plot_kalman_filter(axes[0, 0], dates, y)
    plot_gaussian_process(axes[0, 1], dates, y)
    plot_rf_permutation_importance(axes[1, 0], df)
    plot_weekly_dendrogram(axes[1, 1], df)
    plot_dna_cgr(axes[2, 0], y)
    plot_distribution_pageant(axes[2, 1], y)

    fig.suptitle(
        'Bunker Astral Genesis (Kalman + Gaussian Process + Random Forest + Ward Tree + DNA CGR + AIC Contest)',
        color='#00bbf9', fontsize=15.6, fontweight='bold', y=0.975
    )

    fig.subplots_adjust(left=0.06, right=0.945, top=0.925,
                        bottom=0.06, hspace=0.35, wspace=0.25)
    out_dir = os.path.dirname(OUTPUT_IMAGE)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    plt.savefig(OUTPUT_IMAGE, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'✅ Astral Genesis archived at: {OUTPUT_IMAGE}')


if __name__ == '__main__':
    main()
