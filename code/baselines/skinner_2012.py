"""
Skinner 2012 — Closed-form MDP Cutoff Implementation
======================================================

Implementation of the optimal shot-selection cutoff f*(τ) from:

    Skinner, B. (2012). The Problem of Shot Selection in Basketball.
    PLOS ONE 7(1): e30776.

The cutoff is derived from the Bellman recursion under the assumption
of independent shot opportunities drawn from a Normal shot-quality
distribution at a fixed per-second opportunity rate.

Calibration parameters (Skinner 2012, Section 3):
  F_AVG        = 1.00   — mean shot quality (points per possession, normalized)
  SIGMA_F      = 0.20   — std dev of shot quality distribution
  P_OPPT_PER_SEC = 0.10 — probability of a shot opportunity per second

Result: cutoff schedule f*(τ) for τ ∈ {1, ..., 24} that is monotonically
increasing in τ (longer clock = higher threshold = pickier offense).

Usage:
    from baselines.skinner_2012 import compute_cutoff_schedule, skinner_decision
    cutoffs = compute_cutoff_schedule()
    # cutoffs[20] = f*(20) — the threshold at 20 seconds remaining
    take_shot = skinner_decision(xpts=1.30, tau=20, cutoffs=cutoffs)

Author: Bobby Morong / DataDunkNBA — sole author
License: MIT
Version: v0.1 — 2026-06-16
"""

from scipy.stats import norm


F_AVG = 1.00
SIGMA_F = 0.20
SHOT_CLOCK_MAX = 24
P_OPPT_PER_SEC = 0.10


def expected_max_normal(threshold: float, mean: float, std: float) -> float:
    """
    Compute E[max(X, threshold)] where X ~ Normal(mean, std^2).

    Closed-form: threshold * P(X <= threshold) + E[X * 1{X > threshold}]
                = threshold * Φ(z) + mean * (1 - Φ(z)) + std * φ(z)
    where z = (threshold - mean) / std, Φ is the CDF, φ is the PDF.
    """
    z = (threshold - mean) / std
    return threshold * norm.cdf(z) + mean * norm.sf(z) + std * norm.pdf(z)


def compute_cutoff_schedule(
    f_avg: float = F_AVG,
    sigma_f: float = SIGMA_F,
    shot_clock_max: int = SHOT_CLOCK_MAX,
    p_oppt_per_sec: float = P_OPPT_PER_SEC,
) -> dict:
    """
    Compute the Skinner f*(τ) cutoff schedule via Bellman recursion.

    Returns a dict {τ: f*(τ)} for τ ∈ {1, ..., shot_clock_max}.

    Recursion (per second of shot-clock):
      V[t] = (1 - p_oppt) * V[t-1]                 # no opportunity this tick
           + p_oppt * E[max(f, V[t-1])]            # opportunity → optimal choice

    Cutoff at τ ticks remaining: f*(τ) = V[τ-1]
    (you shoot iff the realized f >= V[τ-1], i.e., iff the realized shot beats
    the value of waiting one more second under the optimal continuation)
    """
    V = [0.0] * (shot_clock_max + 1)
    for t in range(1, shot_clock_max + 1):
        V[t] = (
            (1 - p_oppt_per_sec) * V[t-1]
            + p_oppt_per_sec * expected_max_normal(V[t-1], f_avg, sigma_f)
        )
    return {t: V[t-1] for t in range(1, shot_clock_max + 1)}


def skinner_decision(xpts: float, tau: int, cutoffs: dict = None) -> bool:
    """
    Returns True (SHOOT) if the realized shot's xPTS exceeds the Skinner
    threshold at τ seconds remaining. Returns False (HOLD) otherwise.
    """
    if cutoffs is None:
        cutoffs = compute_cutoff_schedule()
    tau_clamped = max(1, min(tau, max(cutoffs.keys())))
    return xpts >= cutoffs[tau_clamped]


def skinner_score(xpts: float, tau: int, cutoffs: dict = None) -> float:
    """
    Returns the signed gap xpts - f*(τ). Note: Skinner's framework formally
    produces only the binary SHOOT/HOLD decision; this function exposes the
    signed gap for comparison with PASV (which is precisely this signed gap
    using the optimal continuation value V*(s*) in place of f*(τ)).
    """
    if cutoffs is None:
        cutoffs = compute_cutoff_schedule()
    tau_clamped = max(1, min(tau, max(cutoffs.keys())))
    return xpts - cutoffs[tau_clamped]


if __name__ == "__main__":
    print("Skinner 2012 cutoff schedule (default calibration):")
    print(f"  F_AVG = {F_AVG}, SIGMA_F = {SIGMA_F}, P_OPPT_PER_SEC = {P_OPPT_PER_SEC}\n")

    cutoffs = compute_cutoff_schedule()
    for tau in [1, 3, 5, 10, 15, 20, 24]:
        print(f"  τ = {tau:2d}  →  f*(τ) = {cutoffs[tau]:.3f}")

    mono = all(cutoffs[t] <= cutoffs[t+1] for t in range(1, len(cutoffs)))
    print(f"\nMonotonic increasing (longer clock = higher threshold): {mono}")

    print("\nWorked examples (PASV is xPTS - f*(τ); Skinner is binary):")
    print(f"{'Shot':<32} {'xPTS':>6} {'f*(τ)':>7} {'PASV':>7} {'Skinner':>8}")
    examples = [
        ("Rim layup, τ=20 sec",    1.30, 20),
        ("Open 3, τ=15 sec",       1.18, 15),
        ("Contested mid, τ=10 sec", 0.88, 10),
        ("Decent 3, τ=4 sec",      1.05, 4),
        ("Heave, τ=2 sec",         0.25, 2),
    ]
    for name, xpts, tau in examples:
        decision = "SHOOT" if skinner_decision(xpts, tau, cutoffs) else "HOLD"
        score = skinner_score(xpts, tau, cutoffs)
        print(f"{name:<32} {xpts:>6.2f} {cutoffs[tau]:>7.3f} {score:>+7.3f} {decision:>8}")
