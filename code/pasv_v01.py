"""
PASV v0.1 — Team-Aggregate Computation Script
==============================================

Computes the Possibility-Adjusted Shot Value (PASV) team-aggregate proxy
from publicly-available 2025 NBA regular-season team-aggregate statistics.

Per Section 5.1 of the SSAC27 paper:

    PASV_raw(team) = 0.30 × SDQ_z + 0.25 × OPC_team_z + 0.25 × FFS_z − 0.20 × TOV_penalty_z

where each component is z-scored across the 30 NBA teams, then rescaled to 0-10
via min-max normalization.

Component definitions (computed from publicly-available BBR data):
    SDQ           — Shot Diet Quality            = Team TS%
    OPC_team      — Team Option Preservation     = AST / FGM
    FFS           — Forcing Function Score       = FTA / FGA
    TOV_penalty   — Turnover Cost                = TOV / FGA

Author: Bobby Morong / DataDunkNBA — sole author
License: MIT
Version: v0.1 — 2026-05-26 (pre-registered)
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


# -----------------------------------------------------------------------------
# Framework constants (locked in pre-registration, NOT optimized against outcomes)
# -----------------------------------------------------------------------------
WEIGHTS = {
    "SDQ": 0.30,        # Shot Diet Quality
    "OPC_team": 0.25,   # Option Preservation (team-level)
    "FFS": 0.25,        # Forcing Function Score
    "TOV_penalty": -0.20,  # Turnover Penalty (sign-flipped: lower TOV is better)
}

OUTPUT_SCALE_MIN = 0.0
OUTPUT_SCALE_MAX = 10.0


# -----------------------------------------------------------------------------
# Core computation
# -----------------------------------------------------------------------------
def compute_components(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the four PASV v0.1 components from a per-team aggregate DataFrame.

    Expected input columns (BBR conventions):
        team, TS_pct, AST, FGM, FTA, FGA, TOV

    Returns a DataFrame with the four component columns added.
    """
    result = df.copy()
    result["SDQ"] = result["TS_pct"]
    result["OPC_team"] = result["AST"] / result["FGM"]
    result["FFS"] = result["FTA"] / result["FGA"]
    result["TOV_penalty"] = result["TOV"] / result["FGA"]
    return result


def z_score_components(df: pd.DataFrame) -> pd.DataFrame:
    """Z-score the four components across the 30-team population."""
    result = df.copy()
    for component in WEIGHTS:
        col = component
        z_col = f"{component}_z"
        mean = result[col].mean()
        std = result[col].std(ddof=0)  # population stddev — 30 teams is the population
        result[z_col] = (result[col] - mean) / std
    return result


def compute_pasv_raw(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the framework's weights to the z-scored components."""
    result = df.copy()
    result["PASV_raw"] = sum(
        WEIGHTS[component] * result[f"{component}_z"]
        for component in WEIGHTS
    )
    return result


def normalize_to_0_10(df: pd.DataFrame) -> pd.DataFrame:
    """Min-max normalize PASV_raw to the 0-10 scale across the 30 teams."""
    result = df.copy()
    raw_min = result["PASV_raw"].min()
    raw_max = result["PASV_raw"].max()
    result["PASV_v0_1"] = (
        OUTPUT_SCALE_MAX
        * (result["PASV_raw"] - raw_min)
        / (raw_max - raw_min)
    )
    return result


def compute_pasv_v01(input_df: pd.DataFrame) -> pd.DataFrame:
    """Run the full PASV v0.1 computation pipeline on a 30-team input DataFrame."""
    df = compute_components(input_df)
    df = z_score_components(df)
    df = compute_pasv_raw(df)
    df = normalize_to_0_10(df)
    df = df.sort_values("PASV_v0_1", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df


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
    """Write the ranked PASV v0.1 results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_cols = [
        "rank", "team",
        "TS_pct", "AST", "FGM", "FTA", "FGA", "TOV",
        "SDQ", "OPC_team", "FFS", "TOV_penalty",
        "SDQ_z", "OPC_team_z", "FFS_z", "TOV_penalty_z",
        "PASV_raw", "PASV_v0_1",
    ]
    df[output_cols].to_csv(output_path, index=False, float_format="%.4f")
    print(f"Wrote {len(df)} teams to {output_path}")


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Compute PASV v0.1 team-aggregate scores."
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
        default=Path("results/pasv_v01_2025.csv"),
        help="Output CSV path (default: results/pasv_v01_2025.csv)",
    )
    args = parser.parse_args()

    print(f"Computing PASV v0.1 for the {args.season} NBA regular season")
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")

    input_df = load_team_aggregates(args.input)
    result_df = compute_pasv_v01(input_df)

    print("\nTop 10 PASV v0.1, {} regular season:".format(args.season))
    print(result_df[["rank", "team", "PASV_v0_1"]].head(10).to_string(index=False))

    save_results(result_df, args.output)
    print("\nDone.")


if __name__ == "__main__":
    main()
