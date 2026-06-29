import os, sys
import numpy as np
import pandas as pd

HERE = "/sessions/vibrant-confident-faraday/mnt/Basketball Stats Book/pasv-sloan-repo"
CODE = os.path.join(HERE, "code")
DTI = "/sessions/vibrant-confident-faraday/mnt/Basketball Stats Book/dti_data"
RESULTS = os.path.join(HERE, "results")
sys.path.insert(0, CODE); sys.path.insert(0, os.path.join(CODE, "baselines"))
import pasv_per_shot as eng
from skinner_2012 import compute_cutoff_schedule

csv = pd.read_csv(os.path.join(RESULTS, "study1_player_scores.csv"))
r_player = np.corrcoef(csv["PASV_mean"], csv["Skinner_mean"])[0,1]
print("=== 1. PLAYER-LEVEL CORRELATION ===")
print(f"  n players = {len(csv)}")
print(f"  corr(PASV_mean, Skinner_mean) = {r_player:.6f}   r^2 = {r_player**2:.6f}")
b,a = np.polyfit(csv["Skinner_mean"], csv["PASV_mean"], 1)
print(f"  PASV_mean = {b:.4f} * Skinner_mean + ({a:.4f})")
print()

test = eng.prepare(eng.load_poss(os.path.join(DTI, "poss_v3_2024-25_Playoffs.parquet")))
print("=== 2. TAU DISTRIBUTION (held-out 2024-25 Playoffs) ===")
print(f"  total FG attempts = {len(test):,}")
vc = test["tau"].value_counts().sort_index()
for tau,n in vc.items():
    print(f"  tau={tau:2d}  shots={n:7,}  share={n/len(test)*100:5.1f}%")
print(f"  distinct tau = {test['tau'].nunique()} -> {sorted(test['tau'].unique())}")
print()

train = eng.prepare(eng.load_poss(os.path.join(DTI, "poss_v3_2024-25_Regular_Season.parquet")))
xpts_tab = eng.fit_xpts(train); cont_tab = eng.fit_continuation(train)
cutoffs = compute_cutoff_schedule()
fb_x = float(np.mean(list(xpts_tab.values()))); fb_v = float(np.mean(list(cont_tab.values())))
scored = eng.compute_scores(test, xpts_tab, cont_tab, cutoffs, fb_x, fb_v)
scored["diff"] = scored["PASV"] - scored["Skinner_gap"]

print("=== 3. COLLINEARITY HYPOTHESIS ===")
for tau in sorted(test['tau'].unique()):
    sub = scored[scored["tau"]==tau]
    print(f"  tau={tau:2d}  V*={cont_tab[tau]:.4f}  f*={cutoffs[tau]:.4f}  "
          f"diff_mean={sub['diff'].mean():.6f}  diff_std={sub['diff'].std():.2e}  f*-V*={cutoffs[tau]-cont_tab[tau]:.6f}")
print(f"  distinct values of (PASV-Skinner) = {scored['diff'].round(8).nunique()}")
print(f"  per-shot corr(PASV, Skinner_gap) = {np.corrcoef(scored['PASV'], scored['Skinner_gap'])[0,1]:.6f}")
print(f"  per-shot corr(PASV, xPTS)        = {np.corrcoef(scored['PASV'], scored['xPTS'])[0,1]:.6f}")
print(f"  per-shot corr(Skinner, xPTS)     = {np.corrcoef(scored['Skinner_gap'], scored['xPTS'])[0,1]:.6f}")
print(f"  std: xPTS={scored['xPTS'].std():.4f}  Vstar_offset={scored['Vstar'].std():.5f}  fstar_offset={scored['tau'].map(cutoffs).std():.5f}")

g = scored.groupby("primary_offensive_player_id")
pl = pd.DataFrame({"fga":g.size(),"PASV":g["PASV"].mean(),"Skin":g["Skinner_gap"].mean(),
                   "xPTS":g["xPTS"].mean(),"truth":g["fg_pts"].mean()})
pl = pl[pl["fga"]>=50]
print()
print("=== 4. PLAYER-LEVEL OFFSET SPREAD ===")
print(f"  std(PASV_mean - xPTS_mean) = {(pl['PASV']-pl['xPTS']).std():.5f}")
print(f"  std(Skin_mean - xPTS_mean) = {(pl['Skin']-pl['xPTS']).std():.5f}")
print(f"  std(xPTS_mean)             = {pl['xPTS'].std():.5f}")
print(f"  corr(PASV_mean, xPTS_mean) = {np.corrcoef(pl['PASV'],pl['xPTS'])[0,1]:.5f}")
