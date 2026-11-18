import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from scipy.signal import find_peaks
from scipy.stats import gaussian_kde, spearmanr


def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -50, 50)))


def load_clean(path, col_name):
    if not os.path.exists(path):
        return pd.DataFrame(columns=['date', col_name, f'{col_name}_Uniques'])

    df = pd.read_csv(path)
    if df.empty:
        return pd.DataFrame(columns=['date', col_name, f'{col_name}_Uniques'])

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date']).copy()
    df[col_name] = pd.to_numeric(
        df[col_name.lower()], errors='coerce').fillna(0)
    df[f'{col_name}_Uniques'] = pd.to_numeric(
        df['uniques'], errors='coerce').fillna(0)
    return df[['date', col_name, f'{col_name}_Uniques']]


def prepare_merged_df():
    df_c = load_clean('ghrs-data/clones_ledger.csv', 'Clones')
    df_v = load_clean('ghrs-data/views_ledger.csv', 'Views')

    df = pd.merge(df_c, df_v, on='date', how='outer').fillna(0)
    df = df.sort_values('date').reset_index(drop=True)

    if not df.empty:
        iso = df['date'].dt.isocalendar()
        df['week_key'] = iso['year'].astype(
            str) + '-W' + iso['week'].astype(str).str.zfill(2)
    return df


def peak_recon(df_all):
    if df_all.empty:
        return

    one_year_ago = df_all['date'].max() - pd.Timedelta(days=365)
    df = df_all[df_all['date'] >= one_year_ago].reset_index(drop=True)

    fig3, axes3 = plt.subplots(3, 1, figsize=(16, 14))

    # 3.1 时间序列图（Symlog 长尾缩放 + Scipy 寻峰 + MAD 异常警戒线）
    axA = axes3[0]
    axA.fill_between(df['date'], df['Clones'], alpha=0.3,
                     color='#3498db', label='Clones')
    axA.plot(df['date'], df['Clones'], color='#3498db', linewidth=1.3)

    # Scipy 信号寻峰：自动标出次级脉冲波峰
    clones_arr = df['Clones'].to_numpy()
    med = np.median(clones_arr)
    mad = np.median(np.abs(clones_arr - med))
    anomaly_line = med + 3.0 * 1.4826 * max(mad, 1.0)
    peaks, _ = find_peaks(clones_arr, height=anomaly_line,
                          distance=5, prominence=20)
    if len(peaks) > 0:
        axA.scatter(df.loc[peaks, 'date'], df.loc[peaks, 'Clones'],
                    color='yellow', marker='^', s=45, zorder=5, label='Detected Peaks (SciPy)')
    axA.axhline(y=anomaly_line, color='#00ffcc', ls=':', lw=1.1,
                alpha=0.7, label=f'MAD 3σ Threshold ({anomaly_line:.0f})')

    axA.set_yscale('symlog', linthresh=15)
    axA.yaxis.set_major_formatter(FuncFormatter(
        lambda x, _: f'{int(x)}' if x >= 0 else ''))
    axA.set_ylim(bottom=0, top=max(50, df['Clones'].max() * 2.5))

    axA_twin = axA.twinx()
    axA_twin.plot(df['date'], df['Views_Uniques'],
                  color='#e74c3c', linewidth=1.2, label='Unique Visitors')
    axA_twin.fill_between(df['date'], df['Views_Uniques'],
                          alpha=0.15, color='#e74c3c')
    axA_twin.set_ylim(bottom=0, top=max(1, df['Views_Uniques'].max() * 1.25))

    axA.set_ylabel('Clones (Symlog)', color='#3498db', fontsize=12)
    axA_twin.set_ylabel('Unique Visitors', color='#e74c3c', fontsize=12)
    axA.set_title('Bunker Signal Intensity (Peak Detection Mode | SciPy + MAD)',
                  fontsize=14, fontweight='bold', pad=15)

    lines1, labels1 = axA.get_legend_handles_labels()
    lines2, labels2 = axA_twin.get_legend_handles_labels()
    axA.legend(lines1 + lines2, labels1 + labels2,
               loc='upper left', fontsize='small')

    peak_clone_idx = df['Clones'].idxmax()
    axA.annotate(
        f'LEGEND PEAK: {int(df["Clones"].max())}',
        xy=(df.loc[peak_clone_idx, 'date'], df.loc[peak_clone_idx, 'Clones']),
        xytext=(25, 16),
        textcoords='offset points',
        arrowprops=dict(arrowstyle='->', color='yellow', lw=1.5),
        fontsize=10,
        color='yellow',
        fontweight='bold'
    )

    # 3.2 每周汇总
    axB = axes3[1]
    weekly_agg = df.groupby('week_key')[
        ['Clones', 'Clones_Uniques', 'Views_Uniques']].sum().tail(12)
    weekly_agg.plot(kind='bar', ax=axB, alpha=0.85, color=[
                    '#3498db', '#9b59b6', '#e74c3c'])
    axB.set_title('Weekly Operational Summary (Clones vs Unique Cloners vs Unique Visitors)',
                  fontsize=14, fontweight='bold')
    axB.set_xlabel('Week')
    axB.tick_params(axis='x', rotation=30)

    # 3.3 比值分析（Symlog 对数缩放，不让 859 压扁其余天）
    axC = axes3[2]
    df['ratio'] = df['Clones'] / df['Views_Uniques'].replace(0, 1)
    colors3 = ['#2ecc71' if r < 3 else '#f39c12' if r <
               5 else '#e74c3c' for r in df['ratio']]
    axC.bar(df['date'], df['ratio'], color=colors3, alpha=0.75)
    axC.axhline(y=df['ratio'].mean(), color='#9b59b6',
                ls='--', label=f'Mean: {df["ratio"].mean():.2f}')
    axC.axhline(y=df['ratio'].median(), color='#00ffcc',
                ls=':', label=f'Median: {df["ratio"].median():.2f}')
    axC.set_yscale('symlog', linthresh=5)
    axC.yaxis.set_major_formatter(FuncFormatter(
        lambda x, _: f'{int(x)}' if x >= 0 else ''))
    axC.set_ylim(bottom=0, top=max(10, df['ratio'].max() * 1.8))
    axC.set_title('Clones / Unique Visitor Ratio (Symlog | High Ratio = Bots / CI)',
                  fontsize=14, fontweight='bold')
    axC.legend()

    plt.tight_layout()
    plt.savefig('plots/bunker_peak_recon.png', dpi=100)
    plt.close(fig3)


def intelligence_grid(df_all):
    if df_all.empty:
        return

    one_year_ago = df_all['date'].max() - pd.Timedelta(days=365)
    df = df_all[df_all['date'] >= one_year_ago].reset_index(drop=True)

    weekly = df.groupby('week_key').agg({
        'Clones': 'sum',
        'Clones_Uniques': 'sum',
        'Views_Uniques': 'sum',
        'date': ['min', 'max']
    }).reset_index()
    weekly.columns = ['week', 'clones', 'unique_cloners',
                      'unique_visitors', 'start_date', 'end_date']
    weekly = weekly.sort_values('start_date').reset_index(drop=True)

    fig2, axes = plt.subplots(3, 2, figsize=(16, 14))
    fig2.suptitle('Bunker Strategic Analytics - Intelligence Grid',
                  color='#33cc33', fontsize=20)

    # 1. Daily Clone Trend (Symlog + EWMA + 布林带 2σ 上轨)
    ax1 = axes[0, 0]
    ewma = df['Clones'].ewm(span=7, adjust=False).mean()
    ewm_std = df['Clones'].ewm(span=7, adjust=False).std().fillna(0)
    upper_band = ewma + 2 * ewm_std
    ax1.plot(df['date'], df['Clones'], color='#2E86AB',
             linewidth=1.4, alpha=0.85, label='Clones')
    ax1.fill_between(df['date'], df['Clones'], alpha=0.25, color='#2E86AB')
    ax1.plot(df['date'], ewma, color='#00ffcc',
             linewidth=1.3, ls='--', label='EWMA-7')
    ax1.plot(df['date'], upper_band, color='#e74c3c',
             linewidth=1.0, ls=':', alpha=0.8, label='Bollinger +2σ')
    ax1.set_yscale('symlog', linthresh=15)
    ax1.yaxis.set_major_formatter(FuncFormatter(
        lambda x, _: f'{int(x)}' if x >= 0 else ''))
    ax1.set_ylim(bottom=0, top=max(50, df['Clones'].max() * 1.8))
    ax1.set_title('Daily Clone Trend (Symlog + EWMA Bollinger)',
                  fontsize=12, fontweight='bold')
    ax1.set_ylabel('Clones')
    ax1.legend(fontsize='small')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)

    # 2. Daily Unique Visitors（真实网页独立访客）
    ax2 = axes[0, 1]
    ax2.plot(df['date'], df['Views_Uniques'],
             color='#A23B72', linewidth=1.5, alpha=0.85)
    ax2.fill_between(df['date'], df['Views_Uniques'],
                     alpha=0.3, color='#A23B72')
    ax2.axhline(y=df['Views_Uniques'].mean(), color='red', linestyle='--',
                alpha=0.7, label=f'Avg: {df["Views_Uniques"].mean():.1f}')
    ax2.set_title('Daily Unique Commanders (Real Web Visitors)',
                  fontsize=12, fontweight='bold')
    ax2.set_ylabel('Unique Visitors')
    ax2.legend()
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)

    # 3. Clones vs Unique Visitors（仅拟合有 views 数据的时段 + Spearman ρ）
    ax3 = axes[1, 0]
    valid_views = df[(df['Views'] > 0) | (df['Views_Uniques'] > 0)]
    plot_df = valid_views if not valid_views.empty else df
    ax3.scatter(plot_df['Views_Uniques'], plot_df['Clones'], alpha=0.65,
                c=plot_df['date'].map(mdates.date2num), cmap='viridis', s=50)
    ax3.set_xlabel('Unique Visitors')
    ax3.set_ylabel('Clones')
    ax3.set_title('Clones vs Unique Visitors (Color=Time)',
                  fontsize=12, fontweight='bold')
    if plot_df['Views_Uniques'].nunique() >= 2 and len(plot_df) >= 3:
        z = np.polyfit(plot_df['Views_Uniques'], plot_df['Clones'], 1)
        p = np.poly1d(z)
        rho, pval = spearmanr(plot_df['Views_Uniques'], plot_df['Clones'])
        x_sorted = plot_df['Views_Uniques'].sort_values()
        ax3.plot(x_sorted, p(x_sorted), "r--", alpha=0.75,
                 label=f'OLS: y={z[0]:.1f}x+{z[1]:.1f} | ρ={rho:.2f} (p={pval:.2f})')
        ax3.legend(fontsize='small')
    ax3.grid(True, alpha=0.3)

    # 4. 单克隆节点重复强度分布（直方图 + 高斯核密度 KDE 曲线 + P95）
    ax4 = axes[1, 1]
    df['clones_per_cloner'] = df['Clones'] / df['Clones_Uniques'].replace(0, 1)
    vals = df['clones_per_cloner']
    ax4.hist(vals, bins=25, density=True, color='#F18F01',
             alpha=0.6, edgecolor='white', label='Histogram')
    if vals.nunique() >= 2 and len(vals) >= 5:
        try:
            kde = gaussian_kde(vals)
            xs = np.linspace(vals.min(), vals.max(), 200)
            ax4.plot(xs, kde(xs), color='#00ffcc', lw=2, label='Gaussian KDE')
        except Exception:
            pass
    p95 = float(np.percentile(vals, 95))
    ax4.axvline(x=vals.mean(), color='red', linestyle='--',
                label=f'Mean: {vals.mean():.2f}')
    ax4.axvline(x=p95, color='yellow', linestyle=':', label=f'P95: {p95:.2f}')
    ax4.set_xlabel('Clones Per Unique Cloner')
    ax4.set_ylabel('Density')
    ax4.set_title('Repeat Intensity PDF (KDE + P95 Anomaly)',
                  fontsize=12, fontweight='bold')
    ax4.legend(fontsize='small')
    ax4.grid(True, alpha=0.3)

    # 5. Weekly Throughput
    ax5 = axes[2, 0]
    weekly_sorted = weekly.tail(12)
    colors = ['#2E86AB' if c < 300 else '#F18F01' if c <
              600 else '#E63946' for c in weekly_sorted['clones']]
    bars = ax5.bar(range(len(weekly_sorted)),
                   weekly_sorted['clones'], color=colors, alpha=0.8, edgecolor='white')
    ax5.set_xticks(range(len(weekly_sorted)))
    ax5.set_xticklabels(weekly_sorted['week'].str[-2:], rotation=45)
    ax5.set_xlabel('Week Index')
    ax5.set_ylabel('Total Clones')
    ax5.set_title('Weekly Throughput (Last 12 Weeks)',
                  fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='y')
    max_bar = max(1, weekly_sorted['clones'].max())
    ax5.set_ylim(0, max_bar * 1.15)
    for bar, val in zip(bars, weekly_sorted['clones']):
        ax5.text(bar.get_x() + bar.get_width() / 2, bar.get_height() +
                 max_bar * 0.02, str(int(val)), ha='center', va='bottom', fontsize=8)

    # 6. 7-Day Moving Average
    ax6 = axes[2, 1]
    df['clones_ma7'] = df['Clones'].rolling(window=7, min_periods=1).mean()
    df['cloners_ma7'] = df['Clones_Uniques'].rolling(
        window=7, min_periods=1).mean()
    df['visitors_ma7'] = df['Views_Uniques'].rolling(
        window=7, min_periods=1).mean()
    ax6.plot(df['date'], df['clones_ma7'], color='#2E86AB',
             linewidth=2, label='Clones 7D MA')
    ax6.plot(df['date'], df['cloners_ma7'], color='#F18F01',
             linewidth=1.8, linestyle='--', label='Unique Cloners 7D MA')
    ax6.plot(df['date'], df['visitors_ma7'], color='#A23B72',
             linewidth=2, label='Unique Visitors 7D MA')
    ax6.set_title('7-Day Moving Average Trend', fontsize=12, fontweight='bold')
    ax6.set_ylabel('Frequency')
    ax6.legend()
    ax6.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax6.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax6.tick_params(axis='x', rotation=45)
    ax6.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('plots/bunker_intelligence_grid.png', dpi=100)
    plt.close(fig2)


def main_dashboard(df_all):
    if df_all.empty:
        return

    df = df_all.copy()
    df['cumulative'] = df['Clones'].cumsum()

    # 与 deep_intelligence 同步：Noisy-OR Sigmoid 联合人类信号纯度
    headless_ratio = df['Clones_Uniques'] / df['Views_Uniques'].replace(0, 1)
    repeat_ratio = df['Clones'] / df['Clones_Uniques'].replace(0, 1)
    p_headless = sigmoid((headless_ratio - 1.5) * 1.5)
    p_repeat = sigmoid((repeat_ratio - 2.5) * 1.5)
    df['bot_prob'] = 1.0 - (1.0 - p_headless) * (1.0 - p_repeat)
    df['purity'] = (1.0 - df['bot_prob']) * 100
    df['purity_ewm'] = df['purity'].ewm(span=7, adjust=False).mean()

    fig1 = plt.figure(figsize=(12, 14))
    gs1 = fig1.add_gridspec(4, 1)

    # 1. 实时侦察
    ax1 = fig1.add_subplot(gs1[0])
    recent = df.tail(30)
    ax1.plot(recent['date'], recent['Views'], alpha=0.5,
             ls='--', label='Views (Web Total)')
    ax1.plot(recent['date'], recent['Views_Uniques'],
             color='#e74c3c', lw=2, label='Unique Visitors (Web)')
    ax1.plot(recent['date'], recent['Clones'],
             color='#33cc33', lw=2, label='Clones (Terminal)')
    ax1.set_title(
        'Strategic Recon: Web Visitors vs Terminal Clones (30D)', color='#33cc33')
    ax1.legend(loc='upper left', frameon=True, fontsize='small')

    # 2. 累计荣光
    ax2 = fig1.add_subplot(gs1[1])
    ax2.fill_between(df['date'], df['cumulative'], color='#0066ff', alpha=0.2)
    ax2.plot(df['date'], df['cumulative'], color='#0066ff', lw=3)
    ax2.set_title('Bunker Glory: Total Cumulative Growth', color='#0066ff')

    # 3. 信号纯度审计（Noisy-OR Sigmoid + 7日指数平滑包络线）
    ax_p = fig1.add_subplot(gs1[2])
    ax_p.fill_between(df['date'], df['purity'], color='#ff00ff', alpha=0.1)
    ax_p.plot(df['date'], df['purity'], color='#ff00ff', lw=1.2,
              alpha=0.65, label='Instant Purity % (Sigmoid)')
    ax_p.plot(df['date'], df['purity_ewm'],
              color='#00ffcc', lw=2.0, label='EWMA-7 Trend')
    ax_p.set_ylim(0, 105)
    ax_p.axhline(y=50, color='#444', linestyle=':', alpha=0.5)
    ax_p.set_title(
        'Neural Cloud Integrity: Human Signal Purity Audit (Noisy-OR Sigmoid %)', color='#ff00ff')
    ax_p.legend(loc='upper right', fontsize='x-small')

    # 4. 作战热力图（保留 #33cc33 霓虹绿，用 dark_palette + Log1p 告别惨白网格）
    ax3 = fig1.add_subplot(gs1[3])
    pivot = df.assign(day=df['date'].dt.day_name()).pivot_table(
        index='day', columns='week_key', values='Clones', aggfunc='sum'
    ).fillna(0).reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

    if not pivot.empty:
        pivot = pivot.iloc[:, -52:]
        neon_greens = sns.dark_palette('#33cc33', as_cmap=True)
        sns.heatmap(np.log1p(pivot), cmap=neon_greens, ax=ax3,
                    cbar=False, lw=2, linecolor='#1a1a1a')
    ax3.set_title(
        'Global Deployment Heatmap: Log-Scaled Strategic Matrix', color='#33cc33')
    ax3.set_xlabel('Week')

    plt.tight_layout()
    plt.savefig('plots/bunker_main_v7.png', dpi=120)
    plt.close(fig1)


if __name__ == "__main__":
    print("🤖 Pod 042: Rendering Strategic Dashboards...")
    plt.style.use('dark_background')
    os.makedirs('plots', exist_ok=True)

    df_merged = prepare_merged_df()
    peak_recon(df_merged)
    intelligence_grid(df_merged)
    main_dashboard(df_merged)

    print("✅ Dashboards rendered.")
