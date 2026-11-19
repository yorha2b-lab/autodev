import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.signal import periodogram
from scipy.stats import mannwhitneyu, theilslopes, kendalltau
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def compute_hurst(ts):
    """R/S 重标极差法估算 Hurst 分形指数"""
    ts = np.asarray(ts, dtype=float)
    n = len(ts)
    if n < 20:
        return 0.5

    max_lag = max(10, n // 2)
    lags = [k for k in [6, 8, 12, 16, 24, 32, 48, 64, 96] if k <= max_lag]
    if len(lags) < 3:
        lags = np.unique(np.linspace(4, max_lag, 6, dtype=int))

    valid_lags = []
    rs_vals = []
    for lag in lags:
        n_chunks = n // lag
        if n_chunks < 1:
            continue
        chunk_rs = []
        for i in range(n_chunks):
            sub = ts[i * lag:(i + 1) * lag]
            dev = sub - np.mean(sub)
            cum_dev = np.cumsum(dev)
            r = np.max(cum_dev) - np.min(cum_dev)
            s = np.std(sub, ddof=1)
            if s > 1e-8 and r > 0:
                chunk_rs.append(r / s)
        if chunk_rs:
            valid_lags.append(lag)
            rs_vals.append(np.mean(chunk_rs))

    if len(valid_lags) < 2:
        return 0.5
    slope = np.polyfit(np.log(valid_lags), np.log(rs_vals), 1)[0]
    return float(np.clip(slope, 0.0, 1.0))


def compute_gini(arr):
    """离散基尼系数，兼容 NumPy 1.x / 2.x"""
    s = np.sort(np.asarray(arr, dtype=float))
    total = np.sum(s)
    n = len(s)
    if n == 0 or total <= 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float(np.sum((2 * idx - n - 1) * s) / (n * total))


def execute_chronos_quantum():
    print("🤖 Pod 042: 启动‘超时空傅里叶与分形混沌协议’...")

    clone_path = 'ghrs-data/clones_ledger.csv'
    if not os.path.exists(clone_path):
        print("⚠️ clones_ledger.csv 缺失，取消分析。")
        return

    df = pd.read_csv(clone_path).rename(columns={'uniques': 'unique_cloners'})
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date']).copy()

    for col in ['clones', 'unique_cloners']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if df.empty:
        print("⚠️ 账本为空，取消分析。")
        return

    # 补全连续日历，保证 FFT 频率和 Hurst 步长物理对齐
    df = df.groupby('date', as_index=False)[['clones', 'unique_cloners']].sum()
    full_idx = pd.date_range(df['date'].min(), df['date'].max(), freq='D')
    df = df.set_index('date').reindex(
        full_idx, fill_value=0).rename_axis('date')
    df = df.reset_index()

    df['weekday'] = df['date'].dt.dayofweek
    df['is_weekend'] = df['weekday'] >= 5

    plt.style.use('dark_background')
    fig = plt.figure(figsize=(20, 13))
    fig.suptitle(
        'Bunker Chronos Quantum Telemetry (FFT + Fractal + Dual-Court)',
        color='#00ffcc', fontsize=18, fontweight='bold'
    )
    gs = fig.add_gridspec(2, 2, hspace=0.28, wspace=0.22)

    # ==================================================
    # Panel 1: FFT 快速傅里叶功率谱 + 工作日显著性检验
    # ==================================================
    ax1 = fig.add_subplot(gs[0, 0])
    sig = np.log1p(df['clones'].to_numpy())
    sig_centered = sig - np.mean(sig)
    freqs, psd = periodogram(sig_centered, fs=1.0)

    mask = (freqs > 0) & ((1.0 / np.where(freqs > 0, freqs, 1.0)) <= 35.0)
    periods = 1.0 / freqs[mask]
    powers = psd[mask]
    order = np.argsort(periods)
    periods, powers = periods[order], powers[order]

    ax1.plot(periods, powers, color='#00ffcc',
             lw=1.8, label='PSD (Log1p Clones)')
    ax1.fill_between(periods, powers, color='#00ffcc', alpha=0.18)
    ax1.axvline(7.0, color='#ff00ff', ls='--', lw=1.4, label='7.0d Workweek')
    ax1.axvline(3.5, color='#f39c12', ls=':', lw=1.2, label='3.5d Harmonic')

    dom_period = 0.0
    if len(powers) > 0:
        peak_i = int(np.argmax(powers))
        dom_period = float(periods[peak_i])
        ax1.scatter([dom_period], [powers[peak_i]],
                    color='yellow', s=70, zorder=5)
        ax1.annotate(
            f'Peak: {dom_period:.1f}d',
            xy=(dom_period, powers[peak_i]),
            xytext=(10, 6),
            textcoords='offset points',
            color='yellow', fontsize=9, fontweight='bold'
        )

    wk_day = df.loc[~df['is_weekend'], 'clones']
    wk_end = df.loc[df['is_weekend'], 'clones']
    mw_p = 1.0
    wk_ratio = 1.0
    if len(wk_day) >= 3 and len(wk_end) >= 3:
        _, mw_p = mannwhitneyu(wk_day, wk_end, alternative='two-sided')
        wk_ratio = float(wk_day.mean() / max(wk_end.mean(), 1e-6))

    hud1 = (
        f"Dominant Period: {dom_period:.1f} days\n"
        f"Weekday / Weekend: {wk_ratio:.2f}x\n"
        f"Mann-Whitney U: p = {mw_p:.3f}"
    )
    ax1.text(
        0.97, 0.95, hud1, transform=ax1.transAxes, va='top', ha='right',
        fontsize=9, color='#00ffcc', family='monospace',
        bbox=dict(boxstyle='round,pad=0.4',
                  fc='#000000', ec='#00ffcc', alpha=0.8)
    )
    ax1.set_title('Chronos Spectrum (FFT Periodogram)',
                  color='#00ffcc', pad=12)
    ax1.set_xlabel('Period (Days)')
    ax1.set_ylabel('Spectral Power')
    ax1.set_xlim(2, 32)
    ax1.legend(loc='upper left', fontsize='small')
    ax1.grid(alpha=0.15)

    # ==================================================
    # Panel 2: 周一到周日极坐标生物钟雷达图（中位数抗极值）
    # ==================================================
    ax2 = fig.add_subplot(gs[0, 1], projection='polar')
    ax2.set_facecolor('#0d1117')
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    med_clones = [df.loc[df['weekday'] == d, 'clones'].median()
                  for d in range(7)]
    med_cloners = [df.loc[df['weekday'] == d, 'unique_cloners'].median()
                   for d in range(7)]

    angles = np.linspace(0, 2 * np.pi, 7, endpoint=False).tolist()
    angles += angles[:1]
    c_vals = med_clones + med_clones[:1]
    u_vals = med_cloners + med_cloners[:1]

    ax2.set_theta_offset(np.pi / 2)
    ax2.set_theta_direction(-1)
    ax2.plot(angles, c_vals, color='#33cc33', lw=2.2, label='Median Clones')
    ax2.fill(angles, c_vals, color='#33cc33', alpha=0.22)
    ax2.plot(angles, u_vals, color='#ff00ff', lw=2.0,
             ls='--', label='Median Unique Cloners')
    ax2.fill(angles, u_vals, color='#ff00ff', alpha=0.14)

    ax2.set_xticks(angles[:-1])
    ax2.set_xticklabels(day_names, fontsize=11,
                        fontweight='bold', color='white')
    ax2.grid(color='#444', alpha=0.5)
    ax2.set_title('Circadian Weekday Radar (Median Activity)',
                  color='#33cc33', pad=22)
    ax2.legend(loc='upper right', bbox_to_anchor=(
        1.22, 1.12), fontsize='small')

    # ==================================================
    # Panel 3: 洛伦兹曲线 + 基尼系数（流量贫富分化度）
    # ==================================================
    ax3 = fig.add_subplot(gs[1, 0])
    sorted_clones = np.sort(df['clones'].to_numpy())
    gini = compute_gini(sorted_clones)
    n_days = len(sorted_clones)
    total_sum = max(float(np.sum(sorted_clones)), 1.0)

    cum_days = np.linspace(0, 100, n_days + 1)
    cum_share = np.concatenate(
        [[0.0], np.cumsum(sorted_clones) / total_sum * 100.0])

    top10_n = max(1, int(np.ceil(n_days * 0.10)))
    top10_share = float(np.sum(sorted_clones[-top10_n:]) / total_sum * 100.0)

    ax3.plot([0, 100], [0, 100], color='#888',
             ls='--', lw=1.2, label='Uniform (Gini=0)')
    ax3.plot(cum_days, cum_share, color='#f18f01',
             lw=2.5, label=f'Lorenz (Gini={gini:.3f})')
    ax3.fill_between(cum_days, cum_share, cum_days,
                     color='#f18f01', alpha=0.18)
    ax3.scatter([90], [100 - top10_share], color='yellow', s=65, zorder=5)

    hud3 = (
        f"Gini Coefficient: {gini:.3f}\n"
        f"Top 10% Days Share: {top10_share:.1f}%\n"
        f"Bottom 90% Days Share: {100.0 - top10_share:.1f}%"
    )
    ax3.text(
        0.04, 0.94, hud3, transform=ax3.transAxes, va='top', ha='left',
        fontsize=9, color='#f18f01', family='monospace',
        bbox=dict(boxstyle='round,pad=0.4',
                  fc='#000000', ec='#f18f01', alpha=0.8)
    )
    ax3.set_title('Traffic Inequality (Lorenz Curve & Gini)',
                  color='#f18f01', pad=12)
    ax3.set_xlabel('Cumulative Days (%) [Quiet -> Busy]')
    ax3.set_ylabel('Cumulative Clones (%)')
    ax3.set_xlim(0, 100)
    ax3.set_ylim(0, 100)
    ax3.legend(loc='lower right', fontsize='small')
    ax3.grid(alpha=0.15)

    # ==================================================
    # Panel 4: 双模型联合异常法庭 + Hurst 分形 + Theil-Sen 斜率
    # ==================================================
    ax4 = fig.add_subplot(gs[1, 1])
    repeat_ratio = df['clones'] / df['unique_cloners'].replace(0, 1)
    feat_df = pd.DataFrame({
        'log_v': np.log1p(df['clones']),
        'log_u': np.log1p(df['unique_cloners']),
        'log_r': np.log1p(repeat_ratio),
    })

    if len(df) >= 10:
        X = StandardScaler().fit_transform(feat_df)
        db_labels = DBSCAN(eps=0.65, min_samples=4).fit_predict(X)
        iso_labels = IsolationForest(
            contamination=0.06, random_state=42).fit_predict(X)
        votes = (db_labels == -1).astype(int) + (iso_labels == -1).astype(int)
    else:
        votes = np.zeros(len(df), dtype=int)

    hurst_h = compute_hurst(np.log1p(df['clones'].to_numpy()))

    # 对最近 120 天（稳态基线期）算 Theil-Sen 稳健斜率与 Mann-Kendall 检验
    tail_df = df.tail(min(120, len(df))).reset_index(drop=True)
    x_days = np.arange(len(tail_df), dtype=float)
    slope_day, intercept, _, _ = theilslopes(tail_df['clones'], x_days)
    mk_tau, mk_p = kendalltau(x_days, tail_df['clones'])
    slope_week = float(slope_day * 7.0)

    normal_m = votes == 0
    warn_m = votes == 1
    both_m = votes == 2

    ax4.plot(df['date'], df['clones'], color='#2E86AB', lw=1.0, alpha=0.55)
    ax4.scatter(df.loc[normal_m, 'date'], df.loc[normal_m, 'clones'],
                color='#33cc33', s=18, alpha=0.7, label='Normal (0 Votes)')
    ax4.scatter(df.loc[warn_m, 'date'], df.loc[warn_m, 'clones'],
                color='#f39c12', marker='^', s=45, zorder=4, label='Suspect (1 Vote)')
    ax4.scatter(df.loc[both_m, 'date'], df.loc[both_m, 'clones'],
                color='#e74c3c', marker='*', s=130, zorder=5, label='Consensus Anomaly (2 Votes)')

    trend_y = intercept + slope_day * x_days
    ax4.plot(tail_df['date'], np.maximum(0, trend_y), color='#ff00ff', ls='--', lw=2.0,
             label='Theil-Sen Trend (120D)')

    ax4.set_yscale('symlog', linthresh=15)
    ax4.set_ylim(bottom=0, top=max(50, df['clones'].max() * 1.8))
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax4.tick_params(axis='x', rotation=30)

    regime = 'Persistent' if hurst_h > 0.55 else (
        'Mean-Reverting' if hurst_h < 0.45 else 'Random Walk')
    hud4 = (
        f"Hurst Exponent: H = {hurst_h:.2f} ({regime})\n"
        f"Theil-Sen (120D): {slope_week:+.2f} clones/wk\n"
        f"Mann-Kendall: τ = {mk_tau:+.2f} (p={mk_p:.3f})\n"
        f"Dual-Court Consensus: {int(both_m.sum())} days"
    )
    ax4.text(
        0.03, 0.96, hud4, transform=ax4.transAxes, va='top', ha='left',
        fontsize=8.8, color='#00ffcc', family='monospace',
        bbox=dict(boxstyle='round,pad=0.4',
                  fc='#000000', ec='#ff00ff', alpha=0.8)
    )
    ax4.set_title(
        'Dual-Court Anomaly & Fractal Regime (DBSCAN + IsoForest)', color='#ff00ff', pad=12)
    ax4.set_ylabel('Clones (Symlog)')
    ax4.legend(loc='upper right', fontsize='x-small')
    ax4.grid(alpha=0.15)

    plt.tight_layout(rect=[0, 0.02, 1, 0.94])
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/bunker_chronos_quantum.png', dpi=120)
    plt.close(fig)
    print("✅ 地堡第四神兽 bunker_chronos_quantum.png 渲染完毕！")


if __name__ == "__main__":
    execute_chronos_quantum()
