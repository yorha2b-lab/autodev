import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -50, 50)))


def robust_mad_zscore(series):
    """基于中位数绝对偏差 (MAD) 的鲁棒 Z-Score，专治长尾极端脉冲"""
    med = np.median(series)
    mad = np.median(np.abs(series - med))
    return 0.6745 * (series - med) / max(mad, 1e-6)


def shannon_entropy(series):
    """香农信息熵 (bits)：衡量流量分布的不确定性/集中度"""
    s = series[series > 0]
    if s.empty:
        return 0.0
    p = s / s.sum()
    return float(-np.sum(p * np.log2(p)))


def map_rank(cluster_id, baseline_cluster):
    if cluster_id == -1:
        return 'Legendary'
    if cluster_id == baseline_cluster:
        return 'Veteran'
    return f'Tactical Unit {cluster_id}'


def execute_deep_intelligence():
    print("🤖 Pod 042: 启动‘全量量子情报融合协议’...")

    clone_path = 'ghrs-data/clones_ledger.csv'
    view_path = 'ghrs-data/views_ledger.csv'

    if not os.path.exists(clone_path) or not os.path.exists(view_path):
        print("⚠️ 数据账本缺失，取消分析。")
        return

    df_c = pd.read_csv(clone_path).rename(
        columns={'uniques': 'unique_cloners'})
    df_v = pd.read_csv(view_path).rename(
        columns={'uniques': 'unique_visitors'})

    df_c['date'] = pd.to_datetime(df_c['date'], errors='coerce')
    df_v['date'] = pd.to_datetime(df_v['date'], errors='coerce')
    df_c = df_c.dropna(subset=['date'])
    df_v = df_v.dropna(subset=['date'])

    # 记录 views 账本实际开始日期，避免早期缺失日期填 0 污染统计
    view_start_date = df_v['date'].min(
    ) if not df_v.empty else pd.Timestamp.max

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
    # 1. 真实物理特征与修正版 Noisy-OR Sigmoid 门控概率
    # ==================================================
    has_view_record = df['date'] >= view_start_date
    headless_ratio = df['unique_cloners'] / df['unique_visitors'].replace(0, 1)
    repeat_ratio = df['clones'] / df['unique_cloners'].replace(0, 1)

    df['log_volume'] = np.log1p(df['clones'])
    df['log_cloners'] = np.log1p(df['unique_cloners'])
    df['log_repeat'] = np.log1p(repeat_ratio)
    df['mad_z'] = robust_mad_zscore(df['log_volume'])

    # 主信号：单人重复拉取率 + 突发脉冲强度
    p_repeat = sigmoid((repeat_ratio - 3.2) * 1.5)
    p_burst = sigmoid((df['mad_z'] - 2.5) * 1.5)

    # 弱辅助信号：CLI 工具不看网页属正常现象，上限封顶 0.25 且仅在有 view 记录时生效
    p_headless_raw = sigmoid((np.log1p(headless_ratio) - 3.5) * 1.0)
    p_headless = np.where(has_view_record, p_headless_raw * 0.25, 0.0)

    # Noisy-OR 联合门控
    df['bot_prob'] = 1.0 - (1.0 - p_repeat) * \
        (1.0 - p_burst) * (1.0 - p_headless)

    # ==================================================
    # 2. DBSCAN 行为拓扑聚类（只用纯粹的克隆行为三维特征）
    # ==================================================
    sil_score = None
    if len(df) >= 4:
        X = StandardScaler().fit_transform(
            df[['log_volume', 'log_cloners', 'log_repeat']]
        )
        db = DBSCAN(eps=0.65, min_samples=4).fit(X)
        df['cluster'] = db.labels_

        non_noise_mask = df['cluster'] != -1
        non_noise_labels = df.loc[non_noise_mask, 'cluster']
        if non_noise_labels.nunique() >= 2 and non_noise_mask.sum() > non_noise_labels.nunique():
            sil_score = silhouette_score(X[non_noise_mask], non_noise_labels)
        elif 2 <= len(set(db.labels_)) < len(df):
            sil_score = silhouette_score(X, db.labels_)
    else:
        df['cluster'] = 0

    normal_clusters = df[df['cluster'] != -1]['cluster']
    baseline_cluster = normal_clusters.value_counts(
    ).idxmax() if not normal_clusters.empty else 0

    # ==================================================
    # 3. 战力与信息熵结算
    # ==================================================
    bot_clones = float((df['clones'] * df['bot_prob']).sum())
    total_clones = float(df['clones'].sum())
    human_clones = max(0.0, total_clones - bot_clones)

    entropy_bits = shannon_entropy(df['clones'])

    # 相关性仅在 views 账本有效时间段内计算，避免缺失期填 0 产生伪相关
    df_corr = df[has_view_record]
    rho, p_val = (0.0, 1.0)
    if df_corr['unique_visitors'].nunique() >= 2 and df_corr['clones'].nunique() >= 2:
        rho, p_val = spearmanr(df_corr['unique_visitors'], df_corr['clones'])

    df['rank'] = df['cluster'].apply(
        lambda cid: map_rank(cid, baseline_cluster))
    rank_counts = df['rank'].value_counts()

    # ==================================================
    # 4. 原版黑底霓虹三联矩阵
    # ==================================================
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(24, 8))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1.2, 1.8])

    # A. 自动化组成 (Noisy-OR Sigmoid)
    ax1 = fig.add_subplot(gs[0])
    if total_clones > 0:
        ax1.pie(
            [human_clones, bot_clones],
            labels=['Human', 'Machine'],
            colors=['#33cc33', '#e74c3c'],
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.85,
            explode=(0.05, 0)
        )
    ax1.add_artist(plt.Circle((0, 0), 0.70, fc='#0d1117'))
    ax1.text(0, 0, f"H={entropy_bits:.2f}b", ha='center',
             va='center', color='#33cc33', fontsize=12, fontweight='bold')
    ax1.set_title("Operational Composition (Noisy-OR Sigmoid)",
                  color='#33cc33', pad=20)

    # B. 行为层级
    ax2 = fig.add_subplot(gs[1])
    sns.barplot(
        x=rank_counts.index,
        y=rank_counts.values,
        hue=rank_counts.index,
        palette='viridis',
        legend=False,
        ax=ax2
    )
    ax2.set_title("Commander Hierarchy (DBSCAN)", color='#0066ff', pad=20)
    ax2.set_ylabel("Days Count")
    ax2.tick_params(axis='x', rotation=20)
    ax2.grid(axis='y', alpha=0.1)

    # C. 行为拓扑（Log 空间 + 遥测 HUD）
    ax3 = fig.add_subplot(gs[2])
    bubble_size = np.sqrt(df['clones'] + 1) * 20
    ax3.scatter(
        df['log_cloners'],
        df['log_volume'],
        c=df['cluster'],
        cmap='coolwarm',
        s=bubble_size,
        alpha=0.65,
        edgecolors='w'
    )

    peak_idx = df['clones'].idxmax()
    peak_row = df.loc[peak_idx]
    is_right_side = peak_row['log_cloners'] > df['log_cloners'].quantile(0.75)
    ax3.annotate(
        f"PEAK: {int(peak_row['clones'])} (MAD-Z={peak_row['mad_z']:.1f})",
        xy=(peak_row['log_cloners'], peak_row['log_volume']),
        xytext=(-130, -10) if is_right_side else (15, -12),
        textcoords='offset points',
        color='yellow',
        fontsize=9.5,
        fontweight='bold',
        arrowprops=dict(arrowstyle='->', color='yellow', lw=1.3)
    )

    hud_lines = [
        f"Shannon Entropy: H = {entropy_bits:.2f} bits",
        f"Spearman Rank: ρ = {rho:.2f} (p={p_val:.3f})",
        f"Max Robust MAD-Z: {df['mad_z'].max():.2f}σ",
    ]
    if sil_score is not None:
        hud_lines.append(f"DBSCAN Silhouette: {sil_score:.2f}")
    ax3.text(
        0.02, 0.96, '\n'.join(hud_lines),
        transform=ax3.transAxes, va='top', ha='left',
        fontsize=9, color='#00ffcc', family='monospace',
        bbox=dict(boxstyle='round,pad=0.4',
                  fc='#000000', ec='#ff00ff', alpha=0.75)
    )

    ax3.set_title("Sovereign Logistic Matrix (Log Space)",
                  color='#ff00ff', pad=20)
    ax3.set_xlabel("Log(Unique Cloners + 1)")
    ax3.set_ylabel("Log(Total Clones + 1)")
    ax3.grid(alpha=0.1)

    plt.tight_layout()
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/bunker_intelligence_fusion.png', dpi=120)
    plt.close(fig)

    print("✅ 全量情报视觉矩阵封存成功！")


if __name__ == "__main__":
    execute_deep_intelligence()
