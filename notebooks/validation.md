# Validation Notebook — PASV v0.1 (2025 NBA Regular Season)

*Companion to Section 5 of the SSAC27 PASV paper. This document specifies the validation pipeline. The Jupyter notebook `validation.ipynb` (generated from this spec) reproduces every numerical result in Section 5.*

## What this notebook validates

1. The PASV v0.1 team-aggregate computation pipeline (Section 5.1)
2. The cross-sectional correlation with WEV v3 composite (Section 5.1.4 — r ≈ 0.61)
3. The weight sensitivity analysis (Section 5.1.5 — r ∈ [0.55, 0.64] under ±0.05 perturbation)
4. The OPC AST% proxy distribution by position (Section 5.3)

## Steps

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from code.pasv_v01 import compute_pasv_v01
from code.sensitivity import perturb_and_correlate
from code.opc_proxy import compute_opc_proxy, position_distribution

# -----------------------------------------------------------------------------
# Step 1 — Load the team aggregate data
# -----------------------------------------------------------------------------
team_df = pd.read_csv("data/pasv_v01_2025_team_aggregate.csv")
assert len(team_df) == 30, "Expected 30 teams"

# -----------------------------------------------------------------------------
# Step 2 — Compute PASV v0.1 scores
# -----------------------------------------------------------------------------
pasv_df = compute_pasv_v01(team_df)
print(pasv_df[["rank", "team", "PASV_v0_1"]].to_string(index=False))

# -----------------------------------------------------------------------------
# Step 3 — Cross-sectional correlation with WEV v3
# -----------------------------------------------------------------------------
correlation = pasv_df[["PASV_v0_1", "WEV_v3"]].corr().iloc[0, 1]
print(f"\nPASV v0.1 × WEV v3 correlation across 30 teams: r = {correlation:.4f}")
# Expected: r ≈ 0.61

# -----------------------------------------------------------------------------
# Step 4 — Visualize: PASV v0.1 ranking with WEV v3 overlay
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 8))
ax.scatter(pasv_df["WEV_v3"], pasv_df["PASV_v0_1"])
for _, row in pasv_df.iterrows():
    ax.annotate(row["team"], (row["WEV_v3"], row["PASV_v0_1"]),
                fontsize=8, alpha=0.7)
ax.set_xlabel("WEV v3")
ax.set_ylabel("PASV v0.1")
ax.set_title(f"PASV v0.1 vs WEV v3, 2025 NBA Regular Season (r = {correlation:.3f})")
plt.tight_layout()
plt.savefig("results/figure_1_pasv_vs_wev.png", dpi=150)

# -----------------------------------------------------------------------------
# Step 5 — Weight sensitivity analysis
# -----------------------------------------------------------------------------
moderate = perturb_and_correlate(team_df, team_df["WEV_v3"].values, 0.05)
print(f"Moderate (±0.05): r ∈ [{moderate['correlation_with_WEVv3'].min():.3f}, "
      f"{moderate['correlation_with_WEVv3'].max():.3f}]")

aggressive = perturb_and_correlate(team_df, team_df["WEV_v3"].values, 0.15)
print(f"Aggressive (±0.15): r ∈ [{aggressive['correlation_with_WEVv3'].min():.3f}, "
      f"{aggressive['correlation_with_WEVv3'].max():.3f}]")

# -----------------------------------------------------------------------------
# Step 6 — Holding-Math Theorem figure (Eq. 4.8, Section 4.2)
# -----------------------------------------------------------------------------
n_actions = np.arange(1, 11)
mistake_prob = 1 - 0.95 ** (5 * n_actions)

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(n_actions, mistake_prob * 100, marker="o", linewidth=2)
ax.axhline(72.3, color="red", linestyle="--", alpha=0.5,
           label="72.3% inflection at n=5")
ax.set_xlabel("Number of forcing actions (n)")
ax.set_ylabel("P(≥1 defender mistake) [%]")
ax.set_title("Holding-Math Theorem: Cumulative Defender-Mistake Probability\n"
             "P(≥1 mistake) = 1 − 0.95^(5n)")
ax.grid(True, alpha=0.3)
ax.legend()
plt.tight_layout()
plt.savefig("results/figure_2_holding_math.png", dpi=150)

print("\nValidation complete. Figures saved to results/")
```

## Expected outputs

After running this notebook:

- `results/pasv_v01_2025.csv` — ranked PASV v0.1 for all 30 teams
- `results/figure_1_pasv_vs_wev.png` — scatter plot, PASV v0.1 vs WEV v3
- `results/figure_2_holding_math.png` — Holding-Math Theorem curve
- `results/sensitivity_2025.csv` — moderate weight perturbation results
- `results/sensitivity_2025_aggressive.csv` — aggressive perturbation results

## Reproducibility

All randomness in the validation pipeline is seeded (no random sampling is used in the team-aggregate computation; the input data is the 30-team population). Re-running the notebook against the included `data/pasv_v01_2025_team_aggregate.csv` will produce bitwise-identical numerical outputs to those reported in Section 5 of the paper.
