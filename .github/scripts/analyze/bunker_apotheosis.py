from scipy.io import wavfile
from scipy.stats import wasserstein_distance, rankdata
from scipy.interpolate import CubicSpline
from scipy.signal import hilbert, argrelextrema, spectrogram
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import os
import zlib

import matplotlib
matplotlib.use('Agg')


OUTPUT_IMAGE = 'plots/bunker_apotheosis.png'
OUTPUT_AUDIO = 'plots/bunker_symphony.wav'

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
# 1. Hilbert-Huang Transform: Empirical Mode Decomposition (EMD + Hilbert)
# ==============================================================================
def extract_emd_imfs(signal, max_imfs=3, max_sift=20):
    n = len(signal)
    t = np.arange(n, dtype=float)
    residual = signal.astype(float).copy()
    imfs = []

    for _ in range(max_imfs):
        h = residual.copy()
        extracted = False
        for _ in range(max_sift):
            max_idx = argrelextrema(h, np.greater)[0]
            min_idx = argrelextrema(h, np.less)[0]
            if len(max_idx) < 2 or len(min_idx) < 2:
                break

            # 端点钳位填充，防止样条边界飞出天际
            tx_max = max_idx.tolist()
            ty_max = h[max_idx].tolist()
            if tx_max[0] != 0:
                tx_max.insert(0, 0)
                ty_max.insert(0, h[max_idx[0]])
            if tx_max[-1] != n - 1:
                tx_max.append(n - 1)
                ty_max.append(h[max_idx[-1]])

            tx_min = min_idx.tolist()
            ty_min = h[min_idx].tolist()
            if tx_min[0] != 0:
                tx_min.insert(0, 0)
                ty_min.insert(0, h[min_idx[0]])
            if tx_min[-1] != n - 1:
                tx_min.append(n - 1)
                ty_min.append(h[min_idx[-1]])

            upper = CubicSpline(tx_max, ty_max, bc_type='natural')(t)
            lower = CubicSpline(tx_min, ty_min, bc_type='natural')(t)
            mean_env = 0.5 * (upper + lower)

            prev_h = h
            h = h - mean_env
            extracted = True
            denom = float(np.sum(prev_h ** 2))
            sd = float(np.sum(mean_env ** 2)) / max(denom, 1e-12)
            if sd < 0.08:
                break

        if not extracted:
            break
        imfs.append(h)
        residual = residual - h

    return imfs, residual


def plot_emd_hht(ax, dates, y):
    x = np.log1p(y)
    imfs, residual = extract_emd_imfs(x, max_imfs=3)

    layers = []
    labels = []
    colors = ['#00f5d4', '#ffbe0b', '#ff00ff', '#39ff14']
    for idx, imf in enumerate(imfs):
        layers.append(imf)
        analytic = hilbert(imf)
        phase = np.unwrap(np.angle(analytic))
        inst_f = np.diff(phase) / (2.0 * np.pi)
        valid_f = inst_f[(inst_f > 0.015) & (inst_f < 0.48)]
        per_str = f'{1.0 / np.median(valid_f):.1f}d' if len(
            valid_f) > 0 else 'N/A'
        labels.append(f'IMF{idx + 1} (T≈{per_str})')

    layers.append(residual - np.mean(residual))
    labels.append('Secular Trend')

    offsets = []
    step = 2.6
    for idx, (layer, lbl) in enumerate(zip(layers, labels)):
        std_l = max(float(np.std(layer)), 1e-6)
        norm_l = layer / (1.8 * std_l)
        off = -idx * step
        offsets.append(off)
        c = colors[idx % len(colors)]
        ax.plot(dates, norm_l + off, color=c, lw=1.6, label=lbl)
        ax.axhline(off, color=c, ls=':', lw=0.6, alpha=0.35)
        ax.fill_between(dates, off, norm_l + off, color=c, alpha=0.14)

    ax.set_yticks(offsets)
    ax.set_yticklabels(labels, fontsize=8.5, fontweight='bold')
    ax.set_ylim(offsets[-1] - 1.6, 1.8)
    ax.set_title('Hilbert-Huang Transform (EMD Onion Decomposition)',
                 color='#00f5d4', fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=25)
    ax.grid(alpha=0.14, axis='x')


# ==============================================================================
# 2. Optimal Transport: Monthly Wasserstein-1 Earth Mover's Distance Matrix
# ==============================================================================
def plot_wasserstein_matrix(ax, df):
    x_series = pd.Series(np.log1p(df['clones'].values), index=df.index)
    months = x_series.groupby(x_series.index.to_period('M'))
    valid_months = [(str(p), grp.values) for p, grp in months if len(grp) >= 5]

    m_names = [m[0][2:] for m in valid_months]  # e.g. '26-04'
    k = len(valid_months)
    dist_mat = np.zeros((k, k), dtype=float)
    for i in range(k):
        for j in range(i + 1, k):
            d = float(wasserstein_distance(
                valid_months[i][1], valid_months[j][1]))
            dist_mat[i, j] = d
            dist_mat[j, i] = d

    im = ax.imshow(dist_mat, cmap='magma', aspect='auto')
    cbar = plt.colorbar(im, ax=ax, shrink=0.88, pad=0.02)
    cbar.set_label('Wasserstein-1 Distance [Log Clones]', fontsize=8.5)

    vmax = max(float(dist_mat.max()), 1e-6)
    for i in range(k):
        for j in range(k):
            val = dist_mat[i, j]
            txt_c = 'black' if val > 0.62 * vmax else 'white'
            ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                    color=txt_c, fontsize=8, fontweight='bold')

    ax.set_xticks(np.arange(k))
    ax.set_yticks(np.arange(k))
    ax.set_xticklabels(m_names, rotation=30, fontsize=8.5)
    ax.set_yticklabels(m_names, fontsize=8.5)
    ax.set_title("Optimal Transport: Monthly Wasserstein-1 Earth Mover's Matrix",
                 color='#ff00ff', fontweight='bold')
    ax.set_xlabel('Target Civilization Month')
    ax.set_ylabel('Source Civilization Month')


# ==============================================================================
# 3. Multifractal Geometry: MFDFA Singularity Spectrum f(α)
# ==============================================================================
def compute_mfdfa(x):
    n = len(x)
    Y = np.cumsum(x - np.mean(x))
    scales = [s for s in [6, 8, 12, 16, 24, 32, 48] if s <= n // 3]
    if len(scales) < 3:
        scales = [4, 6, 8, 12]
    qs = np.linspace(-3.0, 3.0, 25)
    t_idx = {s: np.arange(s, dtype=float) for s in scales}

    Fq = np.zeros((len(qs), len(scales)))
    for j, s in enumerate(scales):
        ns = n // s
        if ns < 2:
            continue
        segs = []
        for v in range(ns):
            segs.append(Y[v * s:(v + 1) * s])
            segs.append(Y[n - (v + 1) * s:n - v * s])
        vars_seg = []
        ts = t_idx[s]
        for seg in segs:
            coef = np.polyfit(ts, seg, 1)
            fit = coef[0] * ts + coef[1]
            v_val = float(np.mean((seg - fit) ** 2))
            if v_val > 1e-6:
                vars_seg.append(v_val)
        vars_arr = np.array(vars_seg) if vars_seg else np.array([1e-4])

        for i, q in enumerate(qs):
            if abs(q) < 1e-6:
                Fq[i, j] = np.exp(0.5 * np.mean(np.log(vars_arr)))
            else:
                Fq[i, j] = (np.mean(vars_arr ** (0.5 * q))) ** (1.0 / q)

    log_s = np.log(np.array(scales, dtype=float))
    hq = np.array([np.polyfit(log_s, np.log(np.maximum(Fq[i], 1e-9)), 1)[0]
                  for i in range(len(qs))])
    tau = qs * hq - 1.0
    alpha = np.gradient(tau, qs)
    f_alpha = qs * alpha - tau
    return qs, hq, alpha, f_alpha


def plot_mfdfa(ax, y):
    x = np.log1p(y)
    qs, hq, alpha, f_alpha = compute_mfdfa(x)

    rng = np.random.default_rng(42)
    x_shuf = rng.permutation(x)
    _, hq_s, alpha_s, f_alpha_s = compute_mfdfa(x_shuf)

    # 按 alpha 排序画出清晰的奇异谱弓形
    ord_o = np.argsort(alpha)
    ord_s = np.argsort(alpha_s)

    ax.plot(alpha[ord_o], f_alpha[ord_o], color='#ffbe0b', lw=2.4, marker='o', ms=4,
            label='Bunker Original Spectrum f(α)')
    ax.fill_between(alpha[ord_o], np.minimum(
        f_alpha.min(), 0.0), f_alpha[ord_o], color='#ffbe0b', alpha=0.14)

    ax.plot(alpha_s[ord_s], f_alpha_s[ord_s], color='#00bbf9', lw=1.8, ls='--', marker='s', ms=3.5,
            label='Shuffled Surrogate (Time Memory Destroyed)')

    delta_alpha = float(alpha.max() - alpha.min())
    delta_shuf = float(alpha_s.max() - alpha_s.min())
    h_q2 = float(hq[np.argmin(np.abs(qs - 2.0))])

    ax.axhline(1.0, color='#adb5bd', ls=':', lw=1.0, alpha=0.6)
    ax.set_title('Multifractal Singularity Spectrum (MFDFA f(α))',
                 color='#ffbe0b', fontweight='bold')
    ax.set_xlabel('Singularity Strength α (Hölder Exponent)')
    ax.set_ylabel('Fractal Dimension f(α)')
    ax.legend(loc='lower center', fontsize=8, framealpha=0.85)
    ax.grid(alpha=0.15)

    info = (
        f"Multifractal Width Δα: {delta_alpha:.3f}\n"
        f"Shuffled Width Δα_s:   {delta_shuf:.3f}\n"
        f"Hurst h(q=2):          {h_q2:.3f}\n"
        f"h(q=-3) vs h(q=+3):    {hq[0]:.2f} vs {hq[-1]:.2f}"
    )
    ax.text(0.03, 0.96, info, transform=ax.transAxes, va='top', fontsize=8.3,
            color='#ffbe0b', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#ffbe0b', alpha=0.88))


# ==============================================================================
# 4. Ptolemaic Astronomy: Fourier Epicycles Orbit in Delay Complex Plane
# ==============================================================================
def plot_fourier_epicycles(ax, y):
    x = np.log1p(y)
    xc = x - np.mean(x)
    z = xc[2:] + 1j * xc[:-2]
    m_len = len(z)

    fft_c = np.fft.fft(z) / float(m_len)
    freqs = np.fft.fftfreq(m_len)
    order = np.argsort(np.abs(fft_c))[::-1]

    k_epicycles = min(18, m_len)
    top_idx = order[:k_epicycles]

    # 全周期平滑重构轨迹
    t_dense = np.linspace(0, m_len - 1, 600)
    z_recon = np.zeros_like(t_dense, dtype=complex)
    for idx in top_idx:
        z_recon += fft_c[idx] * np.exp(1j * 2.0 * np.pi * freqs[idx] * t_dense)

    ax.scatter(z.real, z.imag, color='#4cc9f0', s=12,
               alpha=0.35, label='Empirical Orbit (Lag 2d)')
    ax.plot(z_recon.real, z_recon.imag, color='#ff00ff', lw=1.2, alpha=0.72,
            label=f'Top-{k_epicycles} Epicycle Trajectory')

    # 在最后一天 t = m_len - 1 冻结绘制同心旋转本轮齿轮！
    t_now = m_len - 1
    center = 0.0 + 0.0j
    theta = np.linspace(0.0, 2.0 * np.pi, 64)
    for rank, idx in enumerate(top_idx):
        radius = float(np.abs(fft_c[idx]))
        vec = fft_c[idx] * np.exp(1j * 2.0 * np.pi * freqs[idx] * t_now)
        next_center = center + vec

        if radius > 0.015:
            cx = center.real + radius * np.cos(theta)
            cy = center.imag + radius * np.sin(theta)
            ax.plot(cx, cy, color='#00f5d4', lw=0.9 if rank < 5 else 0.55,
                    alpha=0.65 if rank < 5 else 0.35)
        ax.plot([center.real, next_center.real], [center.imag, next_center.imag],
                color='#ffea00', lw=1.4 if rank < 5 else 0.8, alpha=0.9)
        center = next_center

    ax.scatter([center.real], [center.imag], color='#39ff14', s=140, marker='*',
               edgecolors='white', lw=0.7, zorder=8, label='Today Target Pointer')
    ax.set_aspect('equal', adjustable='datalim')
    ax.set_title(
        f'Ptolemaic Astronomy: Top-{k_epicycles} Fourier Epicycles', color='#00f5d4', fontweight='bold')
    ax.set_xlabel('Centered Log(Clones[t]+1)')
    ax.set_ylabel('Centered Log(Clones[t-2]+1)')
    ax.legend(loc='upper right', fontsize=7.8, framealpha=0.85)
    ax.grid(alpha=0.14)


# ==============================================================================
# 5. Acoustic Sonification: Synthesize Playable .wav + Spectrogram Waterfall
# ==============================================================================
def plot_acoustic_sonification(ax, dates, y, uniques):
    sr = 16000
    duration = 4.5
    n_samples = int(sr * duration)

    x_log = np.log1p(y)
    x_norm = (x_log - x_log.min()) / \
        max(float(x_log.max() - x_log.min()), 1e-6)
    u_norm = uniques / max(float(uniques.max()), 1.0)

    t_days = np.linspace(0.0, 1.0, len(y))
    t_audio = np.linspace(0.0, 1.0, n_samples)

    x_interp = np.interp(t_audio, t_days, x_norm)
    u_interp = np.interp(t_audio, t_days, u_norm)

    # 频率从 A2 (110 Hz) 映射至 B5 (~980 Hz)，制造出 859 尖啸声呐效果
    freq_t = 110.0 + 870.0 * (x_interp ** 1.35)
    phase = 2.0 * np.pi * np.cumsum(freq_t) / float(sr)
    amp_env = 0.35 + 0.65 * u_interp
    wave = amp_env * (0.75 * np.sin(phase) + 0.25 * np.sin(2.0 * phase))

    # 淡入淡出防爆音并保存真实可听音频文件
    fade = int(0.03 * sr)
    wave[:fade] *= np.linspace(0.0, 1.0, fade)
    wave[-fade:] *= np.linspace(1.0, 0.0, fade)
    pcm = np.int16(wave / max(float(np.max(np.abs(wave))), 1e-6) * 32767.0)

    out_dir = os.path.dirname(OUTPUT_AUDIO)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    wavfile.write(OUTPUT_AUDIO, sr, pcm)

    f_spec, t_spec, sxx = spectrogram(wave, fs=sr, nperseg=512, noverlap=448)
    sxx_db = 10.0 * np.log10(np.maximum(sxx, 1e-12))
    freq_mask = f_spec <= 2200.0

    # 将音频 4.5 秒时间轴映射回真实历史日期
    date_nums = mdates.date2num(dates)
    t_mapped = date_nums[0] + (t_spec / duration) * \
        (date_nums[-1] - date_nums[0])

    ax.pcolormesh(t_mapped, f_spec[freq_mask], sxx_db[freq_mask, :],
                  shading='gouraud', cmap='inferno')

    peak_idx = int(np.argmax(y))
    peak_freq = float(110.0 + 870.0 * (x_norm[peak_idx] ** 1.35))
    ax.scatter([date_nums[peak_idx]], [peak_freq], color='#00f5d4', s=130, marker='*',
               edgecolors='white', lw=0.7, zorder=6)
    ax.annotate(f'Peak {int(y[peak_idx])} Sonar Shriek ({peak_freq:.0f} Hz)',
                xy=(date_nums[peak_idx], peak_freq),
                xytext=(date_nums[min(len(dates) - 1, peak_idx + 18)],
                        min(2000.0, peak_freq + 450.0)),
                color='#00f5d4', fontsize=8.5, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#00f5d4', lw=1.2))

    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=25)
    ax.set_title(
        f'Acoustic Sonification Spectrogram ({OUTPUT_AUDIO})', color='#ff4d6d', fontweight='bold')
    ax.set_ylabel('Synthesized Pitch Frequency (Hz)')
    ax.set_xlabel('Mapped Historical Timeline (4.5s Audio Track)')


# ==============================================================================
# 6. Bioinformatics & Algorithmic Info: DNA Encoding + LZ76 Complexity
# ==============================================================================
def lz76_complexity(seq):
    n = len(seq)
    if n <= 1:
        return float(n)
    i, k, l = 0, 1, 1
    c = 1
    k_max = 1
    while True:
        if seq[i + k - 1] == seq[l + k - 1]:
            k += 1
            if l + k > n:
                c += 1
                break
        else:
            if k > k_max:
                k_max = k
            i += 1
            if i == l:
                c += 1
                l += k_max
                if l + 1 > n:
                    break
                i = 0
                k = 1
                k_max = 1
            else:
                k = 1
    return float(c)


def plot_dna_algorithmic_complexity(ax, dates, y):
    n = len(y)
    pcts = rankdata(y, method='average') / float(n)
    dna_list = []
    for p in pcts:
        if p <= 0.25:
            dna_list.append('A')
        elif p <= 0.50:
            dna_list.append('T')
        elif p <= 0.75:
            dna_list.append('C')
        else:
            dna_list.append('G')
    dna_str = ''.join(dna_list)

    win = min(35, max(14, n // 5))
    gc_roll = []
    lz_roll = []
    roll_dates = dates[win - 1:]
    norm_denom = win / (np.log(win) / np.log(4.0))

    for i in range(win - 1, n):
        sub = dna_str[i - win + 1:i + 1]
        gc = (sub.count('G') + sub.count('C')) / float(win) * 100.0
        lz = lz76_complexity(sub) / norm_denom
        gc_roll.append(gc)
        lz_roll.append(lz)

    # 全局 LZ76 与 150 次基因洗牌零模型对比
    global_lz = lz76_complexity(dna_str)
    rng = np.random.default_rng(42)
    shuf_lzs = []
    dna_arr = np.array(dna_list)
    for _ in range(150):
        shuf_lzs.append(lz76_complexity(''.join(rng.permutation(dna_arr))))
    lz_z = (global_lz - np.mean(shuf_lzs)) / max(float(np.std(shuf_lzs)), 1e-6)

    comp_ratio = len(zlib.compress(dna_str.encode('utf-8'))) / \
        float(len(dna_str))

    ax.plot(roll_dates, gc_roll, color='#39ff14', lw=2.0,
            label=f'Rolling {win}d GC-Content (%) [High Activity]')
    ax.axhline(50.0, color='#39ff14', ls=':', lw=0.9, alpha=0.5)
    ax.set_ylabel('DNA GC-Content (%)', color='#39ff14')
    ax.set_ylim(0, 105)

    ax2 = ax.twinx()
    ax2.plot(roll_dates, lz_roll, color='#00bbf9', lw=1.7,
             ls='--', label=f'Normalized LZ76 Complexity')
    ax2.set_ylabel('Normalized LZ76 Complexity', color='#00bbf9')
    ax2.tick_params(axis='y', colors='#00bbf9')

    ax.set_title('Bioinformatics DNA Genome & Lempel-Ziv Complexity',
                 color='#39ff14', fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=25)
    ax.grid(alpha=0.15)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2,
              loc='upper right', fontsize=8, framealpha=0.85)

    genome_preview = f"5'-{dna_str[:24]}...-3'"
    info = (
        f"Genome: {genome_preview} ({n} bp)\n"
        f"Global LZ76: {int(global_lz)} (Shuffle Z={lz_z:+.2f}σ)\n"
        f"Zlib Ratio:  {comp_ratio:.3f}"
    )
    ax.text(0.02, 0.05, info, transform=ax.transAxes, va='bottom', fontsize=8.3,
            color='#39ff14', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a0f18', edgecolor='#39ff14', alpha=0.88))


def main():
    print('🧬 Pod 042: Engaging Final Apotheosis & Bio-Acoustics (v11.0)...')
    df = load_bunker_data()
    dates = df.index
    y = df['clones'].values.astype(float)
    uniques = df['uniques'].values.astype(float)

    fig, axes = plt.subplots(3, 2, figsize=(20, 18), facecolor='#04060a')
    for ax in axes.flat:
        ax.set_facecolor('#080c14')

    plot_emd_hht(axes[0, 0], dates, y)
    plot_wasserstein_matrix(axes[0, 1], df)
    plot_mfdfa(axes[1, 0], y)
    plot_fourier_epicycles(axes[1, 1], y)
    plot_acoustic_sonification(axes[2, 0], dates, y, uniques)
    plot_dna_algorithmic_complexity(axes[2, 1], dates, y)

    fig.suptitle(
        'Bunker Cosmic Apotheosis (HHT-EMD + Wasserstein OT + MFDFA + Fourier Epicycles + Audio Synth + DNA LZ76)',
        color='#39ff14', fontsize=15.8, fontweight='bold', y=0.975
    )

    fig.subplots_adjust(left=0.06, right=0.945, top=0.925,
                        bottom=0.055, hspace=0.33, wspace=0.25)
    out_dir = os.path.dirname(OUTPUT_IMAGE)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    plt.savefig(OUTPUT_IMAGE, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'✅ Apotheosis visual sealed at: {OUTPUT_IMAGE}')
    print(f'🎵 Bunker Audio Symphony exported at: {OUTPUT_AUDIO}')


if __name__ == '__main__':
    main()
