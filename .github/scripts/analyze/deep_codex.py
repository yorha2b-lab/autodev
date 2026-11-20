from scipy.stats import rankdata, kendalltau
import pandas as pd
import numpy as np
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import os

import matplotlib
matplotlib.use('Agg')


OUTPUT_IMAGE = 'plots/bunker_deep_codex.png'

plt.style.use('dark_background')


def setup_cjk_font():
    preferred = [
        'noto sans cjk', 'noto serif cjk', 'wenquanyi', 'simhei',
        'microsoft yahei', 'pingfang', 'source han', 'droid sans fallback', 'ar pl'
    ]
    available = {f.name.lower(): f.name for f in fm.fontManager.ttflist}
    for key in preferred:
        for low_name, real_name in available.items():
            if key in low_name:
                plt.rcParams['font.sans-serif'] = [real_name, 'DejaVu Sans']
                plt.rcParams['font.monospace'] = [
                    real_name, 'DejaVu Sans Mono']
                plt.rcParams['axes.unicode_minus'] = False
                return True
    plt.rcParams['axes.unicode_minus'] = False
    return False


HAS_CJK = setup_cjk_font()


def tx(zh_text, en_text):
    return zh_text if HAS_CJK else en_text


def load_bunker_data():
    c_path = 'ghrs-data/clones_ledger.csv'
    if not os.path.exists(c_path):
        raise FileNotFoundError(f'Missing required ledger: {c_path}')

    df = pd.read_csv(c_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').drop_duplicates('date', keep='last')

    full_idx = pd.date_range(df['date'].min(), df['date'].max(), freq='D')
    df = df.set_index('date').reindex(full_idx).fillna(0.0)
    df.index.name = 'date'
    return df


def compute_gramian_fields(y):
    x = np.log1p(y)
    x_min, x_max = float(np.min(x)), float(np.max(x))
    denom = max(x_max - x_min, 1e-9)
    # 缩放到 [-1, 1] 极坐标区间
    x_scaled = np.clip(2.0 * (x - x_min) / denom - 1.0, -1.0, 1.0)
    sqrt_term = np.sqrt(np.maximum(1.0 - x_scaled ** 2, 0.0))

    # GASF = cos(phi_i + phi_j) | GADF = sin(phi_i - phi_j)
    gasf = np.outer(x_scaled, x_scaled) - np.outer(sqrt_term, sqrt_term)
    gadf = np.outer(sqrt_term, x_scaled) - np.outer(x_scaled, sqrt_term)
    return gasf, gadf


def set_matrix_date_ticks(ax, dates):
    n = len(dates)
    ticks = np.linspace(0, n - 1, min(6, n), dtype=int)
    lbls = [dates[t].strftime('%m-%d') for t in ticks]
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels(lbls, fontsize=8, rotation=25)
    ax.set_yticklabels(lbls, fontsize=8)


# ==============================================================================
# 1 & 2. Deep Learning Vision Encoding: GASF & GADF
# ==============================================================================
def plot_gasf(ax, dates, y, gasf):
    im = ax.imshow(gasf, cmap='inferno', vmin=-1.0,
                   vmax=1.0, origin='upper', aspect='auto')
    cbar = plt.colorbar(im, ax=ax, shrink=0.88, pad=0.02)
    cbar.set_label('cos(φ_i + φ_j)', fontsize=8.5)
    set_matrix_date_ticks(ax, dates)

    pk = int(np.argmax(y))
    ax.axhline(pk, color='#00f5d4', ls=':', lw=0.9, alpha=0.65)
    ax.axvline(pk, color='#00f5d4', ls=':', lw=0.9, alpha=0.65)
    ax.set_title(tx(f'格拉姆角和场 GASF ({len(y)}×{len(y)} 深度学习视觉编码)',
                    f'Gramian Angular Summation Field GASF ({len(y)}×{len(y)})'),
                 color='#ffbe0b', fontweight='bold')


def plot_gadf(ax, dates, y, gadf):
    im = ax.imshow(gadf, cmap='twilight_shifted', vmin=-1.0,
                   vmax=1.0, origin='upper', aspect='auto')
    cbar = plt.colorbar(im, ax=ax, shrink=0.88, pad=0.02)
    cbar.set_label('sin(φ_i - φ_j)', fontsize=8.5)
    set_matrix_date_ticks(ax, dates)

    pk = int(np.argmax(y))
    ax.scatter([pk], [pk], color='#39ff14', s=90, marker='+', lw=1.8, zorder=5)
    ax.set_title(tx('格拉姆角差场 GADF (反对称时间导数纹理)',
                    'Gramian Angular Difference Field GADF (Directional)'),
                 color='#00f5d4', fontweight='bold')


# ==============================================================================
# 3. Deep Learning Vision Encoding: Markov Transition Field (MTF)
# ==============================================================================
def plot_mtf(ax, dates, y):
    n = len(y)
    Q = 8
    ranks = rankdata(y, method='average') / (float(n) + 1e-9)
    q_bins = np.clip((ranks * Q).astype(int), 0, Q - 1)

    W = np.zeros((Q, Q), dtype=float)
    for t in range(n - 1):
        W[q_bins[t], q_bins[t + 1]] += 1.0
    row_sums = np.maximum(W.sum(axis=1, keepdims=True), 1.0)
    W /= row_sums

    mtf = W[q_bins[:, None], q_bins[None, :]]

    im = ax.imshow(mtf, cmap='viridis', vmin=0.0, vmax=max(float(mtf.max()), 0.35),
                   origin='upper', aspect='auto')
    cbar = plt.colorbar(im, ax=ax, shrink=0.88, pad=0.02)
    cbar.set_label('P(q_i -> q_j)', fontsize=8.5)
    set_matrix_date_ticks(ax, dates)

    ax.set_title(tx(f'马尔可夫转移场 MTF ({Q}-分位动态概率挂毯)',
                    f'Markov Transition Field MTF ({Q}-Quantile Tapestry)'),
                 color='#39ff14', fontweight='bold')


# ==============================================================================
# 4. Elastic Time Geometry: Dynamic Time Warping (DTW Monthly Shape Matrix)
# ==============================================================================
def dtw_normalized(s1, s2):
    n1, n2 = len(s1), len(s2)
    dp = np.full((n1 + 1, n2 + 1), np.inf)
    dp[0, 0] = 0.0
    for i in range(1, n1 + 1):
        for j in range(1, n2 + 1):
            cost = abs(float(s1[i - 1] - s2[j - 1]))
            dp[i, j] = cost + min(dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1])
    return float(dp[n1, n2]) / float(n1 + n2)


def plot_dtw_matrix(ax, df):
    x_series = pd.Series(
        np.log1p(df['clones'].values.astype(float)), index=df.index)
    months = x_series.groupby(x_series.index.to_period('M'))
    valid_months = []
    for p, grp in months:
        if len(grp) >= 5:
            vals = grp.values
            z_vals = (vals - np.mean(vals)) / max(float(np.std(vals)), 1e-6)
            valid_months.append((str(p)[2:], z_vals))

    k = len(valid_months)
    names = [m[0] for m in valid_months]
    dtw_mat = np.zeros((k, k), dtype=float)
    best_pair = (0, 1, np.inf)

    for i in range(k):
        for j in range(i + 1, k):
            d = dtw_normalized(valid_months[i][1], valid_months[j][1])
            dtw_mat[i, j] = d
            dtw_mat[j, i] = d
            if d < best_pair[2]:
                best_pair = (i, j, d)

    im = ax.imshow(dtw_mat, cmap='plasma', aspect='auto')
    cbar = plt.colorbar(im, ax=ax, shrink=0.88, pad=0.02)
    cbar.set_label('Normalized Z-Shape DTW', fontsize=8.5)

    vmax = max(float(dtw_mat.max()), 1e-6)
    for i in range(k):
        for j in range(k):
            v = dtw_mat[i, j]
            c_txt = 'black' if v > 0.60 * vmax else 'white'
            ax.text(j, i, f'{v:.2f}', ha='center', va='center',
                    color=c_txt, fontsize=8, fontweight='bold')

    ax.set_xticks(np.arange(k))
    ax.set_yticks(np.arange(k))
    ax.set_xticklabels(names, rotation=30, fontsize=8.5)
    ax.set_yticklabels(names, fontsize=8.5)
    ax.set_title(tx(f'动态时间规整 DTW 月度波形对齐 (最神似: {names[best_pair[0]]}↔{names[best_pair[1]]})',
                    f'Dynamic Time Warping Shape Matrix (Closest: {names[best_pair[0]]}↔{names[best_pair[1]]})'),
                 color='#ff00ff', fontweight='bold')


# ==============================================================================
# 5. Spectral Graph Theory: Visibility Graph Laplacian & Fiedler Vector Cut
# ==============================================================================
def plot_fiedler_spectral_cut(ax, dates, y):
    n = len(y)
    adj = np.zeros((n, n), dtype=float)
    for i in range(n - 1):
        max_slope = -np.inf
        for j in range(i + 1, n):
            slope = (y[j] - y[i]) / (j - i)
            if slope > max_slope:
                max_slope = slope
                adj[i, j] = 1.0
                adj[j, i] = 1.0

    deg = adj.sum(axis=1)
    d_inv_sqrt = 1.0 / np.sqrt(np.maximum(deg, 1.0))
    L_sym = np.eye(n) - (d_inv_sqrt[:, None] * adj) * d_inv_sqrt[None, :]
    L_sym = 0.5 * (L_sym + L_sym.T)

    evals, evecs = np.linalg.eigh(L_sym)
    fiedler_val = float(evals[1]) if n > 1 else 0.0
    fiedler_vec = evecs[:, 1] if n > 1 else np.zeros(n)

    # 保持近期稳态末段方向一致（正值侧）
    if np.mean(fiedler_vec[-min(30, n):]) < 0:
        fiedler_vec = -fiedler_vec

    pos_mask = fiedler_vec >= 0.0
    neg_mask = fiedler_vec < 0.0

    ax.plot(dates, fiedler_vec, color='#adb5bd', lw=0.9, alpha=0.5)
    ax.fill_between(dates, 0.0, fiedler_vec, where=pos_mask, interpolate=True,
                    color='#00f5d4', alpha=0.35, label=tx('光谱社区 A (+)', 'Spectral Clade +'))
    ax.fill_between(dates, 0.0, fiedler_vec, where=neg_mask, interpolate=True,
                    color='#ff006e', alpha=0.35, label=tx('光谱社区 B (-)', 'Spectral Clade -'))
    ax.axhline(0.0, color='#ffea00', ls='--', lw=1.2,
               label='Fiedler Zero-Cut Boundary')

    # 内嵌拉普拉斯特征值谱（展示谱隙）
    ax_in = ax.inset_axes([0.64, 0.56, 0.33, 0.38])
    ax_in.set_facecolor('#0c1320')
    k_show = min(16, n)
    ax_in.plot(np.arange(k_show), evals[:k_show],
               color='#00bbf9', marker='o', ms=3.5, lw=1.4)
    ax_in.scatter([1], [fiedler_val], color='#ffea00', s=70, zorder=5)
    ax_in.set_title(f'Laplacian λ₁={fiedler_val:.3f}',
                    fontsize=8, color='#ffea00', fontweight='bold')
    ax_in.tick_params(labelsize=6.5)
    ax_in.grid(alpha=0.2)

    ax.set_title(tx(f'拉普拉斯谱图切分 (Fiedler 代数连通度 λ₁={fiedler_val:.3f})',
                    f'Visibility Graph Spectral Cut (Fiedler λ₁={fiedler_val:.3f})'),
                 color='#00bbf9', fontweight='bold')
    ax.set_ylabel('Fiedler Eigenvector v₁(t)')
    ax.tick_params(axis='x', rotation=25)
    ax.legend(loc='upper left', fontsize=8, framealpha=0.85)
    ax.grid(alpha=0.15)


# ==============================================================================
# 6. Rank Geometry: Empirical Copula Density & Tail Dependence (Clones vs Uniques)
# ==============================================================================
def plot_empirical_copula(ax, df):
    c = df['clones'].values.astype(float)
    u_raw = df['uniques'].values.astype(float)
    n = len(c)

    u = rankdata(c, method='average') / (float(n) + 1.0)
    v = rankdata(u_raw, method='average') / (float(n) + 1.0)

    # 10x10 经验 Copula 密度背景
    hist, _, _ = np.histogram2d(
        u, v, bins=10, range=[[0.0, 1.0], [0.0, 1.0]], density=True)
    ax.imshow(hist.T, origin='lower', extent=[
              0.0, 1.0, 0.0, 1.0], cmap='magma', alpha=0.55, aspect='auto')

    ratio = c / np.maximum(u_raw, 1.0)
    sc = ax.scatter(u, v, c=np.clip(ratio, 1.0, 6.0), cmap='cool', s=24,
                    edgecolors='white', lw=0.35, alpha=0.92, zorder=4)
    ax.plot([0.0, 1.0], [0.0, 1.0], color='#39ff14', ls='--',
            lw=1.2, alpha=0.7, label='Comonotonic u=v')

    # 计算上下尾相依系数 (q=0.85 / q=0.15) 与 Kendall tau
    thr_hi, thr_lo = 0.85, 0.15
    lam_u = float(np.mean(u[v > thr_hi] > thr_hi)
                  ) if np.any(v > thr_hi) else 0.0
    lam_l = float(np.mean(u[v < thr_lo] < thr_lo)
                  ) if np.any(v < thr_lo) else 0.0
    tau, _ = kendalltau(c, u_raw)

    # 高亮 859 那天在 Copula 空间的位置（上尾脱钩点）
    pk = int(np.argmax(c))
    ax.scatter([u[pk]], [v[pk]], color='#ffea00', s=190,
               marker='*', edgecolors='white', lw=0.7, zorder=6)
    ax.annotate(f'Peak {int(c[pk])}', (u[pk], v[pk]), xytext=(-48, -16), textcoords='offset points',
                color='#ffea00', fontsize=8.5, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#ffea00', lw=1.1))

    # 框出上尾和下尾相依区域
    ax.add_patch(plt.Rectangle((thr_hi, thr_hi), 1.0 - thr_hi, 1.0 - thr_hi,
                               fill=False, edgecolor='#ffea00', lw=1.4, ls=':', zorder=5))
    ax.add_patch(plt.Rectangle((0.0, 0.0), thr_lo, thr_lo,
                               fill=False, edgecolor='#00f5d4', lw=1.4, ls=':', zorder=5))

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_title(tx('经验 Copula 秩空间密度与极值尾部相依性 (Clones vs Uniques)',
                    'Empirical Copula & Tail Dependence (Clones vs Uniques)'),
                 color='#ff4d6d', fontweight='bold')
    ax.set_xlabel('Pseudo-Obs Rank u = F(Clones)')
    ax.set_ylabel('Pseudo-Obs Rank v = G(Unique Cloners)')
    ax.legend(loc='upper left', fontsize=8, framealpha=0.85)
    ax.grid(alpha=0.15)

    info = tx(
        f"Kendall 秩相关 τ: {tau:.3f}\n上尾相依 λ_U(85%): {lam_u:.2f}\n下尾相依 λ_L(15%): {lam_l:.2f}",
        f"Kendall's τ:     {tau:.3f}\nUpper Tail λ_U:  {lam_u:.2f}\nLower Tail λ_L:  {lam_l:.2f}"
    )
    ax.text(0.98, 0.04, info, transform=ax.transAxes, ha='right', va='bottom', fontsize=8.3,
            color='#00f5d4', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#00f5d4', alpha=0.88))


def main():
    print('📜 Pod 042: Encoding Final Deep Codex & Spectral Geometry (v16.0)...')
    df = load_bunker_data()
    dates = df.index
    y = df['clones'].values.astype(float)
    gasf, gadf = compute_gramian_fields(y)

    fig, axes = plt.subplots(3, 2, figsize=(20, 18), facecolor='#04060a')
    for ax in axes.flat:
        ax.set_facecolor('#080c14')

    plot_gasf(axes[0, 0], dates, y, gasf)
    plot_gadf(axes[0, 1], dates, y, gadf)
    plot_mtf(axes[1, 0], dates, y)
    plot_dtw_matrix(axes[1, 1], df)
    plot_fiedler_spectral_cut(axes[2, 0], dates, y)
    plot_empirical_copula(axes[2, 1], df)

    fig.suptitle(
        tx('地堡终极法典：深度学习视觉场与谱图几何 (GASF + GADF + MTF + DTW + Fiedler + Copula)',
           'Bunker Deep Codex (GASF + GADF + MTF + DTW + Fiedler Spectral Cut + Copula)'),
        color='#ffea00', fontsize=15.6, fontweight='bold', y=0.975
    )

    fig.subplots_adjust(left=0.06, right=0.955, top=0.925,
                        bottom=0.055, hspace=0.33, wspace=0.23)
    out_dir = os.path.dirname(OUTPUT_IMAGE)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    plt.savefig(OUTPUT_IMAGE, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'✅ Final Deep Codex sealed at: {OUTPUT_IMAGE}')


if __name__ == '__main__':
    main()
