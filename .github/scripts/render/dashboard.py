import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def peak_recon():
    df = pd.read_csv('ghrs-data/clones_ledger.csv')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    one_year_ago = df['date'].max() - pd.Timedelta(days=365)
    df = df[df['date'] >= one_year_ago].reset_index(drop=True)
    fig3, axes3 = plt.subplots(3, 1, figsize=(16, 14))
    # 3.1 时间序列图
    axA = axes3[0]
    axA.fill_between(df['date'], df['clones'],
                     alpha=0.3, color='#3498db', label='Clones')
    axA.plot(df['date'], df['clones'], color='#3498db', linewidth=1.2)

    # 💡 1. 核心修复：给左侧 Y 轴增加 25% 的顶部呼吸空间（从 859 扩充到 ~1050）
    axA.set_ylim(bottom=0, top=df['clones'].max() * 1.25)

    axA_twin = axA.twinx()
    axA_twin.plot(df['date'], df['uniques'],
                  color='#e74c3c', linewidth=1.2, label='Visitors')
    axA_twin.fill_between(
        df['date'], df['uniques'], alpha=0.15, color='#e74c3c')
    # 💡 2. 右侧 Y 轴同步给点余量
    axA_twin.set_ylim(bottom=0, top=df['uniques'].max() * 1.2)

    axA.set_ylabel('Clones', color='#3498db', fontsize=12)
    axA_twin.set_ylabel('Visitors', color='#e74c3c', fontsize=12)

    # 💡 3. 给标题加上 pad=15 间距，防止任何碰撞
    axA.set_title('Bunker Signal Intensity (Peak Detection Mode)',
                  fontsize=14, fontweight='bold', pad=15)

    # 💡 4. 战术箭头微调：指向清晰，文字居中悬浮在留白区
    peak_clone_idx = df['clones'].idxmax()
    axA.annotate(f'LEGEND PEAK: {df["clones"].max()}',
                 xy=(df.loc[peak_clone_idx, 'date'],
                     df.loc[peak_clone_idx, 'clones']),
                 xytext=(25, 20), textcoords='offset points',
                 arrowprops=dict(arrowstyle='->', color='yellow', lw=1.5),
                 fontsize=10, color='yellow', fontweight='bold')

    # 3.2 每周汇总
    axB = axes3[1]
    weekly_agg = df.assign(W=df['date'].dt.strftime(
        '%Y-W%V')).groupby('W')[['clones', 'uniques']].sum().tail(12)
    weekly_agg.plot(kind='bar', ax=axB, alpha=0.8)
    axB.set_title('Weekly Operational Summary',
                  fontsize=14, fontweight='bold')

    # 3.3 比值分析
    axC = axes3[2]
    df['ratio'] = df['clones'] / df['uniques'].replace(0, 1)
    colors3 = ['#2ecc71' if r < 3 else '#f39c12' if r <
               5 else '#e74c3c' for r in df['ratio']]
    axC.bar(df['date'], df['ratio'], color=colors3, alpha=0.7)
    axC.axhline(y=df['ratio'].mean(), color='#9b59b6',
                ls='--', label=f'Avg: {df["ratio"].mean():.2f}')
    axC.set_title('Clones/Visitor Ratio (High Ratio = CI/Automation)',
                  fontsize=14, fontweight='bold')
    axC.legend()

    plt.tight_layout()
    plt.savefig('plots/bunker_peak_recon.png', dpi=100)


def intelligence_grid():
    df = pd.read_csv('ghrs-data/clones_ledger.csv')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    one_year_ago = df['date'].max() - pd.Timedelta(days=365)
    df = df[df['date'] >= one_year_ago].reset_index(drop=True)
    df['week'] = df['date'].dt.isocalendar().week
    df['year'] = df['date'].dt.isocalendar().year
    df['week_key'] = df['year'].astype(
        str) + '-W' + df['week'].astype(str).str.zfill(2)
    weekly = df.groupby('week_key').agg({
        'clones': 'sum',
        'uniques': 'sum',
        'date': ['min', 'max']
    }).reset_index()
    weekly.columns = ['week', 'clones',
                      'uniques', 'start_date', 'end_date']
    weekly = weekly.sort_values('start_date').reset_index(drop=True)

    fig2, axes = plt.subplots(3, 2, figsize=(16, 14))
    fig2.suptitle('Bunker Strategic Analytics - Intelligence Grid',
                  color='#33cc33', fontsize=20)

    # 1. Daily Clone Trend
    ax1 = axes[0, 0]
    ax1.plot(df['date'], df['clones'],
             color='#2E86AB', linewidth=1.5, alpha=0.8)
    ax1.fill_between(df['date'], df['clones'],
                     alpha=0.3, color='#2E86AB')
    ax1.axhline(y=df['clones'].mean(), color='red', linestyle='--',
                alpha=0.7, label=f'Avg: {df["clones"].mean():.0f}')
    ax1.set_title('Daily Clone Trend', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Clones')
    ax1.legend()
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)

    # 2. Daily Unique Visitor Trend
    ax2 = axes[0, 1]
    ax2.plot(df['date'], df['uniques'],
             color='#A23B72', linewidth=1.5, alpha=0.8)
    ax2.fill_between(df['date'], df['uniques'],
                     alpha=0.3, color='#A23B72')
    ax2.axhline(y=df['uniques'].mean(), color='red', linestyle='--',
                alpha=0.7, label=f'Avg: {df["uniques"].mean():.0f}')
    ax2.set_title('Daily Unique Commanders',
                  fontsize=12, fontweight='bold')
    ax2.set_ylabel('Unique Visitors')
    ax2.legend()
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)

    # 3. Clones vs Visitors Scatter
    ax3 = axes[1, 0]
    ax3.scatter(df['uniques'], df['clones'], alpha=0.6,
                c=df['date'].map(mdates.date2num), cmap='viridis', s=50)
    ax3.set_xlabel('Unique Visitors')
    ax3.set_ylabel('Clones')
    ax3.set_title('Clones vs Visitors (Color=Time)',
                  fontsize=12, fontweight='bold')
    z = np.polyfit(df['uniques'], df['clones'], 1)
    p = np.poly1d(z)
    ax3.plot(df['uniques'].sort_values(), p(df['uniques'].sort_values(
    )), "r--", alpha=0.7, label=f'Trend: y={z[0]:.1f}x+{z[1]:.1f}')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 4. Clones Per User Distribution
    ax4 = axes[1, 1]
    df['clones_per_unique'] = df['clones'] / df['uniques'].replace(0, 1)
    ax4.hist(df['clones_per_unique'], bins=25,
             color='#F18F01', alpha=0.7, edgecolor='white')
    ax4.axvline(x=df['clones_per_unique'].mean(
    ), color='red', linestyle='--', label=f'Avg: {df["clones_per_unique"].mean():.2f}')
    ax4.set_xlabel('Clones Per Unit')
    ax4.set_ylabel('Days')
    ax4.set_title('Clones Per User Distribution',
                  fontsize=12, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    # 5. Weekly Throughput
    ax5 = axes[2, 0]
    weekly_sorted = weekly.sort_values('start_date').tail(12)
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
    for bar, val in zip(bars, weekly_sorted['clones']):
        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() +
                 10, str(val), ha='center', va='bottom', fontsize=8)

    # 6. 7-Day Moving Average
    ax6 = axes[2, 1]
    df['clones_ma7'] = df['clones'].rolling(
        window=7, min_periods=1).mean()
    df['uniques_ma7'] = df['uniques'].rolling(
        window=7, min_periods=1).mean()
    ax6.plot(df['date'], df['clones_ma7'], color='#2E86AB',
             linewidth=2, label='Clones 7D MA')
    ax6.plot(df['date'], df['uniques_ma7'], color='#A23B72',
             linewidth=2, label='Visitors 7D MA')
    ax6.set_title('7-Day Moving Average Trend',
                  fontsize=12, fontweight='bold')
    ax6.set_ylabel('Frequency')
    ax6.legend()
    ax6.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax6.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax6.tick_params(axis='x', rotation=45)
    ax6.grid(True, alpha=0.3)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('plots/bunker_intelligence_grid.png', dpi=100)


def load_clean(path, col_name):
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date']).copy()

    # 物理强转数字
    df[col_name] = pd.to_numeric(
        df[col_name.lower()], errors='coerce').fillna(0)

    # 💡 核心修正：直接在这里把 uniques 重命名为 [类别]_Uniques
    # 这样合并后，列名就是固定的 'Clones_Uniques' 和 'Views_Uniques'
    new_unique_name = f"{col_name}_Uniques"
    df[new_unique_name] = pd.to_numeric(
        df['uniques'], errors='coerce').fillna(0)

    return df[['date', col_name, new_unique_name]]


def main_dashboard(df_c, df_v):
    # 💡 1. 数据融合与脱水
    df = pd.merge(df_c, df_v, on='date', how='outer').fillna(
        0).sort_values('date')
    df['cumulative'] = df['Clones'].cumsum()
    df['ratio'] = df['Clones'] / df['Views_Uniques'].replace(0, 1)

    # 算法：(比例/10 * 0.6) + (总量/500 * 0.4)
    df['bot_prob'] = (df['ratio'] / 10).clip(upper=1) * 0.6 + \
        (df['Clones'] / 500).clip(upper=1) * 0.4
    df['purity'] = (1.0 - df['bot_prob']) * 100

    # 💡 3. 画布物理扩容：由 3 行 1 列 升级为 4 行 1 列
    fig1 = plt.figure(figsize=(12, 14))  # 增加高度以容纳四个雷达
    gs1 = fig1.add_gridspec(4, 1)

    # --- 子图 1: 实时侦察 (Views vs Clones) ---
    ax1 = fig1.add_subplot(gs1[0])
    ax1.plot(df['date'].tail(30), df['Views'].tail(
        30), alpha=0.5, ls='--', label='Views (Web)')
    ax1.plot(df['date'].tail(30), df['Clones'].tail(30),
             color='#33cc33', lw=2, label='Clones (Terminal)')
    ax1.set_title(
        'Strategic Recon: Web Visitors vs Terminal Commandos (30D)', color='#33cc33')
    ax1.legend(loc='upper left', frameon=True, fontsize='small')

    # --- 子图 2: 累计荣光 (Growth) ---
    ax2 = fig1.add_subplot(gs1[1])
    ax2.fill_between(df['date'], df['cumulative'], color='#0066ff', alpha=0.2)
    ax2.plot(df['date'], df['cumulative'], color='#0066ff', lw=3)
    ax2.set_title('Bunker Glory: Total Cumulative Growth', color='#0066ff')

    # --- 💡 子图 3 [核心新增]: 信号纯度审计 (Signal Purity) ---
    ax_p = fig1.add_subplot(gs1[2])
    # 使用渐变紫色，代表地堡的“骇入感知”
    ax_p.fill_between(df['date'], df['purity'], color='#ff00ff', alpha=0.1)
    ax_p.plot(df['date'], df['purity'],
              color='#ff00ff', lw=1.5, label='Signal Purity %')
    ax_p.set_ylim(0, 105)  # 留点空白放标题
    ax_p.axhline(y=50, color='#444', linestyle=':', alpha=0.5)  # 50% 警戒线
    ax_p.set_title(
        'Neural Cloud Integrity: Human Signal Purity Audit (%)', color='#ff00ff')
    ax_p.legend(loc='lower left', fontsize='x-small')

    # --- 子图 4: 作战热力图 (Heatmap) ---
    ax3 = fig1.add_subplot(gs1[3])
    pivot = df.assign(week=df['date'].dt.isocalendar().week, day=df['date'].dt.day_name()).pivot_table(
        index='day', columns='week', values='Clones', aggfunc='sum'
    ).fillna(0).reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

    sns.heatmap(pivot, cmap='Greens', ax=ax3,
                cbar=False, lw=2, linecolor='#1a1a1a')
    ax3.set_title(
        'Global Deployment Heatmap: Strategic Activity Matrix', color='#33cc33')

    plt.tight_layout()
    plt.savefig('plots/bunker_main_v7.png', dpi=120)


if __name__ == "__main__":
    print("🤖 Pod 042: Rendering Strategic Dashboards...")
    plt.style.use('dark_background')
    os.makedirs('plots', exist_ok=True)

    # 数据准备
    df_c = load_clean('ghrs-data/clones_ledger.csv', 'Clones')
    df_v = load_clean('ghrs-data/views_ledger.csv',
                      'Views').rename(columns={'uniques': 'uv'})

    peak_recon()
    intelligence_grid()
    main_dashboard(df_c, df_v)

    print("✅ Dashboards rendered.")
