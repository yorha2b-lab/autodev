from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.stats import gamma as gamma_dist
from scipy.signal import coherence
from scipy.optimize import minimize
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings

import matplotlib
matplotlib.use('Agg')


OUTPUT_IMAGE = 'plots/bunker_imperial_pantheon.png'

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


def build_complete_week_matrix(df):
    iso = df.index.isocalendar()
    tmp = pd.DataFrame({
        'yw': [f'{y}-W{w:02d}' for y, w in zip(iso.year, iso.week)],
        'dow': df.index.dayofweek,
        'clones': df['clones'].values.astype(float),
    }, index=df.index)
    piv = tmp.pivot_table(index='yw', columns='dow',
                          values='clones', aggfunc='mean').dropna()
    piv.columns = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    return piv


# ==============================================================================
# 1. Wall Street Portfolio Theory: Markowitz Efficient Frontier (Mon-Sun Stocks)
# ==============================================================================
def plot_markowitz_frontier(ax, week_mat):
    names = list(week_mat.columns)
    R = week_mat.values  # shape (n_weeks, 7)
    mu = np.mean(R, axis=0)
    cov = np.cov(R, rowvar=False) + 1e-6 * np.eye(7)
    stds = np.sqrt(np.diag(cov))

    # 随机模拟 2500 个工作日配比组合
    rng = np.random.default_rng(42)
    weights_rand = rng.dirichlet(np.ones(7), size=2500)
    ret_rand = weights_rand @ mu
    vol_rand = np.sqrt(
        np.einsum('ij,jk,ik->i', weights_rand, cov, weights_rand))
    sharpe_rand = ret_rand / np.maximum(vol_rand, 1e-9)

    sc = ax.scatter(vol_rand, ret_rand, c=sharpe_rand,
                    cmap='viridis', s=10, alpha=0.45)

    bounds = [(0.0, 1.0)] * 7
    cons_sum = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}

    # 最小方差组合
    res_mv = minimize(lambda w: float(w @ cov @ w), np.ones(7) / 7.0,
                      method='SLSQP', bounds=bounds, constraints=[cons_sum])
    w_mv = res_mv.x if res_mv.success else np.ones(7) / 7.0
    mu_mv = float(w_mv @ mu)
    vol_mv = float(np.sqrt(w_mv @ cov @ w_mv))

    # 最大夏普组合（多起点防止局部极值）
    best_sr = -np.inf
    w_sr = w_mv
    starts = [np.ones(7) / 7.0, np.eye(7)
              [int(np.argmax(mu / stds))], np.eye(7)[4]]
    for x0 in starts:
        res_sr = minimize(lambda w: -float(w @ mu) / max(float(np.sqrt(w @ cov @ w)), 1e-9),
                          x0, method='SLSQP', bounds=bounds, constraints=[cons_sum])
        if res_sr.success:
            sr_val = float(res_sr.x @ mu) / \
                max(float(np.sqrt(res_sr.x @ cov @ res_sr.x)), 1e-9)
            if sr_val > best_sr:
                best_sr = sr_val
                w_sr = res_sr.x
    mu_sr = float(w_sr @ mu)
    vol_sr = float(np.sqrt(w_sr @ cov @ w_sr))

    # 有效前沿包络线
    ef_vols, ef_rets = [], []
    for targ in np.linspace(mu_mv, float(np.max(mu)) * 0.99, 32):
        cons = [cons_sum, {'type': 'eq',
                           'fun': lambda w, t=targ: float(w @ mu) - t}]
        res_ef = minimize(lambda w: float(w @ cov @ w), w_sr,
                          method='SLSQP', bounds=bounds, constraints=cons)
        if res_ef.success:
            ef_vols.append(float(np.sqrt(res_ef.x @ cov @ res_ef.x)))
            ef_rets.append(float(res_ef.x @ mu))
    if ef_vols:
        ax.plot(ef_vols, ef_rets, color='#00f5d4', lw=2.3,
                ls='--', label='Efficient Frontier')

    # 标注 7 个星期股票本体
    stock_colors = ['#4cc9f0', '#ff006e', '#a8dadc',
                    '#90be6d', '#39ff14', '#ffbe0b', '#adb5bd']
    for i, name in enumerate(names):
        ax.scatter([stds[i]], [mu[i]], color=stock_colors[i],
                   s=90, edgecolors='white', lw=0.8, zorder=6)
        dx = -8 if stds[i] > np.median(stds) * 2.0 else 3
        ha = 'right' if dx < 0 else 'left'
        tag = f'{name} (859 Meme)' if (
            name == 'Tue' and stds[i] > 60) else name
        ax.annotate(tag, (stds[i], mu[i]), xytext=(dx, 4), textcoords='offset points',
                    color=stock_colors[i], fontsize=8.5, fontweight='bold', ha=ha)

    ax.scatter([vol_mv], [mu_mv], color='#00bbf9', marker='D', s=110, edgecolors='white', zorder=7,
               label=f'Min Risk ({vol_mv:.1f}, {mu_mv:.1f})')
    ax.scatter([vol_sr], [mu_sr], color='#ffea00', marker='*', s=240, edgecolors='white', lw=0.7, zorder=8,
               label=f'Max Sharpe ({best_sr:.2f})')

    top_alloc = sorted(zip(names, w_sr * 100.0),
                       key=lambda kv: kv[1], reverse=True)
    alloc_str = ' | '.join(
        [f'{k}:{v:.0f}%' for k, v in top_alloc[:4] if v >= 1.0])

    ax.set_title('Markowitz Efficient Frontier (Mon–Sun as 7 Stocks)',
                 color='#ffea00', fontweight='bold')
    ax.set_xlabel('Daily Risk Volatility σ [Clones/d]')
    ax.set_ylabel('Expected Yield μ [Clones/d]')
    ax.legend(loc='lower right', fontsize=7.8, framealpha=0.85)
    ax.grid(alpha=0.15)

    info = (
        f"Optimal Sharpe Ratio: {best_sr:.2f}\n"
        f"Best Mix: {alloc_str}\n"
        f"Tue Meme Weight: {w_sr[1] * 100:.1f}%"
    )
    ax.text(0.03, 0.96, info, transform=ax.transAxes, va='top', fontsize=8.3,
            color='#ffea00', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#ffea00', alpha=0.88))


# ==============================================================================
# 2. Alien Astrolabe: Archimedean Polar Spiral Chronology
# ==============================================================================
def plot_polar_astrolabe(ax, dates, y):
    day_offset = (
        dates - dates[0]).days.values.astype(float) + float(dates[0].dayofweek)
    theta = day_offset * (2.0 * np.pi / 7.0)
    r = 1.0 + day_offset / 7.0
    x_log = np.log1p(y)

    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)

    ax.plot(theta, r, color='#4cc9f0', lw=0.55, alpha=0.30)
    sizes = 10.0 + 3.2 * (x_log ** 2.2)
    ax.scatter(theta, r, c=x_log, cmap='plasma', s=sizes,
               alpha=0.9, edgecolors='white', lw=0.25, zorder=4)

    peak_idx = int(np.argmax(y))
    ax.scatter([theta[peak_idx]], [r[peak_idx]], color='#ffea00', s=230, marker='*',
               edgecolors='white', lw=0.7, zorder=6)
    ax.annotate(f"Peak {int(y[peak_idx])}\n({dates[peak_idx].strftime('%m-%d %a')})",
                xy=(theta[peak_idx], r[peak_idx]),
                xytext=(theta[peak_idx] + 0.55, r[peak_idx] + 8.0),
                color='#ffea00', fontsize=8.5, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#ffea00', lw=1.2))

    angles = np.arange(7) * (2.0 * np.pi / 7.0)
    ax.set_xticks(angles)
    ax.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                       fontsize=9.5, fontweight='bold', color='#00f5d4')
    ax.set_rlabel_position(135)
    ax.tick_params(axis='y', colors='#adb5bd', labelsize=7.5)
    ax.grid(color='#4cc9f0', alpha=0.18)
    ax.set_title('Polar Cosmic Astrolabe (Archimedean 7D Spiral)',
                 color='#00f5d4', fontweight='bold', pad=14)


# ==============================================================================
# 3. Electrical Engineering: Cross-Spectral Magnitude-Squared Coherence
# ==============================================================================
def plot_spectral_coherence(ax, df):
    c_log = np.log1p(df['clones'].values.astype(float))
    u_log = np.log1p(df['uniques'].values.astype(float))
    v_log = np.log1p(df['views'].values.astype(float))

    # nperseg=56 (=8*7) 让 7.0d 频率精确落在整 bin 上消除栅栏泄漏
    nperseg = min(56, max(14, len(c_log) // 4))
    noverlap = (nperseg * 3) // 4

    f_cu, coh_cu = coherence(c_log, u_log, fs=1.0,
                             nperseg=nperseg, noverlap=noverlap)
    mask = f_cu > 0.01

    ax.plot(f_cu[mask], coh_cu[mask], color='#00f5d4', lw=2.2, marker='o', ms=3.5,
            label='Clones ↔ Unique Cloners')
    ax.fill_between(f_cu[mask], 0.0, coh_cu[mask], color='#00f5d4', alpha=0.14)

    if np.std(v_log) > 1e-6:
        f_cv, coh_cv = coherence(c_log, v_log, fs=1.0,
                                 nperseg=nperseg, noverlap=noverlap)
        ax.plot(f_cv[mask], coh_cv[mask], color='#ff00ff', lw=1.9, ls='--', marker='s', ms=3.0,
                label='Clones ↔ Web Views')

    f_7d = 1.0 / 7.0
    f_35d = 2.0 / 7.0
    ax.axvline(f_7d, color='#39ff14', ls=':', lw=1.6,
               label='7.0d Workweek (0.143 cpd)')
    ax.axvline(f_35d, color='#ffbe0b', ls=':', lw=1.3,
               label='3.5d Harmonic (0.286 cpd)')

    coh_at_7d = float(np.interp(f_7d, f_cu[mask], coh_cu[mask]))
    coh_v_7d = float(np.interp(f_7d, f_cv[mask], coh_cv[mask])) if np.std(
        v_log) > 1e-6 else 0.0

    ax.set_ylim(-0.03, 1.05)
    ax.set_title('Cross-Spectral Coherence γ²(f) (Phase-Lock Resonance)',
                 color='#00f5d4', fontweight='bold')
    ax.set_xlabel('Frequency f (Cycles / Day)')
    ax.set_ylabel('Magnitude-Squared Coherence γ²(f)')
    ax.legend(loc='upper right', fontsize=7.8, framealpha=0.85)
    ax.grid(alpha=0.15)

    info = (
        f"7.0d Coherence (C↔U): {coh_at_7d:.3f}\n"
        f"7.0d Coherence (C↔V): {coh_v_7d:.3f}\n"
        f"FFT Window / Overlap: {nperseg}d / {noverlap}d"
    )
    ax.text(0.03, 0.05, info, transform=ax.transAxes, va='bottom', fontsize=8.3,
            color='#00f5d4', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#00f5d4', alpha=0.88))


# ==============================================================================
# 4. Linear Algebra: SSA Hankel SVD & w-Correlation Matrix
# ==============================================================================
def plot_ssa_wcorr(ax, y):
    x = np.log1p(y)
    xc = x - np.mean(x)
    n = len(xc)
    L = min(28, n // 3)
    K = n - L + 1

    # 构建 L x K Hankel 轨迹矩阵
    H = np.column_stack([xc[j:j + L] for j in range(K)])
    U, S, Vt = np.linalg.svd(H, full_matrices=False)

    n_modes = min(10, len(S))
    modes = np.zeros((n_modes, n))
    mode_labels = []
    freqs = np.fft.rfftfreq(n, d=1.0)

    for m in range(n_modes):
        X_m = S[m] * np.outer(U[:, m], Vt[m, :])
        rec = np.zeros(n)
        for t in range(n):
            i_start = max(0, t - K + 1)
            i_end = min(L - 1, t)
            vals = [X_m[i, t - i] for i in range(i_start, i_end + 1)]
            rec[t] = float(np.mean(vals))
        modes[m] = rec

        # 识别该本征模主导周期
        spec = np.abs(np.fft.rfft(rec - np.mean(rec)))
        if len(spec) > 1:
            dom_idx = int(np.argmax(spec[1:]) + 1)
            dom_f = freqs[dom_idx]
            per_str = f'{1.0 / dom_f:.1f}d' if dom_f > 0 else '∞'
        else:
            per_str = 'Trend'
        mode_labels.append(f'M{m + 1}({per_str})')

    # 计算 SSA 加权正交相关矩阵 (w-Correlation)
    w = np.array([min(t + 1, L, n - t) for t in range(n)], dtype=float)
    w_corr = np.zeros((n_modes, n_modes))
    norms = np.sqrt(np.sum(w[None, :] * (modes ** 2), axis=1))
    for i in range(n_modes):
        for j in range(n_modes):
            denom = max(norms[i] * norms[j], 1e-12)
            w_corr[i, j] = abs(float(np.sum(w * modes[i] * modes[j]))) / denom

    im = ax.imshow(w_corr, cmap='inferno', vmin=0.0, vmax=1.0, aspect='auto')
    cbar = plt.colorbar(im, ax=ax, shrink=0.88, pad=0.02)
    cbar.set_label('SSA |w-Correlation|', fontsize=8.5)

    for i in range(n_modes):
        for j in range(n_modes):
            val = w_corr[i, j]
            if i == j or val >= 0.25:
                c_txt = 'black' if val > 0.65 else 'white'
                ax.text(j, i, f'{val:.2f}', ha='center',
                        va='center', color=c_txt, fontsize=7.2)

    var_top = float(np.sum(S[:n_modes] ** 2) /
                    max(np.sum(S ** 2), 1e-12) * 100.0)
    ax.set_xticks(np.arange(n_modes))
    ax.set_yticks(np.arange(n_modes))
    ax.set_xticklabels(mode_labels, rotation=38, ha='right', fontsize=7.8)
    ax.set_yticklabels(mode_labels, fontsize=7.8)
    ax.set_title(f'SSA Hankel SVD w-Correlation Matrix (Top-{n_modes}: {var_top:.1f}% Energy)',
                 color='#ff00ff', fontweight='bold')


# ==============================================================================
# 5. Manifold Geometry: PCA Biplot of Weekly Civilizations
# ==============================================================================
def plot_weekly_pca_biplot(ax, week_mat):
    X_log = np.log1p(week_mat.values)
    X_std = StandardScaler().fit_transform(X_log)

    pca = PCA(n_components=2)
    scores = pca.fit_transform(X_std)
    loadings = pca.components_.T

    week_labels = list(week_mat.index)
    t_idx = np.linspace(0.0, 1.0, len(week_labels))

    sc = ax.scatter(scores[:, 0], scores[:, 1], c=t_idx, cmap='plasma', s=55,
                    edgecolors='white', lw=0.6, alpha=0.9, zorder=4)

    # 标出最偏离中心的 4 个异变周
    dist_center = np.linalg.norm(scores, axis=1)
    top_outliers = np.argsort(dist_center)[-4:]
    for idx in top_outliers:
        short_w = week_labels[idx].split('-')[1]
        ax.annotate(short_w, (scores[idx, 0], scores[idx, 1]),
                    xytext=(5, 4), textcoords='offset points',
                    color='#ffea00', fontsize=8.5, fontweight='bold')

    # 画 Mon ~ Sun 七个星期载荷方向箭头
    max_s = max(float(np.max(np.abs(scores))), 1.0)
    arrow_scale = max_s * 0.85 / \
        max(float(np.max(np.linalg.norm(loadings, axis=1))), 1e-6)
    day_names = list(week_mat.columns)

    for i, d_name in enumerate(day_names):
        lx, ly = loadings[i, 0] * arrow_scale, loadings[i, 1] * arrow_scale
        c_arr = '#39ff14' if d_name == 'Fri' else (
            '#ff006e' if d_name == 'Tue' else '#00f5d4')
        ax.arrow(0.0, 0.0, lx, ly, color=c_arr, width=0.025, head_width=0.14,
                 length_includes_head=True, alpha=0.88, zorder=5)
        ax.text(lx * 1.12, ly * 1.12, d_name, color=c_arr, fontsize=8.8, fontweight='bold',
                ha='center', va='center', zorder=6)

    evr = pca.explained_variance_ratio_ * 100.0
    ax.axhline(0.0, color='#adb5bd', ls=':', lw=0.8, alpha=0.4)
    ax.axvline(0.0, color='#adb5bd', ls=':', lw=0.8, alpha=0.4)
    ax.set_title(f'Weekly PCA Biplot ({len(week_labels)} Weeks × 7 Weekday Loadings)',
                 color='#ffbe0b', fontweight='bold')
    ax.set_xlabel(f'PC1 ({evr[0]:.1f}% Variance)')
    ax.set_ylabel(f'PC2 ({evr[1]:.1f}% Variance)')
    ax.grid(alpha=0.15)


# ==============================================================================
# 6. Conjugate Bayesian Inference: Gamma-Poisson Posterior Rate Bells
# ==============================================================================
def plot_bayesian_posteriors(ax, df):
    y = df['clones'].values.astype(float)
    dow = df.index.dayofweek.values

    cohorts = [
        ('Weekend (Sat–Sun)', dow >= 5, '#00bbf9'),
        ('Midweek (Mon/Wed/Thu)', np.isin(dow, [0, 2, 3]), '#ffbe0b'),
        ('Friday (Fri)', dow == 4, '#39ff14'),
        ('Tuesday (Tue incl. 859)', dow == 1, '#ff006e'),
    ]

    alpha0, beta0 = 1.0, 0.05  # 弱信息先验
    post_params = []
    mus, sds = [], []

    for label, mask, color in cohorts:
        sub = y[mask]
        a_post = alpha0 + float(np.sum(sub))
        b_post = beta0 + float(len(sub))
        mu_p = a_post / b_post
        sd_p = np.sqrt(a_post) / b_post
        post_params.append((label, a_post, b_post, mu_p, sd_p, color))
        mus.append(mu_p)
        sds.append(sd_p)

    x_lo = max(0.0, min(m - 5.0 * s for m, s in zip(mus, sds)))
    x_hi = max(m + 5.0 * s for m, s in zip(mus, sds))
    x_grid = np.linspace(x_lo, x_hi, 600)

    for label, a_p, b_p, mu_p, sd_p, color in post_params:
        pdf = gamma_dist.pdf(x_grid, a=a_p, scale=1.0 / b_p)
        ax.plot(x_grid, pdf, color=color, lw=2.2,
                label=f'{label}: μ={mu_p:.1f}±{sd_p:.1f}')
        ax.fill_between(x_grid, 0.0, pdf, color=color, alpha=0.18)

    # 蒙特卡洛采样计算准确贝叶斯胜率
    rng = np.random.default_rng(42)
    s_wknd = rng.gamma(post_params[0][1], 1.0 / post_params[0][2], size=100000)
    s_mid = rng.gamma(post_params[1][1], 1.0 / post_params[1][2], size=100000)
    s_fri = rng.gamma(post_params[2][1], 1.0 / post_params[2][2], size=100000)

    p_fri_gt_wknd = float(np.mean(s_fri > s_wknd) * 100.0)
    p_fri_gt_mid = float(np.mean(s_fri > s_mid) * 100.0)
    lift_ratio = s_fri / np.maximum(s_wknd, 1e-6)
    lift_med = float(np.median(lift_ratio))
    lift_lo, lift_hi = np.percentile(lift_ratio, [2.5, 97.5])

    ax.set_title('Conjugate Bayesian Inference (Gamma-Poisson Rate Posteriors)',
                 color='#39ff14', fontweight='bold')
    ax.set_xlabel('Latent True Arrival Rate λ (Clones / Day)')
    ax.set_ylabel('Posterior Probability Density')
    ax.legend(loc='upper right', fontsize=7.8, framealpha=0.85)
    ax.grid(alpha=0.15)

    info = (
        f"P(λ_Fri > λ_Weekend): {p_fri_gt_wknd:.3f}%\n"
        f"P(λ_Fri > λ_Midweek): {p_fri_gt_mid:.2f}%\n"
        f"Fri/Wknd Lift (95% CI): {lift_med:.2f}x [{lift_lo:.2f}x, {lift_hi:.2f}x]"
    )
    ax.text(0.98, 0.68, info, transform=ax.transAxes, ha='right', va='top', fontsize=8.1,
            color='#39ff14', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#39ff14', alpha=0.88))


def main():
    print('🏛️ Pod 042: Erecting Imperial Portfolio & Spectral Pantheon (v13.0)...')
    df = load_bunker_data()
    dates = df.index
    y = df['clones'].values.astype(float)
    week_mat = build_complete_week_matrix(df)

    fig = plt.figure(figsize=(20, 18), facecolor='#04060a')

    ax1 = fig.add_subplot(3, 2, 1, facecolor='#080c14')
    ax2 = fig.add_subplot(3, 2, 2, projection='polar', facecolor='#080c14')
    ax3 = fig.add_subplot(3, 2, 3, facecolor='#080c14')
    ax4 = fig.add_subplot(3, 2, 4, facecolor='#080c14')
    ax5 = fig.add_subplot(3, 2, 5, facecolor='#080c14')
    ax6 = fig.add_subplot(3, 2, 6, facecolor='#080c14')

    plot_markowitz_frontier(ax1, week_mat)
    plot_polar_astrolabe(ax2, dates, y)
    plot_spectral_coherence(ax3, df)
    plot_ssa_wcorr(ax4, y)
    plot_weekly_pca_biplot(ax5, week_mat)
    plot_bayesian_posteriors(ax6, df)

    fig.suptitle(
        'Bunker Imperial Pantheon (Markowitz 7D + Polar Astrolabe + Coherence + SSA SVD + PCA Biplot + Bayesian)',
        color='#ffea00', fontsize=15.4, fontweight='bold', y=0.975
    )

    fig.subplots_adjust(left=0.06, right=0.955, top=0.92,
                        bottom=0.055, hspace=0.35, wspace=0.24)
    out_dir = os.path.dirname(OUTPUT_IMAGE)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    plt.savefig(OUTPUT_IMAGE, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'✅ Imperial Pantheon sealed at: {OUTPUT_IMAGE}')


if __name__ == '__main__':
    main()
