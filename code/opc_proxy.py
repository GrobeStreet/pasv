"""
OPC AST% Proxy — Player-Level Computation
==========================================

Computes the AST% proxy for the Option Preservation Coefficient (OPC)
per Section 5.2 of the SSAC27 paper:

    OPC_proxy(player, season) ≡ AST%(player, season) / 100

The proxy is a conservative lower-bound estimator: it undercounts forcing
actions that do not terminate in assists. Per-possession forcing-action
tagging via tracking data (SportVU, Second Spectrum) would yield the full
OPC operationalization.

The Jokić 2022-23 ceiling (50.3% AST%) establishes the modern center-position
empirical upper bound on the construct.

Author: Bobby Morong / DataDunkNBA — sole author
License: MIT
"""

import argparse
from pathlib import Path

import pandas as pd


# -----------------------------------------------------------------------------
# Framework constants
# -----------------------------------------------------------------------------
JOKIC_2022_23_CEILING_AST_PCT = 50.3
POSITION_ORDER = ["PG", "SG", "SF", "PF", "C"]


# -----------------------------------------------------------------------------
# Core
# -----------------------------------------------------------------------------
def compute_opc_proxy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the OPC AST% proxy from a player-season DataFrame.

    Expected input columns:
        player, position, season, AST_pct, MP (minutes played for qualifying filter)
    """
    result = df.copy()
    result["OPC_proxy"] = result["AST_pct"] / 100.0
    result["pct_of_jokic_ceiling"] = result["AST_pct"] / JOKIC_2022_23_CEILING_AST_PCT
    return result


def position_distribution(df: pd.DataFrame, min_minutes: int = 500) -> pd.DataFrame:
    """
    Compute the position-stratified AST% distribution per Section 5.3.

    Returns a DataFrame with median, top-decile, and top single-season
    AST% per position.
    """
    qualifying = df[df["MP"] >= min_minutes].copy()
    rows = []
    for pos in POSITION_ORDER:
        pos_df = qualifying[qualifying["position"] == pos]
        if pos_df.empty:
            continue
        rows.append({
            "position": pos,
            "n_qualifying": len(pos_df),
            "median_AST_pct": pos_df["AST_pct"].median(),
            "top_decile_AST_pct": pos_df["AST_pct"].quantile(0.9),
            "top_single_season_AST_pct": pos_df["AST_pct"].max(),
            "top_single_season_player": pos_df.loc[
                pos_df["AST_pct"].idxmax(), "player"
            ],
        })
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Compute OPC AST% proxy and position distribution."
    )
    parser.add_argument(
        "--input", type=Path, required=True,
        help="Player-season CSV (cols: player, position, season, AST_pct, MP)",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/opc_proxy.csv"),
        help="Output CSV (default: results/opc_proxy.csv)",
    )
    parser.add_argument(
        "--min-minutes", type=int, default=500,
        help="Minimum minutes-played filter (default: 500)",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    print(f"Loaded {len(df)} player-seasons")

    result = compute_opc_proxy(df)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False, float_format="%.4f")
    print(f"Wrote OPC proxy results to {args.output}")

    print("\nPosition-stratified AST% distribution:")
    print(position_distribution(result, args.min_minutes).to_string(index=False))


if __name__ == "__main__":
    main()
