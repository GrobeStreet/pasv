"""
Study 1 — WITHIN-PLAYER decision test (the decisive computation).

Question: for the SAME player, do higher-PASV shots produce more realized
points than lower-PASV shots? This isolates decision quality from "who can
score" using player fixed effects (within-player demeaning). A per-shot
decision metric must win HERE to claim it improves on shot quality.

We compare three predictors on identical within-player footing:
    PASV        = xPTS - V*(teammate continuation)
    Skinner_gap = xPTS - f*(tau)
    raw xPTS    = the shot-quality baseline PASV is built from

Method:
  1. Calibrate xPTS + player-value map on 2024-25 RS (leakage-clean).
  2. Score held-out 2024-25 playoff FG attempts.
  3. Within each player, demean predictor and outcome (subtract that player's
     own mean) -> the FE-residual. Pool residuals across players.
  4. Within-player Pearson r and R^2 of each predictor-residual vs the
     points-residual. Also a pooled OLS with player fixed effects.
  5. Within-player decile lift: for each player split their shots at their own
     PASV median; does the above-median half score more? Average the gap.

Calibrate RS / test playoffs; player values out-of-sample.

Author: Bobby Morong / DataDunkNBA — 2026-06-25
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


def within_player_demean(df, col, by):
    return df[col] - df.groupby(by)[col].transform("mean")


def r2_pearson(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 5 or x.std() == 0 or y.std() == 0:
        return np.nan, np.nan, len(x)
    r = np.corrcoef(x, y)[0, 1]
    return r, r * r, len(x)


def median_split_lift(df, score_col, pts_col, by, min_shots=30):
    """For each player with >=min_shots, split at own median of score_col;
    return mean(above-median PPP - below-median PPP) across players, and the
    share of players where above>below."""
    gaps = []
    wins = 0
    n = 0
    for pid, g in df.groupby(by):
        if len(g) < min_shots:
            continue
        med = g[score_col].median()
        hi = g[g[score_col] > med][pts_col]
        lo = g[g[score_col] <= med][pts_col]
        if len(hi) < 5 or len(lo) < 5:
            continue
        gap = hi.mean() - lo.mean()
        gaps.append(gap)
        wins += int(gap > 0)
        n += 1
    return (np.mean(gaps) if gaps else np.nan,
            (wins / n) if n else np.nan, n)


def main():
    train = eng.prepare(eng.load_poss(os.path.join(
        DTI, "poss_v3_2024-25_Regular_Season.parquet")))
    test = eng.prepare(eng.load_poss(os.path.join(
        DTI, "poss_v3_LINEUPS_2024-25_Playoffs.parquet")))

    xpts_tab = eng.fit_xpts(train)
    cont_tab = eng.fit_continuation_playervalue(train)
    cutoffs = compute_cutoff_schedule()
    fb_x = float(np.mean(list(xpts_tab.values())))
    fb_v = cont_tab["_league_mean_"]

    s = eng.compute_scores(test, xpts_tab, cont_tab, cutoffs, fb_x, fb_v)
    by = "primary_offensive_player_id"

    # keep players with enough playoff shots for a within estimate
    counts = s.groupby(by).size()
    keep = counts[counts >= 30].index
    s = s[s[by].isin(keep)].copy()
    n_players = s[by].nunique()

    # within-player demeaned residuals
    s["pts_w"] = within_player_demean(s, "fg_pts", by)
    s["PASV_w"] = within_player_demean(s, "PASV", by)
    s["Skin_w"] = within_player_demean(s, "Skinner_gap", by)
    s["xPTS_w"] = within_player_demean(s, "xPTS", by)

    rows = []
    for name, col in [("PASV", "PASV_w"), ("Skinner_gap", "Skin_w"),
                      ("raw xPTS", "xPTS_w")]:
        r, r2, n = r2_pearson(s[col], s["pts_w"])
        lift, winshare, npl = median_split_lift(
            s, {"PASV": "PASV", "Skinner_gap": "Skinner_gap",
                "raw xPTS": "xPTS"}[name], "fg_pts", by)
        rows.append((name, r, r2, n, lift, winshare, npl))

    out = []
    out.append("PASV Study 1 — WITHIN-PLAYER decision test (held-out OOS)")
    out.append("=" * 64)
    out.append(f"Calibrate: 2024-25 RS  |  Test: 2024-25 Playoffs (held out)")
    out.append(f"Players with >=30 playoff FG attempts: {n_players}")
    out.append(f"Within-player shots pooled: {len(s):,}")
    out.append("")
    out.append("Player fixed effects: predictor & outcome demeaned per player.")
    out.append("Tests whether a player's OWN higher-scored shots score more.")
    out.append("-" * 64)
    out.append(f"{'Predictor':<14}{'within-r':>10}{'within-R2':>11}"
               f"{'medsplit lift':>15}{'%players up':>13}")
    for name, r, r2, n, lift, ws, npl in rows:
        out.append(f"{name:<14}{r:>10.4f}{r2:>11.4f}"
                   f"{lift:>+15.4f}{ws*100:>12.1f}%")
    out.append("-" * 64)

    pasv = rows[0]; skin = rows[1]; xpts = rows[2]
    d_skin = pasv[2] - skin[2]
    d_xpts = pasv[2] - xpts[2]
    out.append(f"  within-R2  PASV - Skinner = {d_skin:+.4f}")
    out.append(f"  within-R2  PASV - rawxPTS = {d_xpts:+.4f}")
    out.append("")
    out.append("VERDICT:")
    if d_xpts > 0.005:
        out.append("  PASV ADDS decision signal beyond shot quality (within player).")
        out.append("  -> This is the paper's headline. PASV beats xPTS where it counts.")
    elif d_xpts > -0.005:
        out.append("  PASV is within-player EQUIVALENT to raw xPTS (no add, no loss).")
        out.append("  -> Reframe: PASV is a decision-diagnosis lens, not a predictive")
        out.append("     improvement over shot quality. Honest, novel, less marketable.")
    else:
        out.append("  PASV UNDERPERFORMS raw xPTS within player.")
        out.append("  -> The V* subtraction removes signal. Reframe required.")

    text = "\n".join(out)
    print(text)
    with open(os.path.join(RESULTS, "study1_within_player.txt"), "w") as f:
        f.write(text + "\n")
    print(f"\nwrote results/study1_within_player.txt")


if __name__ == "__main__":
    main()
