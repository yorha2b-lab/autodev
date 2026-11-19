from sklearn.neighbors import NearestNeighbors
from scipy.linalg import eigh_tridiagonal
from scipy.stats import gaussian_kde, genpareto
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import os
from collections import deque

import matplotlib
matplotlib.use('Agg')


OUTPUT_IMAGE = 'plots/bunker_quantum_metaphysics.png'

plt.style.use('dark_background')


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

    v_path = 'ghrs-data/views_ledger.csv'
    if os.path.exists(v_path):
        v_df = pd.read_csv(v_path)
        v_df['date'] = pd.to_datetime(v_df['date'])
        v_df = v_df.sort_values('date').drop_duplicates('date', keep='last')
        v_df = v_df.set_index('date').reindex(full_idx).fillna(0.0)
        df['views'] = v_df['views'].values
        df['views_uniques'] = v_df['uniques'].values
    else:
        df['views'] = 0.0
        df['views_uniques'] = 0.0

    return df


# ==============================================================================
# 1. Quantum Mechanics: 1D Time-Independent Schrödinger Well & WKB Tunneling
# ==============================================================================
def plot_schrodinger_well(ax, y):
    x = np.log1p(y)
    n_grid = 260
    grid = np.linspace(max(0.0, x.min() - 0.35), x.max() + 0.35, n_grid)
    dx = grid[1] - grid[0]

    kde = gaussian_kde(x, bw_method='scott')
    V = -np.log(np.maximum(kde(grid), 1e-12))
    V -= V.min()

    # 有效质量系数由真实朗之万短时扩散系数决定
    coeff = float(np.clip(0.35 * np.var(np.diff(x)), 0.18, 0.75))
    diag = V + 2.0 * coeff / (dx ** 2)
    off_diag = np.full(n_grid - 1, -coeff / (dx ** 2))

    evals, evecs = eigh_tridiagonal(
        diag, off_diag, select='i', select_range=(0, 3))

    ax.plot(grid, V, color='#a8dadc', lw=2.3, label='Quantum Potential V(x)')
    ax.fill_between(grid, V, V.max() * 1.08, color='#1d3557', alpha=0.22)

    colors = ['#39ff14', '#00f5d4', '#ffbe0b', '#ff00ff']
    for k in range(4):
        psi2 = evecs[:, k] ** 2
        psi2_norm = psi2 / max(psi2.max(), 1e-12)
        level = evals[k]
        scale = 0.42
        ax.hlines(level, grid[0], grid[-1], colors=colors[k],
                  linestyles=':', lw=0.9, alpha=0.55)
        ax.plot(grid, level + scale * psi2_norm, color=colors[k], lw=1.6,
                label=f'|ψ_{k}|²  E_{k}={level:.2f} kT')
        ax.fill_between(grid, level, level + scale *
                        psi2_norm, color=colors[k], alpha=0.22)

    # 计算基态 E_0 量子隧穿至 Peak 859 的 WKB 透射率
    well_x = grid[int(np.argmin(V))]
    x_peak = float(x.max())
    barrier = (grid >= well_x) & (grid <= x_peak) & (V > evals[0])
    if np.sum(barrier) >= 2:
        xg = grid[barrier]
        integrand = np.sqrt(np.maximum(V[barrier] - evals[0], 0.0) / coeff)
        # 兼容 NumPy 1.x & 2.x 的梯形积分
        wkb_action = float(
            np.sum(0.5 * (integrand[:-1] + integrand[1:]) * np.diff(xg)))
        tunnel_prob = float(np.exp(-2.0 * wkb_action))
        ax.fill_between(xg, evals[0], V[barrier], color='#ff006e',
                        alpha=0.20, label='Tunneling Barrier')
    else:
        tunnel_prob = 1.0

    v_peak = float(np.interp(x_peak, grid, V))
    ax.scatter([x_peak], [v_peak], color='#ff006e',
               s=110, marker='D', zorder=6)
    ax.annotate(
        f'WKB Tunneling -> Peak {int(y.max())}\nP ≈ {tunnel_prob:.2e}',
        xy=(x_peak, v_peak),
        xytext=(max(well_x + 0.5, x_peak - 2.4),
                min(V.max() * 0.92, evals[0] + 2.5)),
        color='#ff006e', fontsize=8.8, fontweight='bold',
        arrowprops=dict(arrowstyle='->', color='#ff006e', lw=1.3)
    )

    ax.set_ylim(-0.15, max(V.max() * 1.08, evals[-1] + 0.7))
    ax.set_title('Schrödinger Eigenstates & WKB Tunneling Probability',
                 color='#39ff14', fontweight='bold')
    ax.set_xlabel('Log Coordinate x = Log(Clones + 1)')
    ax.set_ylabel('Energy Eigenvalue E_n & Potential V(x)')
    ax.legend(loc='upper left', fontsize=7.8, framealpha=0.84)
    ax.grid(alpha=0.15)


# ==============================================================================
# 2. Extreme Value Theory: GPD "N-Year Flood" Return Period Curve
# ==============================================================================
def plot_evt_return_period(ax, y):
    u = float(max(np.percentile(y, 85), np.median(y) + 1.0))
    exc = y[y > u] - u
    if len(exc) < 8:
        u = float(np.percentile(y, 75))
        exc = y[y > u] - u

    zeta_u = len(exc) / max(len(y), 1)
    xi, _, sigma = genpareto.fit(exc, floc=0.0)
    sigma = max(float(sigma), 1e-6)
    xi = float(xi)

    def return_level(t_years, shape, scale):
        m = 365.25 * t_years * zeta_u
        if abs(shape) < 1e-4:
            return u + scale * np.log(np.maximum(m, 1.0))
        return u + (scale / shape) * (np.maximum(m, 1.0) ** shape - 1.0)

    t_grid = np.logspace(-1.2, 2.0, 200)  # ~23天一遇 到 100年一遇
    rl_curve = return_level(t_grid, xi, sigma)

    # 参数自助法 90% 置信带
    rng = np.random.default_rng(42)
    boot_curves = []
    for _ in range(90):
        sample = rng.choice(exc, size=len(exc), replace=True)
        try:
            b_xi, _, b_sig = genpareto.fit(sample, floc=0.0)
            if 0.0 < b_sig < 1e5 and -0.6 < b_xi < 1.8:
                boot_curves.append(return_level(t_grid, b_xi, b_sig))
        except Exception:
            continue

    if len(boot_curves) >= 10:
        boot_arr = np.vstack(boot_curves)
        lo = np.nanpercentile(boot_arr, 5, axis=0)
        hi = np.nanpercentile(boot_arr, 95, axis=0)
        ax.fill_between(t_grid, np.maximum(lo, u), np.minimum(hi, rl_curve.max() * 5.0),
                        color='#00bbf9', alpha=0.16, label='Bootstrap 90% CI')

    ax.plot(t_grid, rl_curve, color='#00bbf9', lw=2.3,
            label=f'GPD Fit (ξ={xi:.2f}, σ={sigma:.1f})')

    # 经验重现期散点
    y_sorted = np.sort(y[y > u])[::-1]
    ranks = np.arange(1, len(y_sorted) + 1)
    emp_prob = ranks / (len(y) + 1.0)
    emp_years = 1.0 / (365.25 * emp_prob)
    ax.scatter(emp_years, y_sorted, color='#ffbe0b', s=32,
               alpha=0.85, zorder=5, label='Observed Extremes')

    # 标注 Peak 859 究竟是几年一遇
    y_max = float(y.max())
    if xi < 0 and (1.0 + xi * (y_max - u) / sigma) <= 0:
        t_max_yr = np.inf
    elif abs(xi) < 1e-4:
        p_exc = zeta_u * np.exp(-(y_max - u) / sigma)
        t_max_yr = 1.0 / (365.25 * max(p_exc, 1e-12))
    else:
        p_exc = zeta_u * ((1.0 + xi * (y_max - u) / sigma) ** (-1.0 / xi))
        t_max_yr = 1.0 / (365.25 * max(p_exc, 1e-12))

    if np.isfinite(t_max_yr) and t_max_yr <= 500.0:
        ax.scatter([t_max_yr], [y_max], color='#ff006e', marker='*',
                   s=240, edgecolors='white', lw=0.7, zorder=6)
        t_label = f'{t_max_yr:.1f}-Year Flood' if t_max_yr >= 1.0 else f'{t_max_yr * 12:.1f}-Month Storm'
    else:
        t_label = '>500-Year Apocalypse'

    rl_1yr = float(return_level(1.0, xi, sigma))
    rl_10yr = float(return_level(10.0, xi, sigma))
    rl_100yr = float(return_level(100.0, xi, sigma))

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_title('Extreme Value Theory: Flood Return Period (GPD)',
                 color='#00bbf9', fontweight='bold')
    ax.set_xlabel('Return Period T (Years, Log Scale)')
    ax.set_ylabel('Return Level (Daily Clones, Log Scale)')
    ax.legend(loc='lower right', fontsize=8, framealpha=0.85)
    ax.grid(alpha=0.16, which='both')

    info = (
        f"POT Threshold u (P85): {u:.0f} ({len(exc)} events)\n"
        f"Peak {int(y_max)} Rating: {t_label}\n"
        f"1-Yr / 10-Yr Storm: {rl_1yr:.0f} / {rl_10yr:.0f}\n"
        f"100-Yr Apocalypse: {rl_100yr:.0f} clones"
    )
    ax.text(0.03, 0.96, info, transform=ax.transAxes, va='top', fontsize=8.5,
            color='#00bbf9', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#00bbf9', alpha=0.88))


# ==============================================================================
# 3. Nuclear Physics: Random Matrix Theory (Marcenko-Pastur Noise Sea)
# ==============================================================================
def plot_random_matrix_theory(ax, y):
    x = np.log1p(y)
    n = len(x)
    L = min(32, max(10, n // 6))
    windows = np.lib.stride_tricks.sliding_window_view(
        x, L).T  # shape (L, T_eff)
    T_eff = windows.shape[1]

    # 标准化每个延迟通道并构建经验相关矩阵
    stds = windows.std(axis=1, keepdims=True)
    Z = (windows - windows.mean(axis=1, keepdims=True)) / \
        np.where(stds < 1e-9, 1.0, stds)
    corr = (Z @ Z.T) / float(T_eff)
    evals = np.sort(np.linalg.eigvalsh(corr))[::-1]

    q = L / float(T_eff)
    lam_minus = (1.0 - np.sqrt(q)) ** 2
    lam_plus = (1.0 + np.sqrt(q)) ** 2

    lam_grid = np.linspace(lam_minus + 1e-6, lam_plus - 1e-6, 300)
    mp_pdf = np.sqrt((lam_plus - lam_grid) * (lam_grid -
                     lam_minus)) / (2.0 * np.pi * q * lam_grid)

    ax.plot(lam_grid, mp_pdf, color='#ff00ff', lw=2.3,
            label=f'Marcenko-Pastur Noise Sea (q={q:.2f})')
    ax.fill_between(lam_grid, 0.0, mp_pdf, color='#ff00ff', alpha=0.16)

    noise_evals = evals[evals <= lam_plus]
    sig_evals = evals[evals > lam_plus]

    bins = np.linspace(0.0, max(lam_plus * 1.3, evals.max() * 1.05), 24)
    ax.hist(evals, bins=bins, density=True, color='#00f5d4', alpha=0.28, edgecolor='#00f5d4',
            label='Empirical Eigenvalue Density')

    if len(noise_evals) > 0:
        ax.scatter(noise_evals, np.zeros_like(noise_evals) + 0.03, color='#00f5d4',
                   marker='|', s=130, lw=1.8, label=f'Inside Noise Sea ({len(noise_evals)})')
    if len(sig_evals) > 0:
        ax.scatter(sig_evals, np.zeros_like(sig_evals) + 0.06, color='#ffea00',
                   marker='^', s=110, zorder=6, label=f'Escaped Coherent Signals ({len(sig_evals)})')
        ax.annotate(f'λ₁={sig_evals[0]:.2f}', xy=(sig_evals[0], 0.08),
                    xytext=(sig_evals[0] * 0.85, mp_pdf.max() * 0.35),
                    color='#ffea00', fontsize=9, fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='#ffea00', lw=1.2))

    ax.axvline(lam_plus, color='#ff4d6d', ls='--', lw=1.8,
               label=f'MP Edge λ₊ = {lam_plus:.2f}')

    sig_energy = float(np.sum(sig_evals) / np.sum(evals) *
                       100.0) if np.sum(evals) > 0 else 0.0
    ax.set_title('Random Matrix Theory: Marcenko-Pastur Noise Test',
                 color='#ff00ff', fontweight='bold')
    ax.set_xlabel('Eigenvalue λ of L-Lag Correlation Matrix')
    ax.set_ylabel('Spectral Density ρ(λ)')
    ax.legend(loc='upper right', fontsize=8, framealpha=0.85)
    ax.grid(alpha=0.15)

    info = (
        f"Delay Dim L × T: {L} × {T_eff}\n"
        f"MP Noise Band: [{lam_minus:.2f}, {lam_plus:.2f}]\n"
        f"Signal Spikes > λ₊: {len(sig_evals)} / {L}\n"
        f"Non-Noise Energy: {sig_energy:.1f}%"
    )
    ax.text(0.55, 0.56, info, transform=ax.transAxes, va='top', fontsize=8.4,
            color='#00f5d4', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#00f5d4', alpha=0.88))


# ==============================================================================
# 4. 3D Differential Geometry: 3D Takens Strange Attractor Orbit
# ==============================================================================
def plot_3d_attractor(ax, dates, y):
    x = np.log1p(y)
    xt, xt1, xt2 = x[2:], x[1:-1], x[:-2]
    t_norm = np.linspace(0.0, 1.0, len(xt))

    ax.set_facecolor('#04060a')
    for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
        pane.set_facecolor((0.03, 0.05, 0.10, 0.85))
        pane.set_edgecolor('#1b263b')

    ax.plot(xt, xt1, xt2, color='#4cc9f0', lw=0.75, alpha=0.35)
    sc = ax.scatter(xt, xt1, xt2, c=t_norm, cmap='plasma',
                    s=24, alpha=0.9, depthshade=True)

    # 高亮 859 弹射彗星环
    peak_idx = int(np.argmax(y))
    p_rel = np.clip(peak_idx - 2, 1, len(xt) - 2)
    loop_slice = slice(max(0, p_rel - 2), min(len(xt), p_rel + 4))
    ax.plot(xt[loop_slice], xt1[loop_slice], xt2[loop_slice],
            color='#ffea00', lw=2.4, zorder=10)
    ax.scatter([x[peak_idx]], [x[max(0, peak_idx - 1)]], [x[max(0, peak_idx - 2)]],
               color='#ff006e', s=180, marker='*', edgecolors='white', lw=0.7, zorder=11)

    ax.text(x[peak_idx], x[max(0, peak_idx - 1)], x[max(0, peak_idx - 2)] + 0.35,
            f' Peak {int(y[peak_idx])} Slingshot', color='#ffea00', fontsize=8.5, fontweight='bold')

    # 计算 3D 相空间平均轨道速率与维度跨度
    pts = np.column_stack([xt, xt1, xt2])
    speeds = np.linalg.norm(np.diff(pts, axis=0), axis=1)

    ax.view_init(elev=23, azim=-50)
    ax.set_title('3D Takens Strange Attractor Orbit (τ=1d)',
                 color='#ffbe0b', fontweight='bold', pad=10)
    ax.set_xlabel('Log(C[t]+1)', labelpad=6, fontsize=8.5)
    ax.set_ylabel('Log(C[t-1]+1)', labelpad=6, fontsize=8.5)
    ax.set_zlabel('Log(C[t-2]+1)', labelpad=6, fontsize=8.5)
    ax.tick_params(labelsize=7.5)

    info = (
        f"Mean Phase Speed: {speeds.mean():.2f} /day\n"
        f"Max Warp Jump: {speeds.max():.2f} /day\n"
        f"Attractor Core: ~{np.expm1(np.median(x)):.0f} clones/d"
    )
    ax.text2D(0.02, 0.95, info, transform=ax.transAxes, va='top', fontsize=8.3,
              color='#ffbe0b', family='monospace',
              bbox=dict(boxstyle='round,pad=0.35', facecolor='#0a0f18', edgecolor='#ffbe0b', alpha=0.88))


# ==============================================================================
# 5. Time-Series Mining: Matrix Profile (7D Motif Twins & Top-1 Discord)
# ==============================================================================
def plot_matrix_profile(ax, dates, y):
    m = 7
    subseq = np.lib.stride_tricks.sliding_window_view(y, m)
    k = len(subseq)
    means = subseq.mean(axis=1, keepdims=True)
    stds = subseq.std(axis=1, keepdims=True)
    const_mask = (stds.ravel() < 1e-9)
    z_sub = (subseq - means) / np.where(stds < 1e-9, 1.0, stds)

    diff = z_sub[:, None, :] - z_sub[None, :, :]
    dist_mat = np.sqrt(np.sum(diff ** 2, axis=2))

    idx_arr = np.arange(k)
    excl_mask = np.abs(idx_arr[:, None] - idx_arr[None, :]) <= max(m // 2, 3)
    dist_mat[excl_mask] = np.inf
    if np.any(const_mask):
        dist_mat[const_mask, :] = np.inf
        dist_mat[:, const_mask] = np.inf

    mp = dist_mat.min(axis=1)
    mp_idx = dist_mat.argmin(axis=1)

    finite_mask = np.isfinite(mp)
    mp_dates = dates[:k]

    if np.any(finite_mask):
        i_motif = int(np.argmin(np.where(finite_mask, mp, np.inf)))
        j_motif = int(mp_idx[i_motif])
        motif_dist = float(mp[i_motif])
        motif_corr = 1.0 - (motif_dist ** 2) / (2.0 * m)

        i_disc = int(np.argmax(np.where(finite_mask, mp, -1.0)))
        disc_dist = float(mp[i_disc])
    else:
        i_motif, j_motif, motif_dist, motif_corr = 0, min(7, k - 1), 0.0, 0.0
        i_disc, disc_dist = 0, 0.0

    ax.plot(mp_dates[finite_mask], mp[finite_mask], color='#00f5d4',
            lw=1.6, label='7-Day Matrix Profile Distance')
    ax.fill_between(mp_dates[finite_mask], 0.0,
                    mp[finite_mask], color='#00f5d4', alpha=0.14)

    ax.scatter([mp_dates[i_motif], mp_dates[j_motif]], [mp[i_motif], mp[j_motif]],
               color='#39ff14', s=150, marker='*', edgecolors='white', lw=0.6, zorder=6,
               label=f'Motif Twins: {dates[i_motif].strftime("%m-%d")} & {dates[j_motif].strftime("%m-%d")} (r={motif_corr:.2f})')
    ax.scatter([mp_dates[i_disc]], [mp[i_disc]],
               color='#ff006e', s=130, marker='X', edgecolors='white', lw=0.6, zorder=6,
               label=f'Top-1 Weirdest Discord: {dates[i_disc].strftime("%m-%d")} (d={disc_dist:.2f})')

    max_mp = float(np.max(mp[finite_mask])) if np.any(finite_mask) else 4.0
    ax.set_ylim(0.0, max_mp * 1.65)
    ax.set_title('Matrix Profile: 7D Historical Twins (Motif) & Weirdest Week (Discord)',
                 color='#00f5d4', fontweight='bold')
    ax.set_ylabel('Z-Normalized Euclidean Distance')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=25)
    ax.legend(loc='upper left', fontsize=7.8, framealpha=0.85)
    ax.grid(alpha=0.15)

    # 内嵌小图：直接把那对“时空双胞胎周”叠在一起对比！
    ax_in = ax.inset_axes([0.56, 0.54, 0.41, 0.40])
    ax_in.set_facecolor('#0c1320')
    days_w = np.arange(m)
    ax_in.plot(days_w, z_sub[i_motif], color='#39ff14', lw=2.0, marker='o', ms=3.5,
               label=dates[i_motif].strftime('%m-%d'))
    ax_in.plot(days_w, z_sub[j_motif], color='#ffbe0b', lw=1.8, ls='--', marker='s', ms=3.5,
               label=dates[j_motif].strftime('%m-%d'))
    ax_in.set_title(f'Twin Weeks Overlay (r={motif_corr:.3f})',
                    fontsize=8, color='#39ff14', fontweight='bold')
    ax_in.tick_params(labelsize=7)
    ax_in.set_xticks(days_w)
    ax_in.set_xticklabels([f'D{d}' for d in days_w])
    ax_in.legend(loc='upper right', fontsize=7, framealpha=0.8)
    ax_in.grid(alpha=0.2)


# ==============================================================================
# 6. Science Nonlinear Causality: Sugihara Convergent Cross Mapping (CCM)
# ==============================================================================
def run_ccm_curve(source_x, target_y, E=4, tau=1, lib_sizes=None, n_draws=20):
    n = len(source_x)
    start = (E - 1) * tau
    m_len = n - start
    M_y = np.column_stack(
        [target_y[start - k * tau:n - k * tau] for k in range(E)])
    src_aligned = source_x[start:]

    rng = np.random.default_rng(42)
    M_y_jitter = M_y + rng.normal(0.0, 1e-8, size=M_y.shape)

    mean_rhos, std_rhos = [], []
    for L in lib_sizes:
        L_eff = min(L, m_len - 1)
        rhos = []
        for _ in range(n_draws):
            lib_idx = rng.choice(m_len, size=L_eff, replace=False)
            eval_mask = np.ones(m_len, dtype=bool)
            eval_mask[lib_idx] = False
            eval_idx = np.flatnonzero(eval_mask)
            if len(eval_idx) < 10:
                eval_idx = lib_idx

            nbrs = NearestNeighbors(n_neighbors=min(
                E + 2, L_eff)).fit(M_y_jitter[lib_idx])
            dists, inds = nbrs.kneighbors(M_y_jitter[eval_idx])

            # 排除极小零距离自匹配并取前 E+1 个邻居
            k_use = min(E + 1, dists.shape[1])
            d_sub = dists[:, :k_use]
            i_sub = inds[:, :k_use]

            d0 = np.maximum(d_sub[:, [0]], 1e-12)
            w = np.exp(-d_sub / d0)
            w /= np.maximum(w.sum(axis=1, keepdims=True), 1e-12)

            pred = np.sum(w * src_aligned[lib_idx[i_sub]], axis=1)
            obs = src_aligned[eval_idx]

            if np.std(pred) > 1e-12 and np.std(obs) > 1e-12:
                rhos.append(float(np.corrcoef(obs, pred)[0, 1]))
            else:
                rhos.append(0.0)
        mean_rhos.append(float(np.mean(rhos)))
        std_rhos.append(float(np.std(rhos)))

    return np.array(mean_rhos), np.array(std_rhos)


def plot_ccm_causality(ax, df):
    views = np.log1p(df['views'].values.astype(float))
    clones = np.log1p(df['clones'].values.astype(float))

    # 截取 Web 端正式有记录以后的连续区间（避开 4 月全 0 冷启动期）
    nz_views = np.flatnonzero(views > 0)
    if len(nz_views) > 0 and (len(views) - nz_views[0]) >= 60:
        s_idx = int(nz_views[0])
        views = views[s_idx:]
        clones = clones[s_idx:]

    E = 4
    m_len = len(clones) - (E - 1)
    max_L = max(30, m_len - 25)
    lib_sizes = np.unique(np.linspace(20, max_L, 10, dtype=int))

    # M_Clones xmap Views => 测试 Views -> Clones 的因果印记
    rho_v2c, std_v2c = run_ccm_curve(views, clones, E=E, lib_sizes=lib_sizes)
    # M_Views xmap Clones => 测试 Clones -> Views 的因果印记
    rho_c2v, std_c2v = run_ccm_curve(clones, views, E=E, lib_sizes=lib_sizes)

    ax.plot(lib_sizes, rho_v2c, color='#00f5d4', lw=2.2, marker='o', ms=4.5,
            label=f'Web → Clones  (ρ_max={rho_v2c[-1]:.3f})')
    ax.fill_between(lib_sizes, rho_v2c - std_v2c, rho_v2c +
                    std_v2c, color='#00f5d4', alpha=0.16)

    ax.plot(lib_sizes, rho_c2v, color='#ff00ff', lw=2.2, marker='s', ms=4.5,
            label=f'Clones → Web  (ρ_max={rho_c2v[-1]:.3f})')
    ax.fill_between(lib_sizes, rho_c2v - std_c2v, rho_c2v +
                    std_c2v, color='#ff00ff', alpha=0.16)

    ax.axhline(0.0, color='#adb5bd', ls='--', lw=1.1, alpha=0.7)

    delta_v2c = float(rho_v2c[-1] - rho_v2c[0])
    delta_c2v = float(rho_c2v[-1] - rho_c2v[0])
    if max(rho_v2c[-1], rho_c2v[-1]) < 0.15:
        verdict = 'Parallel Universes (Zero Nonlinear Coupling)'
    elif rho_v2c[-1] > rho_c2v[-1]:
        verdict = 'Web Faintly Drives Terminal Clones'
    else:
        verdict = 'Terminal Clones Pull Web Visitors'

    ax.set_title('Sugihara CCM: Nonlinear Shadow Manifold Causality (Science)',
                 color='#ff4d6d', fontweight='bold')
    ax.set_xlabel('Library Length L (Shadow Manifold Samples)')
    ax.set_ylabel('Cross-Mapping Skill ρ(L)')
    ax.set_ylim(min(-0.25, min(rho_v2c.min(), rho_c2v.min()) - 0.12),
                max(0.45, max(rho_v2c.max(), rho_c2v.max()) + 0.15))
    ax.legend(loc='upper left', fontsize=8.2, framealpha=0.85)
    ax.grid(alpha=0.15)

    info = (
        f"Manifold Embedding E: {E}\n"
        f"Convergence Δρ (W→C): {delta_v2c:+.3f}\n"
        f"Convergence Δρ (C→W): {delta_c2v:+.3f}\n"
        f"Verdict: {verdict}"
    )
    ax.text(0.03, 0.05, info, transform=ax.transAxes, va='bottom', fontsize=8.3,
            color='#ff4d6d', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#ff4d6d', alpha=0.88))


def main():
    print('⚛️ Pod 042: Initiating Quantum Metaphysics & Reality Audit (v10.0)...')
    df = load_bunker_data()
    dates = df.index
    y = df['clones'].values.astype(float)

    fig = plt.figure(figsize=(20, 18), facecolor='#04060a')

    ax1 = fig.add_subplot(3, 2, 1, facecolor='#080c14')
    ax2 = fig.add_subplot(3, 2, 2, facecolor='#080c14')
    ax3 = fig.add_subplot(3, 2, 3, facecolor='#080c14')
    ax4 = fig.add_subplot(3, 2, 4, projection='3d')
    ax5 = fig.add_subplot(3, 2, 5, facecolor='#080c14')
    ax6 = fig.add_subplot(3, 2, 6, facecolor='#080c14')

    plot_schrodinger_well(ax1, y)
    plot_evt_return_period(ax2, y)
    plot_random_matrix_theory(ax3, y)
    plot_3d_attractor(ax4, dates, y)
    plot_matrix_profile(ax5, dates, y)
    plot_ccm_causality(ax6, df)

    fig.suptitle(
        'Bunker Quantum Metaphysics (Schrödinger + EVT Flood + Random Matrix + 3D Chaos + Matrix Profile + CCM)',
        color='#ff00ff', fontsize=16.5, fontweight='bold', y=0.975
    )

    fig.subplots_adjust(left=0.055, right=0.955, top=0.925,
                        bottom=0.055, hspace=0.33, wspace=0.24)
    out_dir = os.path.dirname(OUTPUT_IMAGE)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    plt.savefig(OUTPUT_IMAGE, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'✅ Quantum Metaphysics archived at: {OUTPUT_IMAGE}')


if __name__ == '__main__':
    main()
