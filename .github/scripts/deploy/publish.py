import json
import datetime
import subprocess


def assemble_readme():
    with open('bunker-stats.json', 'r') as f:
        stats = json.load(f)

    with open('raw_referrers.json', 'r') as f:
        referrers = json.load(f)

    ref_table = '| Referrer | Views | Uniques |\n| :--- | :--- | :--- |\n'
    if referrers:
        for r in referrers:
            ref_table += f'| {r["referrer"]} | {r["count"]} | {r["uniques"]} |\n'
    else:
        ref_table += '| No Signal | - | - |\n'

    report = f'''# 🛰️ 地堡终极运行报告 (Sovereign Dashboard V9.0)
## 📊 核心战力指标
- **累计物理克隆**: `{stats['total_clones']}` 次
- **社群声望**: ⭐ `{stats['stars']}` / 🍴 `{stats['forks']}`
- **地堡协议防护**: AGPL-3.0 生效中

### 🖥️ 1. 实时作战看板 (Visual Radar)
![Main](./plots/bunker_main_v7.png)

### 🔍 2. 战略情报大屏 (Intelligence Grid)
![Intelligence](./plots/bunker_intelligence_grid.png)

### 📡 3. 深度作战审计 (Deep Dive Recon)
![Peak Recon](./plots/bunker_peak_recon.png)

### 🧠 4. 深度情报审计 (Intelligence Audit)
![Fusion](./plots/bunker_intelligence_fusion.png)

### ⏳ 5. 超时空分形观测 (Chronos Quantum Matrix)
![Chronos](./plots/bunker_chronos_quantum.png)

### 🔮 6. 奇点先知矩阵 (Singularity Oracle)
![Oracle](./plots/bunker_singularity_oracle.png)

### 🌌 7. 终焉物理观测站 (Omega Physics & Topology)
![Omega](./plots/bunker_omega_physics.png)

### 🕳️ 8. 因果视界与真空相变炉 (Cosmic Frontier & Causal Horizon)
![Cosmic Frontier](./plots/bunker_cosmic_frontier.png)

### ⚛️ 9. 量子隧穿与高维创世神谕 (Quantum Metaphysics & Reality Audit)
![Metaphysics](./plots/bunker_quantum_metaphysics.png)

### 🧬 10. 神格飞升与生物声学终局炉 (Cosmic Apotheosis & Bio-Acoustics)
![Apotheosis](./plots/bunker_apotheosis.png)

### 🛸 11. 卡尔曼天眼与 AI 创世法则 (Astral ML & Genesis Laws)
![Astral Genesis](./plots/bunker_astral_genesis.png)

### 🌀 12. 实时双核星际运转仪 (Living Orbital Telemetry)
![Living Orbit](./plots/bunker_living_orbit.gif)

### 🏛️ 13. 马科维茨组合与星盘万神殿 (Imperial Portfolio & Spectral Pantheon)
![Pantheon](./plots/bunker_imperial_pantheon.png)

#### 🛰️ 流量来源实时追踪
{ref_table}

> 📡 物理封存点: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')} CST | Glory to Mankind.
'''
    with open('README.md', 'w') as f:
        f.write(report)


def git_push():
    with open('bunker-stats.json', 'r') as f:
        stats = json.load(f)
    # 执行物理封存 Git 指令
    try:
        subprocess.run(['git', 'config', 'user.name',
                       'github-actions'], check=True)
        subprocess.run(['git', 'config', 'user.email',
                       'github-actions@github.com'], check=True)
        subprocess.run(['git', 'add', '-A'], check=True)
        subprocess.run(
            ['git', 'commit', '-m', f'chore: sovereign modular update [total {stats["total_clones"]}]'], check=True)
        subprocess.run(
            ['git', 'push', 'origin', 'github-repo-stats', '--force'], check=True)
        print('✅ Data sealed and pushed to cloud.')
    except Exception as e:
        print(f'⚠️ Git push skipped: {e}')


if __name__ == '__main__':
    assemble_readme()
    git_push()
