import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler


def sigmoid(x):
    """
    概率平滑函数：
    避免指标达到某个值后直接封顶，
    让异常程度呈渐进变化。
    """
    return 1 / (1 + np.exp(-x))


def map_rank(cluster_id):
    """
    DBSCAN 的 cluster 数量不是固定的，
    不能写死 0/1/2，否则新增聚类会出现 NaN。
    """
    if cluster_id == -1:
        return 'Legendary'
    if cluster_id == 0:
        return 'Veteran'
    return f'Tactical Unit {cluster_id}'


def execute_deep_intelligence():

    print("🤖 Pod 042: 启动‘全量情报融合协议’...")

    clone_path = 'ghrs-data/clones_ledger.csv'
    view_path = 'ghrs-data/views_ledger.csv'

    if not os.path.exists(clone_path) or not os.path.exists(view_path):
        print("⚠️ 数据账本缺失，取消分析。")
        return

    # 1. 物理对账
    df_c = pd.read_csv(clone_path)
    df_v = pd.read_csv(view_path)

    df = pd.merge(df_c, df_v, on='date', how='inner').fillna(0)

    # ==================================================
    # 2. 特征工程
    # ==================================================

    # 访问转化强度
    df['ratio'] = (df['clones'] / df['views'].replace(0, 1))

    # Github 行为天然长尾，因此进入 Log 空间
    df['log_volume'] = np.log1p(df['clones'])
    df['log_intensity'] = np.log1p(df['ratio'])

    # ==================================================
    # 3. 自动化概率审计
    # ==================================================

    # 原始 ratio 越高，越像自动化行为
    ratio_score = sigmoid(df['ratio'] - 3)

    # 单日爆发越高，异常概率越高
    burst_score = sigmoid((df['clones'] - 100) / 100)

    # 综合异常系数
    df['bot_prob'] = (ratio_score * 0.6 + burst_score * 0.4)

    # ==================================================
    # 4. DBSCAN 行为聚类
    # ==================================================
    X = StandardScaler().fit_transform(df[['log_volume', 'log_intensity']])
    db = DBSCAN(eps=0.4, min_samples=3).fit(X)
    df['cluster'] = db.labels_

    # ==================================================
    # 5. 战力结算
    # ==================================================
    bot_clones = (df['clones'] * df['bot_prob']).sum()
    total_clones = df['clones'].sum()
    human_clones = max(0, total_clones - bot_clones)
    df['rank'] = df['cluster'].apply(map_rank)
    rank_counts = (df['rank'].value_counts())

    # ==================================================
    # 6. 全频道视觉矩阵
    # ==================================================

    plt.style.use('dark_background')
    fig = plt.figure(figsize=(24, 8))

    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1.2, 1.8])

    # ----------------------------
    # A. 自动化组成
    # ----------------------------

    ax1 = fig.add_subplot(gs[0])

    ax1.pie(
        [human_clones, bot_clones],
        labels=['Human', 'Machine'],
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.85,
        explode=(0.05, 0)
    )

    ax1.add_artist(plt.Circle((0, 0), 0.70, fc='#0d1117'))
    ax1.set_title("Operational Composition", color='#33cc33', pad=20)

    # ----------------------------
    # B. 行为层级
    # ----------------------------

    ax2 = fig.add_subplot(gs[1])
    sns.barplot(x=rank_counts.index, y=rank_counts.values,
                palette='viridis', ax=ax2)

    ax2.set_title("Commander Hierarchy", color='#0066ff', pad=20)

    ax2.set_ylabel("Days Count")

    ax2.grid(axis='y', alpha=0.1)

    # ----------------------------
    # C. 行为拓扑
    # ----------------------------

    ax3 = fig.add_subplot(gs[2])

    # sqrt 缩放避免极端 clone 撑爆气泡
    bubble_size = (np.sqrt(df['clones'] + 1) * 20)
    ax3.scatter(
        df['log_volume'],
        df['log_intensity'],
        c=df['cluster'],
        cmap='coolwarm',
        s=bubble_size,
        alpha=0.6,
        edgecolors='w'
    )
    ax3.set_title("Sovereign Logistic Matrix (Log Space)",
                  color='#ff00ff', pad=20)
    ax3.set_xlabel("Log(Total Clones)")
    ax3.set_ylabel("Log(Intensity)")
    ax3.grid(alpha=0.1)
    plt.tight_layout()
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/bunker_intelligence_fusion.png', dpi=120)

    print("✅ 全量情报视觉矩阵封存成功！")


if __name__ == "__main__":
    execute_deep_intelligence()
