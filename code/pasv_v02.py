"""
PASV v0.2 — DTI-Incorporated Team-Aggregate Computation Script
================================================================

Computes the Possibility-Adjusted Shot Value (PASV) team-aggregate score
using the v0.2 formulation, which augments the four v0.1 components with
a fifth component derived from the Defender Targeting Index (DTI v0.2)
substrate.

Per the Math Appendix v2 (Section 4.4.5) of the SSAC27 paper:

    PASV_raw_v2(team) = 0.22 × SDQ_z
                     + 0.20 × OPC_team_z
                     + 0.18 × FFS_z
                     − 0.15 × TOV_penalty_z
                     + 0.25 × DTI_team_z

where DTI_team is the team-aggregate Defender Targeting Index — the per-
possession lift the team's offense generates against league-baseline
defender execution, normalized across the 30-team population.

v0.1 vs v0.2:
  - v0.1: 4 components, weights (0.30, 0.25, 0.25, -0.20) on (SDQ, OPC_team, FFS, TOV_penalty)
  - v0.2: 5 components, weights re-balanced; DTI_team becomes the dominant weight

Pre-registration: the v0.2 weights are LOCKED at the values above prior to
running the backtest, consistent with the canon-discipline requirement of
publishing falsifiable predictions before observing the result.

Component definitions:
    SDQ           — Shot Diet Quality            = Team TS%
    OPC_team      — Team Option Preservation     = AST / FGM
    FFS           — Forcing Function Score       = FTA / FGA
    TOV_penalty   — Turnover Cost                = TOV / FGA
    DTI_team      — Defender Targeting Index     = Team_ORtg − Opp_DRtg_allowed
                                                   (when not provided, fallback uses
                                                   TS% deviation from league mean × 100)

Author: Bobby Morong / DataDunkNBA — sole author
License: MIT
Version: v0.2 — 2026-06-16 (pre-registered; DTI-incorporated)
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


# -----------------------------------------------------------------------------
# Framework constants — LOCKED in v0.2 pre-registration, NOT optimized to outcome
# -----------------------------------------------------------------------------
WEIGHTS_V2 = {
    "SDQ": 0.22,
    "OPC_team": 0.20,
    "FFS": 0.18,
    "TOV_penalty": -0.15,
    "DTI_team": 0.25,
}

OUTPUT_SCALE_MIN = 0.0
OUTPUT_SCALE_MAX = 10.0

LEAGUE_BASELINE_TS = 0.557  # 2024-25 league-average TS% (basketball-reference)


# -----------------------------------------------------------------------------
# Core computation
# -----------------------------------------------------------------------------
def compute_components_v2(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the five PASV v0.2 components from a per-team aggregate DataFrame.

    Expected input columns (BBR conventions):
        team, TS_pct, AST, FGM, FTA, FGA, TOV
    Optional columns:
        DTI_team     — pre-computed team-aggregate DTI from DTI v0.2 leaderboard
                       (if absent, derived from TS% deviation × 100 as a defensible
                       proxy consistent with DTI's definition as defender-targeting lift)

    Returns a DataFrame with the five component columns added.
    """
    result = df.copy()
    result["SDQ"] = result["TS_pct"]
    result["OPC_team"] = result["AST"] / result["FGM"]
    result["FFS"] = result["FTA"] / result["FGA"]
    result["TOV_penalty"] = result["TOV"] / result["FGA"]

    if "DTI_team" not in result.columns:
        # Fallback: TS% deviation from league baseline × 100 = the team's
        # observed scoring exploitation above the league-defender baseline.
        # This is the publicly-reproducible substitute when the DTI v0.2 leaderboard
        # has not yet been wired into the team-aggregate CSV.
        result["DTI_team"] = (result["TS_pct"] - LEAGUE_BASELINE_TS) * 100.0
        result["DTI_source"] = "fallback_TS_dev"
    else:
        result["DTI_source"] = "DTI_v02_leaderboard"

    return result


def z_score_components_v2(df: pd.DataFrame) -> pd.DataFrame:
    """Z-score the five components across the 30-team population."""
    result = df.copy()
    for component in WEIGHTS_V2:
        col = component
        z_col = f"{component}_z"
        mean = result[col].mean()
        std = result[col].std(ddof=0)  # population stddev — 30 teams is the population
        result[z_col] = (result[col] - mean) / std
    return result


def compute_pasv_raw_v2(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the v0.2 weights to the z-scored components."""
    result = df.copy()
    result["PASV_raw_v2"] = sum(
        WEIGHTS_V2[component] * result[f"{component}_z"]
        for component in WEIGHTS_V2
    )
    return result


def normalize_to_0_10_v2(df: pd.DataFrame) -> pd.DataFrame:
    """Min-max normalize PASV_raw_v2 to the 0-10 scale across the 30 teams."""
    result = df.copy()
    raw_min = result["PASV_raw_v2"].min()
    raw_max = result["PASV_raw_v2"].max()
    result["PASV_v0_2"] = (
        OUTPUT_SCALE_MAX
        * (result["PASV_raw_v2"] - raw_min)
        / (raw_max - raw_min)
    )
    return result


def compute_pasv_v02(input_df: pd.DataFrame) -> pd.DataFrame:
    """Run the full PASV v0.2 computation pipeline on a 30-team input DataFrame."""
    df = compute_components_v2(input_df)
    df = z_score_components_v2(df)
    df = compute_pasv_raw_v2(df)
    df = normalize_to_0_10_v2(df)
    df = df.sort_values("PASV_v0_2", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df


# -----------------------------------------------------------------------------
# Correlation with WEV v3
# -----------------------------------------------------------------------------
def report_wev_correlation(df: pd.DataFrame) -> dict:
    """
    Compute Pearson and Spearman correlation between PASV_v0_2 and WEV_v3.
    Returns a dict suitable for printing or logging.
    """
    if "WEV_v3" not in df.columns:
        return {"status": "WEV_v3 column not present; skipping correlation"}

    pearson = df["PASV_v0_2"].corr(df["WEV_v3"], method="pearson")
    spearman = df["PASV_v0_2"].corr(df["WEV_v3"], method="spearman")

    return {
        "status": "ok",
        "pearson_r": round(pearson, 4),
        "spearman_rho": round(spearman, 4),
        "n_teams": len(df),
    }


# -----------------------------------------------------------------------------
# I/O
# -----------------------------------------------------------------------------
def load_team_aggregates(csv_path: Path) -> pd.DataFrame:
    """Load the 30-team aggregate CSV. Validates expected columns."""
    df = pd.read_csv(csv_path)
    required = {"team", "TS_pct", "AST", "FGM", "FTA", "FGA", "TOV"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input CSV missing required columns: {missing}")
    if len(df) != 30:
        raise ValueError(f"Expected 30 teams, got {len(df)}.")
    return df


def save_results(df: pd.DataFrame, output_path: Path) -> None:
    """Write the ranked PASV v0.2 results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_cols = [
        "rank", "team",
        "TS_pct", "AST", "FGM", "FTA", "FGA", "TOV",
        "SDQ", "OPC_team", "FFS", "TOV_penalty", "DTI_team", "DTI_source",
        "SDQ_z", "OPC_team_z", "FFS_z", "TOV_penalty_z", "DTI_team_z",
        "PASV_raw_v2", "PASV_v0_2",
    ]
    if "WEV_v3" in df.columns:
        output_cols.append("WEV_v3")
    df[output_cols].to_csv(output_path, index=False, float_format="%.4f")
    print(f"Wrote {len(df)} teams to {output_path}")


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Compute PASV v0.2 team-aggregate scores (DTI-incorporated)."
    )
    parser.add_argument(
        "--season", type=int, default=2025,
        help="NBA season to compute (default: 2025)",
    )
    parser.add_argument(
        "--input", type=Path,
        default=Path("data/pasv_v01_2025_team_aggregate.csv"),
        help="Input CSV path (default: data/pasv_v01_2025_team_aggregate.csv)",
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("results/pasv_v02_2025.csv"),
        help="Output CSV path (default: results/pasv_v02_2025.csv)",
    )
    args = parser.parse_args()

    print(f"Computing PASV v0.2 (DTI-incorporated) for the {args.season} NBA regular season")
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print(f"Pre-registered weights: {WEIGHTS_V2}")

    input_df = load_team_aggregates(args.input)
    result_df = compute_pasv_v02(input_df)

    print("\nTop 10 PASV v0.2, {} regular season:".format(args.season))
    print(
        result_df[["rank", "team", "PASV_v0_2", "WEV_v3"]].head(10).to_string(index=False)
        if "WEV_v3" in result_df.columns
        else result_df[["rank", "team", "PASV_v0_2"]].head(10).to_string(index=False)
    )

    print("\nBottom 5 PASV v0.2, {} regular season:".format(args.season))
    print(
        result_df[["rank", "team", "PASV_v0_2", "WEV_v3"]].tail(5).to_string(index=False)
        if "WEV_v3" in result_df.columns
        else result_df[["rank", "team", "PASV_v0_2"]].tail(5).to_string(index=False)
    )

    corr = report_wev_correlation(result_df)
    print(f"\nCorrelation with WEV v3:")
    for k, v in corr.items():
        print(f"  {k}: {v}")

    save_results(result_df, args.output)
    print("\nDone.")


if __name__ == "__main__":
    main()
