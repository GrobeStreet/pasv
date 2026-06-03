"""
PASV v0.1 — Weight Sensitivity Analysis
========================================

Per Section 5.1.5 of the SSAC27 paper. Perturbs each component weight by
±0.05 and ±0.15, recomputes the cross-team correlation with the WEV v3
team composite, and reports the range of correlations observed across
perturbation configurations.

The qualitative claim — that PASV v0.1 correlates meaningfully with the
WEV v3 team composite — should be robust to perturbation within the
±0.05 range. The more aggressive ±0.15 range tests structural robustness.

Author: Bobby Morong / DataDunkNBA — sole author
License: MIT
"""

import argparse
import itertools
from pathlib import Path

import numpy as np
import pandas as pd

from pasv_v01 import (
    WEIGHTS,
    compute_components,
    z_score_components,
)


def perturb_and_correlate(
    df_input: pd.DataFrame,
    wev_v3: pd.Series,
    perturbation_range: float,
    perturbation_steps: int = 3,
) -> pd.DataFrame:
    """
    Run all combinations of weight perturbations in [-perturbation_range, +perturbation_range]
    and compute the correlation between perturbed PASV_raw and WEV v3.

    perturbation_steps = 3 means each weight tested at: -range, 0, +range.
    """
    df = compute_components(df_input)
    df = z_score_components(df)

    step_values = np.linspace(-perturbation_range, perturbation_range, perturbation_steps)

    results = []
    for s_sdq, s_opc, s_ffs, s_tov in itertools.product(
        step_values, step_values, step_values, step_values
    ):
        perturbed_weights = {
            "SDQ": WEIGHTS["SDQ"] + s_sdq,
            "OPC_team": WEIGHTS["OPC_team"] + s_opc,
            "FFS": WEIGHTS["FFS"] + s_ffs,
            "TOV_penalty": WEIGHTS["TOV_penalty"] + s_tov,
        }
        pasv_perturbed = sum(
            perturbed_weights[component] * df[f"{component}_z"]
            for component in perturbed_weights
        )
        correlation = np.corrcoef(pasv_perturbed, wev_v3)[0, 1]
        results.append({
            "delta_SDQ": s_sdq,
            "delta_OPC_team": s_opc,
            "delta_FFS": s_ffs,
            "delta_TOV_penalty": s_tov,
            "weight_SDQ": perturbed_weights["SDQ"],
            "weight_OPC_team": perturbed_weights["OPC_team"],
            "weight_FFS": perturbed_weights["FFS"],
            "weight_TOV_penalty": perturbed_weights["TOV_penalty"],
            "correlation_with_WEVv3": correlation,
        })
    return pd.DataFrame(results)


def summarize_sensitivity(df: pd.DataFrame, label: str) -> None:
    correlations = df["correlation_with_WEVv3"]
    print(f"\n--- {label} ---")
    print(f"  Configurations tested: {len(df)}")
    print(f"  Correlation min:       {correlations.min():.4f}")
    print(f"  Correlation max:       {correlations.max():.4f}")
    print(f"  Correlation mean:      {correlations.mean():.4f}")
    print(f"  Correlation median:    {correlations.median():.4f}")


def main():
    parser = argparse.ArgumentParser(
        description="PASV v0.1 weight sensitivity analysis."
    )
    parser.add_argument(
        "--input", type=Path,
        default=Path("data/pasv_v01_2025_team_aggregate.csv"),
        help="Team aggregate input CSV (default: data/pasv_v01_2025_team_aggregate.csv)",
    )
    parser.add_argument(
        "--wev-column", type=str, default="WEV_v3",
        help="Name of the WEV v3 column in the input CSV (default: WEV_v3)",
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("results/sensitivity_2025.csv"),
        help="Output CSV (default: results/sensitivity_2025.csv)",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    if args.wev_column not in df.columns:
        raise ValueError(
            f"Input CSV missing WEV v3 column '{args.wev_column}'. "
            f"Sensitivity analysis requires a benchmark composite column."
        )
    wev_v3 = df[args.wev_column].values

    print(f"Loaded {len(df)} teams; running sensitivity analysis.")

    moderate = perturb_and_correlate(df, wev_v3, perturbation_range=0.05)
    aggressive = perturb_and_correlate(df, wev_v3, perturbation_range=0.15)

    summarize_sensitivity(moderate, "Moderate perturbation (±0.05 per weight)")
    summarize_sensitivity(aggressive, "Aggressive perturbation (±0.15 per weight)")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    moderate.to_csv(args.output, index=False, float_format="%.4f")
    aggressive_path = args.output.with_name(args.output.stem + "_aggressive.csv")
    aggressive.to_csv(aggressive_path, index=False, float_format="%.4f")
    print(f"\nWrote moderate sensitivity to {args.output}")
    print(f"Wrote aggressive sensitivity to {aggressive_path}")


if __name__ == "__main__":
    main()
