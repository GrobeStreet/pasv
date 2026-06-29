"""
Study 1 runner — per-shot PASV vs Skinner 2012, held-out OOS.

CALIBRATE: 2024-25 Regular Season (284,382 poss; 219,527 FG attempts)
TEST OOS : 2024-25 Playoffs (held out; never seen by xPTS / V* calibration)

Ground truth: each primary offensive player's realized on-ball points-per-FGA
in the held-out playoff sample. PASV and Skinner are each aggregated to the
same player level and regressed against the SAME ground truth.

Outputs:
  results/study1_player_scores.csv
  results/study1_summary.txt
"""
import os
import numpy as np
import pandas as pd

import pasv_per_shot as eng
from skinner_2012 import compute_cutoff_schedule

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DTI = os.path.join(ROOT, "dti_data")
RESULTS = os.path.join(HERE, "..", "results")
os.makedirs(RESULTS, exist_ok=True)


def r2(x, y):
    """Coefficient of determination of the OLS fit y ~ x (squared Pearson r)."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 3 or x.std() == 0:
        return np.nan, len(x)
    r = np.corrcoef(x, y)[0, 1]
    return r * r, len(x)


def main():
    train_path = os.path.join(DTI, "poss_v3_2024-25_Regular_Season.parquet")
    # held-out test uses the LINEUPS file so V* can read who else is on the floor.
    test_path = os.path.join(DTI, "poss_v3_LINEUPS_2024-25_Playoffs.parquet")

    train = eng.prepare(eng.load_poss(train_path))
    test = eng.prepare(eng.load_poss(test_path))
    print(f"train FG attempts: {len(train):,}  | test FG attempts: {len(test):,}")

    # --- calibrate on TRAIN only ---
    xpts_tab = eng.fit_xpts(train)
    # V* player-value map calibrated on RS (leakage-clean): player shooting
    # values come from the RS season; lineup COMPOSITION comes from each test
    # possession at scoring time. Build the player-value map from RS, then the
    # teammate-environment V* is computed per test shot from its off_lineup_ids.
    cont_tab = eng.fit_continuation_playervalue(train)
    cutoffs = compute_cutoff_schedule()
    fb_x = float(np.mean(list(xpts_tab.values())))
    fb_v = float(np.mean(list(cont_tab.values())))

    print("\nxPTS table (calibrated, 2024-25 RS):")
    for k, v in sorted(xpts_tab.items()):
        print(f"  {k:10s} {v:.3f}")
    pv = {k: v for k, v in cont_tab.items() if isinstance(k, int)}
    print(f"\nV* player-value map (calibrated, 2024-25 RS): {len(pv)} players, "
          f"league mean {cont_tab['_league_mean_']:.3f}, "
          f"range {min(pv.values()):.3f}-{max(pv.values()):.3f}")
    print("\nSkinner f*(tau) cutoffs:")
    for k in sorted(cutoffs):
        if k in (2, 5, 10, 14):
            print(f"  tau={k:2d}  {cutoffs[k]:.3f}")

    # --- score the held-out TEST sample ---
    scored = eng.compute_scores(test, xpts_tab, cont_tab, cutoffs, fb_x, fb_v)

    # --- aggregate to player level on the held-out sample ---
    g = scored.groupby("primary_offensive_player_id")
    player = pd.DataFrame({
        "fga": g.size(),
        "ppfga_truth": g["fg_pts"].mean(),     # ground truth: realized pts / FGA
        "PASV_mean": g["PASV"].mean(),
        "Skinner_mean": g["Skinner_gap"].mean(),
        "xPTS_mean": g["xPTS"].mean(),
    }).reset_index()

    # require a minimum playoff FGA sample for a stable player estimate
    MIN_FGA = 50
    pl = player[player["fga"] >= MIN_FGA].copy()
    print(f"\nplayers with >= {MIN_FGA} held-out playoff FGA: {len(pl)}")

    # --- the comparison: R^2 vs the SAME ground truth ---
    r2_pasv, n1 = r2(pl["PASV_mean"], pl["ppfga_truth"])
    r2_skin, n2 = r2(pl["Skinner_mean"], pl["ppfga_truth"])
    r2_xpts, _ = r2(pl["xPTS_mean"], pl["ppfga_truth"])
    delta = r2_pasv - r2_skin

    summary = []
    summary.append("PASV Study 1 — per-shot PASV vs Skinner 2012 (held-out OOS)")
    summary.append("=" * 64)
    summary.append(f"Calibration: 2024-25 Regular Season ({len(train):,} FG attempts)")
    summary.append(f"Held-out test: 2024-25 Playoffs ({len(test):,} FG attempts)")
    summary.append(f"Player aggregation, min {MIN_FGA} playoff FGA: n = {len(pl)} players")
    summary.append("")
    summary.append("Ground truth: player realized points-per-FGA in held-out playoffs")
    summary.append("-" * 64)
    summary.append(f"  R^2(Skinner gap,  truth) = {r2_skin:.4f}   [baseline]")
    summary.append(f"  R^2(PASV per-shot, truth) = {r2_pasv:.4f}   [contribution]")
    summary.append(f"  R^2(raw xPTS,      truth) = {r2_xpts:.4f}   [reference]")
    summary.append("-" * 64)
    summary.append(f"  Delta R^2 (PASV - Skinner) = {delta:+.4f}")
    summary.append(f"  Validation-plan target: Delta R^2 > 0.04 in PASV's favor")
    summary.append(f"  Target met: {'YES' if delta > 0.04 else 'NO'}")
    text = "\n".join(summary)
    print("\n" + text)

    pl.sort_values("PASV_mean", ascending=False).to_csv(
        os.path.join(RESULTS, "study1_player_scores.csv"), index=False)
    with open(os.path.join(RESULTS, "study1_summary.txt"), "w") as f:
        f.write(text + "\n")
    print(f"\nwrote results/study1_player_scores.csv and results/study1_summary.txt")


if __name__ == "__main__":
    main()
