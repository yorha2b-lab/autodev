import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge, Polygon, FancyBboxPatch


ZODIAC_SIGNS = [
    ('ARI', '白羊', 3, 21), ('TAU', '金牛', 4, 20), ('GEM', '双子', 5, 21),
    ('CAN', '巨蟹', 6, 21), ('LEO', '狮子', 7, 23), ('VIR', '处女', 8, 23),
    ('LIB', '天秤', 9, 23), ('SCO', '天蝎', 10, 23), ('SAG', '射手', 11, 22),
    ('CAP', '摩羯', 12, 22), ('AQU', '水瓶', 1, 20), ('PIS', '双鱼', 2, 19),
]


def date_to_zodiac(dt):
    """返回日期对应的星座索引(0..11)和黄道角度(0..360)"""
    m, d = int(dt.month), int(dt.day)
    sign_idx = 11
    for i in range(12):
        _, _, sm, sd = ZODIAC_SIGNS[i]
        _, _, nm, nd = ZODIAC_SIGNS[(i + 1) % 12]
        if (m == sm and d >= sd) or (m == nm and d < nd):
            sign_idx = i
            break
        if sm == 12 and ((m == 12 and d >= 22) or (m == 1 and d < 20)):
            sign_idx = 9
            break

    _, _, sm, sd = ZODIAC_SIGNS[sign_idx]
    start_dt = pd.Timestamp(year=dt.year if m >=
                            sm else dt.year - 1, month=sm, day=sd)
    if sign_idx == 9 and m == 1:
        start_dt = pd.Timestamp(year=dt.year - 1, month=12, day=22)
    day_in_sign = max(0, min(29, (dt - start_dt).days))
    angle = sign_idx * 30.0 + day_in_sign
    return sign_idx, angle


def draw_sacred_emblem(ax, cx, cy, kind, color, reversed_card=False):
    """用纯矢量绘制塔罗牌内几何图腾，避免 Linux 缺字方块"""
    sign = -1.0 if reversed_card else 1.0
    if kind == 'tower':
        pts = np.array([
            [cx - 0.55, cy - 0.9], [cx + 0.55, cy - 0.9],
            [cx + 0.38, cy + 0.45], [cx - 0.38, cy + 0.45]
        ])
        if reversed_card:
            pts[:, 1] = 2 * cy - pts[:, 1]
        ax.add_patch(Polygon(pts, closed=True, fc='none', ec=color, lw=1.8))
        bolt = np.array([
            [cx + 0.65, cy + 0.95 * sign], [cx - 0.05, cy + 0.42 * sign],
            [cx + 0.25, cy + 0.42 * sign], [cx - 0.55, cy - 0.25 * sign]
        ])
        ax.plot(bolt[:, 0], bolt[:, 1], color='yellow', lw=2.0)
    elif kind == 'wheel':
        ax.add_patch(Circle((cx, cy), 0.75, fc='none', ec=color, lw=1.8))
        ax.add_patch(Circle((cx, cy), 0.32, fc='none', ec=color, lw=1.2))
        for deg in range(0, 360, 45):
            rad = np.deg2rad(deg)
            ax.plot([cx, cx + 0.75 * np.cos(rad)],
                    [cy, cy + 0.75 * np.sin(rad)], color=color, lw=1.1)
    elif kind == 'sun':
        ax.add_patch(Circle((cx, cy), 0.38, fc=color,
                     alpha=0.25, ec=color, lw=1.8))
        for deg in range(0, 360, 30):
            r1 = np.deg2rad(deg)
            r_out = 0.85 if deg % 60 == 0 else 0.62
            ax.plot([cx + 0.42 * np.cos(r1), cx + r_out * np.cos(r1)],
                    [cy + 0.42 * np.sin(r1), cy + r_out * np.sin(r1)],
                    color=color, lw=1.5)
    elif kind == 'star':
        for rot in [0, 60]:
            angles = np.deg2rad([90 + rot, 210 + rot, 330 + rot])
            tri = np.column_stack([cx + 0.75 * np.cos(angles),
                                   cy + 0.75 * np.sin(angles) * sign])
            ax.add_patch(Polygon(tri, closed=True,
                         fc='none', ec=color, lw=1.6))
        ax.add_patch(Circle((cx, cy), 0.14, fc='yellow', ec='none'))
    elif kind == 'chariot':
        tri = np.array([
            [cx, cy + 0.8 * sign], [cx - 0.68, cy - 0.55 * sign],
            [cx + 0.68, cy - 0.55 * sign]
        ])
        ax.add_patch(Polygon(tri, closed=True, fc=color,
                     alpha=0.18, ec=color, lw=1.8))
        ax.add_patch(Circle((cx, cy - 0.08 * sign), 0.25,
                     fc='none', ec='yellow', lw=1.5))
    else:  # magician / temperance
        theta = np.linspace(0, 2 * np.pi, 100)
        lx = cx + 0.7 * np.sin(theta)
        ly = cy + 0.32 * np.sin(2 * theta) * sign
        ax.plot(lx, ly, color=color, lw=2.0)
        ax.add_patch(Circle((cx, cy), 0.15, fc='none', ec='yellow', lw=1.4))


def draw_qimen_panel(ax, df):
    """Panel 1: 奇门遁甲 · 洛书九宫战局盘"""
    ax.set_facecolor('#05080f')
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 3)
    ax.axis('off')

    luoshu_grid = [
        [(4, '巽四宫·东南'), (9, '离九宫·正南'), (2, '坤二宫·西南')],
        [(3, '震三宫·正东'), (5, '中五宫·中枢'), (7, '兑七宫·正西')],
        [(8, '艮八宫·东北'), (1, '坎一宫·正北'), (6, '乾六宫·西北')],
    ]
    ring_order = [1, 8, 3, 4, 9, 2, 7, 6]
    gates = ['休门', '生门', '伤门', '杜门', '景门', '死门', '惊门', '开门']
    stars = {
        1: '天蓬', 2: '天芮', 3: '天冲', 4: '天辅', 5: '天禽',
        6: '天心', 7: '天柱', 8: '天任', 9: '天英'
    }
    deities = ['值符', '腾蛇', '太阴', '六合', '白虎', '玄武', '九地', '九天']

    tail9 = df.tail(9)['clones'].to_numpy()
    if len(tail9) < 9:
        tail9 = np.pad(tail9, (9 - len(tail9), 0), mode='edge')

    last_dt = df['date'].iloc[-1]
    last_val = int(df['clones'].iloc[-1])
    total_val = int(df['clones'].sum())

    gate_shift = (last_val + last_dt.day) % 8
    deity_shift = (last_dt.weekday() + total_val) % 8
    star_shift = total_val % 8

    palace_val = {p: int(tail9[p - 1]) for p in range(1, 10)}
    zhifu_palace = ring_order[deity_shift % 8]
    kaimen_palace = ring_order[(7 + gate_shift) % 8]

    gate_map = {}
    deity_map = {}
    star_map = {5: '天禽'}
    ring_stars = ['天蓬', '天任', '天冲', '天辅', '天英', '天芮', '天柱', '天心']

    for idx, p in enumerate(ring_order):
        gate_map[p] = gates[(idx - gate_shift) % 8]
        deity_map[p] = deities[(idx - deity_shift) % 8]
        star_map[p] = ring_stars[(idx - star_shift) % 8]

    for row_i in range(3):
        for col_i in range(3):
            p_num, p_name = luoshu_grid[row_i][col_i]
            x0, y0 = col_i, 2 - row_i
            val = palace_val[p_num]
            g_name = gate_map.get(p_num, '中寄')
            s_name = star_map.get(p_num, stars[p_num])
            d_name = deity_map.get(p_num, '太极')

            if p_num == zhifu_palace:
                ec, fc, alpha = '#f1c40f', '#f1c40f', 0.16
            elif g_name in ['开门', '生门', '休门']:
                ec, fc, alpha = '#00ffcc', '#00ffcc', 0.10
            elif g_name in ['死门', '惊门']:
                ec, fc, alpha = '#e74c3c', '#e74c3c', 0.10
            else:
                ec, fc, alpha = '#3498db', '#111827', 0.35

            rect = FancyBboxPatch(
                (x0 + 0.05, y0 + 0.05), 0.90, 0.90,
                boxstyle='round,pad=0.02,rounding_size=0.06',
                fc=fc, ec=ec, lw=2.0 if p_num == zhifu_palace else 1.2, alpha=alpha
            )
            ax.add_patch(rect)
            border = FancyBboxPatch(
                (x0 + 0.05, y0 + 0.05), 0.90, 0.90,
                boxstyle='round,pad=0.02,rounding_size=0.06',
                fc='none', ec=ec, lw=2.2 if p_num == zhifu_palace else 1.1
            )
            ax.add_patch(border)

            ax.text(x0 + 0.11, y0 + 0.87, p_name,
                    color='#aaa', fontsize=8.5, va='top')
            ax.text(x0 + 0.89, y0 + 0.87, d_name, color=ec, fontsize=9,
                    fontweight='bold', ha='right', va='top')
            ax.text(x0 + 0.50, y0 + 0.54, f"{s_name} · {g_name}",
                    color='white', fontsize=11.5, fontweight='bold',
                    ha='center', va='center')
            ax.text(x0 + 0.50, y0 + 0.22, f"Clones: {val}",
                    color='#00ffcc' if p_num != zhifu_palace else '#f1c40f',
                    fontsize=9.5, family='monospace', ha='center', va='center')

    verdict = f"值符驻宫: {zhifu_palace}宫 | 开门吉位: {kaimen_palace}宫 | 宜重构代码"
    ax.set_title(f'奇门遁甲 · 洛书九宫战局盘\n({verdict})',
                 color='#f1c40f', pad=10, fontsize=12, fontweight='bold')


def draw_zodiac_panel(ax, df):
    """Panel 2: 黄道十二星座本命星盘"""
    ax.set_facecolor('#05080f')
    ax.set_xlim(-1.42, 1.42)
    ax.set_ylim(-1.35, 1.35)
    ax.set_aspect('equal')
    ax.axis('off')

    df_z = df.copy()
    z_info = df_z['date'].apply(date_to_zodiac)
    df_z['sign_idx'] = [z[0] for z in z_info]
    sign_means = df_z.groupby('sign_idx')['clones'].mean()
    max_mean = max(float(sign_means.max()),
                   1.0) if not sign_means.empty else 1.0

    for i, (abbr, cn, _, _) in enumerate(ZODIAC_SIGNS):
        t1, t2 = i * 30.0, (i + 1) * 30.0
        val = float(sign_means.get(i, 0.0))
        norm = val / max_mean
        wedge_col = '#ff00ff' if norm > 0.65 else (
            '#00ffcc' if norm > 0.2 else '#1f2937')
        w_alpha = 0.25 + 0.45 * norm if val > 0 else 0.08
        ax.add_patch(Wedge((0, 0), 1.0, t1, t2, width=0.30,
                           fc=wedge_col, alpha=w_alpha, ec='#444', lw=1.0))

        mid_rad = np.deg2rad(t1 + 15.0)
        lx, ly = 1.18 * np.cos(mid_rad), 1.18 * np.sin(mid_rad)
        ax.text(lx, ly, f"{abbr}\n{cn}", color='white' if val > 0 else '#666',
                fontsize=8.2, fontweight='bold', ha='center', va='center')
        if val > 0:
            vx, vy = 0.85 * np.cos(mid_rad), 0.85 * np.sin(mid_rad)
            ax.text(vx, vy, f"{val:.0f}", color='yellow', fontsize=7.5,
                    fontweight='bold', ha='center', va='center')

    ax.add_patch(Circle((0, 0), 1.0, fc='none', ec='#00ffcc', lw=1.6))
    ax.add_patch(Circle((0, 0), 0.70, fc='none', ec='#ff00ff', lw=1.2))
    ax.add_patch(Circle((0, 0), 0.54, fc='#0d1117', ec='#333', lw=0.8))

    peak_row = df.loc[df['clones'].idxmax()]
    _, sun_ang = date_to_zodiac(peak_row['date'])
    _, moon_ang = date_to_zodiac(df['date'].iloc[-1])

    wk_means = df.groupby(df['date'].dt.dayofweek)['clones'].mean()
    best_wk = int(wk_means.idxmax()) if not wk_means.empty else 4

    planets = [
        ('SUN (Peak 859)', sun_ang, '#f1c40f', 110),
        ('MOON (Today)', moon_ang, '#00ffcc', 90),
        ('MERC (Median)', (moon_ang + 48) % 360, '#3498db', 65),
        ('VEN (Fri Peak)', (best_wk * 51.4 + 20) % 360, '#ff66cc', 75),
        ('MARS (Apr Burst)', 32.0, '#e74c3c', 75),
        ('JUP (Cumul)', (int(df['clones'].sum()) % 360), '#2ecc71', 80),
        ('SAT (Floor)', 260.0, '#9b59b6', 65),
    ]

    p_coords = []
    for label, ang, col, sz in planets:
        rad = np.deg2rad(ang)
        px, py = 0.54 * np.cos(rad), 0.54 * np.sin(rad)
        p_coords.append((px, py, ang, label, col))
        ax.scatter([px], [py], color=col, s=sz,
                   zorder=5, edgecolors='white', lw=1.0)
        tx, ty = 0.39 * np.cos(rad), 0.39 * np.sin(rad)
        short_tag = label.split(' ')[0]
        ax.text(tx, ty, short_tag, color=col, fontsize=7.2, fontweight='bold',
                ha='center', va='center')

    for i in range(len(p_coords)):
        for j in range(i + 1, len(p_coords)):
            x1, y1, a1, _, _ = p_coords[i]
            x2, y2, a2, _, _ = p_coords[j]
            diff = abs(a1 - a2) % 360
            diff = min(diff, 360 - diff)
            if abs(diff - 120) < 14:
                ax.plot([x1, x2], [y1, y2],
                        color='#2ecc71', lw=1.3, alpha=0.75)
            elif abs(diff - 90) < 14:
                ax.plot([x1, x2], [y1, y2], color='#e74c3c',
                        lw=1.2, ls='--', alpha=0.75)
            elif abs(diff - 180) < 14:
                ax.plot([x1, x2], [y1, y2], color='#ff00ff',
                        lw=1.1, ls=':', alpha=0.7)

    top_sign_i = int(sign_means.idxmax()) if not sign_means.empty else 3
    top_sign_cn = ZODIAC_SIGNS[top_sign_i][1]
    _, cur_sign_cn, _, _ = ZODIAC_SIGNS[date_to_zodiac(df['date'].iloc[-1])[0]]
    ax.set_title(
        f'黄道十二星座本命星盘\n(守护爆发宫: {top_sign_cn}座 | 当前行运: {cur_sign_cn}座)',
        color='#00ffcc', pad=10, fontsize=12, fontweight='bold'
    )


def draw_tarot_panel(ax, df):
    """Panel 3: 赛博塔罗大阿卡那三牌阵"""
    ax.set_facecolor('#05080f')
    ax.set_xlim(0, 9.6)
    ax.set_ylim(0, 5.2)
    ax.axis('off')

    n = len(df)
    early = df.head(max(1, n // 3))['clones']
    recent = df.tail(min(30, n))['clones']
    last7 = df.tail(min(7, n))['clones'].mean()
    prev23 = df.tail(min(30, n)).head(max(1, min(30, n) - 7))['clones'].mean()

    if early.max() >= 300:
        c1 = ('XVI', '高塔 THE TOWER', 'tower',
              False, '#e74c3c', '创世雷霆脉冲\n冲破天际引爆开局')
    else:
        c1 = ('I', '魔术师 MAGICIAN', 'magic',
              False, '#00ffcc', '零宣启动破局\n初露锋芒显神通')

    med_r = float(recent.median())
    std_r = float(recent.std()) if len(recent) > 1 else 0.0
    if std_r / max(med_r, 1.0) < 1.0:
        c2 = ('XIV', '节制 TEMPERANCE', 'magic', False,
              '#33cc33', f'中位 {med_r:.0f}/d 稳如磐石\n阴阳调和零故障')
    else:
        c2 = ('VII', '战车 CHARIOT', 'chariot',
              False, '#3498db', f'高并发推进\n日均波动冲锋中')

    if last7 >= prev23 * 1.1:
        c3 = ('XIX', '太阳 THE SUN', 'sun', False, '#f1c40f', '势头回暖照耀\n破万荣光近在眼前')
    elif last7 >= prev23 * 0.85:
        c3 = ('XVII', '星星 THE STAR', 'star',
              False, '#ff00ff', '静默长流不断\n暗中蓄力向未来')
    else:
        c3 = ('X', '命运之轮 WHEEL', 'wheel', True, '#f39c12', '短期周期回落\n蓄势待发待下轮')

    cards = [
        ('I. 过去 (PAST)', 0.35, c1),
        ('II. 现在 (PRESENT)', 3.45, c2),
        ('III. 未来 (FUTURE)', 6.55, c3),
    ]

    for slot, x0, (roman, title, emblem, is_rev, col, desc) in cards:
        ax.text(x0 + 1.35, 4.92, slot, color='#aaa', fontsize=9,
                fontweight='bold', ha='center')
        outer = FancyBboxPatch(
            (x0, 0.25), 2.70, 4.45,
            boxstyle='round,pad=0.04,rounding_size=0.14',
            fc='#0d1117', ec=col, lw=2.2
        )
        inner = FancyBboxPatch(
            (x0 + 0.14, 0.40), 2.42, 4.15,
            boxstyle='round,pad=0.02,rounding_size=0.08',
            fc='none', ec='#f1c40f', lw=0.8, alpha=0.6
        )
        ax.add_patch(outer)
        ax.add_patch(inner)

        pos_tag = '逆位 REV' if is_rev else '正位 UP'
        ax.text(x0 + 1.35, 4.30, f"{roman}  [{pos_tag}]", color='#f1c40f',
                fontsize=9.5, fontweight='bold', ha='center')
        draw_sacred_emblem(ax, x0 + 1.35, 2.85, emblem,
                           col, reversed_card=is_rev)
        ax.text(x0 + 1.35, 1.52, title, color=col, fontsize=9.8,
                fontweight='bold', ha='center')
        ax.text(x0 + 1.35, 0.88, desc, color='#ddd', fontsize=8.5,
                ha='center', va='center', linespacing=1.45)

    ax.set_title('赛博塔罗 · 大阿卡那命运三牌阵',
                 color='#ff00ff', pad=10, fontsize=12, fontweight='bold')


def draw_almanac_panel(ax, df):
    """Panel 4: 地堡赛博黄历 · 水逆监测与今日签筒"""
    ax.set_facecolor('#05080f')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    recent14 = df.tail(min(14, len(df)))['clones']
    recent7 = df.tail(min(7, len(df)))['clones']
    hist_med = float(df['clones'].median())
    last_dt = df['date'].iloc[-1]
    last_clones = int(df['clones'].iloc[-1])

    cv = float(recent14.std() / max(recent14.mean(), 1.0)
               ) if len(recent14) > 1 else 0.0
    retro_pct = int(np.clip(cv * 45.0, 5, 95))
    ratio_boost = np.clip((recent7.mean() / max(hist_med, 1.0)) * 35.0, 15, 50)
    fortune = int(np.clip(45 + ratio_boost - retro_pct * 0.25, 52, 99))

    if fortune >= 85:
        lot_rank, lot_col = '上上签 · 大吉', '#f1c40f'
    elif fortune >= 72:
        lot_rank, lot_col = '上吉签 · 顺遂', '#00ffcc'
    else:
        lot_rank, lot_col = '中吉签 · 稳进', '#3498db'

    card = FancyBboxPatch(
        (0.35, 0.35), 9.3, 9.2,
        boxstyle='round,pad=0.1,rounding_size=0.35',
        fc='#11141d', ec=lot_col, lw=2.4
    )
    ax.add_patch(card)

    ax.text(5.0, 8.85, f"【 地堡今日运势：{lot_rank} 】",
            color=lot_col, fontsize=15, fontweight='bold', ha='center')
    ax.text(5.0, 8.05, f"占卜基准日: {last_dt.strftime('%Y-%m-%d')} | 综合气运: {fortune} / 100",
            color='#bbb', fontsize=10, family='monospace', ha='center')

    ax.plot([0.9, 9.1], [7.45, 7.45], color='#333', lw=1.2)

    yi_text = "【宜】 拖截图生成CRUD / 静默迭代 / 周五冲刺收尾"
    ji_text = "【忌】 周日硬改Config / 无脑刷Actions自己拉自己"
    ax.text(1.0, 6.65, yi_text, color='#2ecc71',
            fontsize=11, fontweight='bold')
    ax.text(1.0, 5.75, ji_text, color='#e74c3c',
            fontsize=11, fontweight='bold')

    ax.plot([0.9, 9.1], [5.05, 5.05], color='#333', lw=1.2)

    bars = [
        ('代码运 (近期活力)', int(np.clip(recent7.mean() /
         max(hist_med, 1.0) * 65, 25, 98)), '#00ffcc'),
        ('护盾值 (抗噪稳态)', int(np.clip(100 - retro_pct * 0.7, 30, 96)), '#33cc33'),
        ('破万势 (进度冲刺)', int(
            np.clip(df['clones'].sum() / 10000.0 * 100, 10, 99)), '#f1c40f'),
        ('水逆值 (波动风险)', retro_pct, '#ff00ff'),
    ]

    y_pos = 4.25
    for label, pct, col in bars:
        ax.text(1.0, y_pos, label, color='white', fontsize=10, va='center')
        ax.add_patch(FancyBboxPatch(
            (4.1, y_pos - 0.22), 4.2, 0.44,
            boxstyle='round,pad=0.0,rounding_size=0.12',
            fc='#1f2937', ec='none'
        ))
        ax.add_patch(FancyBboxPatch(
            (4.1, y_pos - 0.22), 4.2 * (pct / 100.0), 0.44,
            boxstyle='round,pad=0.0,rounding_size=0.12',
            fc=col, ec='none', alpha=0.85
        ))
        ax.text(8.55, y_pos, f"{pct}%", color=col, fontsize=10,
                fontweight='bold', family='monospace', va='center')
        y_pos -= 1.02

    ax.set_title(f'地堡赛博黄历 · 水逆与求签神坛 (末日克隆: {last_clones})',
                 color='#f18f01', pad=10, fontsize=12, fontweight='bold')


def execute_mystic_arcana():
    print("🤖 天机道长 042: 正在焚香沐浴，开启奇门占星塔罗大法阵...")

    clone_path = 'ghrs-data/clones_ledger.csv'
    if not os.path.exists(clone_path):
        print("⚠️ clones_ledger.csv 缺失，无法起卦。")
        return

    df = pd.read_csv(clone_path)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date']).copy()
    df['clones'] = pd.to_numeric(df['clones'], errors='coerce').fillna(0)
    df = df.groupby('date', as_index=False)['clones'].sum()

    if df.empty:
        print("⚠️ 账本为空，无法起卦。")
        return

    full_idx = pd.date_range(df['date'].min(), df['date'].max(), freq='D')
    df = df.set_index('date').reindex(full_idx, fill_value=0)
    df = df.rename_axis('date').reset_index()

    plt.style.use('dark_background')
    plt.style.use('dark_background')
    plt.rcParams['font.sans-serif'] = [
        'Noto Sans CJK SC', 'Noto Sans CJK JP',
        'Noto Sans CJK TC', 'WenQuanYi Micro Hei', 'DejaVu Sans'
    ]
    plt.rcParams['axes.unicode_minus'] = False
    fig = plt.figure(figsize=(20, 14))
    fig.suptitle(
        '天机道长 042：奇门遁甲 · 黄道星盘 · 赛博塔罗终极玄学法阵',
        color='#f1c40f', fontsize=19, fontweight='bold'
    )
    gs = fig.add_gridspec(2, 2, hspace=0.26, wspace=0.16)

    draw_qimen_panel(fig.add_subplot(gs[0, 0]), df)
    draw_zodiac_panel(fig.add_subplot(gs[0, 1]), df)
    draw_tarot_panel(fig.add_subplot(gs[1, 0]), df)
    draw_almanac_panel(fig.add_subplot(gs[1, 1]), df)

    plt.tight_layout(rect=[0, 0.02, 1, 0.94])
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/mystic_arcana.png', dpi=120)
    plt.close(fig)
    print("✅ 奇门占星塔罗大法阵 mystic_arcana.png 结印完成！")


if __name__ == "__main__":
    execute_mystic_arcana()
