import os
import json
import numpy as np
import pandas as pd
from scipy.stats import rankdata

OUTPUT_SVG = 'plots/bunker_hud.svg'


def build_dna_head(y, length=18):
    pcts = rankdata(y, method='average') / max(float(len(y)), 1.0)
    bases = []
    for p in pcts[:length]:
        if p <= 0.25:
            bases.append('A')
        elif p <= 0.50:
            bases.append('T')
        elif p <= 0.75:
            bases.append('C')
        else:
            bases.append('G')
    return ''.join(bases)


def main():
    c_df = pd.read_csv('ghrs-data/clones_ledger.csv')
    c_df['date'] = pd.to_datetime(c_df['date'])
    c_df = c_df.sort_values('date').drop_duplicates('date', keep='last')
    full_idx = pd.date_range(c_df['date'].min(), c_df['date'].max(), freq='D')
    c_df = c_df.set_index('date').reindex(full_idx).fillna(0.0)

    y = c_df['clones'].values.astype(float)
    dates = c_df.index

    stats = {'total_clones': int(y.sum()), 'stars': 3, 'forks': 0}
    if os.path.exists('bunker-stats.json'):
        with open('bunker-stats.json', 'r') as f:
            stats.update(json.load(f))

    total_clones = int(stats.get('total_clones', int(y.sum())))
    stars = int(stats.get('stars', 0))
    forks = int(stats.get('forks', 0))
    latest_date = dates[-1].strftime('%Y-%m-%d')
    latest_clones = int(y[-1])
    avg_clones = float(np.mean(y))
    peak_idx = int(np.argmax(y))
    peak_val = int(y[peak_idx])
    peak_date = dates[peak_idx].strftime('%m-%d')
    dna_head = build_dna_head(y)

    # 10,000 里程碑进度条
    target = 10000
    pct = min(100.0, total_clones / float(target) * 100.0)
    remaining = max(0, target - total_clones)
    bar_w = 516.0 * (pct / 100.0)
    vip_ratio = 16.0 / max(stars, 1)

    # 右侧最近 30 天实时心跳折线 (x: 572..846, y: 88..194)
    tail30 = y[-30:] if len(y) >= 30 else y
    s_min, s_max = int(np.min(tail30)), int(np.max(tail30))
    span_y = max(float(s_max - s_min), 1.0)
    xs = np.linspace(572.0, 846.0, len(tail30))
    ys = 194.0 - ((tail30 - s_min) / span_y) * 100.0

    poly_pts = ' '.join(f'{px:.1f},{py:.1f}' for px, py in zip(xs, ys))
    area_pts = f'572.0,196.0 {poly_pts} 846.0,196.0'
    lx, ly = xs[-1], ys[-1]

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 230" width="100%">
  <defs>
    <linearGradient id="barGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00bbf9"/>
      <stop offset="60%" stop-color="#00f5d4"/>
      <stop offset="100%" stop-color="#39ff14"/>
    </linearGradient>
    <linearGradient id="sparkFill" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#39ff14" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#00f5d4" stop-opacity="0.02"/>
    </linearGradient>
    <pattern id="gridPat" width="22" height="22" patternUnits="userSpaceOnUse">
      <path d="M 22 0 L 0 0 0 22" fill="none" stroke="#132238" stroke-width="0.7"/>
    </pattern>
  </defs>

  <!-- 赛博切角底板 -->
  <polygon points="16,4 864,4 876,16 876,214 864,226 16,226 4,214 4,16"
           fill="#050811" stroke="#00f5d4" stroke-width="1.5"/>
  <polygon points="18,6 862,6 874,18 874,212 862,224 18,224 6,212 6,18"
           fill="url(#gridPat)" opacity="0.55"/>

  <!-- 顶部状态栏 -->
  <circle cx="28" cy="27" r="4.5" fill="#39ff14">
    <animate attributeName="opacity" values="1;0.2;1" dur="1.8s" repeatCount="indefinite"/>
  </circle>
  <text x="41" y="31" fill="#00f5d4" font-family="Consolas, Monaco, monospace" font-size="13" font-weight="bold">
    POD 042 // SOVEREIGN BUNKER HUD [V9.0]
  </text>
  <text x="856" y="31" text-anchor="end" fill="#8ecae6" font-family="Consolas, Monaco, monospace" font-size="10.5">
    AGPL-3.0 ACTIVE  |  SYNC: {latest_date}  |  16 TEMPLES ONLINE
  </text>
  <line x1="20" y1="44" x2="860" y2="44" stroke="#1b3a4b" stroke-width="1"/>

  <!-- KPI 卡片 1: 累计克隆 -->
  <rect x="20" y="56" width="166" height="88" rx="4" fill="#08101d" stroke="#1b3a4b" stroke-width="1"/>
  <text x="32" y="75" fill="#8ecae6" font-family="Consolas, Monaco, monospace" font-size="10">TOTAL CLONES</text>
  <text x="32" y="109" fill="#39ff14" font-family="Consolas, Monaco, monospace" font-size="26" font-weight="bold">{total_clones:,}</text>
  <text x="32" y="131" fill="#ffbe0b" font-family="Consolas, Monaco, monospace" font-size="10">10K TARGET: {pct:.1f}%</text>

  <!-- KPI 卡片 2: 社群声望 -->
  <rect x="198" y="56" width="166" height="88" rx="4" fill="#08101d" stroke="#1b3a4b" stroke-width="1"/>
  <text x="210" y="75" fill="#8ecae6" font-family="Consolas, Monaco, monospace" font-size="10">SOCIAL PRESTIGE</text>
  <text x="210" y="107" fill="#ffbe0b" font-family="Consolas, Monaco, monospace" font-size="20" font-weight="bold">★ {stars}  |  FORK {forks}</text>
  <text x="210" y="131" fill="#ff00ff" font-family="Consolas, Monaco, monospace" font-size="10">VIP: {vip_ratio:.1f} TEMPLES/STAR</text>

  <!-- KPI 卡片 3: 宇宙规律 -->
  <rect x="376" y="56" width="166" height="88" rx="4" fill="#08101d" stroke="#1b3a4b" stroke-width="1"/>
  <text x="388" y="75" fill="#8ecae6" font-family="Consolas, Monaco, monospace" font-size="10">COSMIC TELEMETRY</text>
  <text x="388" y="99" fill="#00f5d4" font-family="Consolas, Monaco, monospace" font-size="13" font-weight="bold">LAW: LOG-NORMAL</text>
  <text x="388" y="117" fill="#ff4d6d" font-family="Consolas, Monaco, monospace" font-size="10.5">APEX: {peak_val} ({peak_date})</text>
  <text x="388" y="133" fill="#adb5bd" font-family="Consolas, Monaco, monospace" font-size="10">TODAY: {latest_clones} CLONES</text>

  <!-- 破万进度条 + DNA 基因组 -->
  <text x="24" y="167" fill="#00f5d4" font-family="Consolas, Monaco, monospace" font-size="10" font-weight="bold">
    10,000 CLONE SINGULARITY PROGRESS ({total_clones:,} / 10,000)
  </text>
  <text x="540" y="167" text-anchor="end" fill="#39ff14" font-family="Consolas, Monaco, monospace" font-size="10">
    {remaining:,} LEFT
  </text>
  <rect x="24" y="175" width="516" height="12" rx="3" fill="#0d1b2a" stroke="#1b3a4b" stroke-width="1"/>
  <rect x="24" y="175" width="{bar_w:.1f}" height="12" rx="3" fill="url(#barGrad)"/>
  <text x="24" y="209" fill="#8ecae6" font-family="Consolas, Monaco, monospace" font-size="10">
    DNA: 5'-{dna_head}...-3'  |  {len(y)} DAYS  |  AVG: {avg_clones:.1f}/D
  </text>

  <!-- 右侧 30 天实时心跳折线 -->
  <rect x="558" y="56" width="302" height="156" rx="4" fill="#08101d" stroke="#1b3a4b" stroke-width="1"/>
  <text x="570" y="74" fill="#00f5d4" font-family="Consolas, Monaco, monospace" font-size="10" font-weight="bold">
    30D HEARTBEAT SPARKLINE
  </text>
  <text x="848" y="74" text-anchor="end" fill="#ffbe0b" font-family="Consolas, Monaco, monospace" font-size="9.5">
    MAX {s_max} / MIN {s_min}
  </text>
  <line x1="572" y1="196" x2="846" y2="196" stroke="#1b3a4b" stroke-dasharray="3,3" stroke-width="1"/>
  <polygon points="{area_pts}" fill="url(#sparkFill)"/>
  <polyline points="{poly_pts}" fill="none" stroke="#39ff14" stroke-width="2" stroke-linejoin="round"/>
  <circle cx="{lx:.1f}" cy="{ly:.1f}" r="4" fill="#00f5d4" stroke="#ffffff" stroke-width="1.2">
    <animate attributeName="r" values="3.5;6;3.5" dur="1.8s" repeatCount="indefinite"/>
  </circle>
</svg>'''

    out_dir = os.path.dirname(OUTPUT_SVG)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(OUTPUT_SVG, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f'✅ YoRHa Tactical HUD SVG minted at: {OUTPUT_SVG}')


if __name__ == '__main__':
    main()
