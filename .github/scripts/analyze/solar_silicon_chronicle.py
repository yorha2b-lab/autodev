from sklearn.preprocessing import StandardScaler
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist
from scipy.spatial import Voronoi
from scipy.signal import butter, sosfiltfilt, hilbert
from scipy.linalg import solve_toeplitz
import pandas as pd
import numpy as np
from matplotlib.patches import Wedge
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import os
import warnings

import matplotlib
matplotlib.use('Agg')


OUTPUT_IMAGE = 'plots/bunker_solar_silicon.png'

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

    v_path = 'ghrs-data/views_ledger.csv'
    if os.path.exists(v_path):
        v_df = pd.read_csv(v_path)
        v_df['date'] = pd.to_datetime(v_df['date'])
        v_df = v_df.sort_values('date').drop_duplicates('date', keep='last')
        v_df = v_df.set_index('date').reindex(full_idx).fillna(0.0)
        df['views'] = v_df['views'].values
    else:
        df['views'] = 0.0

    return df


# 2026 年真实公历二十四节气时间表 (太阳黄经 0° = 春分)
SOLAR_TERMS_2026 = [
    ('2026-01-05', '小寒', 'XiaoHan', 285.0),
    ('2026-01-20', '大寒', 'DaHan', 300.0),
    ('2026-02-04', '立春', 'LiChun', 315.0),
    ('2026-02-18', '雨水', 'YuShui', 330.0),
    ('2026-03-05', '惊蛰', 'JingZhe', 345.0),
    ('2026-03-20', '春分', 'ChunFen', 0.0),
    ('2026-04-05', '清明', 'QingMing', 15.0),
    ('2026-04-20', '谷雨', 'GuYu', 30.0),
    ('2026-05-05', '立夏', 'LiXia', 45.0),
    ('2026-05-21', '小满', 'XiaoMan', 60.0),
    ('2026-06-05', '芒种', 'MangZhong', 75.0),
    ('2026-06-21', '夏至', 'XiaZhi', 90.0),
    ('2026-07-07', '小暑', 'XiaoShu', 105.0),
    ('2026-07-23', '大暑', 'DaShu', 120.0),
    ('2026-08-07', '立秋', 'LiQiu', 135.0),
    ('2026-08-23', '处暑', 'ChuShu', 150.0),
    ('2026-09-07', '白露', 'BaiLu', 165.0),
    ('2026-09-23', '秋分', 'QiuFen', 180.0),
    ('2026-10-08', '寒露', 'HanLu', 195.0),
    ('2026-10-23', '霜降', 'ShuangJiang', 210.0),
    ('2026-11-07', '立冬', 'LiDong', 225.0),
    ('2026-11-22', '小雪', 'XiaoXue', 240.0),
    ('2026-12-07', '大雪', 'DaXue', 255.0),
    ('2026-12-22', '冬至', 'DongZhi', 270.0),
]


# ==============================================================================
# 1. 二十四节气太阳黄经罗盘 (24 Solar Terms Celestial Wheel)
# ==============================================================================
def plot_solar_terms_wheel(ax, dates, y):
    term_dates = [pd.Timestamp(t[0]) for t in SOLAR_TERMS_2026]
    term_stats = []

    for i in range(len(SOLAR_TERMS_2026)):
        t_start = term_dates[i]
        t_end = term_dates[i + 1] if i + \
            1 < len(SOLAR_TERMS_2026) else pd.Timestamp('2027-01-05')
        mask = (dates >= t_start) & (dates < t_end)
        vals = y[mask]
        term_stats.append((
            SOLAR_TERMS_2026[i][1] if HAS_CJK else SOLAR_TERMS_2026[i][2],
            SOLAR_TERMS_2026[i][3],
            float(np.mean(vals)) if len(vals) > 0 else 0.0,
            float(np.max(vals)) if len(vals) > 0 else 0.0,
            len(vals),
        ))

    max_mean = max([s[2] for s in term_stats] + [1.0])
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)

    angles = []
    heights = []
    colors = []
    width = (2.0 * np.pi / 24.0) * 0.88

    for name, lam, mean_v, max_v, cnt in term_stats:
        # 让 夏至(90°) 对准正北 12 点钟方向 (0°)，顺时针推进至 秋分/冬至/春分
        ang_deg = (lam - 90.0) % 360.0
        ang_rad = np.deg2rad(ang_deg)
        angles.append(ang_rad)
        if cnt > 0:
            heights.append(0.35 + 0.65 * (mean_v / max_mean))
            colors.append(plt.get_cmap('plasma')(min(1.0, mean_v / max_mean)))
        else:
            heights.append(0.18)
            colors.append('#1b263b')

    bars = ax.bar(angles, heights, width=width, bottom=0.18, color=colors,
                  edgecolor='#00f5d4', linewidth=0.7, alpha=0.88)

    # 标注已测节气名称与旺季尖峰
    for i, (name, lam, mean_v, max_v, cnt) in enumerate(term_stats):
        ang = angles[i]
        r_lbl = (heights[i] + 0.30) if cnt > 0 else 0.48
        c_lbl = '#ffea00' if max_v == y.max() else ('#e0fbfc' if cnt > 0 else '#555b6e')
        fw = 'bold' if (cnt > 0 and mean_v >= 0.55 * max_mean) else 'normal'
        lbl = f'{name}\n{mean_v:.0f}' if cnt > 0 else name
        ax.text(ang, r_lbl, lbl, ha='center', va='center', fontsize=7.2,
                color=c_lbl, fontweight=fw)

    # 中心夏至→859说明
    best_i = int(np.argmax([s[2] for s in term_stats]))
    best_term = term_stats[best_i]
    ax.set_ylim(0, 1.38)
    ax.set_yticks([])
    ax.set_xticks(np.deg2rad([0, 90, 180, 270]))
    ax.set_xticklabels([tx('夏至 (昼极)', 'Summer Solstice'),
                        tx('秋分', 'Autumn Equinox'),
                        tx('冬至 (夜极)', 'Winter Solstice'),
                        tx('春分', 'Spring Equinox')],
                       fontsize=8.5, fontweight='bold', color='#39ff14')
    ax.grid(color='#4cc9f0', alpha=0.15)
    ax.set_title(tx(f'二十四节气太阳黄经罗盘 (最旺节气: {best_term[0]} {best_term[2]:.1f}/d)',
                    f'24 Solar Terms Celestial Dial (Peak: {best_term[0]} {best_term[2]:.1f}/d)'),
                 color='#ffea00', fontweight='bold', pad=14)


# ==============================================================================
# 2. 希尔伯特空间填充曲线“量子 CPU 晶圆图” (Hilbert Curve Die)
# ==============================================================================
def hilbert_d2xy(n_side, d):
    x = y = 0
    s = 1
    t = int(d)
    while s < n_side:
        rx = 1 & (t // 2)
        ry = 1 & (t ^ rx)
        if ry == 0:
            if rx == 1:
                x = s - 1 - x
                y = s - 1 - y
            x, y = y, x
        x += s * rx
        y += s * ry
        t //= 4
        s *= 2
    return x, y


def plot_hilbert_cpu_die(ax, dates, y):
    n = len(y)
    side = 16 if n <= 256 else 32
    grid = np.full((side, side), np.nan)

    xs, ys = [], []
    x_log = np.log1p(y)
    for d in range(n):
        gx, gy = hilbert_d2xy(side, d)
        grid[gy, gx] = x_log[d]
        xs.append(gx)
        ys.append(gy)

    cmap = plt.get_cmap('inferno').copy()
    cmap.set_bad(color='#0d1321')
    im = ax.imshow(grid, cmap=cmap, origin='lower', aspect='equal')
    cbar = plt.colorbar(im, ax=ax, shrink=0.88, pad=0.02)
    cbar.set_label('Log(Clones + 1)', fontsize=8.5)

    # 画出连续希尔伯特电路走线
    ax.plot(xs, ys, color='#00f5d4', lw=0.75, alpha=0.42)

    peak_idx = int(np.argmax(y))
    px, py = xs[peak_idx], ys[peak_idx]
    ax.scatter([px], [py], color='#39ff14', s=180, marker='*',
               edgecolors='white', lw=0.7, zorder=6)
    ax.annotate(
        tx(f'过载核心 #{peak_idx}\n{int(y[peak_idx])} ({dates[peak_idx].strftime("%m-%d")})',
           f'Hotspot Core #{peak_idx}\n{int(y[peak_idx])} ({dates[peak_idx].strftime("%m-%d")})'),
        xy=(px, py), xytext=(min(side - 1.5, px + 2.2), min(side - 1.5, py + 2.0)),
        color='#39ff14', fontsize=8.5, fontweight='bold',
        arrowprops=dict(arrowstyle='->', color='#39ff14', lw=1.2)
    )

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(tx(f'{side}×{side} 希尔伯特空间填充曲线“地堡芯片晶圆图” ({n}/{side*side} 核心激活)',
                    f'{side}×{side} Hilbert Space-Filling CPU Die ({n}/{side*side} Active)'),
                 color='#00f5d4', fontweight='bold')


# ==============================================================================
# 3. 半导体车间六西格玛质检：双边 CUSUM & Cpk (Six Sigma Fab Control)
# ==============================================================================
def plot_six_sigma_cusum(ax, dates, y):
    x = np.log1p(y)
    n = len(x)
    mu0 = float(np.median(x))
    mad_sig = max(1.4826 * float(np.median(np.abs(x - mu0))), 0.1)

    k_allow = 0.5 * mad_sig
    h_limit = 4.5 * mad_sig

    c_pos = np.zeros(n)
    c_neg = np.zeros(n)
    for t in range(1, n):
        c_pos[t] = max(0.0, c_pos[t - 1] + (x[t] - mu0) - k_allow)
        c_neg[t] = max(0.0, c_neg[t - 1] + (mu0 - x[t]) - k_allow)

    # 设定理想合格流水线规格：[5, 100] clones/day
    lsl, usl = np.log1p(5.0), np.log1p(100.0)
    mu_mean = float(np.mean(x))
    sig_std = max(float(np.std(x)), 1e-6)
    cpk = min((usl - mu_mean) / (3.0 * sig_std),
              (mu_mean - lsl) / (3.0 * sig_std))
    defects = float(np.mean((y < 5.0) | (y > 100.0)))
    dpmo = defects * 1_000_000.0

    ax.plot(dates, c_pos, color='#ff4d6d', lw=1.9, label=tx(
        '正向过热累积漂移 C⁺', 'Upper CUSUM C⁺ (Surge)'))
    ax.fill_between(dates, 0.0, c_pos, color='#ff4d6d', alpha=0.18)
    ax.plot(dates, -c_neg, color='#00bbf9', lw=1.9,
            label=tx('负向冷寂累积漂移 -C⁻', 'Lower CUSUM -C⁻ (Drop)'))
    ax.fill_between(dates, 0.0, -c_neg, color='#00bbf9', alpha=0.18)

    ax.axhline(h_limit, color='#ffbe0b', ls='--', lw=1.3,
               label=f'UCL / LCL (±{h_limit:.2f})')
    ax.axhline(-h_limit, color='#ffbe0b', ls='--', lw=1.3)
    ax.axhline(0.0, color='#adb5bd', ls=':', lw=0.8)

    ax.set_title(tx('半导体车间质检：双边 CUSUM 漂移与 Cpk 良率',
                    'Six Sigma Fab Control: Two-Sided CUSUM & Cpk'),
                 color='#ff4d6d', fontweight='bold')
    ax.set_ylabel('Cumulative Drift Score')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=25)
    ax.legend(loc='upper right', fontsize=7.8, framealpha=0.85)
    ax.grid(alpha=0.15)

    info = tx(
        f"流水线 Spec: [5, 100] /天\n过程能力 Cpk: {cpk:.3f}\n良率 Yield: {(1-defects)*100:.1f}%\nDPMO 不良率: {dpmo:,.0f}",
        f"Spec Band: [5, 100] /d\nProcess Cpk: {cpk:.3f}\nFab Yield:   {(1-defects)*100:.1f}%\nDPMO:        {dpmo:,.0f}"
    )
    ax.text(0.03, 0.05, info, transform=ax.transAxes, va='bottom', fontsize=8.2,
            color='#ffbe0b', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#ffbe0b', alpha=0.88))


# ==============================================================================
# 4. 神经科学脑电锁相玫瑰图 (Kuramoto Phase-Locking Value PLV)
# ==============================================================================
def plot_kuramoto_plv(ax, df):
    c = np.log1p(df['clones'].values.astype(float))
    u = np.log1p(df['uniques'].values.astype(float))
    v = np.log1p(df['views'].values.astype(float))

    # 4~12天带通滤波提取周律脑电波段 (Sampling rate = 1/day -> Nyquist = 0.5 cpd)
    sos = butter(3, [1.0 / 6.0, 0.50], btype='band', output='sos')
    c_bp = sosfiltfilt(sos, c - np.mean(c))
    u_bp = sosfiltfilt(sos, u - np.mean(u))
    v_bp = sosfiltfilt(sos, v - np.mean(v)
                       ) if np.std(v) > 1e-6 else np.zeros_like(c_bp)

    ph_c = np.angle(hilbert(c_bp))
    ph_u = np.angle(hilbert(u_bp))
    ph_v = np.angle(hilbert(v_bp))

    dphi_cu = (ph_c - ph_u + np.pi) % (2.0 * np.pi) - np.pi
    dphi_cv = (ph_c - ph_v + np.pi) % (2.0 * np.pi) - np.pi

    plv_cu = float(np.abs(np.mean(np.exp(1j * dphi_cu))))
    plv_cv = float(np.abs(np.mean(np.exp(1j * dphi_cv))))

    bins = np.linspace(-np.pi, np.pi, 25)
    centers = 0.5 * (bins[:-1] + bins[1:])
    width = 2.0 * np.pi / 24.0

    cnt_cu, _ = np.histogram(dphi_cu, bins=bins)
    cnt_cv, _ = np.histogram(dphi_cv, bins=bins)

    ax.bar(centers, cnt_cu / max(cnt_cu.sum(), 1), width=width * 0.9, color='#00f5d4',
           alpha=0.55, edgecolor='#00f5d4', label=f'Clones ↔ Uniques (PLV={plv_cu:.3f})')
    ax.bar(centers, cnt_cv / max(cnt_cv.sum(), 1), width=width * 0.55, color='#ff00ff',
           alpha=0.55, edgecolor='#ff00ff', label=f'Clones ↔ Views (PLV={plv_cv:.3f})')

    ax.set_theta_zero_location('E')
    ax.tick_params(labelsize=8)
    ax.grid(color='#4cc9f0', alpha=0.18)
    ax.legend(loc='upper left', bbox_to_anchor=(-0.18, 1.05),
              fontsize=8, framealpha=0.85)
    ax.set_title(tx(f'脑电锁相环玫瑰图 (7d频段 PLV: C↔U={plv_cu:.2f} | C↔V={plv_cv:.2f})',
                    f'Kuramoto Phase-Locking Rose (PLV: C↔U={plv_cu:.2f} | C↔V={plv_cv:.2f})'),
                 color='#ff00ff', fontweight='bold', pad=14)


# ==============================================================================
# 5. t-SNE + Voronoi 文明6势力版图 (t-SNE Manifold Territory)
# ==============================================================================
def plot_tsne_voronoi(ax, dates, y):
    x = np.log1p(y)
    win = 7
    half = win // 2
    sub = np.lib.stride_tricks.sliding_window_view(x, win)
    sub_dates = dates[half:len(x) - half]
    sub_y = y[half:len(x) - half]

    X_std = StandardScaler().fit_transform(sub)
    perp = min(25, max(5, len(X_std) // 6))
    emb = TSNE(n_components=2, perplexity=perp, init='pca',
               learning_rate='auto', random_state=42).fit_transform(X_std)

    km = KMeans(n_clusters=4, n_init=10, random_state=42)
    labels = km.fit_predict(emb)
    centers = km.cluster_centers_

    # 用网格近邻染色画出无边界漏洞的泰森多边形疆域
    pad_x = (emb[:, 0].max() - emb[:, 0].min()) * 0.12
    pad_y = (emb[:, 1].max() - emb[:, 1].min()) * 0.12
    x_min, x_max = emb[:, 0].min() - pad_x, emb[:, 0].max() + pad_x
    y_min, y_max = emb[:, 1].min() - pad_y, emb[:, 1].max() + pad_y

    gx, gy = np.meshgrid(np.linspace(x_min, x_max, 220),
                         np.linspace(y_min, y_max, 220))
    grid_pts = np.column_stack([gx.ravel(), gy.ravel()])
    region_grid = cdist(grid_pts, centers).argmin(axis=1).reshape(gx.shape)

    ax.imshow(region_grid, extent=[x_min, x_max, y_min, y_max], origin='lower',
              cmap='viridis', alpha=0.20, aspect='auto')

    # 画 Voronoi 领土边界线
    vor = Voronoi(centers)
    for p_idx in vor.ridge_points:
        p1, p2 = centers[p_idx[0]], centers[p_idx[1]]
        mid = 0.5 * (p1 + p2)
        direction = np.array([-(p2[1] - p1[1]), p2[0] - p1[0]])
        direction /= max(float(np.linalg.norm(direction)), 1e-9)
        far = max(x_max - x_min, y_max - y_min) * 2.0
        ax.plot([mid[0] - far * direction[0], mid[0] + far * direction[0]],
                [mid[1] - far * direction[1], mid[1] + far * direction[1]],
                color='#00f5d4', ls='--', lw=1.2, alpha=0.65)

    cluster_colors = ['#00bbf9', '#39ff14', '#ffbe0b', '#ff006e']
    for k in range(4):
        m_k = labels == k
        mean_k = float(np.mean(sub_y[m_k]))
        ax.scatter(emb[m_k, 0], emb[m_k, 1], color=cluster_colors[k], s=26,
                   edgecolors='white', lw=0.4, alpha=0.88,
                   label=tx(f'城邦 {k+1} (均 {mean_k:.1f}/d)', f'Empire {k+1} (Avg {mean_k:.1f}/d)'))
        ax.scatter([centers[k, 0]], [centers[k, 1]], color=cluster_colors[k],
                   s=160, marker='P', edgecolors='white', lw=1.0, zorder=6)

    pk_rel = int(np.argmax(sub_y))
    ax.scatter([emb[pk_rel, 0]], [emb[pk_rel, 1]], color='#ffea00', s=210, marker='*',
               edgecolors='white', lw=0.7, zorder=7)
    ax.annotate(f'Peak {int(sub_y[pk_rel])}', (emb[pk_rel, 0], emb[pk_rel, 1]),
                xytext=(6, 6), textcoords='offset points', color='#ffea00', fontsize=8.5, fontweight='bold')

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_title(tx('t-SNE + Voronoi 泰森多边形“文明6势力疆域图”',
                    't-SNE + Voronoi Manifold Empires'),
                 color='#39ff14', fontweight='bold')
    ax.set_xlabel('t-SNE Dim 1')
    ax.set_ylabel('t-SNE Dim 2')
    ax.legend(loc='upper left', fontsize=7.8, framealpha=0.85)
    ax.grid(alpha=0.14)


# ==============================================================================
# 6. 时间序列祖师爷查漏补缺：ACF & PACF 定阶棒图
# ==============================================================================
def plot_acf_pacf(ax, y):
    x = np.log1p(y)
    xc = x - np.mean(x)
    n = len(xc)
    max_lag = 21

    denom = max(float(np.sum(xc ** 2)), 1e-12)
    full_corr = np.correlate(xc, xc, mode='full')[n - 1:] / denom
    acf = full_corr[:max_lag + 1]

    pacf = np.zeros(max_lag + 1)
    pacf[0] = 1.0
    for k in range(1, max_lag + 1):
        phi = solve_toeplitz(acf[:k], acf[1:k + 1])
        pacf[k] = float(phi[-1])

    lags = np.arange(1, max_lag + 1)
    ci = 1.96 / np.sqrt(float(n))

    w = 0.36
    ax.bar(lags - w / 2, acf[1:], width=w, color='#00bbf9',
           alpha=0.85, label='ACF (Total Autocorrelation)')
    ax.bar(lags + w / 2, pacf[1:], width=w, color='#ff00ff',
           alpha=0.85, label='PACF (Yule-Walker AR Order)')

    ax.axhspan(-ci, ci, color='#39ff14', alpha=0.14,
               label=f'95% White-Noise Band (±{ci:.2f})')
    ax.axhline(ci, color='#39ff14', ls='--', lw=1.0, alpha=0.75)
    ax.axhline(-ci, color='#39ff14', ls='--', lw=1.0, alpha=0.75)
    ax.axhline(0.0, color='#adb5bd', lw=0.8)

    sig_lags = [int(k) for k in lags if abs(pacf[k]) > ci]
    ax.set_xticks(lags)
    ax.set_title(tx(f'时间序列祖师爷：ACF / PACF 定阶 (显著 AR 滞后: {sig_lags})',
                    f'Classic Time-Series: ACF & PACF (Significant AR Lags: {sig_lags})'),
                 color='#00bbf9', fontweight='bold')
    ax.set_xlabel('Lag Days (k)')
    ax.set_ylabel('Correlation Coefficient')
    ax.legend(loc='upper right', fontsize=8, framealpha=0.85)
    ax.grid(alpha=0.15)


def main():
    print('🌞 Pod 042: Engaging Solar-Silicon Finale Chronicle (v15.0)...')
    df = load_bunker_data()
    dates = df.index
    y = df['clones'].values.astype(float)

    fig = plt.figure(figsize=(20, 18), facecolor='#04060a')

    ax1 = fig.add_subplot(3, 2, 1, projection='polar', facecolor='#080c14')
    ax2 = fig.add_subplot(3, 2, 2, facecolor='#080c14')
    ax3 = fig.add_subplot(3, 2, 3, facecolor='#080c14')
    ax4 = fig.add_subplot(3, 2, 4, projection='polar', facecolor='#080c14')
    ax5 = fig.add_subplot(3, 2, 5, facecolor='#080c14')
    ax6 = fig.add_subplot(3, 2, 6, facecolor='#080c14')

    plot_solar_terms_wheel(ax1, dates, y)
    plot_hilbert_cpu_die(ax2, dates, y)
    plot_six_sigma_cusum(ax3, dates, y)
    plot_kuramoto_plv(ax4, df)
    plot_tsne_voronoi(ax5, dates, y)
    plot_acf_pacf(ax6, y)

    fig.suptitle(
        tx('地堡天象与硅基晶圆番外篇 (二十四节气 + 希尔伯特CPU + 六西格玛 + 脑电锁相 + Voronoi疆域 + PACF)',
           'Bunker Solar-Silicon Chronicle (24 Solar Terms + Hilbert Die + Six Sigma + PLV + Voronoi + PACF)'),
        color='#00f5d4', fontsize=15.6, fontweight='bold', y=0.975
    )

    fig.subplots_adjust(left=0.06, right=0.955, top=0.92,
                        bottom=0.055, hspace=0.35, wspace=0.23)
    out_dir = os.path.dirname(OUTPUT_IMAGE)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    plt.savefig(OUTPUT_IMAGE, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'✅ Solar-Silicon Chronicle sealed at: {OUTPUT_IMAGE}')


if __name__ == '__main__':
    main()
