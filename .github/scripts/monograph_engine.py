import os
import sys
import json
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
from scipy.stats import chisquare, mannwhitneyu, spearmanr


SCRIPTS_ROOT = os.path.dirname(os.path.abspath(__file__))

TASKS = [
    'render/dashboard.py',
    'analyze/deep_intelligence.py',
    'analyze/chronos_quantum.py',
    'analyze/singularity_oracle.py',
    'analyze/omega_physics.py',
    'analyze/cosmic_frontier.py',
    'analyze/quantum_metaphysics.py',
    'analyze/bunker_apotheosis.py',
    'analyze/ml_genesis.py',
    'analyze/living_orbit_gif.py',
    'analyze/imperial_pantheon.py',
    'analyze/cyber_iching.py',
    'analyze/solar_silicon_chronicle.py',
    'analyze/deep_codex.py',
    'analyze/mystic_arcana.py',
    'render/hud_banner.py',
]


def run_one(rel_path):
    full_path = os.path.join(SCRIPTS_ROOT, rel_path)
    if not os.path.exists(full_path):
        return rel_path, False, 0.0, 'File not found'
    t0 = time.time()
    proc = subprocess.run([sys.executable, full_path],
                          capture_output=True, text=True)
    dt = time.time() - t0
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or '').strip().splitlines()[-3:]
        return rel_path, False, dt, ' | '.join(err)
    return rel_path, True, dt, 'OK'


def compute_paper_metrics():
    metrics = {
        'n_days': 0, 'start_date': 'N/A', 'end_date': 'N/A',
        'mean_clones': 0.0, 'median_clones': 0.0, 'peak_val': 0, 'peak_date': 'N/A',
        'entropy_bits': 0.0, 'gini': 0.0, 'wk_ratio': 1.0, 'mw_p': 1.0,
        'benford_chi2': 0.0, 'benford_p': 1.0, 'benford_mad': 0.0,
        'spearman_rho': 0.0, 'spearman_p': 1.0, 'eta_10k': 'TBD',
        'temples_count': len(TASKS),
    }
    c_path = 'ghrs-data/clones_ledger.csv'
    if not os.path.exists(c_path):
        return metrics

    df = pd.read_csv(c_path)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df['clones'] = pd.to_numeric(df['clones'], errors='coerce').fillna(0.0)
    df = df.groupby('date', as_index=False)['clones'].sum()
    if df.empty:
        return metrics

    full_idx = pd.date_range(df['date'].min(), df['date'].max(), freq='D')
    df = df.set_index('date').reindex(full_idx, fill_value=0.0)
    df = df.rename_axis('date').reset_index()

    y = df['clones'].to_numpy(dtype=float)
    n = len(y)
    pk_i = int(np.argmax(y))
    metrics['n_days'] = n
    metrics['start_date'] = df['date'].iloc[0].strftime('%Y-%m-%d')
    metrics['end_date'] = df['date'].iloc[-1].strftime('%Y-%m-%d')
    metrics['mean_clones'] = round(float(np.mean(y)), 1)
    metrics['median_clones'] = round(float(np.median(y)), 1)
    metrics['peak_val'] = int(y[pk_i])
    metrics['peak_date'] = df['date'].iloc[pk_i].strftime('%Y-%m-%d')

    s_pos = y[y > 0]
    if len(s_pos) > 0:
        p = s_pos / s_pos.sum()
        metrics['entropy_bits'] = round(float(-np.sum(p * np.log2(p))), 2)

    s_ord = np.sort(y)
    if np.sum(s_ord) > 0:
        idx = np.arange(1, n + 1)
        gini = np.sum((2 * idx - n - 1) * s_ord) / (n * np.sum(s_ord))
        metrics['gini'] = round(float(gini), 3)

    is_wknd = df['date'].dt.dayofweek >= 5
    if np.any(~is_wknd) and np.any(is_wknd):
        wk_d, wk_e = y[~is_wknd], y[is_wknd]
        _, mw_p = mannwhitneyu(wk_d, wk_e, alternative='two-sided')
        metrics['wk_ratio'] = round(
            float(wk_d.mean() / max(wk_e.mean(), 1e-6)), 2)
        metrics['mw_p'] = round(float(mw_p), 4)

    pos_int = y[y >= 1].astype(int)
    if len(pos_int) >= 10:
        digs = np.arange(1, 10)
        ben_p = np.log10(1.0 + 1.0 / digs)
        fd = pd.Series([int(str(v)[0]) for v in pos_int]).value_counts()
        obs = fd.reindex(digs, fill_value=0).to_numpy(dtype=float)
        f_exp = ben_p * obs.sum()
        f_exp *= obs.sum() / f_exp.sum()
        chi2, chi_p = chisquare(obs, f_exp=f_exp)
        mad = np.mean(np.abs(obs / obs.sum() - ben_p))
        metrics['benford_chi2'] = round(float(chi2), 2)
        metrics['benford_p'] = round(float(chi_p), 3)
        metrics['benford_mad'] = round(float(mad), 4)

    v_path = 'ghrs-data/views_ledger.csv'
    if os.path.exists(v_path):
        df_v = pd.read_csv(v_path)
        df_v['date'] = pd.to_datetime(df_v['date'], errors='coerce')
        df_v = df_v.dropna(subset=['date'])
        df_v['uv'] = pd.to_numeric(
            df_v['uniques'], errors='coerce').fillna(0.0)
        df_v = df_v.groupby('date', as_index=False)['uv'].sum()
        if not df_v.empty:
            m_df = pd.merge(df, df_v[df_v['date'] >= df_v['date'].min()],
                            on='date', how='inner')
            if m_df['uv'].nunique() >= 2 and m_df['clones'].nunique() >= 2:
                rho, pval = spearmanr(m_df['uv'], m_df['clones'])
                metrics['spearman_rho'] = round(float(rho), 2)
                metrics['spearman_p'] = round(float(pval), 3)

    cur_tot = float(np.sum(y))
    target = float(((int(cur_tot) // 5000) + 1) * 5000)
    if target - cur_tot < 300:
        target += 5000
    pool = y[-min(120, n):]
    rng = np.random.default_rng(42)
    horizon, n_sims, blk = 150, 1000, 7
    max_st = max(1, len(pool) - blk + 1)
    n_blk = int(np.ceil(horizon / blk))
    paths = np.zeros((n_sims, horizon))
    for i in range(n_sims):
        st = rng.integers(0, max_st, size=n_blk)
        samp = np.concatenate([pool[s:s + blk] for s in st])[:horizon]
        paths[i] = cur_tot + np.cumsum(samp)
    p50 = np.percentile(paths, 50, axis=0)
    hit = np.where(p50 >= target)[0]
    if len(hit) > 0:
        eta_d = df['date'].iloc[-1] + pd.Timedelta(days=int(hit[0]) + 1)
        metrics['eta_10k'] = f"{eta_d.strftime('%Y-%m-%d')} (+{int(hit[0]) + 1}d to {int(target):,})"
    else:
        metrics['eta_10k'] = f">{horizon}d"

    return metrics


def main():
    print(
        f"🛰️ Pod 042 Monograph Engine: Launching {len(TASKS)} temples (4 workers)...")
    t_all = time.time()
    ok_cnt = 0

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(run_one, t): t for t in TASKS}
        for fut in as_completed(futures):
            rel, ok, dt, msg = fut.result()
            if ok:
                ok_cnt += 1
                print(f"  ✅ {rel:<38} ({dt:.2f}s)")
            else:
                print(f"  ⚠️ {rel:<38} FAILED ({dt:.2f}s): {msg}")

    metrics = compute_paper_metrics()
    with open('paper_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print(
        f"📜 Engine finished: {ok_cnt}/{len(TASKS)} succeeded in {time.time() - t_all:.2f}s.")


if __name__ == '__main__':
    main()
