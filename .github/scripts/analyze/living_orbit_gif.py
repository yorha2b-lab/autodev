import pandas as pd
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
import matplotlib.pyplot as plt
import os

import matplotlib
matplotlib.use('Agg')


OUTPUT_GIF = 'plots/bunker_living_orbit.gif'

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
    return df


def main():
    print('🌀 Pod 042: Rendering Dual-Core Living Orbital GIF...')
    df = load_bunker_data()
    dates = df.index
    y = df['clones'].values.astype(float)
    x = np.log1p(y)

    # 复平面延迟轨迹 (长度 m_len = len(y) - 2)
    xc = x - np.mean(x)
    z = xc[2:] + 1j * xc[:-2]
    m_len = len(z)
    orbit_dates = dates[2:]
    orbit_y = y[2:]

    # 3D Takens 坐标 (同步对应同一天)
    xt, xt1, xt2 = x[2:], x[1:-1], x[:-2]

    # 傅立叶本轮分解 (32个矢量，渲染前14个主齿轮圈)
    fft_c = np.fft.fft(z) / float(m_len)
    freqs = np.fft.fftfreq(m_len)
    order = np.argsort(np.abs(fft_c))[::-1]
    k_vec = min(32, m_len)
    k_circ = min(14, k_vec)
    top_idx = order[:k_vec]

    n_draw = 64
    n_hold = 8
    total_frames = n_draw + n_hold
    t_vals = np.linspace(0.0, m_len - 1.0, n_draw)

    # 预计算每一帧所有本轮向量节点，确保画面边界稳定不抖动
    chain = np.zeros((n_draw, k_vec + 1), dtype=complex)
    radii = np.abs(fft_c[top_idx])
    for i_t, t_v in enumerate(t_vals):
        cur = 0.0 + 0.0j
        for k_i, idx in enumerate(top_idx):
            cur = cur + fft_c[idx] * \
                np.exp(1j * 2.0 * np.pi * freqs[idx] * t_v)
            chain[i_t, k_i + 1] = cur

    pad = max(float(np.max(radii[:k_circ])) * 0.6, 0.6)
    x_min = float(np.min(chain.real)) - pad
    x_max = float(np.max(chain.real)) + pad
    y_min = float(np.min(chain.imag)) - pad
    y_max = float(np.max(chain.imag)) + pad
    span = max(x_max - x_min, y_max - y_min) * 0.52
    cx_mid = 0.5 * (x_min + x_max)
    cy_mid = 0.5 * (y_min + y_max)

    # 高亮 859 弹射环索引
    peak_idx = int(np.argmax(y))
    p_rel = int(np.clip(peak_idx - 2, 1, m_len - 2))
    loop_slice = slice(max(0, p_rel - 2), min(m_len, p_rel + 4))

    # 创建双核画布
    fig = plt.figure(figsize=(14, 6.5), facecolor='#04060a')
    ax1 = fig.add_subplot(1, 2, 1, facecolor='#080c14')
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')

    # --- 左图初始化：傅立叶本轮机械表 ---
    ax1.scatter(z.real, z.imag, color='#4cc9f0', s=10, alpha=0.22)
    theta = np.linspace(0.0, 2.0 * np.pi, 48)
    cos_t, sin_t = np.cos(theta), np.sin(theta)

    circle_lines = []
    for k_i in range(k_circ):
        ln, = ax1.plot([], [], color='#00f5d4', lw=0.9 if k_i < 5 else 0.55,
                       alpha=0.58 if k_i < 5 else 0.30)
        circle_lines.append(ln)

    arm_line, = ax1.plot([], [], color='#ffbe0b', lw=1.35, alpha=0.9)
    trace_line, = ax1.plot([], [], color='#ff00ff', lw=1.9, alpha=0.88)
    tip_dot, = ax1.plot([], [], color='#39ff14', marker='*', markersize=13,
                        markeredgecolor='white', markeredgewidth=0.6, linestyle='None')

    hud_txt = ax1.text(
        0.03, 0.96, '', transform=ax1.transAxes, va='top', fontsize=9,
        color='#00f5d4', family='monospace', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.35', facecolor='#0a0f18',
                  edgecolor='#00f5d4', alpha=0.88)
    )

    ax1.set_xlim(cx_mid - span, cx_mid + span)
    ax1.set_ylim(cy_mid - span, cy_mid + span)
    ax1.set_aspect('equal', adjustable='box')
    ax1.set_title(
        f'Fourier Epicycle Clockwork ({k_vec} Phasors)', color='#00f5d4', fontweight='bold')
    ax1.set_xlabel('Centered Log(Clones[t]+1)')
    ax1.set_ylabel('Centered Log(Clones[t-2]+1)')
    ax1.grid(alpha=0.14)

    # --- 右图初始化：3D 奇异吸引子缓慢自转 ---
    ax2.set_facecolor('#04060a')
    for pane in (ax2.xaxis.pane, ax2.yaxis.pane, ax2.zaxis.pane):
        pane.set_facecolor((0.03, 0.05, 0.10, 0.85))
        pane.set_edgecolor('#1b263b')

    t_norm = np.linspace(0.0, 1.0, m_len)
    ax2.plot(xt, xt1, xt2, color='#4cc9f0', lw=0.65, alpha=0.28)
    ax2.scatter(xt, xt1, xt2, c=t_norm, cmap='plasma',
                s=18, alpha=0.78, depthshade=True)
    ax2.plot(xt[loop_slice], xt1[loop_slice], xt2[loop_slice],
             color='#ffea00', lw=2.2, alpha=0.95)
    ax2.scatter([xt[p_rel]], [xt1[p_rel]], [xt2[p_rel]],
                color='#ff006e', s=130, marker='*', edgecolors='white', lw=0.6)

    comet_3d, = ax2.plot([xt[0]], [xt1[0]], [xt2[0]], color='#39ff14', marker='o',
                         markersize=9, markeredgecolor='white', markeredgewidth=0.9, linestyle='None')

    ax2.set_title('3D Strange Attractor (360° Orbital Scan)',
                  color='#ff00ff', fontweight='bold', pad=8)
    ax2.set_xlabel('Log(C[t]+1)', labelpad=4, fontsize=8)
    ax2.set_ylabel('Log(C[t-1]+1)', labelpad=4, fontsize=8)
    ax2.set_zlabel('Log(C[t-2]+1)', labelpad=4, fontsize=8)
    ax2.tick_params(labelsize=7)

    fig.suptitle('Bunker Living Orbital Telemetry (Pod 042 Real-Time Scan)',
                 color='#39ff14', fontsize=14.5, fontweight='bold', y=0.96)
    fig.subplots_adjust(left=0.06, right=0.97, top=0.87,
                        bottom=0.10, wspace=0.14)

    def update(frame):
        idx_f = min(frame, n_draw - 1)
        day_i = int(round(t_vals[idx_f]))

        # 更新左边傅立叶旋转圆与连杆
        pts = chain[idx_f]
        for k_i in range(k_circ):
            c_xy = pts[k_i]
            r = radii[k_i]
            circle_lines[k_i].set_data(
                c_xy.real + r * cos_t, c_xy.imag + r * sin_t)

        arm_line.set_data(pts.real, pts.imag)
        tips = chain[:idx_f + 1, -1]
        trace_line.set_data(tips.real, tips.imag)
        tip_dot.set_data([tips[-1].real], [tips[-1].imag])

        cur_date = orbit_dates[day_i].strftime('%Y-%m-%d')
        cur_val = int(orbit_y[day_i])
        hud_txt.set_text(f'Date:   {cur_date}\nClones: {cur_val}')

        # 更新右边 3D 视角与同步彗星位置
        azim = -55.0 + 360.0 * (frame / float(total_frames))
        elev = 22.0 + 5.0 * np.sin(2.0 * np.pi * frame / float(total_frames))
        ax2.view_init(elev=elev, azim=azim)

        comet_3d.set_data([xt[day_i]], [xt1[day_i]])
        comet_3d.set_3d_properties([xt2[day_i]])

        return circle_lines + [arm_line, trace_line, tip_dot, hud_txt, comet_3d]

    anim = FuncAnimation(fig, update, frames=total_frames,
                         interval=70, blit=False)
    out_dir = os.path.dirname(OUTPUT_GIF)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    anim.save(OUTPUT_GIF, writer=PillowWriter(fps=14), dpi=95)
    plt.close(fig)
    print(f'✅ Living Orbital GIF sealed at: {OUTPUT_GIF}')


if __name__ == '__main__':
    main()
