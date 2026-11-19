import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Ellipse
from scipy.stats import chisquare
from sklearn.mixture import GaussianMixture


def estimate_lyapunov(series, max_step=8):
    """Rosenstein 延迟相空间最大 Lyapunov 指数估算"""
    ts = np.asarray(series, dtype=float)
    if len(ts) < 25:
        return 0.0
    pts = np.column_stack([ts[:-1], ts[1:]])
    n = len(pts)
    min_sep = 4
    divs = [[] for _ in range(max_step)]

    for i in range(n - max_step):
        dists = np.linalg.norm(pts - pts[i], axis=1)
        valid = np.ones(n, dtype=bool)
        valid[max(0, i - min_sep):min(n, i + min_sep + 1)] = False
        valid[n - max_step:] = False
        if not np.any(valid):
            continue
        masked = np.where(valid, dists, np.inf)
        j = int(np.argmin(masked))
        d0 = masked[j]
        if d0 < 1e-6:
            continue
        for k in range(1, max_step + 1):
            if i + k < n and j + k < n:
                dk = np.linalg.norm(pts[i + k] - pts[j + k])
                if dk > 1e-8:
                    divs[k - 1].append(np.log(dk / d0))

    means = [np.mean(v) for v in divs if len(v) >= 5]
    if len(means) < 3:
        return 0.0
    ks = np.arange(1, len(means) + 1, dtype=float)
    return float(np.polyfit(ks, means, 1)[0])


def execute_singularity_oracle():
    print("🤖 Pod 042: 启动‘奇点先知与混沌审计协议’...")

    clone_path = 'ghrs-data/clones_ledger.csv'
    if not os.path.exists(clone_path):
        print("⚠️ clones_ledger.csv 缺失，取消分析。")
        return

    df = pd.read_csv(clone_path)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date']).copy()
    df['clones'] = pd.to_numeric(df['clones'], errors='coerce').fillna(0)

    if df.empty:
        print("⚠️ 账本为空，取消分析。")
        return

    df = df.groupby('date', as_index=False)['clones'].sum()
    full_idx = pd.date_range(df['date'].min(), df['date'].max(), freq='D')
    df = df.set_index('date').reindex(full_idx, fill_value=0)
    df = df.rename_axis('date').reset_index()
    df['cum_clones'] = df['clones'].cumsum()

    plt.style.use('dark_background')
    fig = plt.figure(figsize=(20, 13))
    fig.suptitle(
        'Bunker Singularity Oracle (Benford + Chaos + Markov + Monte Carlo)',
        color='#ff00ff', fontsize=18, fontweight='bold'
    )
    gs = fig.add_gridspec(2, 2, hspace=0.28, wspace=0.22)

    # ==================================================
    # Panel 1: 本福特定律首位数字法务审计 (Benford's Law)
    # ==================================================
    ax1 = fig.add_subplot(gs[0, 0])
    pos = df.loc[df['clones'] >= 1, 'clones'].astype(int)
    digits = np.arange(1, 10)
    benford_p = np.log10(1.0 + 1.0 / digits)

    if len(pos) >= 10:
        first_digits = pos.apply(lambda v: int(str(v)[0]))
        counts = first_digits.value_counts().reindex(digits, fill_value=0)
        obs = counts.to_numpy(dtype=float)
        obs_pct = obs / obs.sum() * 100.0
        exp_pct = benford_p * 100.0

        f_exp = benford_p * obs.sum()
        f_exp = f_exp * (obs.sum() / f_exp.sum())
        chi2_stat, chi2_p = chisquare(obs, f_exp=f_exp)
        benford_mad = float(np.mean(np.abs(obs_pct - exp_pct)) / 100.0)
    else:
        obs_pct = np.zeros(9)
        exp_pct = benford_p * 100.0
        chi2_stat, chi2_p, benford_mad = 0.0, 1.0, 0.0

    ax1.bar(digits, obs_pct, color='#00ffcc', alpha=0.65,
            edgecolor='white', label='Observed Leading Digit %')
    ax1.plot(digits, exp_pct, color='#ff00ff', marker='o', lw=2.2,
             label="Benford's Law Theoretical %")

    verdict = 'Natural Conformity' if benford_mad < 0.025 else 'Synthetic Spike'
    hud1 = (
        f"Chi-Square: χ² = {chi2_stat:.2f} (p={chi2_p:.3f})\n"
        f"Benford MAD: {benford_mad:.4f}\n"
        f"Audit Verdict: {verdict}"
    )
    ax1.text(
        0.97, 0.95, hud1, transform=ax1.transAxes, va='top', ha='right',
        fontsize=9, color='#00ffcc', family='monospace',
        bbox=dict(boxstyle='round,pad=0.4', fc='#000000',
                  ec='#00ffcc', alpha=0.8)
    )
    ax1.set_title("Benford's Law Forensic Audit (Leading Digit)",
                  color='#00ffcc', pad=12)
    ax1.set_xticks(digits)
    ax1.set_xlabel('First Digit (1 - 9)')
    ax1.set_ylabel('Frequency (%)')
    ax1.legend(loc='upper left', fontsize='small')
    ax1.grid(alpha=0.15)

    # ==================================================
    # Panel 2: 庞加莱相空间吸引子 + Lyapunov 混沌指数
    # ==================================================
    ax2 = fig.add_subplot(gs[0, 1])
    log_x = np.log1p(df['clones'].to_numpy())
    x_t, x_t1 = log_x[:-1], log_x[1:]

    if len(x_t) >= 5:
        sd1 = float(np.std((x_t1 - x_t) / np.sqrt(2.0), ddof=1))
        sd2 = float(np.std((x_t1 + x_t) / np.sqrt(2.0), ddof=1))
        sd_ratio = sd1 / max(sd2, 1e-6)
        lyap = estimate_lyapunov(log_x)
        mx, my = float(np.mean(x_t)), float(np.mean(x_t1))
        lim_max = max(float(np.max(log_x)) * 1.08, 1.0)

        ax2.plot([0, lim_max], [0, lim_max], color='#666', ls='--', lw=1.2)
        ax2.plot(x_t, x_t1, color='#3498db', alpha=0.18, lw=0.8)
        t_colors = np.linspace(0, 1, len(x_t))
        sc = ax2.scatter(x_t, x_t1, c=t_colors, cmap='plasma',
                         s=28, alpha=0.8, edgecolors='none')
        ellipse = Ellipse(
            xy=(mx, my), width=4.0 * sd2, height=4.0 * sd1, angle=45,
            edgecolor='#ff00ff', fc='none', lw=2.0, ls='-',
            label='Poincaré 2σ Attractor'
        )
        ax2.add_patch(ellipse)
        ax2.set_xlim(0, lim_max)
        ax2.set_ylim(0, lim_max)
        cbar = fig.colorbar(sc, ax=ax2, fraction=0.046, pad=0.03)
        cbar.set_label('Time Flow (Apr -> Now)', fontsize=8)
    else:
        sd1, sd2, sd_ratio, lyap = 0.0, 0.0, 0.0, 0.0

    chaos_tag = 'Chaotic' if lyap > 0.05 else 'Stable Attractor'
    hud2 = (
        f"SD1 (Short-Term): {sd1:.2f}\n"
        f"SD2 (Long-Term):  {sd2:.2f}\n"
        f"SD1 / SD2 Ratio:  {sd_ratio:.2f}\n"
        f"Lyapunov λ₁: {lyap:+.3f} ({chaos_tag})"
    )
    ax2.text(
        0.03, 0.96, hud2, transform=ax2.transAxes, va='top', ha='left',
        fontsize=8.8, color='#ff00ff', family='monospace',
        bbox=dict(boxstyle='round,pad=0.4', fc='#000000',
                  ec='#ff00ff', alpha=0.8)
    )
    ax2.set_title('Poincaré Chaos Phase Portrait (Log Space)',
                  color='#ff00ff', pad=12)
    ax2.set_xlabel('Log(Clones[t] + 1)')
    ax2.set_ylabel('Log(Clones[t+1] + 1)')
    ax2.legend(loc='lower right', fontsize='small')
    ax2.grid(alpha=0.15)

    # ==================================================
    # Panel 3: GMM 3态马尔可夫状态转移矩阵
    # ==================================================
    ax3 = fig.add_subplot(gs[1, 0])
    state_names = ['Dormant', 'Cruise', 'Blitz']
    trans_prob = np.zeros((3, 3))
    trans_cnt = np.zeros((3, 3), dtype=int)
    steady = np.array([1 / 3, 1 / 3, 1 / 3])

    if len(df) >= 15 and df['clones'].nunique() >= 3:
        gmm = GaussianMixture(n_components=3, random_state=42)
        raw_labels = gmm.fit_predict(log_x.reshape(-1, 1))
        order_idx = np.argsort(gmm.means_.ravel())
        remap = {old: new for new, old in enumerate(order_idx)}
        states = np.array([remap[s] for s in raw_labels])

        for s_from, s_to in zip(states[:-1], states[1:]):
            trans_cnt[s_from, s_to] += 1

        row_sums = trans_cnt.sum(axis=1, keepdims=True)
        trans_prob = np.divide(
            trans_cnt, row_sums,
            out=np.eye(3), where=row_sums > 0
        )

        pi = np.array([1 / 3, 1 / 3, 1 / 3])
        for _ in range(100):
            pi = pi @ trans_prob
        steady = pi

    im = ax3.imshow(trans_prob * 100.0, cmap='YlGnBu', vmin=0, vmax=100)
    ax3.set_xticks(range(3))
    ax3.set_yticks(range(3))
    ax3.set_xticklabels([f'To: {s}' for s in state_names], fontsize=10)
    ax3.set_yticklabels([f'From: {s}' for s in state_names], fontsize=10)

    for i in range(3):
        for j in range(3):
            p_val = trans_prob[i, j] * 100.0
            txt_color = 'black' if p_val > 55 else 'white'
            ax3.text(
                j, i, f"{p_val:.1f}%\n(n={trans_cnt[i, j]})",
                ha='center', va='center', color=txt_color,
                fontsize=10, fontweight='bold'
            )

    steady_str = (
        f"Equilibrium π: Dormant {steady[0]*100:.0f}% | "
        f"Cruise {steady[1]*100:.0f}% | Blitz {steady[2]*100:.0f}%"
    )
    ax3.set_title(f'GMM Markov Regime Matrix\n({steady_str})',
                  color='#33cc33', pad=10, fontsize=11)
    fig.colorbar(im, ax=ax3, fraction=0.046, pad=0.03, label='Prob (%)')

    # ==================================================
    # Panel 4: Monte Carlo Block-Bootstrap 破万倒计时预测
    # ==================================================
    ax4 = fig.add_subplot(gs[1, 1])
    current_total = float(df['cum_clones'].iloc[-1])
    target = float(((int(current_total) // 5000) + 1) * 5000)
    if target - current_total < 300:
        target += 5000

    recent_pool = df['clones'].tail(min(120, len(df))).to_numpy()
    horizon = 120
    n_sims = 1000
    block_len = 7
    rng = np.random.default_rng(42)

    sim_paths = np.zeros((n_sims, horizon))
    max_start = max(1, len(recent_pool) - block_len + 1)
    n_blocks = int(np.ceil(horizon / block_len))

    for s_idx in range(n_sims):
        starts = rng.integers(0, max_start, size=n_blocks)
        sampled = np.concatenate(
            [recent_pool[st:st + block_len] for st in starts]
        )[:horizon]
        sim_paths[s_idx] = current_total + np.cumsum(sampled)

    p10 = np.percentile(sim_paths, 10, axis=0)
    p25 = np.percentile(sim_paths, 25, axis=0)
    p50 = np.percentile(sim_paths, 50, axis=0)
    p75 = np.percentile(sim_paths, 75, axis=0)
    p90 = np.percentile(sim_paths, 90, axis=0)

    last_date = df['date'].iloc[-1]
    future_dates = pd.date_range(
        last_date + pd.Timedelta(days=1), periods=horizon, freq='D'
    )
    hist_tail = df.tail(min(120, len(df)))

    ax4.plot(hist_tail['date'], hist_tail['cum_clones'],
             color='#3498db', lw=2.5, label='Historical Cumulative')

    for k in range(min(25, n_sims)):
        ax4.plot(future_dates, sim_paths[k], color='#00ffcc',
                 alpha=0.06, lw=0.8)

    ax4.fill_between(future_dates, p10, p90, color='#f18f01',
                     alpha=0.16, label='80% Confidence (P10-P90)')
    ax4.fill_between(future_dates, p25, p75, color='#f18f01',
                     alpha=0.28, label='50% Confidence (P25-P75)')
    ax4.plot(future_dates, p50, color='#33cc33', lw=2.4, ls='--',
             label='Median Forecast (P50)')
    ax4.axhline(target, color='yellow', ls=':', lw=1.6,
                label=f'Milestone: {int(target):,}')

    hit_p50 = np.where(p50 >= target)[0]
    hit_p10 = np.where(p10 >= target)[0]
    hit_p90 = np.where(p90 >= target)[0]

    if len(hit_p50) > 0:
        eta_idx = int(hit_p50[0])
        eta_date = future_dates[eta_idx]
        ax4.scatter([eta_date], [target], color='yellow', marker='*',
                    s=180, zorder=6)
        eta_str = f"{eta_date.strftime('%Y-%m-%d')} (+{eta_idx + 1}d)"
    else:
        eta_str = f">{horizon} days"

    low_str = (
        future_dates[int(hit_p90[0])].strftime('%m-%d')
        if len(hit_p90) > 0 else f">{horizon}d"
    )
    high_str = (
        future_dates[int(hit_p10[0])].strftime('%m-%d')
        if len(hit_p10) > 0 else f">{horizon}d"
    )

    hud4 = (
        f"Current Total: {int(current_total):,}\n"
        f"Next Target:   {int(target):,}\n"
        f"P50 Median ETA: {eta_str}\n"
        f"80% CI Window:  {low_str} ~ {high_str}"
    )
    ax4.text(
        0.03, 0.96, hud4, transform=ax4.transAxes, va='top', ha='left',
        fontsize=8.8, color='yellow', family='monospace',
        bbox=dict(boxstyle='round,pad=0.4', fc='#000000',
                  ec='yellow', alpha=0.8)
    )
    ax4.set_title('Monte Carlo Block-Bootstrap Oracle (1,000 Paths)',
                  color='#f18f01', pad=12)
    ax4.set_ylabel('Total Clones')
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%y-%m'))
    ax4.tick_params(axis='x', rotation=25)
    ax4.legend(loc='lower right', fontsize='x-small')
    ax4.grid(alpha=0.15)

    plt.tight_layout(rect=[0, 0.02, 1, 0.94])
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/bunker_singularity_oracle.png', dpi=120)
    plt.close(fig)
    print("✅ 地堡第五神兽 bunker_singularity_oracle.png 渲染完毕！")


if __name__ == "__main__":
    execute_singularity_oracle()
