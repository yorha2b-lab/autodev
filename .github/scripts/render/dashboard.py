import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap

BG_OUTER = '#0d1117'
BG_PANEL = '#161b22'
BORDER = '#30363d'
TEXT_MAIN = '#e6edf3'
TEXT_MUTED = '#8b949e'
CYAN = '#58a6ff'
GREEN = '#3fb950'
CORAL = '#f78166'
AMBER = '#d29922'
GOLD = '#ffd33d'
PURPLE = '#bc8cff'

GITHUB_GREENS = LinearSegmentedColormap.from_list(
    'gh_dark_greens',
    ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353']
)


def init_theme():
    plt.rcParams.update({
        'figure.facecolor': BG_OUTER,
        'axes.facecolor': BG_PANEL,
        'text.color': TEXT_MAIN,
        'axes.labelcolor': TEXT_MUTED,
        'xtick.color': TEXT_MUTED,
        'ytick.color': TEXT_MUTED,
        'axes.edgecolor': BORDER,
        'legend.facecolor': BG_OUTER,
        'legend.edgecolor': BORDER,
    })


def style_axes(ax):
    ax.set_facecolor(BG_PANEL)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(1)
    ax.grid(True, color=BORDER, alpha=0.45, linestyle='--')


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

    fig3, axes3 = plt.subplots(3, 1, figsize=(16, 14), facecolor=BG_OUTER)

    # 1.1 Clones vs Unique Visitors
    axA = axes3[0]
    style_axes(axA)
    axA.fill_between(df['date'], df['Clones'], alpha=0.22, color=CYAN)
    axA.plot(df['date'], df['Clones'], color=CYAN,
             linewidth=1.6, label='Clones')
    axA.set_ylim(bottom=0, top=max(1, df['Clones'].max() * 1.25))

    axA_twin = axA.twinx()
    axA_twin.spines['top'].set_color(BORDER)
    axA_twin.spines['right'].set_color(BORDER)
    axA_twin.tick_params(colors=CORAL)
    axA_twin.plot(df['date'], df['Views_Uniques'], color=CORAL,
                  linewidth=1.4, label='Unique Visitors')
    axA_twin.fill_between(
        df['date'], df['Views_Uniques'], alpha=0.12, color=CORAL)
    axA_twin.set_ylim(bottom=0, top=max(1, df['Views_Uniques'].max() * 1.25))

    axA.set_ylabel('Clones', color=CYAN, fontsize=11)
    axA_twin.set_ylabel('Unique Visitors', color=CORAL, fontsize=11)
    axA.set_title('Bunker Signal Intensity (Peak Detection Mode)',
                  color=TEXT_MAIN, fontsize=14, fontweight='bold', pad=14)

    lines1, labels1 = axA.get_legend_handles_labels()
    lines2, labels2 = axA_twin.get_legend_handles_labels()
    axA.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    peak_clone_idx = df['Clones'].idxmax()
    axA.annotate(
        f'LEGEND PEAK: {int(df["Clones"].max())}',
        xy=(df.loc[peak_clone_idx, 'date'], df.loc[peak_clone_idx, 'Clones']),
        xytext=(24, 18),
        textcoords='offset points',
        arrowprops=dict(arrowstyle='->', color=GOLD, lw=1.5),
        bbox=dict(boxstyle='round,pad=0.25', fc=BG_OUTER, ec=GOLD, alpha=0.9),
        fontsize=10,
        color=GOLD,
        fontweight='bold'
    )

    # 1.2 Weekly Summary
    axB = axes3[1]
    style_axes(axB)
    weekly_agg = df.groupby('week_key')[
        ['Clones', 'Clones_Uniques', 'Views_Uniques']].sum().tail(12)
    weekly_agg.plot(kind='bar', ax=axB, alpha=0.9, color=[
                    CYAN, PURPLE, CORAL], edgecolor=BG_OUTER)
    axB.set_title('Weekly Operational Summary (Clones vs Unique Cloners vs Unique Visitors)',
                  color=TEXT_MAIN, fontsize=14, fontweight='bold')
    axB.set_xlabel('Week')
    axB.tick_params(axis='x', rotation=30)

    # 1.3 Ratio
    axC = axes3[2]
    style_axes(axC)
    df['ratio'] = df['Clones'] / df['Views_Uniques'].replace(0, 1)
    colors3 = [GREEN if r < 3 else AMBER if r <
               5 else CORAL for r in df['ratio']]
    axC.bar(df['date'], df['ratio'], color=colors3, alpha=0.85, width=0.9)
    axC.axhline(y=df['ratio'].mean(), color=PURPLE, ls='--',
                lw=1.5, label=f'Avg: {df["ratio"].mean():.2f}')
    axC.set_title('Clones / Unique Visitor Ratio (High Ratio = Bots / CI)',
                  color=TEXT_MAIN, fontsize=14, fontweight='bold')
    axC.legend()

    plt.tight_layout()
    plt.savefig('plots/bunker_peak_recon.png', dpi=110, facecolor=BG_OUTER)
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

    fig2, axes = plt.subplots(3, 2, figsize=(16, 14), facecolor=BG_OUTER)
    fig2.suptitle('Bunker Strategic Analytics - Intelligence Grid',
                  color=GREEN, fontsize=20, fontweight='bold')

    # 1. Daily Clone Trend
    ax1 = axes[0, 0]
    style_axes(ax1)
    ax1.plot(df['date'], df['Clones'], color=CYAN, linewidth=1.6, alpha=0.9)
    ax1.fill_between(df['date'], df['Clones'], alpha=0.22, color=CYAN)
    ax1.axhline(y=df['Clones'].mean(), color=CORAL, linestyle='--',
                alpha=0.85, label=f'Avg: {df["Clones"].mean():.0f}')
    ax1.set_title('Daily Clone Trend', color=TEXT_MAIN,
                  fontsize=12, fontweight='bold')
    ax1.set_ylabel('Clones')
    ax1.legend()
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax1.tick_params(axis='x', rotation=45)

    # 2. Daily Unique Visitors
    ax2 = axes[0, 1]
    style_axes(ax2)
    ax2.plot(df['date'], df['Views_Uniques'],
             color=PURPLE, linewidth=1.6, alpha=0.9)
    ax2.fill_between(df['date'], df['Views_Uniques'], alpha=0.2, color=PURPLE)
    ax2.axhline(y=df['Views_Uniques'].mean(), color=CORAL, linestyle='--',
                alpha=0.85, label=f'Avg: {df["Views_Uniques"].mean():.1f}')
    ax2.set_title('Daily Unique Commanders (Real Web Visitors)',
                  color=TEXT_MAIN, fontsize=12, fontweight='bold')
    ax2.set_ylabel('Unique Visitors')
    ax2.legend()
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax2.tick_params(axis='x', rotation=45)

    # 3. Clones vs Unique Visitors（仅对有 views 记录的区间拟合趋势线，避免 4 月缺失拉斜）
    ax3 = axes[1, 0]
    style_axes(ax3)
    valid_views = df[(df['Views'] > 0) | (df['Views_Uniques'] > 0)]
    plot_df = valid_views if not valid_views.empty else df
    ax3.scatter(plot_df['Views_Uniques'], plot_df['Clones'], alpha=0.75,
                c=plot_df['date'].map(mdates.date2num), cmap='plasma', s=55, edgecolors=BG_OUTER, linewidths=0.7)
    ax3.set_xlabel('Unique Visitors')
    ax3.set_ylabel('Clones')
    ax3.set_title('Clones vs Unique Visitors (Color=Time)',
                  color=TEXT_MAIN, fontsize=12, fontweight='bold')
    if plot_df['Views_Uniques'].nunique() >= 2:
        z = np.polyfit(plot_df['Views_Uniques'], plot_df['Clones'], 1)
        p = np.poly1d(z)
        x_sorted = plot_df['Views_Uniques'].sort_values()
        ax3.plot(x_sorted, p(x_sorted), '--', color=GOLD, alpha=0.85,
                 label=f'Trend: y={z[0]:.1f}x+{z[1]:.1f}')
        ax3.legend()

    # 4. Repeat Intensity Distribution
    ax4 = axes[1, 1]
    style_axes(ax4)
    df['clones_per_cloner'] = df['Clones'] / df['Clones_Uniques'].replace(0, 1)
    ax4.hist(df['clones_per_cloner'], bins=25,
             color=AMBER, alpha=0.85, edgecolor=BG_OUTER)
    ax4.axvline(x=df['clones_per_cloner'].mean(), color=CORAL, linestyle='--',
                lw=1.5, label=f'Avg: {df["clones_per_cloner"].mean():.2f}')
    ax4.set_xlabel('Clones Per Unique Cloner')
    ax4.set_ylabel('Days')
    ax4.set_title('Repeat Intensity Distribution (CI / Retry Detection)',
                  color=TEXT_MAIN, fontsize=12, fontweight='bold')
    ax4.legend()

    # 5. Weekly Throughput
    ax5 = axes[2, 0]
    style_axes(ax5)
    weekly_sorted = weekly.tail(12)
    colors = [CYAN if c < 150 else AMBER if c <
              250 else CORAL for c in weekly_sorted['clones']]
    bars = ax5.bar(range(len(weekly_sorted)),
                   weekly_sorted['clones'], color=colors, alpha=0.9, edgecolor=BG_OUTER)
    ax5.set_xticks(range(len(weekly_sorted)))
    ax5.set_xticklabels(weekly_sorted['week'].str[-2:], rotation=45)
    ax5.set_xlabel('Week Index')
    ax5.set_ylabel('Total Clones')
    ax5.set_title('Weekly Throughput (Last 12 Weeks)',
                  color=TEXT_MAIN, fontsize=12, fontweight='bold')
    max_bar = max(1, weekly_sorted['clones'].max())
    ax5.set_ylim(0, max_bar * 1.15)
    for bar, val in zip(bars, weekly_sorted['clones']):
        ax5.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max_bar * 0.02,
                 str(int(val)), ha='center', va='bottom', color=TEXT_MAIN, fontsize=8.5)

    # 6. 7-Day Moving Average
    ax6 = axes[2, 1]
    style_axes(ax6)
    df['clones_ma7'] = df['Clones'].rolling(window=7, min_periods=1).mean()
    df['cloners_ma7'] = df['Clones_Uniques'].rolling(
        window=7, min_periods=1).mean()
    df['visitors_ma7'] = df['Views_Uniques'].rolling(
        window=7, min_periods=1).mean()
    ax6.plot(df['date'], df['clones_ma7'], color=CYAN,
             linewidth=2, label='Clones 7D MA')
    ax6.plot(df['date'], df['cloners_ma7'], color=AMBER,
             linewidth=1.8, linestyle='--', label='Unique Cloners 7D MA')
    ax6.plot(df['date'], df['visitors_ma7'], color=PURPLE,
             linewidth=2, label='Unique Visitors 7D MA')
    ax6.set_title('7-Day Moving Average Trend', color=TEXT_MAIN,
                  fontsize=12, fontweight='bold')
    ax6.set_ylabel('Frequency')
    ax6.legend()
    ax6.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax6.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax6.tick_params(axis='x', rotation=45)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('plots/bunker_intelligence_grid.png',
                dpi=110, facecolor=BG_OUTER)
    plt.close(fig2)


def main_dashboard(df_all):
    if df_all.empty:
        return

    df = df_all.copy()
    df['cumulative'] = df['Clones'].cumsum()

    human_est = np.minimum(df['Clones_Uniques'], df['Views_Uniques'])
    df['purity'] = np.where(
        df['Clones'] > 0, (human_est / df['Clones']) * 100, 100.0).clip(0, 100)

    fig1 = plt.figure(figsize=(13, 14), facecolor=BG_OUTER)
    gs1 = fig1.add_gridspec(4, 1, hspace=0.38)

    # 1. 实时侦察 (30D)
    ax1 = fig1.add_subplot(gs1[0])
    style_axes(ax1)
    recent = df.tail(30)
    ax1.plot(recent['date'], recent['Views'], alpha=0.55,
             ls='--', color=TEXT_MUTED, label='Views (Total)')
    ax1.plot(recent['date'], recent['Views_Uniques'], lw=2,
             color=CORAL, label='Unique Visitors (Web)')
    ax1.plot(recent['date'], recent['Clones'], color=GREEN,
             lw=2.2, label='Clones (Terminal)')
    ax1.fill_between(recent['date'], recent['Clones'], color=GREEN, alpha=0.12)
    ax1.set_title('Strategic Recon: Web Visitors vs Terminal Clones (30D)',
                  color=GREEN, fontsize=13, fontweight='bold')
    ax1.legend(loc='upper left', frameon=True, fontsize='small')

    # 2. 累计荣光
    ax2 = fig1.add_subplot(gs1[1])
    style_axes(ax2)
    ax2.fill_between(df['date'], df['cumulative'], color=CYAN, alpha=0.18)
    ax2.plot(df['date'], df['cumulative'], color=CYAN, lw=2.5)
    ax2.set_title('Bunker Glory: Total Cumulative Growth',
                  color=CYAN, fontsize=13, fontweight='bold')

    # 3. 信号纯度审计
    ax_p = fig1.add_subplot(gs1[2])
    style_axes(ax_p)
    ax_p.fill_between(df['date'], df['purity'], color=PURPLE, alpha=0.15)
    ax_p.plot(df['date'], df['purity'], color=PURPLE, lw=1.6,
              label='Human Signal Purity % (Upper Bound)')
    ax_p.set_ylim(0, 105)
    ax_p.axhline(y=50, color=TEXT_MUTED, linestyle=':', alpha=0.6)
    ax_p.set_title('Neural Cloud Integrity: Human Signal Purity Audit (%)',
                   color=PURPLE, fontsize=13, fontweight='bold')
    ax_p.legend(loc='upper right', fontsize='x-small')

    # 4. 作战热力图（GitHub 同款暗夜贡献图配色，用 95 分位截断避免单日 859 洗白全图）
    ax3 = fig1.add_subplot(gs1[3])
    ax3.set_facecolor(BG_OUTER)
    pivot = df.assign(day=df['date'].dt.day_name()).pivot_table(
        index='day', columns='week_key', values='Clones', aggfunc='sum'
    ).fillna(0).reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

    if not pivot.empty:
        pivot = pivot.iloc[:, -52:]
        non_zero = pivot.values[pivot.values > 0]
        vmax = max(10, float(np.percentile(non_zero, 95))
                   ) if len(non_zero) > 0 else 10
        sns.heatmap(
            pivot,
            cmap=GITHUB_GREENS,
            vmin=0,
            vmax=vmax,
            ax=ax3,
            cbar=False,
            linewidths=2.2,
            linecolor=BG_OUTER
        )
    ax3.set_title('Global Deployment Heatmap: Strategic Activity Matrix',
                  color=GREEN, fontsize=13, fontweight='bold')
    ax3.set_xlabel('Week')
    ax3.set_ylabel('')

    plt.savefig('plots/bunker_main_v7.png', dpi=120,
                bbox_inches='tight', facecolor=BG_OUTER)
    plt.close(fig1)


if __name__ == "__main__":
    print("🤖 Pod 042: Rendering Strategic Dashboards...")
    init_theme()
    os.makedirs('plots', exist_ok=True)

    df_merged = prepare_merged_df()
    peak_recon(df_merged)
    intelligence_grid(df_merged)
    main_dashboard(df_merged)

    print("✅ Dashboards rendered.")
