"""
PASV v0.2 — Weight Sensitivity Test
=====================================

Tests robustness of the PASV v0.2 → WEV v3 correlation under perturbations
of the pre-registered weight vector.

Per the pre-registered weights:
    SDQ            = +0.22
    OPC_team       = +0.20
    FFS            = +0.18
    TOV_penalty    = -0.15
    DTI_team       = +0.25

For each weight, we test perturbations of ±0.05 and ±0.10 holding the
other four weights fixed (asymmetric — does not re-normalize). The intent
is to demonstrate that the headline correlation result is not fragile
to small misspecifications of any single weight.

Author: Bobby Morong / DataDunkNBA — sole author
License: MIT
Version: v0.1 — 2026-06-16
"""

from pathlib import Path

import numpy as np
import pandas as pd

# Reuse the same component computation as pasv_v02.py
import sys
sys.path.insert(0, str(Path(__file__).parent))
from pasv_v02 import (
    WEIGHTS_V2,
    compute_components_v2,
    z_score_components_v2,
    LEAGUE_BASELINE_TS,
)


PERTURBATIONS = [-0.10, -0.05, 0.00, +0.05, +0.10]
INPUT_CSV = Path(__file__).parent.parent / "data" / "pasv_v01_2025_team_aggregate.csv"
OUTPUT_CSV = Path(__file__).parent.parent / "results" / "sensitivity_v02_2025.csv"


def compute_pasv_with_weights(df_zscored: pd.DataFrame, weights: dict) -> pd.Series:
    """Compute the raw v2 score under an arbitrary weight vector on a pre-z-scored DataFrame."""
    raw = sum(weights[c] * df_zscored[f"{c}_z"] for c in weights)
    return raw


def run_sensitivity():
    print("Loading 2025 team-aggregate CSV…")
    df = pd.read_csv(INPUT_CSV)
    df = compute_components_v2(df)
    df = z_score_components_v2(df)

    print(f"\nBaseline weights (pre-registered): {WEIGHTS_V2}\n")

    # Baseline
    baseline_raw = compute_pasv_with_weights(df, WEIGHTS_V2)
    baseline_pearson = baseline_raw.corr(df["WEV_v3"], method="pearson")
    baseline_spearman = baseline_raw.corr(df["WEV_v3"], method="spearman")
    print(f"BASELINE      Pearson r = {baseline_pearson:.4f}, Spearman ρ = {baseline_spearman:.4f}")

    results = []
    results.append({
        "perturbed_weight": "BASELINE",
        "perturbation": 0.0,
        "new_weight_value": None,
        "pearson_r": round(baseline_pearson, 4),
        "spearman_rho": round(baseline_spearman, 4),
        "delta_pearson": 0.0,
        "delta_spearman": 0.0,
    })

    # Perturb each weight separately
    for w_name, w_base in WEIGHTS_V2.items():
        for perturbation in PERTURBATIONS:
            if perturbation == 0.0:
                continue
            new_weights = dict(WEIGHTS_V2)
            new_weights[w_name] = w_base + perturbation

            perturbed_raw = compute_pasv_with_weights(df, new_weights)
            pearson = perturbed_raw.corr(df["WEV_v3"], method="pearson")
            spearman = perturbed_raw.corr(df["WEV_v3"], method="spearman")

            results.append({
                "perturbed_weight": w_name,
                "perturbation": perturbation,
                "new_weight_value": new_weights[w_name],
                "pearson_r": round(pearson, 4),
                "spearman_rho": round(spearman, 4),
                "delta_pearson": round(pearson - baseline_pearson, 4),
                "delta_spearman": round(spearman - baseline_spearman, 4),
            })

    results_df = pd.DataFrame(results)

    print("\nFull sensitivity results:")
    print(results_df.to_string(index=False))

    print("\nWorst-case perturbations (lowest Pearson):")
    print(results_df.nsmallest(5, "pearson_r").to_string(index=False))

    print("\nBest-case perturbations (highest Pearson):")
    print(results_df.nlargest(5, "pearson_r").to_string(index=False))

    # Robustness summary
    pearson_range = results_df["pearson_r"].max() - results_df["pearson_r"].min()
    spearman_range = results_df["spearman_rho"].max() - results_df["spearman_rho"].min()
    print(f"\nPearson r range across all perturbations:  {results_df['pearson_r'].min():.4f} → {results_df['pearson_r'].max():.4f}  (span: {pearson_range:.4f})")
    print(f"Spearman ρ range across all perturbations: {results_df['spearman_rho'].min():.4f} → {results_df['spearman_rho'].max():.4f}  (span: {spearman_range:.4f})")

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUTPUT_CSV, index=False, float_format="%.4f")
    print(f"\nSaved sensitivity results to: {OUTPUT_CSV}")


if __name__ == "__main__":
    run_sensitivity()
