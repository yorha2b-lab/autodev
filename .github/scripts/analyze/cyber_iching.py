from scipy.stats import f_oneway
import pandas as pd
import numpy as np
from matplotlib.patches import Circle, Wedge
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import os

import matplotlib
matplotlib.use('Agg')


OUTPUT_IMAGE = 'plots/bunker_cyber_iching.png'

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


# ==============================================================================
# 传统《周易》精确编码表（爻序：自下而上 (初爻, 中爻, 上爻) | 0=阴, 1=阳）
# ==============================================================================
TRIGRAMS = {
    (1, 1, 1): ('乾', 'QIAN', 'Heaven'),
    (1, 1, 0): ('兑', 'DUI', 'Lake'),
    (1, 0, 1): ('离', 'LI', 'Fire'),
    (1, 0, 0): ('震', 'ZHEN', 'Thunder'),
    (0, 1, 1): ('巽', 'XUN', 'Wind'),
    (0, 1, 0): ('坎', 'KAN', 'Water'),
    (0, 0, 1): ('艮', 'GEN', 'Mountain'),
    (0, 0, 0): ('坤', 'KUN', 'Earth'),
}

# 伏羲先天八卦圆图顺时针方位角（度，以正南=90°为乾起点）
FUXI_RING = [
    ((1, 1, 1), 90.0),    # 正南：乾
    ((0, 1, 1), 45.0),    # 西南：巽
    ((0, 1, 0), 0.0),     # 正西：坎
    ((0, 0, 1), 315.0),   # 西北：艮
    ((0, 0, 0), 270.0),   # 正北：坤
    ((1, 0, 0), 225.0),   # 东北：震
    ((1, 0, 1), 180.0),   # 正东：离
    ((1, 1, 0), 135.0),   # 东南：兑
]

# 8x8 矩阵行列顺序：乾, 坤, 震, 艮, 离, 坎, 兑, 巽
ORDER_8 = [
    (1, 1, 1), (0, 0, 0), (1, 0, 0), (0, 0, 1),
    (1, 0, 1), (0, 1, 0), (1, 1, 0), (0, 1, 1),
]

# 键为 (下卦bits, 上卦bits) -> (卦序, 中文名, 拼音名)
HEXAGRAM_TABLE = {
    ((1, 1, 1), (1, 1, 1)): (1, '乾为天', 'Qian'),
    ((1, 1, 1), (0, 0, 0)): (11, '地天泰', 'Tai'),
    ((1, 1, 1), (1, 0, 0)): (34, '雷天大壮', 'DaZhuang'),
    ((1, 1, 1), (0, 0, 1)): (26, '山天大畜', 'DaXu'),
    ((1, 1, 1), (1, 0, 1)): (14, '火天大有', 'DaYou'),
    ((1, 1, 1), (0, 1, 0)): (5, '水天需', 'Xu'),
    ((1, 1, 1), (1, 1, 0)): (43, '泽天夬', 'Guai'),
    ((1, 1, 1), (0, 1, 1)): (9, '风天小畜', 'XiaoXu'),

    ((0, 0, 0), (1, 1, 1)): (12, '天地否', 'Pi'),
    ((0, 0, 0), (0, 0, 0)): (2, '坤为地', 'Kun'),
    ((0, 0, 0), (1, 0, 0)): (16, '雷地豫', 'Yu'),
    ((0, 0, 0), (0, 0, 1)): (23, '山地剥', 'Bo'),
    ((0, 0, 0), (1, 0, 1)): (35, '火地晋', 'Jin'),
    ((0, 0, 0), (0, 1, 0)): (8, '水地比', 'Bi'),
    ((0, 0, 0), (1, 1, 0)): (45, '泽地萃', 'Cui'),
    ((0, 0, 0), (0, 1, 1)): (20, '风地观', 'Guan'),

    ((1, 0, 0), (1, 1, 1)): (25, '天雷无妄', 'WuWang'),
    ((1, 0, 0), (0, 0, 0)): (24, '地雷复', 'Fu'),
    ((1, 0, 0), (1, 0, 0)): (51, '震为雷', 'Zhen'),
    ((1, 0, 0), (0, 0, 1)): (27, '山雷颐', 'Yi'),
    ((1, 0, 0), (1, 0, 1)): (21, '火雷噬嗑', 'ShiHe'),
    ((1, 0, 0), (0, 1, 0)): (3, '水雷屯', 'Zhun'),
    ((1, 0, 0), (1, 1, 0)): (17, '泽雷随', 'Sui'),
    ((1, 0, 0), (0, 1, 1)): (42, '风雷益', 'Yi+'),

    ((0, 0, 1), (1, 1, 1)): (33, '天山遁', 'Dun'),
    ((0, 0, 1), (0, 0, 0)): (15, '地山谦', 'Qian-'),
    ((0, 0, 1), (1, 0, 0)): (62, '雷山小过', 'XiaoGuo'),
    ((0, 0, 1), (0, 0, 1)): (52, '艮为山', 'Gen'),
    ((0, 0, 1), (1, 0, 1)): (56, '火山旅', 'Lv'),
    ((0, 0, 1), (0, 1, 0)): (39, '水山蹇', 'Jian'),
    ((0, 0, 1), (1, 1, 0)): (31, '泽山咸', 'Xian'),
    ((0, 0, 1), (0, 1, 1)): (53, '风山渐', 'Jian+'),

    ((1, 0, 1), (1, 1, 1)): (13, '天火同人', 'TongRen'),
    ((1, 0, 1), (0, 0, 0)): (36, '地火明夷', 'MingYi'),
    ((1, 0, 1), (1, 0, 0)): (55, '雷火丰', 'Feng'),
    ((1, 0, 1), (0, 0, 1)): (22, '山火贲', 'Bi+'),
    ((1, 0, 1), (1, 0, 1)): (30, '离为火', 'Li'),
    ((1, 0, 1), (0, 1, 0)): (63, '水火既济', 'JiJi'),
    ((1, 0, 1), (1, 1, 0)): (49, '泽火革', 'Ge'),
    ((1, 0, 1), (0, 1, 1)): (37, '风火家人', 'JiaRen'),

    ((0, 1, 0), (1, 1, 1)): (6, '天水讼', 'Song'),
    ((0, 1, 0), (0, 0, 0)): (7, '地水师', 'Shi'),
    ((0, 1, 0), (1, 0, 0)): (40, '雷水解', 'Xie'),
    ((0, 1, 0), (0, 0, 1)): (4, '山水蒙', 'Meng'),
    ((0, 1, 0), (1, 0, 1)): (64, '火水未济', 'WeiJi'),
    ((0, 1, 0), (0, 1, 0)): (29, '坎为水', 'Kan'),
    ((0, 1, 0), (1, 1, 0)): (47, '泽水困', 'Kun-'),
    ((0, 1, 0), (0, 1, 1)): (59, '风水涣', 'Huan'),

    ((1, 1, 0), (1, 1, 1)): (10, '天泽履', 'Lv+'),
    ((1, 1, 0), (0, 0, 0)): (19, '地泽临', 'Lin'),
    ((1, 1, 0), (1, 0, 0)): (54, '雷泽归妹', 'GuiMei'),
    ((1, 1, 0), (0, 0, 1)): (41, '山泽损', 'Sun'),
    ((1, 1, 0), (1, 0, 1)): (38, '火泽睽', 'Kui'),
    ((1, 1, 0), (0, 1, 0)): (60, '水泽节', 'Jie'),
    ((1, 1, 0), (1, 1, 0)): (58, '兑为泽', 'Dui'),
    ((1, 1, 0), (0, 1, 1)): (61, '风泽中孚', 'ZhongFu'),

    ((0, 1, 1), (1, 1, 1)): (44, '天风姤', 'Gou'),
    ((0, 1, 1), (0, 0, 0)): (46, '地风升', 'Sheng'),
    ((0, 1, 1), (1, 0, 0)): (32, '雷风恒', 'Heng'),
    ((0, 1, 1), (0, 0, 1)): (18, '山风蛊', 'Gu'),
    ((0, 1, 1), (1, 0, 1)): (50, '火风鼎', 'Ding'),
    ((0, 1, 1), (0, 1, 0)): (48, '水风井', 'Jing'),
    ((0, 1, 1), (1, 1, 0)): (28, '泽风大过', 'DaGuo'),
    ((0, 1, 1), (0, 1, 1)): (57, '巽为风', 'Xun'),
}

# 干支万年历锚点：2026-04-03 = 丁未日 (天干3, 地支7)
ANCHOR_DATE = pd.Timestamp('2026-04-03')
STEMS_ZH = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
STEMS_EN = ['Jia', 'Yi', 'Bing', 'Ding',
            'Wu', 'Ji', 'Geng', 'Xin', 'Ren', 'Gui']
BRANCHES_ZH = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
BRANCHES_EN = ['Zi-Rat', 'Chou-Ox', 'Yin-Tiger', 'Mao-Rabbit', 'Chen-Dragon', 'Si-Snake',
               'Wu-Horse', 'Wei-Goat', 'Shen-Monkey', 'You-Rooster', 'Xu-Dog', 'Hai-Pig']
STEM_ELEMENT = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]  # 0=木, 1=火, 2=土, 3=金, 4=水


def get_ganzhi(dates):
    days_diff = (dates - ANCHOR_DATE).days.values
    stems = (3 + days_diff) % 10
    branches = (7 + days_diff) % 12
    elems = np.array([STEM_ELEMENT[s] for s in stems])
    return stems, branches, elems


def draw_yao_segment(ax, cx, cy, theta_rad, is_yang, half_len=0.11, lw=4.0, color='#00f5d4'):
    tx_v, ty_v = -np.sin(theta_rad), np.cos(theta_rad)
    if is_yang:
        ax.plot([cx - half_len * tx_v, cx + half_len * tx_v],
                [cy - half_len * ty_v, cy + half_len * ty_v],
                color=color, lw=lw, solid_capstyle='butt', zorder=5)
    else:
        gap = half_len * 0.22
        ax.plot([cx - half_len * tx_v, cx - gap * tx_v],
                [cy - half_len * ty_v, cy - gap * ty_v],
                color=color, lw=lw, solid_capstyle='butt', zorder=5)
        ax.plot([cx + gap * tx_v, cx + half_len * tx_v],
                [cy + gap * ty_v, cy + half_len * ty_v],
                color=color, lw=lw, solid_capstyle='butt', zorder=5)


# ==============================================================================
# 1. 中宫太极与先天八卦罗盘 (Taiji + Fu Xi Bagua Compass)
# ==============================================================================
def plot_taiji_bagua(ax, y):
    med = float(np.median(y))
    bits = (y >= med).astype(int)
    tri_counts = {k: 0 for k in TRIGRAMS}
    for i in range(2, len(bits)):
        tri = (int(bits[i - 2]), int(bits[i - 1]), int(bits[i]))
        tri_counts[tri] += 1

    max_cnt = max(max(tri_counts.values()), 1)
    yang_pct = float(np.mean(bits) * 100.0)
    yin_pct = 100.0 - yang_pct

    # 画八角频率扇区
    for tri, deg in FUXI_RING:
        cnt = tri_counts[tri]
        r_out = 0.44 + 0.36 * (cnt / float(max_cnt))
        is_hot = cnt == max_cnt
        fc = '#ff00ff' if is_hot else '#00bbf9'
        alpha = 0.45 if is_hot else 0.16 + 0.25 * (cnt / float(max_cnt))
        w = Wedge((0.0, 0.0), r_out, deg - 21.5, deg + 21.5, width=r_out - 0.41,
                  facecolor=fc, edgecolor='#00f5d4', lw=1.0, alpha=alpha, zorder=2)
        ax.add_patch(w)

        rad = np.deg2rad(deg)
        # 自内向外画三根爻（初爻在内，上爻在外）
        for pos_i, r_bar in enumerate([0.89, 0.97, 1.05]):
            bar_color = '#ffea00' if is_hot else '#00f5d4'
            draw_yao_segment(ax, r_bar * np.cos(rad), r_bar * np.sin(rad),
                             rad, tri[pos_i] == 1, half_len=0.105, lw=3.8, color=bar_color)

        zh, en, eng = TRIGRAMS[tri]
        lbl = f'{zh} ({cnt})' if HAS_CJK else f'{en} ({cnt})'
        ax.text(1.26 * np.cos(rad), 1.26 * np.sin(rad), lbl,
                color='#ffea00' if is_hot else '#e0fbfc',
                fontsize=8.8, fontweight='bold', ha='center', va='center')

    # 画中心赛博太极阴阳鱼
    r_tj = 0.37
    ax.add_patch(Wedge((0, 0), r_tj, -90, 90,
                 facecolor='#00f5d4', edgecolor='none', zorder=3))
    ax.add_patch(Wedge((0, 0), r_tj, 90, 270,
                 facecolor='#0c1424', edgecolor='none', zorder=3))
    ax.add_patch(Circle((0, r_tj / 2), r_tj / 2,
                 facecolor='#00f5d4', edgecolor='none', zorder=4))
    ax.add_patch(Circle((0, -r_tj / 2), r_tj / 2,
                 facecolor='#0c1424', edgecolor='none', zorder=4))
    ax.add_patch(Circle((0, r_tj / 2), r_tj / 6.5,
                 facecolor='#0c1424', edgecolor='#ff006e', lw=1.2, zorder=5))
    ax.add_patch(Circle((0, -r_tj / 2), r_tj / 6.5,
                 facecolor='#00f5d4', edgecolor='white', lw=1.0, zorder=5))
    ax.add_patch(Circle((0, 0), r_tj, fill=False,
                 edgecolor='#39ff14', lw=2.0, zorder=6))

    ax.set_xlim(-1.48, 1.48)
    ax.set_ylim(-1.48, 1.48)
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')
    ax.set_title(tx('先天太极八卦罗盘 (3日阴阳共振)', 'Prior-Heaven Taiji & Bagua Compass'),
                 color='#00f5d4', fontweight='bold')

    ax.text(0.0, -1.43,
            tx(f'阳日(≥中位{med:.0f}): {yang_pct:.1f}%  |  阴日: {yin_pct:.1f}%',
               f'Yang (≥Med {med:.0f}): {yang_pct:.1f}%  |  Yin: {yin_pct:.1f}%'),
            ha='center', va='bottom', fontsize=8.5, color='#39ff14', family='monospace')


# ==============================================================================
# 2. 今日占卜推演：最近6天四象起卦 (本卦 -> 动爻 -> 之卦)
# ==============================================================================
def plot_hexagram_divination(ax, dates, y):
    q25, q50, q75 = np.quantile(y, [0.25, 0.50, 0.75])
    last6_y = y[-6:]
    last6_d = dates[-6:]

    # 6=老阴(变阳), 8=少阴, 7=少阳, 9=老阳(变阴)
    si_xiang = []
    primary_bits = []
    trans_bits = []
    moving = []

    for val in last6_y:
        if val <= q25:
            si_xiang.append((6, tx('老阴×', 'OldYin×')))
            primary_bits.append(0)
            trans_bits.append(1)
            moving.append(True)
        elif val <= q50:
            si_xiang.append((8, tx('少阴', 'YngYin')))
            primary_bits.append(0)
            trans_bits.append(0)
            moving.append(False)
        elif val <= q75:
            si_xiang.append((7, tx('少阳', 'YngYang')))
            primary_bits.append(1)
            trans_bits.append(1)
            moving.append(False)
        else:
            si_xiang.append((9, tx('老阳○', 'OldYang○')))
            primary_bits.append(1)
            trans_bits.append(0)
            moving.append(True)

    p_low, p_up = tuple(primary_bits[:3]), tuple(primary_bits[3:])
    t_low, t_up = tuple(trans_bits[:3]), tuple(trans_bits[3:])
    p_num, p_zh, p_en = HEXAGRAM_TABLE[(p_low, p_up)]
    t_num, t_zh, t_en = HEXAGRAM_TABLE[(t_low, t_up)]

    def draw_hex_bar(x0, x1, y_pos, bit, color, lw=8.5):
        if bit == 1:
            ax.plot([x0, x1], [y_pos, y_pos], color=color,
                    lw=lw, solid_capstyle='butt')
        else:
            mid = 0.5 * (x0 + x1)
            gap = (x1 - x0) * 0.12
            ax.plot([x0, mid - gap], [y_pos, y_pos],
                    color=color, lw=lw, solid_capstyle='butt')
            ax.plot([mid + gap, x1], [y_pos, y_pos],
                    color=color, lw=lw, solid_capstyle='butt')

    yao_names_zh = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']
    yao_names_en = ['Line 1', 'Line 2', 'Line 3', 'Line 4', 'Line 5', 'Line 6']

    for i in range(6):
        y_pos = 1.0 + i * 1.0
        is_mov = moving[i]
        c_left = '#ff006e' if is_mov else '#00f5d4'
        c_right = '#ffbe0b' if is_mov else '#39ff14'

        draw_hex_bar(2.3, 4.3, y_pos, primary_bits[i], c_left)
        draw_hex_bar(6.2, 8.2, y_pos, trans_bits[i], c_right)

        yn = yao_names_zh[i] if HAS_CJK else yao_names_en[i]
        sx_code, sx_lbl = si_xiang[i]
        ax.text(2.1, y_pos, f"{last6_d[i].strftime('%m-%d')} ({int(last6_y[i])}) {yn} [{sx_lbl}]",
                ha='right', va='center', fontsize=8.0, color='#ffbe0b' if is_mov else '#adb5bd',
                family='monospace')

        if is_mov:
            ax.annotate('', xy=(5.95, y_pos), xytext=(4.55, y_pos),
                        arrowprops=dict(arrowstyle='->', color='#ff006e', lw=1.6))

    p_title = f"#{p_num} {p_zh}" if HAS_CJK else f"#{p_num} {p_en}"
    t_title = f"#{t_num} {t_zh}" if HAS_CJK else f"#{t_num} {t_en}"

    ax.text(3.3, 6.9, tx(f'【今日·本卦】\n{p_title}', f'[Primary Hexagram]\n{p_title}'),
            ha='center', va='center', fontsize=10.5, fontweight='bold', color='#00f5d4')
    ax.text(7.2, 6.9, tx(f'【变爻·之卦】\n{t_title}', f'[Transformed Hexagram]\n{t_title}'),
            ha='center', va='center', fontsize=10.5, fontweight='bold', color='#39ff14')

    ax.annotate('', xy=(5.85, 6.9), xytext=(4.65, 6.9),
                arrowprops=dict(arrowstyle='->', color='#ffbe0b', lw=2.2))

    n_mov = sum(moving)
    verdict = tx(
        f'动爻数: {n_mov}  |  起卦窗口: {last6_d[0].strftime("%m-%d")} ~ {last6_d[-1].strftime("%m-%d")}',
        f'Moving Lines: {n_mov}  |  Window: {last6_d[0].strftime("%m-%d")} ~ {last6_d[-1].strftime("%m-%d")}'
    )
    ax.text(5.2, 0.15, verdict, ha='center', va='center', fontsize=8.4, color='#ffbe0b',
            family='monospace',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#0a0f18', edgecolor='#ffbe0b', alpha=0.88))

    ax.set_xlim(-1.4, 8.7)
    ax.set_ylim(-0.4, 7.7)
    ax.axis('off')
    ax.set_title(tx('赛博龟甲占卜：本卦 → 动爻 → 之卦', 'Cyber Divination: Primary -> Moving -> Transformed'),
                 color='#ff00ff', fontweight='bold')

    return (p_low, p_up), (t_low, t_up)


# ==============================================================================
# 3. 64卦全息遍历矩阵 (8x8 Hexagram Matrix)
# ==============================================================================
def plot_64_hexagram_matrix(ax, y, today_pair):
    med = float(np.median(y))
    bits = (y >= med).astype(int)

    mat = np.zeros((8, 8), dtype=int)
    idx_map = {tri: i for i, tri in enumerate(ORDER_8)}

    for t in range(5, len(bits)):
        low = (int(bits[t - 5]), int(bits[t - 4]), int(bits[t - 3]))
        up = (int(bits[t - 2]), int(bits[t - 1]), int(bits[t]))
        mat[idx_map[low], idx_map[up]] += 1

    im = ax.imshow(mat, cmap='magma', aspect='auto')
    vmax = max(int(mat.max()), 1)

    best_r, best_c = np.unravel_index(np.argmax(mat), mat.shape)
    today_r, today_c = idx_map[today_pair[0]], idx_map[today_pair[1]]

    for r in range(8):
        for c in range(8):
            cnt = mat[r, c]
            _, zh, en = HEXAGRAM_TABLE[(ORDER_8[r], ORDER_8[c])]
            short_name = zh if HAS_CJK else en[:6]
            txt_c = 'black' if cnt > 0.62 * \
                vmax else ('white' if cnt > 0 else '#555b6e')
            ax.text(c, r, f'{short_name}\n{cnt}', ha='center', va='center',
                    color=txt_c, fontsize=6.8, fontweight='bold' if cnt > 0 else 'normal')

    # 高亮命运最高频卦（金框）与今日卦（绿框）
    ax.add_patch(plt.Rectangle((best_c - 0.48, best_r - 0.48), 0.96, 0.96,
                               fill=False, edgecolor='#ffea00', lw=2.3, zorder=5))
    ax.add_patch(plt.Rectangle((today_c - 0.44, today_r - 0.44), 0.88, 0.88,
                               fill=False, edgecolor='#39ff14', lw=2.0, ls='--', zorder=6))

    tick_lbls = [f'{TRIGRAMS[t][0]}' if HAS_CJK else TRIGRAMS[t][1]
                 for t in ORDER_8]
    ax.set_xticks(np.arange(8))
    ax.set_yticks(np.arange(8))
    ax.set_xticklabels(tick_lbls, fontsize=8.5, fontweight='bold')
    ax.set_yticklabels(tick_lbls, fontsize=8.5, fontweight='bold')
    ax.set_xlabel(tx('上卦 (外卦)', 'Upper Trigram'))
    ax.set_ylabel(tx('下卦 (内卦)', 'Lower Trigram'))

    unlocked = int(np.sum(mat > 0))
    _, b_zh, b_en = HEXAGRAM_TABLE[(ORDER_8[best_r], ORDER_8[best_c])]
    b_name = b_zh if HAS_CJK else b_en
    ax.set_title(tx(f'六十四卦遍历棋盘 (已解锁 {unlocked}/64 | 本命卦: {b_name} ×{mat[best_r, best_c]})',
                    f'64-Hexagram Matrix ({unlocked}/64 Unlocked | Destiny: {b_name} ×{mat[best_r, best_c]})'),
                 color='#ffbe0b', fontweight='bold')


# ==============================================================================
# 4. 五行生克五芒星阵 (WuXing Generating & Overcoming Pentagon + ANOVA)
# ==============================================================================
def plot_wuxing_pentagon(ax, dates, y):
    _, _, elems = get_ganzhi(dates)
    names_zh = ['木 (甲乙)', '火 (丙丁)', '土 (戊己)', '金 (庚辛)', '水 (壬癸)']
    names_en = ['WOOD (Jia/Yi)', 'FIRE (Bing/Ding)',
                'EARTH (Wu/Ji)', 'METAL (Geng/Xin)', 'WATER (Ren/Gui)']
    colors = ['#39ff14', '#ff4d6d', '#ffbe0b', '#e0fbfc', '#00bbf9']

    groups = [y[elems == i] for i in range(5)]
    means = np.array([float(np.mean(g)) if len(g)
                     > 0 else 0.0 for g in groups])
    log_groups = [np.log1p(g) for g in groups if len(g) > 1]
    _, p_val = f_oneway(*log_groups) if len(log_groups) == 5 else (0.0, 1.0)

    # 五个顶点的顺时针角度（顶=90°木，顺时针：火、土、金、水）
    angles = np.deg2rad([90.0, 18.0, -54.0, -126.0, 162.0])
    coords = np.column_stack([np.cos(angles), np.sin(angles)])

    # 外圈相生绿箭头：木->火->土->金->水->木
    for i in range(5):
        j = (i + 1) % 5
        p1, p2 = coords[i], coords[j]
        vec = p2 - p1
        ax.annotate('', xy=p1 + 0.80 * vec, xytext=p1 + 0.20 * vec,
                    arrowprops=dict(arrowstyle='->', color='#39ff14', lw=1.8, alpha=0.68))

    # 内五角星相克红虚线：木克土(0->2), 土克水(2->4), 水克火(4->1), 火克金(1->3), 金克木(3->0)
    for i in range(5):
        j = (i + 2) % 5
        p1, p2 = coords[i], coords[j]
        vec = p2 - p1
        ax.annotate('', xy=p1 + 0.82 * vec, xytext=p1 + 0.18 * vec,
                    arrowprops=dict(arrowstyle='->', color='#ff006e', ls='--', lw=1.3, alpha=0.55))

    # 节点大小对应各五行日均 Clones
    m_min, m_max = means.min(), max(means.max(), means.min() + 1e-6)
    sizes = 420.0 + 1350.0 * ((means - m_min) / (m_max - m_min))
    for i in range(5):
        ax.scatter([coords[i, 0]], [coords[i, 1]], s=sizes[i], color=colors[i],
                   edgecolors='white', lw=1.5, alpha=0.88, zorder=5)
        lbl = names_zh[i] if HAS_CJK else names_en[i]
        ax.text(coords[i, 0], coords[i, 1] + (0.23 if i in (0, 1, 4) else -0.25),
                f'{lbl}\n{means[i]:.1f}/d', color=colors[i], fontsize=8.8,
                fontweight='bold', ha='center', va='center')

    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-1.48, 1.50)
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')
    ax.set_title(tx('干支五行生克星阵 (绿生 / 红克)', 'WuXing Five-Element Pentagon (Gen/Overcome)'),
                 color='#39ff14', fontweight='bold')

    best_e = int(np.argmax(means))
    weak_e = int(np.argmin(means))
    b_name = (names_zh[best_e] if HAS_CJK else names_en[best_e]).split(' ')[0]
    w_name = (names_zh[weak_e] if HAS_CJK else names_en[weak_e]).split(' ')[0]
    info = tx(
        f'最旺五行: {b_name} ({means[best_e]:.1f}) | 命中缺: {w_name} ({means[weak_e]:.1f})\nANOVA p={p_val:.3f}',
        f'Strongest: {b_name} ({means[best_e]:.1f}) | Weakest: {w_name} ({means[weak_e]:.1f})\nANOVA p={p_val:.3f}'
    )
    ax.text(0.0, -1.42, info, ha='center', va='bottom', fontsize=8.2, color='#ffbe0b',
            family='monospace',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#0a0f18', edgecolor='#ffbe0b', alpha=0.88))


# ==============================================================================
# 5. 十二生肖地支日柱图 (12 Earthly Branches Zodiac Pillars)
# ==============================================================================
def plot_earthly_branches(ax, dates, y):
    stems, branches, _ = get_ganzhi(dates)
    means = [float(np.mean(y[branches == b])) if np.any(
        branches == b) else 0.0 for b in range(12)]
    medians = [float(np.median(y[branches == b])) if np.any(
        branches == b) else 0.0 for b in range(12)]

    peak_idx = int(np.argmax(y))
    peak_b = int(branches[peak_idx])
    peak_gz = (f'{STEMS_ZH[stems[peak_idx]]}{BRANCHES_ZH[peak_b]}'
               if HAS_CJK else f'{STEMS_EN[stems[peak_idx]]}-{BRANCHES_EN[peak_b]}')

    today_b = int(branches[-1])
    today_gz = (f'{STEMS_ZH[stems[-1]]}{BRANCHES_ZH[today_b]}'
                if HAS_CJK else f'{STEMS_EN[stems[-1]]}-{BRANCHES_EN[today_b]}')

    x_pos = np.arange(12)
    bar_colors = ['#ff006e' if b == peak_b else (
        '#39ff14' if b == today_b else '#00bbf9') for b in range(12)]
    ax.bar(x_pos, means, color=bar_colors, alpha=0.82, edgecolor='white', lw=0.6,
           label=tx('日均 Clones', 'Mean Clones'))
    ax.plot(x_pos, medians, color='#ffea00', marker='o', ms=5, lw=1.8,
            label=tx('中位 Clones', 'Median Clones'))

    ax.annotate(
        tx(f'859暴走日: {peak_gz}日', f'Peak 859: {peak_gz}'),
        xy=(peak_b, means[peak_b]),
        xytext=(min(11, peak_b + 1.3), means[peak_b] * 0.92),
        color='#ffea00', fontsize=8.5, fontweight='bold',
        arrowprops=dict(arrowstyle='->', color='#ffea00', lw=1.2)
    )

    lbls = BRANCHES_ZH if HAS_CJK else BRANCHES_EN
    ax.set_xticks(x_pos)
    ax.set_xticklabels(lbls, rotation=0 if HAS_CJK else 35,
                       ha='center' if HAS_CJK else 'right', fontsize=8.5)
    ax.set_ylabel(tx('日均克隆数', 'Clones / Day'))
    ax.set_title(tx(f'十二地支生肖日柱战力榜 (末日柱: {today_gz})',
                    f'12 Earthly Branches Zodiac Performance (Latest: {today_gz})'),
                 color='#00bbf9', fontweight='bold')
    ax.legend(loc='upper right', fontsize=8, framealpha=0.85)
    ax.grid(alpha=0.15, axis='y')


# ==============================================================================
# 6. 八卦非重叠转移矩阵 (8x8 Bagua Transition Matrix: (t-2..t) -> (t+1..t+3))
# ==============================================================================
def plot_bagua_transitions(ax, y):
    med = float(np.median(y))
    bits = (y >= med).astype(int)
    idx_map = {tri: i for i, tri in enumerate(ORDER_8)}

    trans = np.zeros((8, 8), dtype=float)
    for t in range(2, len(bits) - 3):
        src = (int(bits[t - 2]), int(bits[t - 1]), int(bits[t]))
        dst = (int(bits[t + 1]), int(bits[t + 2]), int(bits[t + 3]))
        trans[idx_map[src], idx_map[dst]] += 1.0

    row_sums = np.maximum(trans.sum(axis=1, keepdims=True), 1.0)
    prob = trans / row_sums * 100.0

    im = ax.imshow(prob, cmap='inferno', vmin=0.0, vmax=max(
        float(prob.max()), 30.0), aspect='auto')
    cbar = plt.colorbar(im, ax=ax, shrink=0.88, pad=0.02)
    cbar.set_label(tx('转移概率 (%)', 'Transition Prob (%)'), fontsize=8.5)

    vmax = max(float(prob.max()), 1.0)
    for i in range(8):
        for j in range(8):
            v = prob[i, j]
            if v >= 5.0:
                c_txt = 'black' if v > 0.62 * vmax else 'white'
                ax.text(j, i, f'{v:.0f}%', ha='center',
                        va='center', color=c_txt, fontsize=7.5)

    tick_lbls = [f'{TRIGRAMS[t][0]}' if HAS_CJK else TRIGRAMS[t][1]
                 for t in ORDER_8]
    ax.set_xticks(np.arange(8))
    ax.set_yticks(np.arange(8))
    ax.set_xticklabels(tick_lbls, fontsize=8.5, fontweight='bold')
    ax.set_yticklabels(tick_lbls, fontsize=8.5, fontweight='bold')
    ax.set_xlabel(tx('后三日演化卦象 (To)', 'Next 3-Day Trigram (To)'))
    ax.set_ylabel(tx('前三日原卦象 (From)', 'Current 3-Day Trigram (From)'))
    ax.set_title(tx('八卦无重叠马尔可夫演化阵 (t → t+3)', 'Bagua Markov Transition Matrix (t -> t+3)'),
                 color='#ff4d6d', fontweight='bold')


def main():
    print('☯️ 天机道长 042: Executing Cyber I Ching Divination Protocol (v14.0)...')
    df = load_bunker_data()
    dates = df.index
    y = df['clones'].values.astype(float)

    fig, axes = plt.subplots(3, 2, figsize=(20, 18), facecolor='#04060a')
    for ax in axes.flat:
        ax.set_facecolor('#080c14')

    plot_taiji_bagua(axes[0, 0], y)
    today_pair, _ = plot_hexagram_divination(axes[0, 1], dates, y)
    plot_64_hexagram_matrix(axes[1, 0], y, today_pair)
    plot_wuxing_pentagon(axes[1, 1], dates, y)
    plot_earthly_branches(axes[2, 0], dates, y)
    plot_bagua_transitions(axes[2, 1], y)

    fig.suptitle(
        tx('天机道长 042：地堡赛博周易八卦与五行玄学神坛 (Cyber I Ching Oracle)',
           'Pod 042: Bunker Cyber I Ching & WuXing Divination Altar'),
        color='#ffea00', fontsize=16.8, fontweight='bold', y=0.975
    )

    fig.subplots_adjust(left=0.06, right=0.95, top=0.925,
                        bottom=0.06, hspace=0.33, wspace=0.22)
    out_dir = os.path.dirname(OUTPUT_IMAGE)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    plt.savefig(OUTPUT_IMAGE, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(
        f'✅ Cyber I Ching Altar sealed at: {OUTPUT_IMAGE} (CJK Font Active: {HAS_CJK})')


if __name__ == '__main__':
    main()
