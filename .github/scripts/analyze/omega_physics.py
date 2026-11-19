import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import spearmanr


def morlet_cwt(ts, periods, w=6.0):
    """纯 NumPy 复莫莱小波连续变换（兼容全版本 SciPy）"""
    ts = np.asarray(ts, dtype=float)
    ts = ts - np.mean(ts)
    n = len(ts)
    flambda = (4.0 * np.pi) / (w + np.sqrt(2.0 + w ** 2))
    t_grid = np.arange(-(n // 2), (n // 2) + 1, dtype=float)
    power = np.zeros((len(periods), n), dtype=float)

    for idx, period in enumerate(periods):
        scale = max(period / flambda, 1e-6)
        eta = t_grid / scale
        norm = (np.pi ** -0.25) / np.sqrt(scale)
        wavelet = norm * np.exp(1j * w * eta) * np.exp(-0.5 * (eta ** 2))
        conv = np.convolve(ts, np.conj(wavelet[::-1]), mode='same')
        power[idx] = np.abs(conv) ** 2

    edges = np.minimum(np.arange(n), n - 1 - np.arange(n))
    coi_periods = (edges / np.sqrt(2.0)) * flambda
    return power, coi_periods


def compute_rqa(series, emb_dim=3, pct=15):
    """Takens 延迟嵌入距离矩阵与 RQA 递归定量指标"""
    ts = np.asarray(series, dtype=float)
    n = len(ts)
    if n < emb_dim + 5:
        return None, 0.0, 0.0, 0.0, 1.0

    cols = [ts[i:n - emb_dim + 1 + i] for i in range(emb_dim)]
    vec = np.column_stack(cols)
    m_n = len(vec)
    dist_mat = np.linalg.norm(vec[:, None, :] - vec[None, :, :], axis=2)
    eps = max(float(np.percentile(dist_mat, pct)), 1e-6)
    rec = (dist_mat <= eps).astype(int)

    total_rec = int(rec.sum() - m_n)
    rr = total_rec / max(m_n * (m_n - 1), 1)

    diag_pts = 0
    for k in range(1, m_n):
        diag = np.diag(rec, k=k)
        run = 0
        for val in diag:
            if val == 1:
                run += 1
            else:
                if run >= 2:
                    diag_pts += run
                run = 0
        if run >= 2:
            diag_pts += run
    det = (2.0 * diag_pts) / max(total_rec, 1)

    vert_pts = 0
    for c in range(m_n):
        col = rec[:, c].copy()
        col[c] = 0
        run = 0
        for val in col:
            if val == 1:
                run += 1
            else:
                if run >= 2:
                    vert_pts += run
                run = 0
        if run >= 2:
            vert_pts += run
    lam = vert_pts / max(total_rec, 1)

    return dist_mat, rr, det, lam, eps


def transfer_entropy(src, dst):
    """离散香农传递熵 T(src -> dst) (bits)"""
    s = np.asarray(src[:-1], dtype=int)
    yp = np.asarray(dst[:-1], dtype=int)
    yn = np.asarray(dst[1:], dtype=int)
    if len(yn) < 10:
        return 0.0

    te = 0.0
    for v_yn in np.unique(yn):
        for v_yp in np.unique(yp):
            m_yp = (yp == v_yp)
            p_yp = float(np.mean(m_yp))
            p_yn_yp = float(np.mean((yn == v_yn) & m_yp))
            if p_yp <= 0 or p_yn_yp <= 0:
                continue
            for v_s in np.unique(s):
                m_yps = m_yp & (s == v_s)
                p_yps = float(np.mean(m_yps))
                p_all = float(np.mean((yn == v_yn) & m_yps))
                if p_yps > 0 and p_all > 0:
                    te += p_all * np.log2((p_all / p_yps) / (p_yn_yp / p_yp))
    return float(max(0.0, te))


def compute_0d_persistence(y):
    """1D 上水平集 0维代数拓扑持续同调 (H0 Birth-Death Pairs)"""
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n < 3:
        return []

    order = np.argsort(-y)
    parent = list(range(n))
    birth = list(y)
    active = np.zeros(n, dtype=bool)
    pairs = []

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for idx in order:
        active[idx] = True
        nbrs = []
        if idx > 0 and active[idx - 1]:
            nbrs.append(find(idx - 1))
        if idx < n - 1 and active[idx + 1]:
            nbrs.append(find(idx + 1))
        nbrs = list(set(nbrs))
        if not nbrs:
            continue
        nbrs.sort(key=lambda r: (-birth[r], r))
        oldest = nbrs[0]
        parent[idx] = oldest
        for other in nbrs[1:]:
            if other != oldest:
                pairs.append((float(birth[other]), float(y[idx]), int(other)))
                parent[other] = oldest

    global_root = find(int(order[0]))
    pairs.append((float(birth[global_root]),
                 float(np.min(y)), int(global_root)))
    return pairs


def execute_omega_physics():
    print("🤖 Pod 042: 启动‘终焉物理与代数拓扑观测站’...")

    clone_path = 'ghrs-data/clones_ledger.csv'
    view_path = 'ghrs-data/views_ledger.csv'
    if not os.path.exists(clone_path):
        print("⚠️ clones_ledger.csv 缺失，取消分析。")
        return

    df_c = pd.read_csv(clone_path)
    df_c['date'] = pd.to_datetime(df_c['date'], errors='coerce')
    df_c = df_c.dropna(subset=['date']).copy()
    df_c['clones'] = pd.to_numeric(df_c['clones'], errors='coerce').fillna(0)
    df_c = df_c.groupby('date', as_index=False)['clones'].sum()

    if df_c.empty:
        print("⚠️ 账本为空，取消分析。")
        return

    full_idx = pd.date_range(df_c['date'].min(), df_c['date'].max(), freq='D')
    df = df_c.set_index('date').reindex(full_idx, fill_value=0)
    df = df.rename_axis('date').reset_index()

    has_views = False
    if os.path.exists(view_path):
        df_v = pd.read_csv(view_path)
        if not df_v.empty:
            df_v['date'] = pd.to_datetime(df_v['date'], errors='coerce')
            df_v = df_v.dropna(subset=['date']).copy()
            df_v['unique_visitors'] = pd.to_numeric(
                df_v['uniques'], errors='coerce'
            ).fillna(0)
            df_v = df_v.groupby('date', as_index=False)[
                'unique_visitors'].sum()
            if not df_v.empty:
                has_views = True
                view_start = df_v['date'].min()
                df = pd.merge(df, df_v, on='date', how='left')
                df['unique_visitors'] = df['unique_visitors'].fillna(0)
                df['has_view'] = df['date'] >= view_start

    log_x = np.log1p(df['clones'].to_numpy())

    plt.style.use('dark_background')
    fig = plt.figure(figsize=(20, 13))
    fig.suptitle(
        'Bunker Omega Physics (Wavelet + Recurrence + Transfer Entropy + TDA)',
        color='#00ffcc', fontsize=18, fontweight='bold'
    )
    gs = fig.add_gridspec(2, 2, hspace=0.28, wspace=0.22)

    # ==================================================
    # Panel 1: Complex Morlet Wavelet 时频火焰谱 (LIGO 风格)
    # ==================================================
    ax1 = fig.add_subplot(gs[0, 0])
    periods = np.linspace(2.0, 32.0, 64)
    power, coi_periods = morlet_cwt(log_x, periods, w=6.0)
    date_nums = mdates.date2num(df['date'])

    pcm = ax1.pcolormesh(
        date_nums, periods, np.log1p(power),
        shading='auto', cmap='inferno'
    )
    ax1.plot(date_nums, np.clip(coi_periods, 2.0, 32.0),
             color='white', ls='--', lw=1.3, alpha=0.8, label='Cone of Influence')
    ax1.axhline(7.0, color='#00ffcc', ls=':',
                lw=1.5, label='7.0d Workweek Belt')
    ax1.set_ylim(2.0, 32.0)
    ax1.xaxis_date()
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax1.tick_params(axis='x', rotation=25)
    ax1.set_title('Morlet Wavelet Scalogram (Time-Frequency)',
                  color='#f18f01', pad=12)
    ax1.set_ylabel('Oscillation Period (Days)')
    ax1.legend(loc='upper right', fontsize='small')
    fig.colorbar(pcm, ax=ax1, fraction=0.046, pad=0.03, label='Log Power')

    # ==================================================
    # Panel 2: Takens 相空间复发矩阵 & RQA 动力学指标
    # ==================================================
    ax2 = fig.add_subplot(gs[0, 1])
    dist_mat, rr, det, lam, eps = compute_rqa(log_x, emb_dim=3, pct=15)
    if dist_mat is not None:
        sim_mat = np.exp(-dist_mat / eps)
        im2 = ax2.imshow(sim_mat, origin='lower', cmap='magma', aspect='auto')
        fig.colorbar(im2, ax=ax2, fraction=0.046,
                     pad=0.03, label='Phase Similarity')

    hud2 = (
        f"Recurrence Rate (RR): {rr * 100:.1f}%\n"
        f"Determinism (DET):    {det * 100:.1f}%\n"
        f"Laminarity (LAM):     {lam * 100:.1f}%"
    )
    ax2.text(
        0.03, 0.96, hud2, transform=ax2.transAxes, va='top', ha='left',
        fontsize=9, color='#00ffcc', family='monospace',
        bbox=dict(boxstyle='round,pad=0.4', fc='#000000',
                  ec='#00ffcc', alpha=0.82)
    )
    ax2.set_title('Takens Delay Recurrence Matrix (RQA Chaos)',
                  color='#ff00ff', pad=12)
    ax2.set_xlabel('Time Index t (Days)')
    ax2.set_ylabel('Time Index t (Days)')

    # ==================================================
    # Panel 3: 香农传递熵 + 滞后因果扫描 (Web <-> Terminal)
    # ==================================================
    ax3 = fig.add_subplot(gs[1, 0])
    lags = np.arange(-7, 8)
    corrs = np.zeros(len(lags))
    te_w2c, te_c2w = 0.0, 0.0

    if has_views:
        sub = df[df['has_view']].reset_index(drop=True)
        if len(sub) >= 15:
            vx = np.log1p(sub['unique_visitors'].to_numpy())
            cy = np.log1p(sub['clones'].to_numpy())
            for i, lag in enumerate(lags):
                if lag > 0:
                    a, b = vx[:-lag], cy[lag:]
                elif lag < 0:
                    a, b = vx[-lag:], cy[:lag]
                else:
                    a, b = vx, cy
                if len(np.unique(a)) >= 2 and len(np.unique(b)) >= 2:
                    corrs[i] = float(spearmanr(a, b)[0])

            bx = (sub['unique_visitors'].to_numpy() >
                  sub['unique_visitors'].median()).astype(int)
            by = (sub['clones'].to_numpy() >
                  sub['clones'].median()).astype(int)
            te_w2c = transfer_entropy(bx, by)
            te_c2w = transfer_entropy(by, bx)

    bar_colors = ['#33cc33' if c >= 0 else '#e74c3c' for c in corrs]
    ax3.bar(lags, corrs, color=bar_colors, alpha=0.8, edgecolor='white')
    ax3.axhline(0, color='#888', lw=1.0)
    ax3.axvline(0, color='#00ffcc', ls='--', lw=1.2)

    net_dir = 'Web -> Clone' if te_w2c > te_c2w else 'Clone -> Web'
    hud3 = (
        f"T(Web -> Clone): {te_w2c:.4f} bits\n"
        f"T(Clone -> Web): {te_c2w:.4f} bits\n"
        f"Net Info Flow:   {net_dir}"
    )
    ax3.text(
        0.03, 0.96, hud3, transform=ax3.transAxes, va='top', ha='left',
        fontsize=9, color='yellow', family='monospace',
        bbox=dict(boxstyle='round,pad=0.4', fc='#000000',
                  ec='yellow', alpha=0.82)
    )
    ax3.set_title('Transfer Entropy & Lag Causality (Web <-> Terminal)',
                  color='#33cc33', pad=12)
    ax3.set_xlabel('Lag Days (+: Web Leads Clone | -: Clone Leads Web)')
    ax3.set_ylabel('Spearman Cross-Correlation')
    ax3.set_xticks(lags)
    ax3.grid(alpha=0.15)

    # ==================================================
    # Panel 4: 代数拓扑 H0 持续同调 (Persistent Homology)
    # ==================================================
    ax4 = fig.add_subplot(gs[1, 1])
    pairs = compute_0d_persistence(log_x)

    if pairs:
        births = np.array([p[0] for p in pairs])
        deaths = np.array([p[1] for p in pairs])
        pers = np.maximum(births - deaths, 1e-6)
        p_norm = pers / np.sum(pers)
        pers_entropy = float(-np.sum(p_norm * np.log2(p_norm)))

        lim = max(float(np.max(births)) * 1.08, 1.0)
        ax4.plot([0, lim], [0, lim], color='#666', ls='--', lw=1.3,
                 label='Zero-Persistence Diagonal')
        sc4 = ax4.scatter(
            births, deaths, c=pers, cmap='cool',
            s=30 + pers * 60, alpha=0.85, edgecolors='white'
        )
        fig.colorbar(sc4, ax=ax4, fraction=0.046, pad=0.03,
                     label='Topological Persistence')

        top_idx = np.argsort(-pers)[:2]
        for ti in top_idx:
            raw_val = int(np.expm1(births[ti]))
            ax4.annotate(
                f"Peak {raw_val} (L={pers[ti]:.2f})",
                xy=(births[ti], deaths[ti]),
                xytext=(-115, 10),
                textcoords='offset points',
                color='yellow', fontsize=8.5, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='yellow', lw=1.2)
            )
        ax4.set_xlim(0, lim)
        ax4.set_ylim(0, lim)
    else:
        pers_entropy = 0.0

    hud4 = (
        f"Topological Features (H0): {len(pairs)}\n"
        f"Persistence Entropy: {pers_entropy:.2f} bits\n"
        f"Max Persistence: {max([p[0]-p[1] for p in pairs], default=0):.2f}"
    )
    ax4.text(
        0.03, 0.96, hud4, transform=ax4.transAxes, va='top', ha='left',
        fontsize=9, color='#00ffcc', family='monospace',
        bbox=dict(boxstyle='round,pad=0.4', fc='#000000',
                  ec='#ff00ff', alpha=0.82)
    )
    ax4.set_title('Algebraic Topology H0 Persistence (TDA Homology)',
                  color='#ff00ff', pad=12)
    ax4.set_xlabel('Topological Birth Height [Log(Clones+1)]')
    ax4.set_ylabel('Topological Death Height [Log(Clones+1)]')
    ax4.legend(loc='lower right', fontsize='small')
    ax4.grid(alpha=0.15)

    plt.tight_layout(rect=[0, 0.02, 1, 0.94])
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/bunker_omega_physics.png', dpi=120)
    plt.close(fig)
    print("✅ 终焉物理观测站 bunker_omega_physics.png 渲染完毕！")


if __name__ == "__main__":
    execute_omega_physics()
