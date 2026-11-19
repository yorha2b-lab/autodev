from scipy.sparse import csgraph
from scipy.optimize import minimize
from scipy.stats import gaussian_kde, t as student_t
import pandas as pd
import numpy as np
from matplotlib.collections import LineCollection
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import os
import math
from collections import deque

import matplotlib
matplotlib.use('Agg')


OUTPUT_IMAGE = 'plots/bunker_cosmic_frontier.png'

plt.style.use('dark_background')


def load_bunker_data():
    c_path = 'ghrs-data/clones_ledger.csv'
    if not os.path.exists(c_path):
        raise FileNotFoundError(f'Missing required ledger: {c_path}')

    df = pd.read_csv(c_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').drop_duplicates('date', keep='last')

    # 自动按完整自然日补齐（防止 GitHub API 跳过 0 次日导致时序断裂）
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
# 1. Complex Network: Lacasa Natural Visibility Graph
# ==============================================================================
def compute_visibility_graph(y):
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
    dist = csgraph.shortest_path(adj, directed=False, unweighted=True)
    triu = np.triu_indices(n, k=1)
    avg_path = float(np.mean(dist[triu])) if n > 1 else 0.0

    a3_diag = np.diag(adj @ adj @ adj)
    denom = deg * (deg - 1.0)
    cc = np.where(denom > 0, a3_diag / np.maximum(denom, 1.0), 0.0)
    avg_cc = float(np.mean(cc))

    # Brandes exact unweighted Betweenness Centrality
    bc = np.zeros(n, dtype=float)
    neighbors = [np.flatnonzero(adj[v]) for v in range(n)]
    for s in range(n):
        stack = []
        pred = [[] for _ in range(n)]
        sigma = np.zeros(n, dtype=float)
        sigma[s] = 1.0
        dist_v = np.full(n, -1, dtype=int)
        dist_v[s] = 0
        q = deque([s])
        while q:
            v = q.popleft()
            stack.append(v)
            for w in neighbors[v]:
                if dist_v[w] < 0:
                    q.append(w)
                    dist_v[w] = dist_v[v] + 1
                if dist_v[w] == dist_v[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        delta = np.zeros(n, dtype=float)
        while stack:
            w = stack.pop()
            for v in pred[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != s:
                bc[w] += delta[w]
    if n > 2:
        bc /= ((n - 1) * (n - 2))

    return adj, deg, bc, avg_path, avg_cc


def plot_visibility_graph(ax, dates, y):
    n = len(y)
    adj, deg, bc, avg_path, avg_cc = compute_visibility_graph(y)
    hub_idx = int(np.argmax(deg))

    u_grid = np.linspace(0.0, 1.0, 20)
    normal_segs = []
    hub_segs = []

    rows, cols = np.where(np.triu(adj, k=1) > 0)
    for i, j in zip(rows, cols):
        x_arc = i + (j - i) * u_grid
        height = np.sqrt(j - i)
        y_arc = height * 4.0 * u_grid * (1.0 - u_grid)
        pts = np.column_stack([x_arc, y_arc])
        if i == hub_idx or j == hub_idx:
            hub_segs.append(pts)
        else:
            normal_segs.append(pts)

    if normal_segs:
        lc_norm = LineCollection(
            normal_segs, colors='#00f5d4', linewidths=0.55, alpha=0.14)
        ax.add_collection(lc_norm)
    if hub_segs:
        lc_hub = LineCollection(
            hub_segs, colors='#ff00aa', linewidths=1.05, alpha=0.62)
        ax.add_collection(lc_hub)

    # 底部节点度分布散点
    sizes = 8.0 + (deg / max(deg.max(), 1.0)) * 120.0
    sc = ax.scatter(np.arange(n), np.zeros(n), s=sizes, c=deg, cmap='plasma',
                    edgecolors='white', linewidths=0.3, zorder=4)
    ax.scatter([hub_idx], [0.0], s=180, color='#ffea00', marker='*',
               edgecolors='white', linewidths=0.6, zorder=5)

    ax.annotate(
        f"APEX HUB: {int(y[hub_idx])} ({dates[hub_idx].strftime('%m-%d')})\n"
        f"deg={int(deg[hub_idx])}, BC={bc[hub_idx]:.2f}",
        xy=(hub_idx, 0.2),
        xytext=(min(n - 1, hub_idx + max(10, n // 8)), np.sqrt(n) * 0.72),
        color='#ffea00', fontsize=9, fontweight='bold',
        arrowprops=dict(arrowstyle='->', color='#ffea00', lw=1.2)
    )

    ticks = np.linspace(0, n - 1, min(8, n), dtype=int)
    ax.set_xticks(ticks)
    ax.set_xticklabels([dates[t].strftime('%m-%d')
                       for t in ticks], rotation=25)
    ax.set_xlim(-3, n + 3)
    ax.set_ylim(-1.2, np.sqrt(n) * 1.15)
    ax.set_yticks([])
    ax.set_title('Visibility Graph Complex Network (Lacasa Topology)',
                 color='#00f5d4', fontweight='bold')
    ax.set_xlabel('Timeline (Nodes = Days | Arcs = Line-of-Sight Bridges)')

    info = (
        f"Nodes / Edges: {n} / {len(rows)}\n"
        f"Avg Degree <k>: {deg.mean():.2f} (Max {int(deg.max())})\n"
        f"Clustering Coeff: {avg_cc:.3f}\n"
        f"Avg Shortest Path: {avg_path:.2f}"
    )
    ax.text(0.02, 0.96, info, transform=ax.transAxes, va='top', fontsize=8.5,
            color='#00f5d4', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#00f5d4', alpha=0.88))
    ax.grid(alpha=0.14, axis='x')


# ==============================================================================
# 2. Statistical Physics: Langevin / Boltzmann Effective Potential & Drift
# ==============================================================================
def plot_langevin_potential(ax, y):
    x = np.log1p(y)
    grid = np.linspace(max(0.0, x.min() - 0.2), x.max() + 0.25, 320)

    kde = gaussian_kde(x, bw_method='scott')
    pdf = np.maximum(kde(grid), 1e-12)
    potential = -np.log(pdf)
    potential -= potential.min()

    # Nadaraya-Watson 局部漂移力 D^(1)(x) = E[dx | x]
    dx = np.diff(x)
    x_prev = x[:-1]
    bw = max(float(np.std(x)) * 0.45, 0.25)
    drift = np.zeros_like(grid)
    weights_sum = np.zeros_like(grid)
    for idx, g in enumerate(grid):
        w = np.exp(-0.5 * ((x_prev - g) / bw) ** 2)
        weights_sum[idx] = w.sum()
        drift[idx] = (w @ dx) / max(w.sum(), 1e-9)

    ax.plot(grid, potential, color='#00bbf9', lw=2.5,
            label='Effective Potential U(x) = -ln P(x)')
    ax.fill_between(grid, potential, potential.max() *
                    1.05, color='#00bbf9', alpha=0.12)

    well_idx = int(np.argmin(potential))
    well_x = grid[well_idx]
    well_clones = np.expm1(well_x)
    ax.scatter([well_x], [potential[well_idx]], color='#39ff14', s=150, marker='*',
               zorder=6, label=f'Ground State Well (~{well_clones:.1f} clones/d)')

    x_peak = x.max()
    u_peak = float(np.interp(x_peak, grid, potential))
    ax.scatter([x_peak], [u_peak], color='#ff006e', s=95, marker='D', zorder=6,
               label=f'Peak {int(y.max())} Barrier (ΔU={u_peak:.2f} kT)')

    # 次坐标叠加回复漂移力 D^(1)(x)
    ax2 = ax.twinx()
    valid = weights_sum > 1.2
    ax2.plot(grid[valid], drift[valid], color='#ff9e00', ls='--', lw=1.8, alpha=0.9,
             label='Langevin Drift Force D⁽¹⁾(x)')
    ax2.axhline(0.0, color='#ff9e00', ls=':', lw=0.9, alpha=0.45)
    ax2.set_ylabel(
        'Drift Force D⁽¹⁾(x)  [+Push Up / -Pull Back]', color='#ff9e00')
    ax2.tick_params(axis='y', colors='#ff9e00')

    ax.set_title('Langevin Potential Well & Restoring Force (Fokker-Planck)',
                 color='#00bbf9', fontweight='bold')
    ax.set_xlabel('System State x = Log(Clones + 1)')
    ax.set_ylabel('Effective Potential Energy U(x) [k_B T]', color='#00bbf9')
    ax.grid(alpha=0.16)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2,
              loc='upper left', fontsize=8, framealpha=0.82)


# ==============================================================================
# 3. Symbolic Dynamics: Bandt-Pompe Complexity-Entropy Causality Plane
# ==============================================================================
def bandt_pompe_ch(series, D=4):
    s = np.asarray(series, dtype=float)
    n = len(s)
    if n < D + 10:
        D = 3
    M = math.factorial(D)

    # 微小确定性扰动以打破整数相等时的排序平局
    s_tie = s + np.linspace(0.0, 1e-9, n)
    windows = np.lib.stride_tricks.sliding_window_view(s_tie, D)
    patterns = np.argsort(windows, axis=1, kind='mergesort')
    _, counts = np.unique(patterns, axis=0, return_counts=True)

    p = np.zeros(M, dtype=float)
    p[:len(counts)] = counts / counts.sum()

    nz = p > 0
    s_p = float(-np.sum(p[nz] * np.log(p[nz])))
    h_s = s_p / np.log(M)

    pe = np.full(M, 1.0 / M)
    p_avg = 0.5 * (p + pe)
    nz_a = p_avg > 0
    s_avg = float(-np.sum(p_avg[nz_a] * np.log(p_avg[nz_a])))
    jsd = max(s_avg - 0.5 * s_p - 0.5 * np.log(M), 0.0)

    q0 = -2.0 / (((M + 1.0) / M) * np.log(M + 1.0) -
                 2.0 * np.log(2.0 * M) + np.log(M))
    c_js = q0 * jsd * h_s
    return h_s, c_js


def ch_theoretical_bounds(D=4):
    M = math.factorial(D)
    q0 = -2.0 / (((M + 1.0) / M) * np.log(M + 1.0) -
                 2.0 * np.log(2.0 * M) + np.log(M))
    pe = np.full(M, 1.0 / M)

    def eval_hc(p):
        nz = p > 1e-15
        s_p = float(-np.sum(p[nz] * np.log(p[nz])))
        h = s_p / np.log(M)
        p_avg = 0.5 * (p + pe)
        nz_a = p_avg > 1e-15
        s_avg = float(-np.sum(p_avg[nz_a] * np.log(p_avg[nz_a])))
        jsd = max(s_avg - 0.5 * s_p - 0.5 * np.log(M), 0.0)
        return h, q0 * jsd * h

    # Lower bound C_min
    h_min, c_min = [], []
    for r in np.linspace(0.0, 1.0 / M, 180):
        p = np.full(M, r)
        p[0] = max(0.0, 1.0 - (M - 1) * r)
        h, c = eval_hc(p)
        h_min.append(h)
        c_min.append(c)

    # Upper bound C_max
    h_max, c_max = [], []
    for k in range(M - 1):
        m_rem = M - 1 - k
        for r in np.linspace(1.0 / (M - k), 1.0 / m_rem, 25):
            p = np.zeros(M)
            p[k:M - 1] = r
            p[M - 1] = max(0.0, 1.0 - m_rem * r)
            h, c = eval_hc(p)
            h_max.append(h)
            c_max.append(c)

    order_min = np.argsort(h_min)
    order_max = np.argsort(h_max)
    return (np.array(h_min)[order_min], np.array(c_min)[order_min],
            np.array(h_max)[order_max], np.array(c_max)[order_max])


def plot_ch_plane(ax, df):
    D = 4 if len(df) >= 60 else 3
    h_min, c_min, h_max, c_max = ch_theoretical_bounds(D)

    ax.plot(h_max, c_max, color='#a8dadc', lw=1.6,
            ls='--', label='Theoretical C_max / C_min')
    ax.plot(h_min, c_min, color='#a8dadc', lw=1.6, ls='--')
    h_grid = np.linspace(0, 1, 200)
    ax.fill_between(h_grid, np.interp(h_grid, h_min, c_min),
                    np.interp(h_grid, h_max, c_max), color='#457b9d', alpha=0.14)

    # 物理学标准参照物
    rng = np.random.default_rng(42)
    white_noise = rng.normal(size=2000)
    lx = 0.123456
    logistic = []
    for i in range(1300):
        lx = 4.0 * lx * (1.0 - lx)
        if i >= 300:
            logistic.append(lx)
    sine_7d = np.sin(2.0 * np.pi * np.arange(500) / 7.0)

    h_wn, c_wn = bandt_pompe_ch(white_noise, D)
    h_lg, c_lg = bandt_pompe_ch(logistic, D)
    h_sn, c_sn = bandt_pompe_ch(sine_7d, D)
    h_cl, c_cl = bandt_pompe_ch(df['clones'].values, D)
    h_uc, c_uc = bandt_pompe_ch(df['uniques'].values, D)

    ax.scatter([h_lg], [c_lg], color='#ff00ff', marker='^', s=110, zorder=5,
               label=f'Logistic Chaos r=4 ({h_lg:.2f}, {c_lg:.2f})')
    ax.scatter([h_sn], [c_sn], color='#39ff14', marker='s', s=95, zorder=5,
               label=f'7D Periodic Sine ({h_sn:.2f}, {c_sn:.2f})')
    ax.scatter([h_wn], [c_wn], color='#e0e0e0', marker='o', s=95, zorder=5,
               label=f'Gaussian White Noise ({h_wn:.2f}, {c_wn:.2f})')

    ax.scatter([h_uc], [c_uc], color='#00f5d4', marker='D', s=130, edgecolors='white', lw=0.8, zorder=6,
               label=f'Bunker Unique Cloners ({h_uc:.2f}, {c_uc:.2f})')
    ax.scatter([h_cl], [c_cl], color='#ffea00', marker='*', s=260, edgecolors='white', lw=0.8, zorder=7,
               label=f'BUNKER CLONES ({h_cl:.2f}, {c_cl:.2f})')

    ax.set_xlim(-0.02, 1.03)
    ax.set_ylim(-0.02, max(c_max.max() * 1.12, 0.45))
    ax.set_title(
        f'Complexity-Entropy Causality Plane (Bandt-Pompe D={D})', color='#ff00ff', fontweight='bold')
    ax.set_xlabel('Normalized Permutation Entropy H_S  [0=Order -> 1=Random]')
    ax.set_ylabel('MPR Statistical Complexity C_JS')
    ax.legend(loc='upper left', fontsize=8, framealpha=0.85)
    ax.grid(alpha=0.16)


# ==============================================================================
# 4. Epidemiology & Seismology: Kaplan-Meier Survival & Discrete Hawkes Process
# ==============================================================================
def plot_hawkes_kaplan_meier(ax, y):
    n = len(y)
    med = float(np.median(y))
    mad_sigma = 1.4826 * float(np.median(np.abs(y - med)))
    thr = med + 3.0 * max(mad_sigma, 1.0)
    events = (y > thr).astype(int)

    if events.sum() < 3:
        thr = float(np.percentile(y, 90))
        events = (y > thr).astype(int)

    idx = np.flatnonzero(events == 1)
    if len(idx) >= 2:
        gaps = np.diff(idx).astype(float)
        obs = np.ones_like(gaps)
        trailing_calm = float(n - 1 - idx[-1])
        if trailing_calm > 0:
            durations = np.append(gaps, trailing_calm)
            observed = np.append(obs, 0.0)
        else:
            durations = gaps
            observed = obs
    else:
        durations = np.array([float(n)])
        observed = np.array([0.0])

    # Exact Kaplan-Meier Estimator + Greenwood 95% CI
    unique_t = np.sort(np.unique(durations[observed == 1]))
    km_t = [0.0]
    km_s = [1.0]
    km_lo = [1.0]
    km_hi = [1.0]
    s_cur = 1.0
    var_sum = 0.0

    for t_val in unique_t:
        at_risk = float(np.sum(durations >= t_val))
        d_i = float(np.sum((durations == t_val) & (observed == 1)))
        if at_risk > 0 and d_i > 0:
            s_cur *= (1.0 - d_i / at_risk)
            if at_risk > d_i:
                var_sum += d_i / (at_risk * (at_risk - d_i))
            se = s_cur * np.sqrt(var_sum)
            km_t.append(t_val)
            km_s.append(s_cur)
            km_lo.append(max(0.0, s_cur - 1.96 * se))
            km_hi.append(min(1.0, s_cur + 1.96 * se))

    max_t = max(float(durations.max()), 15.0)
    if km_t[-1] < max_t:
        km_t.append(max_t)
        km_s.append(km_s[-1])
        km_lo.append(km_lo[-1])
        km_hi.append(km_hi[-1])

    # Discrete Hawkes Self-Exciting MLE: lambda_t = mu + alpha * sum_{s<t} I_s exp(-beta*(t-s))
    base_rate = max(float(events.mean()), 1e-3)

    def hawkes_nll(params):
        mu, alpha, beta = params
        if mu <= 1e-6 or alpha < 0 or beta <= 0.01:
            return 1e12
        r_hist = 0.0
        nll = 0.0
        decay = np.exp(-beta)
        for t in range(n):
            lam = max(mu + alpha * r_hist, 1e-8)
            nll += lam - events[t] * np.log(lam)
            r_hist = decay * (r_hist + events[t])
        return nll

    res = minimize(hawkes_nll, x0=[base_rate * 0.7, 0.2, 0.5],
                   bounds=[(1e-5, 0.8), (0.0, 3.0), (0.05, 4.0)], method='L-BFGS-B')
    mu_hat, alpha_hat, beta_hat = res.x
    branching_ratio = float(alpha_hat / max(np.exp(beta_hat) - 1.0, 1e-6))
    aftershock_hl = float(np.log(2.0) / beta_hat)

    # 绘图
    ax.step(km_t, km_s, where='post', color='#00f5d4',
            lw=2.4, label='KM Calm-Spell Survival S(t)')
    ax.fill_between(km_t, km_lo, km_hi, step='post',
                    color='#00f5d4', alpha=0.16, label='Greenwood 95% CI')

    t_grid = np.linspace(0, max_t, 200)
    lam_null = float(np.sum(observed) / max(np.sum(durations), 1.0))
    ax.plot(t_grid, np.exp(-lam_null * t_grid), color='#adb5bd', ls='--', lw=1.6,
            label=f'Memoryless Poisson Null (λ={lam_null:.3f}/d)')

    ax.axhline(0.5, color='#ffbe0b', ls=':', lw=1.1, alpha=0.7)
    ax.set_xlim(0, max_t)
    ax.set_ylim(-0.03, 1.05)
    ax.set_title('Calm Survival (Kaplan-Meier) & Hawkes Aftershocks',
                 color='#39ff14', fontweight='bold')
    ax.set_xlabel(f'Days Without Blitz Attack (Threshold > {thr:.0f} clones)')
    ax.set_ylabel('Survival Probability S(t)')
    ax.legend(loc='upper right', fontsize=8, framealpha=0.85)
    ax.grid(alpha=0.16)

    calm_now = int(n - 1 - idx[-1]) if len(idx) > 0 else n
    med_surv = next((t for t, s in zip(km_t, km_s) if s <= 0.5), None)
    med_str = f'{med_surv:.0f}d' if med_surv is not None else f'>{max_t:.0f}d'

    info = (
        f"Blitz Events: {int(events.sum())} (Thr > {thr:.0f})\n"
        f"Median Calm Spell: {med_str}\n"
        f"Current Calm Streak: {calm_now}d\n"
        f"Hawkes Branching η: {branching_ratio:.3f}\n"
        f"Aftershock Half-Life: {aftershock_hl:.2f}d"
    )
    ax.text(0.03, 0.05, info, transform=ax.transAxes, va='bottom', fontsize=8.5,
            color='#39ff14', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#39ff14', alpha=0.88))


# ==============================================================================
# 5. Wall Street Risk Desk: GARCH(1,1) Volatility Clustering & Bubble Drawdown
# ==============================================================================
def plot_garch_volatility(ax, dates, y):
    log_y = np.log1p(y)
    r = np.diff(log_y)
    r_c = r - np.mean(r)
    var_r = max(float(np.var(r_c)), 1e-6)
    n_r = len(r_c)

    def garch_nll(params):
        omega, alpha, beta = params
        if omega <= 1e-9 or alpha < 0 or beta < 0 or (alpha + beta) >= 0.996:
            return 1e12
        sig2 = np.empty(n_r)
        sig2[0] = var_r
        for t in range(1, n_r):
            sig2[t] = omega + alpha * (r_c[t - 1] ** 2) + beta * sig2[t - 1]
        return 0.5 * float(np.sum(np.log(sig2) + (r_c ** 2) / sig2))

    res = minimize(garch_nll, x0=[0.08 * var_r, 0.12, 0.78],
                   bounds=[(1e-7, 10.0 * var_r), (0.0, 0.65), (0.0, 0.98)],
                   method='L-BFGS-B')
    omega, alpha, beta = res.x
    sig2 = np.empty(n_r)
    sig2[0] = var_r
    for t in range(1, n_r):
        sig2[t] = omega + alpha * (r_c[t - 1] ** 2) + beta * sig2[t - 1]
    sigma_t = np.sqrt(sig2)

    persistence = float(alpha + beta)
    half_life = np.log(
        0.5) / np.log(persistence) if 0.0 < persistence < 1.0 else np.inf

    # 99% VaR / CVaR on daily log-returns
    var_99 = float(np.percentile(r, 1))
    tail = r[r <= var_99]
    cvar_99 = float(tail.mean()) if len(tail) > 0 else var_99

    # EWMA-7 Momentum Underwater Drawdown (%)
    ewma7 = pd.Series(y).ewm(span=7, adjust=False).mean().values
    running_max = np.maximum(np.maximum.accumulate(ewma7), 1e-9)
    drawdown = (ewma7 - running_max) / running_max * 100.0
    max_dd = float(drawdown.min())

    d_ret = dates[1:]
    ax.bar(d_ret, np.abs(r_c), width=0.8, color='#495057',
           alpha=0.45, label='|Log Return| Shock')
    ax.plot(d_ret, sigma_t, color='#ffbe0b', lw=2.1,
            label='GARCH(1,1) Volatility σ_t')

    ax2 = ax.twinx()
    ax2.plot(dates, drawdown, color='#ff4d6d', lw=1.2,
             alpha=0.85, label='EWMA-7 Drawdown (%)')
    ax2.fill_between(dates, drawdown, 0.0, color='#ff4d6d', alpha=0.14)
    ax2.set_ylim(-105, 8)
    ax2.set_ylabel('Momentum Underwater Drawdown (%)', color='#ff4d6d')
    ax2.tick_params(axis='y', colors='#ff4d6d')

    ax.set_title('Quant Risk Desk: GARCH(1,1) Volatility & Drawdown',
                 color='#ffbe0b', fontweight='bold')
    ax.set_ylabel('Conditional Volatility σ_t (Log Space)', color='#ffbe0b')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=25)
    ax.grid(alpha=0.15)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2,
              loc='upper right', fontsize=8, framealpha=0.85)

    hl_str = f'{half_life:.1f}d' if np.isfinite(half_life) else '∞'
    info = (
        f"GARCH Persistence (α+β): {persistence:.3f}\n"
        f"Shock Vol Half-Life: {hl_str}\n"
        f"99% VaR / CVaR: {var_99:.2f} / {cvar_99:.2f}\n"
        f"Max EWMA-7 Drawdown: {max_dd:.1f}%"
    )
    ax.text(0.02, 0.96, info, transform=ax.transAxes, va='top', fontsize=8.5,
            color='#ffbe0b', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#ffbe0b', alpha=0.88))


# ==============================================================================
# 6. Bayesian Chronology: Adams-MacKay BOCPD Changepoints
# ==============================================================================
def plot_bocpd_regimes(ax, dates, y):
    x = np.log1p(y)
    n = len(x)
    hazard = 1.0 / 35.0

    mu0 = float(np.mean(x[:min(14, n)]))
    kappa0 = 0.5
    alpha0 = 1.5
    beta0 = max(float(np.var(x)) * 0.8, 0.1)

    R = np.array([1.0])
    mu = np.array([mu0])
    kappa = np.array([kappa0])
    alpha = np.array([alpha0])
    beta = np.array([beta0])

    expected_rl = np.zeros(n)
    map_rl = np.zeros(n, dtype=int)
    regime_mean = np.zeros(n)

    for t in range(n):
        scale = np.sqrt(beta * (kappa + 1.0) / (alpha * kappa))
        pred_probs = np.maximum(student_t.pdf(
            x[t], df=2.0 * alpha, loc=mu, scale=scale), 1e-300)

        growth = R * pred_probs * (1.0 - hazard)
        cp = float(np.sum(R * pred_probs * hazard))
        new_R = np.concatenate([[cp], growth])
        s = new_R.sum()
        if s > 0:
            new_R /= s
        else:
            new_R = np.zeros_like(new_R)
            new_R[0] = 1.0

        rls = np.arange(len(new_R))
        expected_rl[t] = float(np.sum(rls * new_R))
        map_rl[t] = int(np.argmax(new_R))

        kappa_n = kappa + 1.0
        mu_n = (kappa * mu + x[t]) / kappa_n
        alpha_n = alpha + 0.5
        beta_n = beta + 0.5 * kappa * ((x[t] - mu) ** 2) / kappa_n

        mu = np.concatenate([[mu0], mu_n])
        kappa = np.concatenate([[kappa0], kappa_n])
        alpha = np.concatenate([[alpha0], alpha_n])
        beta = np.concatenate([[beta0], beta_n])
        R = new_R
        regime_mean[t] = float(np.sum(mu * R))

    # 识别真正的时代变点（MAP 时代年龄出现大跳水）
    changepoints = []
    for t in range(1, n):
        if (map_rl[t - 1] - map_rl[t] >= 7) and (map_rl[t] <= 4):
            if not changepoints or (t - changepoints[-1] >= 7):
                changepoints.append(t)

    ax.scatter(dates, x, color='#4cc9f0', s=14,
               alpha=0.55, label='Observed Log(Clones+1)')
    ax.plot(dates, regime_mean, color='#39ff14',
            lw=2.2, label='Bayesian Adaptive Mean μ_t')

    for cp_t in changepoints:
        ax.axvline(dates[cp_t], color='#ff00ff', ls='--', lw=1.3, alpha=0.8)
        ax.text(dates[cp_t], x.max() * 0.96, f" {dates[cp_t].strftime('%m-%d')}",
                color='#ff00ff', fontsize=8, fontweight='bold', rotation=90, va='top')

    ax2 = ax.twinx()
    ax2.plot(dates, expected_rl, color='#f72585', lw=1.4,
             alpha=0.85, label='Expected Era Age E[r_t]')
    ax2.fill_between(dates, 0.0, expected_rl, color='#f72585', alpha=0.14)
    ax2.set_ylabel('Bayesian Era Age E[r_t] (Days)', color='#f72585')
    ax2.tick_params(axis='y', colors='#f72585')

    ax.set_title('Bayesian Online Changepoints (BOCPD Era Segmentation)',
                 color='#f72585', fontweight='bold')
    ax.set_ylabel('Log(Clones + 1)', color='#4cc9f0')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=25)
    ax.grid(alpha=0.15)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2,
              loc='upper right', fontsize=8, framealpha=0.85)

    cur_clones = np.expm1(regime_mean[-1])
    info = (
        f"Paradigm Shifts Detected: {len(changepoints)}\n"
        f"Current Era Age: {expected_rl[-1]:.1f} days\n"
        f"Posterior Mean: ~{cur_clones:.1f} clones/d"
    )
    ax.text(0.02, 0.96, info, transform=ax.transAxes, va='top', fontsize=8.5,
            color='#f72585', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#f72585', alpha=0.88))


def main():
    print('🛸 Pod 042: Engaging Cosmic Frontier Protocol (v9.0)...')
    df = load_bunker_data()
    dates = df.index
    y = df['clones'].values.astype(float)

    fig, axes = plt.subplots(3, 2, figsize=(20, 18), facecolor='#04060a')
    for ax in axes.flat:
        ax.set_facecolor('#080c14')

    plot_visibility_graph(axes[0, 0], dates, y)
    plot_langevin_potential(axes[0, 1], y)
    plot_ch_plane(axes[1, 0], df)
    plot_hawkes_kaplan_meier(axes[1, 1], y)
    plot_garch_volatility(axes[2, 0], dates, y)
    plot_bocpd_regimes(axes[2, 1], dates, y)

    fig.suptitle(
        'Bunker Cosmic Frontier (Visibility Graph + Langevin + CH-Plane + Hawkes + GARCH + BOCPD)',
        color='#00f5d4', fontsize=17, fontweight='bold', y=0.98
    )

    plt.tight_layout(rect=[0.01, 0.01, 0.985, 0.955], h_pad=3.2, w_pad=4.0)
    out_dir = os.path.dirname(OUTPUT_IMAGE)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    plt.savefig(OUTPUT_IMAGE, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'✅ Cosmic Frontier sealed at: {OUTPUT_IMAGE}')


if __name__ == '__main__':
    main()
