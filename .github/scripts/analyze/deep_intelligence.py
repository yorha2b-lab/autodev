import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler


def map_rank(cluster_id, baseline_cluster):
    if cluster_id == -1:
        return 'Legendary'
    if cluster_id == baseline_cluster:
        return 'Veteran'
    return f'Tactical Unit {cluster_id}'


def execute_deep_intelligence():
    print("🤖 Pod 042: 启动‘全量情报融合协议’...")

    clone_path = 'ghrs-data/clones_ledger.csv'
    view_path = 'ghrs-data/views_ledger.csv'

    if not os.path.exists(clone_path) or not os.path.exists(view_path):
        print("⚠️ 数据账本缺失，取消分析。")
        return

    # 1. 读取并区分同名 uniques 列，再按日期外连接合并
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

    # ==================================================
    # 2. 正经特征工程（不再用总 Views 稀释）
    # ==================================================
    # 真人克隆数合理上限：既看过网页（unique_visitors）又克隆（unique_cloners），且按每人 1 次算
    df['human_clones_est'] = np.minimum(
        df['unique_cloners'], df['unique_visitors'])
    df['bot_clones_est'] = (
        df['clones'] - df['human_clones_est']).clip(lower=0)

    # 单节点重复拉取强度（1.0 = 正常单次；越高越像 CI / 脚本循环）
    df['repeat_intensity'] = df['clones'] / df['unique_cloners'].replace(0, 1)

    # 进入 Log 空间供聚类使用
    df['log_clones'] = np.log1p(df['clones'])
    df['log_visitors'] = np.log1p(df['unique_visitors'])
    df['log_repeat'] = np.log1p(df['repeat_intensity'])

    # ==================================================
    # 3. DBSCAN 行为聚类（克隆量 + 独立访客 + 重复强度）
    # ==================================================
    if len(df) >= 3:
        features = df[['log_clones', 'log_visitors', 'log_repeat']]
        X = StandardScaler().fit_transform(features)
        db = DBSCAN(eps=0.55, min_samples=3).fit(X)
        df['cluster'] = db.labels_
    else:
        df['cluster'] = 0

    # 找出样本数最多的常规聚类作为 Veteran 基线
    normal_clusters = df[df['cluster'] != -1]['cluster']
    baseline_cluster = normal_clusters.value_counts(
    ).idxmax() if not normal_clusters.empty else 0

    # ==================================================
    # 4. 战力结算
    # ==================================================
    human_clones = float(df['human_clones_est'].sum())
    bot_clones = float(df['bot_clones_est'].sum())

    df['rank'] = df['cluster'].apply(
        lambda cid: map_rank(cid, baseline_cluster))
    rank_counts = df['rank'].value_counts()

    # ==================================================
    # 5. 全频道视觉矩阵（保持原文件名与暗黑三联布局）
    # ==================================================
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(24, 8))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1.2, 1.8])

    # ----------------------------
    # A. 真人 vs 机器克隆构成
    # ----------------------------
    ax1 = fig.add_subplot(gs[0])
    if human_clones + bot_clones > 0:
        ax1.pie(
            [human_clones, bot_clones],
            labels=['Human (Upper Bound)', 'Machine'],
            colors=['#33cc33', '#e74c3c'],
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.85,
            explode=(0.05, 0)
        )
    else:
        ax1.text(0, 0, 'No Clone Data', ha='center', va='center', color='gray')

    ax1.add_artist(plt.Circle((0, 0), 0.70, fc='#0d1117'))
    ax1.set_title("Operational Composition", color='#33cc33', pad=20)

    # ----------------------------
    # B. 行为层级分布
    # ----------------------------
    ax2 = fig.add_subplot(gs[1])
    sns.barplot(
        x=rank_counts.index,
        y=rank_counts.values,
        hue=rank_counts.index,
        palette='viridis',
        legend=False,
        ax=ax2
    )
    ax2.set_title("Commander Hierarchy", color='#0066ff', pad=20)
    ax2.set_ylabel("Days Count")
    ax2.grid(axis='y', alpha=0.1)

    # ----------------------------
    # C. 行为拓扑（横轴=真人独立访客，纵轴=总克隆量）
    # ----------------------------
    ax3 = fig.add_subplot(gs[2])
    bubble_size = np.sqrt(df['clones'] + 1) * 20
    ax3.scatter(
        df['log_visitors'],
        df['log_clones'],
        c=df['cluster'],
        cmap='coolwarm',
        s=bubble_size,
        alpha=0.7,
        edgecolors='w'
    )

    # 标出克隆最高峰那一天
    peak_idx = df['clones'].idxmax()
    peak_row = df.loc[peak_idx]
    ax3.annotate(
        f"PEAK: {int(peak_row['clones'])} ({peak_row['date']})",
        xy=(peak_row['log_visitors'], peak_row['log_clones']),
        xytext=(12, -12),
        textcoords='offset points',
        color='yellow',
        fontsize=9,
        fontweight='bold',
        arrowprops=dict(arrowstyle='->', color='yellow', lw=1.2)
    )

    ax3.set_title("Sovereign Logistic Matrix (Log Space)",
                  color='#ff00ff', pad=20)
    ax3.set_xlabel("Log(Unique Visitors + 1)")
    ax3.set_ylabel("Log(Total Clones + 1)")
    ax3.grid(alpha=0.15)

    plt.tight_layout()
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/bunker_intelligence_fusion.png', dpi=120)
    plt.close(fig)

    print("✅ 全量情报视觉矩阵封存成功！")


if __name__ == "__main__":
    execute_deep_intelligence()
