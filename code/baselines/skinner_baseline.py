"""
Skinner 2012 — Optimal Shot Selection Cutoff
============================================

Reimplements the closed-form solution from:
    Brian Skinner (2012). "The Problem of Shot Selection in Basketball."
    PLOS ONE 7(1): e30776.
    https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0030776

The Setup
---------
A basketball possession is modeled as a Markov Decision Process. At each
tick of the shot clock t in {1, 2, ..., 24}, the offense observes a
randomly drawn shot quality `f` and chooses to either:

    1. SHOOT — collect immediate reward f
    2. HOLD  — pay a one-tick delay cost and draw a new shot quality
               at t-1 (or turn the ball over if the clock expires)

Skinner derives the optimal value function V(t) — the expected points
the offense earns starting with t ticks remaining under the optimal
policy — as a recursion:

    V(t) = E[ max(f, V(t-1)) ]
    V(0) = 0  (shot-clock turnover, no points)

If the shot-quality distribution F(f) has known density g(f), the
expectation has a closed form. Skinner notes that under any reasonable
single-team shot-quality distribution the optimal CUTOFF — the minimum
shot quality the offense should accept at time t — is simply V(t-1).

That is:

    Cutoff(t) = V(t-1)

Which says: "accept this shot only if its quality is at least as good
as the expected value of continuing the possession one more tick."

This module implements the cutoff under two distributional assumptions:

    (a) Uniform shot quality f ~ Uniform[0, f_max]
        — the closed-form case Skinner uses for pedagogical clarity.

    (b) Empirical shot quality drawn from a user-supplied CDF
        — the case PASV's empirical comparison study (Study 1 in
          PASV_Empirical_Validation_Plan_2026-06-05.md) requires.

Usage
-----
    # Closed-form uniform case (Skinner's Figure 1)
    from skinner_baseline import cutoff_uniform
    cutoffs = cutoff_uniform(f_max=3.0, clock=24)

    # Empirical case (calibrated on real NBA data)
    from skinner_baseline import cutoff_from_samples
    cutoffs = cutoff_from_samples(shot_quality_samples)

    # Grade a single shot against the Skinner threshold
    from skinner_baseline import grade_shot
    is_above_cutoff = grade_shot(xpts=1.10, t=14, cutoffs=cutoffs)

CLI:
    python skinner_baseline.py --f_max 2.5 --clock 24 --plot

Author: Bobby Morong / DataDunkNBA / 2026-06-05
License: MIT (see repository LICENSE)
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


# ---------------------------------------------------------------------------
# 1. Closed-form uniform-distribution case (Skinner's pedagogical example)
# ---------------------------------------------------------------------------

def cutoff_uniform(f_max: float = 3.0, clock: int = 24) -> np.ndarray:
    """
    Compute the optimal shot-quality cutoff at each shot-clock tick t,
    assuming shot quality is drawn from Uniform[0, f_max] independently
    at each tick.

    Recursion (Skinner 2012, derivation around Eq. 3):

        V(t) = E[ max(f, V(t-1)) ]
             = integral over [V(t-1), f_max] of f * (1/f_max) df
               + V(t-1) * P(f < V(t-1))
             = (f_max^2 - V(t-1)^2) / (2 * f_max)
               + V(t-1) * (V(t-1) / f_max)
             = (f_max^2 + V(t-1)^2) / (2 * f_max)

        V(0) = 0
        Cutoff(t) = V(t-1)

    Args:
        f_max: maximum possible shot quality (xPTS). Skinner uses 3.0 as
               the natural three-pointer ceiling.
        clock: number of shot-clock ticks (NBA = 24).

    Returns:
        cutoffs: numpy array of length `clock` where cutoffs[t-1] is the
                 optimal shoot-or-hold threshold at clock instant t.
                 Note the indexing: index 0 corresponds to t=1 (one tick
                 remaining), index 23 corresponds to t=24 (fresh possession).
    """
    if f_max <= 0:
        raise ValueError(f"f_max must be positive (got {f_max})")
    if clock < 1:
        raise ValueError(f"clock must be at least 1 (got {clock})")

    V = np.zeros(clock + 1, dtype=float)   # V[0] = 0 (shot-clock violation)
    for t in range(1, clock + 1):
        V[t] = (f_max ** 2 + V[t - 1] ** 2) / (2.0 * f_max)

    # cutoff(t) = V(t-1)
    cutoffs = V[:clock].copy()
    return cutoffs


# ---------------------------------------------------------------------------
# 2. Empirical case (calibrated on actual NBA shot quality distribution)
# ---------------------------------------------------------------------------

def cutoff_from_samples(
    samples: Sequence[float],
    clock: int = 24,
    rng_seed: int = 42,
) -> np.ndarray:
    """
    Compute the optimal shot-quality cutoff using an empirical shot-quality
    distribution drawn from a real NBA dataset.

    Recursion (same as uniform case but with empirical expectation):

        V(t) = E_emp[ max(f, V(t-1)) ]
             = (1/N) * sum_i max(f_i, V(t-1))
        V(0) = 0
        Cutoff(t) = V(t-1)

    This is the version PASV's empirical comparison study uses. Pass in
    the held-out 2024-25 xPTS distribution and you get the data-grounded
    cutoff schedule.

    Args:
        samples: 1-D iterable of empirical shot-quality xPTS values.
                 Must be non-empty.
        clock: number of shot-clock ticks (NBA = 24).
        rng_seed: unused for the deterministic empirical case; reserved
                  for future Monte-Carlo variants.

    Returns:
        cutoffs: numpy array of length `clock`, same indexing as
                 `cutoff_uniform`.
    """
    samples = np.asarray(list(samples), dtype=float)
    if samples.size == 0:
        raise ValueError("samples must be non-empty")
    if clock < 1:
        raise ValueError(f"clock must be at least 1 (got {clock})")

    V = np.zeros(clock + 1, dtype=float)
    for t in range(1, clock + 1):
        V[t] = float(np.mean(np.maximum(samples, V[t - 1])))

    cutoffs = V[:clock].copy()
    return cutoffs


# ---------------------------------------------------------------------------
# 3. Per-shot grading API
# ---------------------------------------------------------------------------

@dataclass
class ShotGrade:
    """Skinner-style grade of a single shot decision."""
    xpts: float            # the realized shot's expected points
    t: int                 # shot-clock instant (1 = one tick left, 24 = fresh)
    cutoff: float          # the Skinner threshold at instant t
    above_cutoff: bool     # was the shot above threshold (= take the shot)?
    margin: float          # signed margin xpts - cutoff


def grade_shot(xpts: float, t: int, cutoffs: np.ndarray) -> ShotGrade:
    """
    Grade a single shot against the Skinner cutoff schedule.

    Args:
        xpts: expected points of the realized shot (from any xPTS model).
        t: shot-clock instant at which the shot was taken (1..24).
        cutoffs: cutoff array from `cutoff_uniform` or `cutoff_from_samples`.

    Returns:
        ShotGrade dataclass with the cutoff, the binary verdict, and the
        signed margin. The signed margin is what PASV will compare its
        own per-shot signed scalar against.
    """
    if t < 1 or t > len(cutoffs):
        raise ValueError(f"t={t} outside cutoff range [1, {len(cutoffs)}]")
    cutoff = float(cutoffs[t - 1])
    margin = float(xpts) - cutoff
    return ShotGrade(
        xpts=float(xpts),
        t=int(t),
        cutoff=cutoff,
        above_cutoff=margin >= 0.0,
        margin=margin,
    )


def grade_shots(
    xpts: Iterable[float],
    times: Iterable[int],
    cutoffs: np.ndarray,
) -> np.ndarray:
    """
    Vectorized grader. Returns the signed margin (xpts - cutoff) for each
    shot. Use the sign of the margin for the binary "should have shot"
    verdict; use the magnitude for the head-to-head comparison with PASV
    in Study 1 of the validation plan.
    """
    xpts = np.asarray(list(xpts), dtype=float)
    times = np.asarray(list(times), dtype=int)
    if xpts.shape != times.shape:
        raise ValueError("xpts and times must be the same length")
    if np.any((times < 1) | (times > len(cutoffs))):
        raise ValueError(
            f"all times must be in [1, {len(cutoffs)}]; "
            f"got min={times.min()} max={times.max()}"
        )
    # Vectorized lookup
    cutoff_vec = cutoffs[times - 1]
    return xpts - cutoff_vec


# ---------------------------------------------------------------------------
# 4. CLI for sanity check + plot
# ---------------------------------------------------------------------------

def _cli() -> None:
    p = argparse.ArgumentParser(
        description="Skinner 2012 optimal shot cutoff baseline."
    )
    p.add_argument(
        "--f_max", type=float, default=3.0,
        help="Maximum shot quality under the uniform case. Default 3.0 "
             "(three-pointer ceiling).",
    )
    p.add_argument(
        "--clock", type=int, default=24,
        help="Number of shot-clock ticks. NBA = 24.",
    )
    p.add_argument(
        "--plot", action="store_true",
        help="Save a PNG of the cutoff schedule to "
             "results/skinner_cutoff.png. Requires matplotlib.",
    )
    args = p.parse_args()

    cutoffs = cutoff_uniform(f_max=args.f_max, clock=args.clock)

    print("Skinner 2012 — Optimal Shot Cutoff Schedule")
    print(f"  Shot-quality distribution: Uniform[0, {args.f_max}]")
    print(f"  Shot clock: {args.clock} ticks")
    print()
    print(f"  {'t':>4}  {'Cutoff(t)':>12}")
    for t in range(1, args.clock + 1):
        print(f"  {t:>4d}  {cutoffs[t-1]:>12.4f}")

    # Sanity check the asymptote (Skinner's Eq. 4):
    # As t -> infinity the cutoff approaches f_max.
    print()
    print(f"  Asymptote (Skinner Eq. 4): cutoff(infty) -> f_max = {args.f_max}")
    print(f"  Empirical cutoff at t={args.clock}: {cutoffs[args.clock-1]:.4f}")

    if args.plot:
        try:
            import os
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            print("\nmatplotlib not installed — skipping plot.")
            return
        os.makedirs("results", exist_ok=True)
        fig, ax = plt.subplots(figsize=(8, 5))
        ts = np.arange(1, args.clock + 1)
        ax.plot(ts, cutoffs, marker="o", linewidth=2)
        ax.axhline(args.f_max, linestyle="--", linewidth=1, alpha=0.5,
                   label=f"f_max = {args.f_max}")
        ax.set_xlabel("Shot-clock instant t (ticks remaining)")
        ax.set_ylabel("Optimal cutoff (xPTS)")
        ax.set_title(
            "Skinner 2012 — Optimal Shot-Quality Cutoff Schedule\n"
            f"Uniform[0, {args.f_max}] shot-quality distribution"
        )
        ax.grid(True, alpha=0.3)
        ax.legend()
        plt.tight_layout()
        out_path = "results/skinner_cutoff.png"
        plt.savefig(out_path, dpi=150)
        print(f"\nPlot saved: {out_path}")


if __name__ == "__main__":
    _cli()
