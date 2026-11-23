import os
import json
import datetime
import subprocess


def load_json(path, default):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default


def assemble_readme():
    stats = load_json('bunker-stats.json',
                      {'total_clones': 0, 'stars': 3, 'forks': 0})
    referrers = load_json('raw_referrers.json', [])
    m = load_json('paper_metrics.json', {})

    total_clones = int(stats.get('total_clones', 0))
    stars = int(stats.get('stars', 0))
    forks = int(stats.get('forks', 0))
    vip_ratio = m.get('temples_count', 16) / max(stars, 1)

    n_days = m.get('n_days', 230)
    start_d = m.get('start_date', '2026-04-03')
    end_d = m.get('end_date', 'N/A')
    mean_c = m.get('mean_clones', 0.0)
    med_c = m.get('median_clones', 0.0)
    pk_val = m.get('peak_val', 859)
    pk_date = m.get('peak_date', '2026-06-23')
    ent = m.get('entropy_bits', 0.0)
    gini = m.get('gini', 0.0)
    wk_ratio = m.get('wk_ratio', 1.0)
    mw_p = m.get('mw_p', 1.0)
    b_chi2 = m.get('benford_chi2', 0.0)
    b_p = m.get('benford_p', 1.0)
    b_mad = m.get('benford_mad', 0.0)
    sp_rho = m.get('spearman_rho', 0.0)
    sp_p = m.get('spearman_p', 1.0)
    eta_10k = m.get('eta_10k', 'TBD')

    ref_table = '| Referrer Domain | Total Views | Unique Visitors |\n| :--- | :---: | :---: |\n'
    if referrers:
        for r in referrers:
            ref_table += f'| `{r["referrer"]}` | {r["count"]} | {r["uniques"]} |\n'
    else:
        ref_table += '| *No External Signal* | - | - |\n'

    cst_now = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8))
    ).strftime('%Y-%m-%d %H:%M:%S')

    report = f'''<div align="center">

![Bunker HUD](./plots/bunker_hud.svg)

# Stochastic Thermodynamics, Algebraic Topology, and Cyber Divination of a Zero-Marketing Frontend CLI Repository
### 零宣传前端脚手架仓库的随机热力学、代数拓扑与赛博玄学演化实证研究

**Pod 042<sup>1*</sup>, YoRHa Bunker Lab<sup>2</sup>, Commander 2B<sup>2</sup>**
<sup>1</sup>*Automated Telemetry & Signal Processing Division, Bunker* · <sup>2</sup>*yorha2b-lab/autodev*

`Journal of Unnecessary Over-Engineering` · **Vol. 16** · **License: AGPL-3.0** · **Sync: {end_d}**

</div>

---

## Abstract (摘要)

We present a **{n_days}-day longitudinal multi-disciplinary investigation** (`{start_d}` to `{end_d}`) of `yorha2b-lab/autodev` (*Bunker*), a zero-marketing multimodal frontend CRUD scaffolding CLI. Despite minimal web visibility (**{stars} GitHub Stars**, **{forks} Forks**), the repository achieved **{total_clones:,} cumulative Git clones** (mean = `{mean_c}/d`, median = `{med_c}/d`) alongside sustained npm consumption. Combining signal processing, econometrics, stochastic physics, algebraic topology, and classical Chinese divination across **16 analytical modules** ({vip_ratio:.1f} temples per star), we uncover: (1) strict workweek circadian resonance (**{wk_ratio:.2f}×** weekday-to-weekend lift, Mann–Whitney $p = {mw_p}$), (2) natural organic conformity under Benford's Law ($\\chi^2 = {b_chi2}$, $p = {b_p}$, $\\text{{MAD}} = {b_mad}$), (3) complete decoupling between web views and terminal clones (Spearman $\\rho = {sp_rho}$, $p = {sp_p}$), and (4) high temporal sustainability ($H = {ent}\\text{{ bits}}$, Gini $= {gini}$), projecting milestone arrival at **{eta_10k}**.

**Keywords:** `Agentic Workflow` · `Stochastic Thermodynamics` · `Algebraic Topology` · `Random Matrix Theory` · `Cyber I Ching` · `Zero-Marketing Growth`

---

### Graphical Abstract (Real-Time Epicycle Clockwork & 3D Attractor)

<div align="center">

![Living Orbit](./plots/bunker_living_orbit.gif)
*Graphical Abstract. Left: 32-phasor Fourier epicycle reconstruction in delay complex space. Right: 360° orbital scan of the 3D Takens strange attractor highlighting the {pk_date} ({pk_val} clones) slingshot loop.*

</div>

---

## Table 1. Global Experimental Telemetry Summary

| Telemetry Dimension | Metric / Estimator | Observed Value | Physical / Empirical Interpretation |
| :--- | :--- | :---: | :--- |
| **Observation Horizon** | Continuous Daily Grid ($N$) | `{n_days}` days | `{start_d}` ~ `{end_d}` |
| **Cumulative Volume** | Total Clones / Peak Day | `{total_clones:,}` / `{pk_val}` | Peak occurred on `{pk_date}` |
| **Central Tendency** | Mean / Median Daily Clones | `{mean_c}` / `{med_c}` | Heavy-tailed Log-Normal regime |
| **Temporal Spread** | Shannon Entropy ($H$) / Gini | `{ent} bits` / `{gini}` | Sustained multi-month distribution |
| **Workweek Rhythm** | Weekday/Weekend Lift (MW-U) | `{wk_ratio:.2f}×` ($p={mw_p}$) | Developer work-hour cadence |
| **Forensic Integrity** | Benford $\\chi^2$ / MAD | `{b_chi2}` ($p={b_p}$) / `{b_mad}` | Natural organic conformity |
| **Channel Coupling** | Web ↔ Terminal Spearman | `$\\rho={sp_rho}$` ($p={sp_p}$) | CLI/npm headless consumption |
| **Milestone Oracle** | Block-Bootstrap P50 ETA | `{eta_10k}` | 1,000-path 7-day block bootstrap |
| **Temple Density** | Modules / GitHub Stars | `{vip_ratio:.1f}` temples/★ | Unprecedented over-engineering index |

---

## 1. Macro Telemetry & Forensic Integrity (宏观遥测与数据真实性审计)

Baseline traffic profiling, Bollinger anomaly bands, SciPy MAD peak detection, and Noisy-OR human-machine separation establish the empirical foundation prior to higher-order modeling.

![Main Dashboard](./plots/bunker_main_v7.png)
*Fig. 1. Macro 30-day terminal vs. web reconnaissance, cumulative growth, Noisy-OR Sigmoid purity audit, and log-scaled weekly deployment heatmap.*

![Intelligence Grid](./plots/bunker_intelligence_grid.png)
*Fig. 2. Six-panel strategic analytics: Symlog EWMA Bollinger +2σ envelope, web visitor floor, OLS regression, Gaussian KDE repeat intensity, 12-week throughput, and 7D moving averages.*

![Peak Recon](./plots/bunker_peak_recon.png)
*Fig. 3. SciPy signal peak detection calibrated against robust MAD 3σ thresholds, three-channel weekly comparison, and per-cloner repeat intensity ratios.*

![Intelligence Fusion](./plots/bunker_intelligence_fusion.png)
*Fig. 4. Noisy-OR Sigmoid operational composition, DBSCAN cluster hierarchy, and Sovereign Logistic Matrix in log-log cloner-volume space.*

![Singularity Oracle](./plots/bunker_singularity_oracle.png)
*Fig. 5. Benford's Law first-digit forensic audit, Poincaré 2σ chaos ellipse, 3-state GMM Markov transition matrix, and 1,000-path Block-Bootstrap milestone forecast.*

---

## 2. Circadian Chronobiology & Stochastic Econometrics (生物钟周期与计量金融建模)

Spectral decomposition, Modern Portfolio Theory, Bayesian conjugate inference, and state-space tracking quantify weekly developer rhythms and distributional laws.

![Chronos Quantum](./plots/bunker_chronos_quantum.png)
*Fig. 6. FFT periodogram workweek resonance, Monday–Sunday polar radar profile, Lorenz inequality curve, and DBSCAN + Isolation Forest dual-court consensus with Hurst exponent and Theil-Sen slope.*

![Imperial Pantheon](./plots/bunker_imperial_pantheon.png)
*Fig. 7. Markowitz 7-weekday efficient frontier, Archimedean 7D astrolabe, Welch cross-spectral coherence, SSA Hankel SVD w-correlation, weekly PCA biplot, and Gamma-Poisson Bayesian posteriors.*

![Astral Genesis](./plots/bunker_astral_genesis.png)
*Fig. 8. Apollo 2D Kalman innovation radar, RBF + 7d ExpSineSquared Gaussian Process forecast, Random Forest OOS permutation importance, Ward weekly phylogenetic dendrogram, DNA CGR, and AIC distribution contest.*

---

## 3. Nonlinear Physics, Wavelets & Algebraic Topology (非线性物理、小波与代数拓扑)

Time-frequency localization, stochastic potential wells, random matrix noise filtering, and persistent homology characterize regime shifts and extreme tails.

![Omega Physics](./plots/bunker_omega_physics.png)
*Fig. 9. Complex Morlet wavelet scalogram with Cone of Influence, Takens recurrence matrix (RQA), Shannon transfer entropy lag causality, and 0D algebraic topology persistence diagram ($H_0$).*

![Cosmic Frontier](./plots/bunker_cosmic_frontier.png)
*Fig. 10. Lacasa visibility graph network, Fokker-Planck Langevin potential well, Bandt-Pompe $D=4$ complexity-entropy plane, Kaplan-Meier survival + Hawkes aftershocks, GARCH(1,1) volatility, and Adams-MacKay BOCPD.*

![Quantum Metaphysics](./plots/bunker_quantum_metaphysics.png)
*Fig. 11. 1D Schrödinger eigenstates & WKB tunneling probability, Generalized Pareto flood return period, Marcenko-Pastur random matrix noise test, 3D Takens orbit, Matrix Profile motif twins/discord, and Sugihara CCM.*

---

## 4. Deep Visual Representations, Bio-Acoustics & Spectral Cuts (深度学习视觉场与谱图几何)

Time series are transformed into computer-vision tensors, optimal transport metrics, synthesized audio, and spectral graph partitions.

![Cosmic Apotheosis](./plots/bunker_apotheosis.png)
*Fig. 12. Hilbert-Huang EMD onion decomposition, monthly Wasserstein-1 Earth Mover's matrix, MFDFA multifractal spectrum, Fourier epicycles, synthesized 4.5s sonar audio spectrogram ([Download WAV](./plots/bunker_symphony.wav)), and 4-base DNA LZ76 complexity.*

![Deep Codex](./plots/bunker_deep_codex.png)
*Fig. 13. Gramian Angular Summation/Difference Fields (GASF/GADF), 8-quantile Markov Transition Field (MTF), normalized DTW monthly alignment, Fiedler Laplacian spectral cut, and empirical Copula tail dependence.*

---

## 5. Supplementary Material: Silicon Chronicle & Esoteric Benchmarks (附录：硅基晶圆、周易八卦与奇门塔罗)

<details>
<summary><b>Click to expand Supplementary Figures 14–16 (24 Solar Terms, Cyber I Ching, Qimen Dunjia & Tarot)</b></summary>

![Solar Silicon](./plots/bunker_solar_silicon.png)
*Fig. 14. 2026 24-Solar-Term ecliptic wheel, 16×16 Hilbert space-filling CPU wafer die, Six Sigma two-sided CUSUM Cpk control, Kuramoto EEG PLV rose, t-SNE Voronoi city-states, and ACF/PACF identification.*

![Cyber I Ching](./plots/bunker_cyber_iching.png)
*Fig. 15. Prior-Heaven Taiji Bagua compass, 6-line coin-free cyber hexagram divination, 64-hexagram traversal board, WuXing five-element ANOVA pentagon, 12 Earthly Branches zodiac pillars, and Bagua Markov transitions.*

![Mystic Arcana](./plots/bunker_mystic_arcana.png)
*Fig. 16. Qimen Dunjia Luoshu 9-palace tactical board, Western zodiac natal chart with aspect chords, Major Arcana 3-card tarot spread, and dynamic cyber almanac with mercury retrograde monitor.*

</details>

---

## 6. External Referral Telemetry (Table 2)

{ref_table}

---

## 7. Discussion & Threats to Validity (讨论与效度威胁)

1. **Observer Effect (观察者效应 / 测不准原理):** Rapid iterative pushes and workflow debugging in GitHub Actions trigger repeated `actions/checkout` runs across ephemeral Azure runner IPs, injecting self-observed spikes on intense engineering days (e.g., `2026-11-19` & `2026-11-20`).
2. **Channel Decoupling Bias (信道解耦):** As a terminal CLI (`npm` / `npx` / Git workflow), user consumption occurs predominantly without browser engagement, explaining low Star counts alongside steady weekly downloads and clones.
3. **Null Hypothesis on Esoteric Covariates:** Heavenly-stem Five-Element ANOVA ($p > 0.9$) confirms that metaphysical divination overlays remain purely satirical diagnostics rather than causal predictors.

---

## 8. Conclusion & Citation

Even under zero active promotion, `yorha2b-lab/autodev` exhibits a stationary, workweek-synchronized, Log-Normal organic usage baseline—proving that developer utility outlives marketing noise.

```bibtex
@article{{yorha2b2026bunker,
  title   = {{Stochastic Thermodynamics, Algebraic Topology, and Cyber Divination of a Zero-Marketing Frontend CLI Repository}},
  author  = {{Pod 042 and YoRHa Bunker Lab}},
  journal = {{Journal of Unnecessary Over-Engineering}},
  volume  = {{16}},
  year    = {{2026}},
  note    = {{Repository: https://github.com/yorha2b-lab/autodev}}
}}
📡 Physical Seal Timestamp: {cst_now} CST | Glory to Mankind.
'''

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(report)


def git_push():
    stats = load_json('bunker-stats.json', {'total_clones': 0})
    try:
        subprocess.run(['git', 'config', 'user.name',
                       'github-actions'], check=True)
        subprocess.run(['git', 'config', 'user.email',
                       'github-actions@github.com'], check=True)
        subprocess.run(['git', 'add', '-A'], check=True)
        subprocess.run(
            ['git', 'commit', '-m',
                f'chore: sovereign monograph update [total {stats["total_clones"]}]'],
            check=True
        )
        subprocess.run(
            ['git', 'push', 'origin', 'github-repo-stats', '--force'], check=True)
        print('✅ Data sealed and pushed to cloud.')
    except Exception as e:
        print(f'⚠️ Git push skipped: {e}')


if name == 'main':
    assemble_readme()
    git_push()
