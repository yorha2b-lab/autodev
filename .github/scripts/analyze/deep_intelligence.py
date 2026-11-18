import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

BG_OUTER = '#0d1117'
BG_PANEL = '#161b22'
BORDER = '#30363d'
TEXT_MAIN = '#e6edf3'
TEXT_MUTED = '#8b949e'
GREEN = '#3fb950'
CORAL = '#f78166'
CYAN = '#58a6ff'
PURPLE = '#bc8cff'
GOLD = '#ffd33d'


def style_axes(ax):
    ax.set_facecolor(BG_PANEL)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(1)
    ax.tick_params(colors=TEXT_MUTED, labelsize=9)
    ax.xaxis.label.set_color(TEXT_MUTED)
    ax.yaxis.label.set_color(TEXT_MUTED)


def map_rank(cluster_id, baseline_cluster):
    if cluster_id == -1:
        return 'Legendary'
    if cluster_id == baseline_cluster:
        return 'Veteran'
    return f'Unit #{cluster_id}'


def execute_deep_intelligence():
    print("🤖 Pod 042: 启动‘全量情报融合协议’...")

    clone_path = 'ghrs-data/clones_ledger.csv'
    view_path = 'ghrs-data/views_ledger.csv'

    if not os.path.exists(clone_path) or not os.path.exists(view_path):
        print("⚠️ 数据账本缺失，取消分析。")
        return

    df_c = pd.read_csv(clone_path).rename(
        columns={'uniques': 'unique_cloners'})
    df_v = pd.read_csv(view_path).rename(
        columns={'uniques': 'unique_visitors'})

    df = pd.merge(
        df_c[['date', 'clones', 'unique_cloners']],
        df_v[['date', 'views', 'unique_visitors']],
        on='date',
        how='outer'
    ).fillna(0).sort_values('date').reset_index(drop=True)

    for col in ['clones', 'unique_cloners', 'views', 'unique_visitors']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if df.empty:
        print("⚠️ 账本为空，取消分析。")
        return

    df['human_clones_est'] = np.minimum(
        df['unique_cloners'], df['unique_visitors'])
    df['bot_clones_est'] = (
        df['clones'] - df['human_clones_est']).clip(lower=0)
    df['repeat_intensity'] = df['clones'] / df['unique_cloners'].replace(0, 1)

    df['log_clones'] = np.log1p(df['clones'])
    df['log_cloners'] = np.log1p(df['unique_cloners'])
    df['log_visitors'] = np.log1p(df['unique_visitors'])
    df['log_repeat'] = np.log1p(df['repeat_intensity'])

    # eps 放宽到 0.9，避免切出过多碎片簇导致 X 轴文字拥挤
    if len(df) >= 3:
        features = df[['log_clones', 'log_cloners',
                       'log_visitors', 'log_repeat']]
        X = StandardScaler().fit_transform(features)
        db = DBSCAN(eps=0.9, min_samples=4).fit(X)
        df['cluster'] = db.labels_
    else:
        df['cluster'] = 0

    normal_clusters = df[df['cluster'] != -1]['cluster']
    baseline_cluster = normal_clusters.value_counts(
    ).idxmax() if not normal_clusters.empty else 0

    human_clones = float(df['human_clones_est'].sum())
    bot_clones = float(df['bot_clones_est'].sum())
    total_clones = int(human_clones + bot_clones)

    df['rank'] = df['cluster'].apply(
        lambda cid: map_rank(cid, baseline_cluster))
    rank_counts = df['rank'].value_counts()

    plt.rcParams.update({
        'figure.facecolor': BG_OUTER,
        'axes.facecolor': BG_PANEL,
        'text.color': TEXT_MAIN,
        'axes.edgecolor': BORDER,
    })

    fig = plt.figure(figsize=(22, 7.5), facecolor=BG_OUTER)
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1.15, 1.85], wspace=0.22)

    # A. 甜甜圈图：统一底色 + 中心展示总克隆量
    ax1 = fig.add_subplot(gs[0])
    ax1.set_facecolor(BG_OUTER)
    if total_clones > 0:
        ax1.pie(
            [human_clones, bot_clones],
            labels=['Human (Upper)', 'Machine'],
            colors=[GREEN, CORAL],
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.81,
            explode=(0.04, 0),
            wedgeprops={'edgecolor': BG_OUTER, 'linewidth': 2.5},
            textprops={'color': TEXT_MAIN, 'fontsize': 10}
        )
        ax1.text(0, 0.06, f'{total_clones:,}', ha='center',
                 va='center', color=TEXT_MAIN, fontsize=18, fontweight='bold')
        ax1.text(0, -0.14, 'Total Clones', ha='center',
                 va='center', color=TEXT_MUTED, fontsize=10)
    else:
        ax1.text(0, 0, 'No Clone Data', ha='center',
                 va='center', color=TEXT_MUTED)

    ax1.add_artist(plt.Circle((0, 0), 0.62, fc=BG_OUTER))
    ax1.set_title("Operational Composition", color=GREEN,
                  fontsize=13, fontweight='bold', pad=16)

    # B. 行为层级分布（不拥挤的渐变柱状图）
    ax2 = fig.add_subplot(gs[1])
    style_axes(ax2)
    bar_colors = sns.color_palette("crest", n_colors=len(rank_counts))
    bars = ax2.bar(rank_counts.index, rank_counts.values,
                   color=bar_colors, edgecolor=BORDER, linewidth=1, alpha=0.92)
    for bar, val in zip(bars, rank_counts.values):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(1, rank_counts.max() * 0.02),
                 str(int(val)), ha='center', va='bottom', color=TEXT_MAIN, fontsize=9)
    ax2.set_ylim(0, max(1, rank_counts.max() * 1.15))
    ax2.set_title("Commander Hierarchy", color=CYAN,
                  fontsize=13, fontweight='bold', pad=16)
    ax2.set_ylabel("Days Count", fontsize=10)
    ax2.tick_params(axis='x', rotation=20)
    plt.setp(ax2.get_xticklabels(), ha='right')
    ax2.grid(axis='y', color=BORDER, alpha=0.45, linestyle='--')

    # C. 行为拓扑（横轴改用独立克隆者，告别 5 根糖葫芦）
    ax3 = fig.add_subplot(gs[2])
    style_axes(ax3)
    bubble_size = np.sqrt(df['clones'] + 1) * 18
    ax3.scatter(
        df['log_cloners'],
        df['log_clones'],
        c=df['cluster'],
        cmap='cool',
        s=bubble_size,
        alpha=0.75,
        edgecolors=BG_OUTER,
        linewidths=0.8
    )

    peak_idx = df['clones'].idxmax()
    peak_row = df.loc[peak_idx]
    ax3.annotate(
        f"PEAK: {int(peak_row['clones'])} ({peak_row['date']})",
        xy=(peak_row['log_cloners'], peak_row['log_clones']),
        xytext=(14, -14),
        textcoords='offset points',
        color=GOLD,
        fontsize=9.5,
        fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', fc=BG_OUTER, ec=GOLD, alpha=0.9),
        arrowprops=dict(arrowstyle='->', color=GOLD, lw=1.4)
    )

    ax3.set_title("Sovereign Logistic Matrix (Log Space)",
                  color=PURPLE, fontsize=13, fontweight='bold', pad=16)
    ax3.set_xlabel("Log(Unique Cloners + 1)", fontsize=10)
    ax3.set_ylabel("Log(Total Clones + 1)", fontsize=10)
    ax3.grid(color=BORDER, alpha=0.45, linestyle='--')

    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/bunker_intelligence_fusion.png', dpi=120,
                bbox_inches='tight', facecolor=BG_OUTER)
    plt.close(fig)
    print("✅ 全量情报视觉矩阵封存成功！")


if __name__ == "__main__":
    execute_deep_intelligence()
