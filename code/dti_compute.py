"""
DTI — Defender Targeting Index (v0.1 Computation Engine)
========================================================

Implements the three-layer Defender Targeting Index for the DataDunkNBA
framework. DTI fills the "Open Lane 1" identified in the Optimization Gap
master dossier (`OptGap_MASTER_Dossier_2026-06-13.md`):

    "Nobody has published a player-grain Defender Targeting Index (DTI)
     that scores every NBA possession by which defender ended up guarding
     the primary action, the PPP of that possession vs. the league
     baseline PPP for that defender on that action type, and a summary
     stat: 'this defender is hunted X possessions/game and surrenders Y
     PPP above his baseline.'"

This is the computational engine. The math spec is the authoritative
algebra (see `DTI_v0.1_Math_Spec_2026-06-13.md`); this module is the
operational pandas/parquet implementation that consumes the possession-
level data ingested by the parallel ingest pipeline and emits three
layers of output:

    Layer 1 — DTI_poss  : per-possession lift over the league baseline
                          PPP for the action type the defender was
                          attacked on (signed scalar).
    Layer 2 — DTI_def   : per-defender aggregate. Positive = defender
                          surrenders points when hunted; negative =
                          defender suppresses targeting. The "hunted
                          target" leaderboard.
    Layer 3 — DTI_hunt  : per-offensive-player aggregate. Positive =
                          this offensive player generates above-expected
                          PPP when the action is routed at the weakest
                          defender. The "hunter skill" leaderboard.

Expected upstream schema
------------------------
The parallel ingest pipeline emits `poss_level_<season>.parquet` with the
following per-possession (one row per ball-handler-defender-matchup-event)
columns. The exact schema is owned by the ingest module; this engine is
tolerant to extra columns and only requires the ones listed here.

    Required columns
    ----------------
    poss_id              str    : unique possession identifier
    game_id              str    : NBA game id
    season               str    : e.g. "2025-26"
    season_type          str    : "Regular Season" or "Playoffs"
    period               int    : quarter (1..4) or OT (5+)
    seconds_remaining    float  : seconds left in the period
    offense_team_id      int    : team id of the team with the ball
    defense_team_id      int    : team id of the defending team
    hunter_id            int    : the offensive player who initiated the
                                  action (the "hunter")
    hunter_name          str
    defender_id          int    : the primary defender of the action
                                  (the "target")
    defender_name        str
    action_type          str    : one of {"PnR_BH", "PnR_Roll", "Iso",
                                  "Post", "Off_screen", "Spot_up",
                                  "Handoff", "Cut", "Transition",
                                  "Other"}
    points_scored        float  : points scored on the possession
                                  (0/1/2/3, includes free throws)
    is_targeted          bool   : did the offense intentionally route at
                                  this defender (switch-hunt, drag, ISO
                                  call, post-up against a smaller man)?
                                  This flag drives the Layer 3 "hunter"
                                  numerator.

    Optional columns
    ----------------
    possessions_used     float  : usage weight (1.0 for full possession)
    garbage_time_flag    bool   : true if score margin > 20 in 4th
                                  (v0.2 will filter on this)

The baseline file `baseline_<season>.parquet` carries the league-wide
expected PPP per action type:

    action_type          str
    league_PPP           float : expected PPP across all possessions of
                                 this action type, league-wide
    n_possessions        int

Author : Bobby Morong / DataDunkNBA (sole author)
License: MIT (see repository LICENSE)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Framework constants
# ---------------------------------------------------------------------------

# Action type vocabulary. Any action_type not in this set is bucketed as
# "Other" and inherits the "Other" baseline.
ACTION_TYPES: Tuple[str, ...] = (
    "PnR_BH",
    "PnR_Roll",
    "Iso",
    "Post",
    "Off_screen",
    "Spot_up",
    "Handoff",
    "Cut",
    "Transition",
    "Other",
)

# Per-100-possession scaler — DTI_def_per100 and DTI_hunt_per100 are the
# headline numbers that surface on the leaderboards.
PER_100_SCALE: float = 100.0

# 2026 playoff hunt-targets named in the OptGap master dossier (Pattern 6,
# Slice 1, Slice 5). Used by validate_against_known_targets().
KNOWN_TARGETS_2026: Dict[str, Dict[str, str]] = {
    "Devin Booker": {
        "team": "PHX",
        "context": "Knicks hunted Booker on switches (Slice 1).",
    },
    "Donovan Mitchell": {
        "team": "CLE",
        "context": "Frequently switched-hunted in modern playoffs.",
    },
    "Nikola Jokic": {
        "team": "DEN",
        "context": "Hunted as defender despite offensive dominance.",
    },
    "Karl-Anthony Towns": {
        "team": "NYK",
        "context": "Knicks target — hunted on every switch (Slice 1).",
    },
    "Mike Conley": {
        "team": "MIN",
        "context": "Mavs historically targeted Conley (dossier).",
    },
    "Aaron Nesmith": {
        "team": "IND",
        "context": "Celtics 2024 ECF hunted Nesmith (26-for-48, dossier).",
    },
}


# ---------------------------------------------------------------------------
# Layer 1 — DTI_poss (per-possession lift)
# ---------------------------------------------------------------------------

def _normalize_action_type(series: pd.Series) -> pd.Series:
    """Coerce action_type to the closed vocabulary, bucket unknowns as 'Other'."""
    allowed = set(ACTION_TYPES)
    cleaned = series.fillna("Other").astype(str)
    return cleaned.where(cleaned.isin(allowed), "Other")


def compute_dti_poss(
    poss_df: pd.DataFrame,
    baseline_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute Layer 1 DTI_poss — per-possession signed lift over baseline.

    For each possession i with action type a_i, observed points y_i, and a
    usage weight w_i (default 1.0):

        DTI_poss_i = (y_i - league_PPP[a_i]) * w_i

    DTI_poss is positive when the offense outscored the league baseline
    for that action type on that possession (the hunter exploited the
    target). It is negative when the defender held the possession below
    baseline.

    Args:
        poss_df: possession-level DataFrame from the ingest. Must contain
            the required schema (see module docstring).
        baseline_df: action-type baseline DataFrame with columns
            'action_type' and 'league_PPP'.

    Returns:
        A copy of `poss_df` with two added columns:
            - 'baseline_PPP'  : league baseline PPP for the action type
            - 'DTI_poss'      : per-possession signed lift

    Raises:
        KeyError: if the required columns are missing from `poss_df`.
        ValueError: if the baseline does not cover every action type
                    present in the data.
    """
    required = {
        "poss_id", "action_type", "points_scored",
        "hunter_id", "defender_id",
    }
    missing = required - set(poss_df.columns)
    if missing:
        raise KeyError(
            f"poss_df missing required columns: {sorted(missing)}"
        )

    if not {"action_type", "league_PPP"}.issubset(baseline_df.columns):
        raise KeyError(
            "baseline_df must have columns ['action_type', 'league_PPP']"
        )

    out = poss_df.copy()
    out["action_type"] = _normalize_action_type(out["action_type"])

    # Build the baseline lookup. Any action type missing from the
    # baseline file falls back to the "Other" bucket if present, else 1.0
    # PPP (a no-op signal).
    bl = baseline_df.copy()
    bl["action_type"] = _normalize_action_type(bl["action_type"])
    bl_map: Dict[str, float] = dict(
        zip(bl["action_type"], bl["league_PPP"].astype(float))
    )
    other_fallback = bl_map.get("Other")
    if other_fallback is None:
        other_fallback = float(np.nan)

    unmatched = set(out["action_type"].unique()) - set(bl_map.keys())
    if unmatched and np.isnan(other_fallback):
        raise ValueError(
            f"Baseline does not cover action types {sorted(unmatched)} "
            "and no 'Other' fallback baseline is present."
        )

    out["baseline_PPP"] = out["action_type"].map(bl_map).fillna(other_fallback)

    if "possessions_used" in out.columns:
        weights = out["possessions_used"].astype(float).fillna(1.0)
    else:
        weights = 1.0

    out["DTI_poss"] = (
        out["points_scored"].astype(float) - out["baseline_PPP"].astype(float)
    ) * weights

    return out


# ---------------------------------------------------------------------------
# Layer 2 — DTI_def (per-defender, the "hunted target" leaderboard)
# ---------------------------------------------------------------------------

def compute_dti_def(
    poss_df_with_dti: pd.DataFrame,
    min_targeted_possessions: int = 200,
) -> pd.DataFrame:
    """
    Aggregate Layer 1 to per-defender — the "hunted target" leaderboard.

    For each defender d:

        n_d                  = number of possessions defender d was the
                               primary defender
        raw_PPP_against_d    = sum(points_scored_i) / n_d   over i where
                               defender_id_i = d
        expected_PPP_against_d
                             = sum(baseline_PPP_i) / n_d  over the same i
        DTI_def_d            = raw_PPP_against_d - expected_PPP_against_d
        DTI_def_per100_d     = DTI_def_d * 100  (points per 100 targeted
                               possessions, the headline number)

    Interpretation:
        DTI_def > 0  -> defender SURRENDERS points when targeted; he
                        is a hunt-magnet (Booker, KAT, Mitchell).
        DTI_def < 0  -> defender SUPPRESSES targeting; offenses get
                        less than expected when they attack him
                        (Wemby, Mitchell Robinson).

    Args:
        poss_df_with_dti: output of compute_dti_poss().
        min_targeted_possessions: minimum sample size to qualify for the
            leaderboard. Default 200 — roughly one full month of
            high-usage defender possessions; calibrated to keep noise
            from small-sample defenders (rookie minutes, garbage-time
            specialists) off the headline board.

    Returns:
        DataFrame sorted by DTI_def_per100 descending (most-hunted first)
        with columns:
            defender_id, defender_name, defense_team_id,
            possessions_targeted, raw_PPP_against, expected_PPP_against,
            DTI_def, DTI_def_per100, rank
    """
    required = {
        "defender_id", "defender_name", "points_scored",
        "baseline_PPP", "DTI_poss",
    }
    missing = required - set(poss_df_with_dti.columns)
    if missing:
        raise KeyError(
            f"poss_df_with_dti missing required columns: {sorted(missing)}"
        )

    weights = (
        poss_df_with_dti["possessions_used"].astype(float).fillna(1.0)
        if "possessions_used" in poss_df_with_dti.columns
        else pd.Series(1.0, index=poss_df_with_dti.index)
    )

    df = poss_df_with_dti.copy()
    df["_w"] = weights

    # team_id column — prefer defense_team_id, else fall back to a
    # 'team_id' column if the ingest uses that name.
    team_col = (
        "defense_team_id" if "defense_team_id" in df.columns
        else "team_id" if "team_id" in df.columns
        else None
    )

    name_col = "defender_name"

    group_cols: List[str] = ["defender_id", name_col]
    if team_col is not None:
        group_cols.append(team_col)

    grouped = df.groupby(group_cols, dropna=False, observed=True)
    agg = grouped.agg(
        possessions_targeted=("_w", "sum"),
        points_against=("points_scored", lambda s: float(np.sum(
            s.astype(float).to_numpy() * df.loc[s.index, "_w"].to_numpy()
        ))),
        expected_points_against=("baseline_PPP", lambda s: float(np.sum(
            s.astype(float).to_numpy() * df.loc[s.index, "_w"].to_numpy()
        ))),
    ).reset_index()

    # Guard against zero-possession rows (shouldn't happen post-groupby,
    # but pandas can land odd edge cases on empty groups).
    agg = agg[agg["possessions_targeted"] > 0].copy()

    agg["raw_PPP_against"] = (
        agg["points_against"] / agg["possessions_targeted"]
    )
    agg["expected_PPP_against"] = (
        agg["expected_points_against"] / agg["possessions_targeted"]
    )
    agg["DTI_def"] = agg["raw_PPP_against"] - agg["expected_PPP_against"]
    agg["DTI_def_per100"] = agg["DTI_def"] * PER_100_SCALE

    qualifying = agg[
        agg["possessions_targeted"] >= float(min_targeted_possessions)
    ].copy()
    qualifying.sort_values("DTI_def_per100", ascending=False, inplace=True)
    qualifying.reset_index(drop=True, inplace=True)
    qualifying["rank"] = np.arange(1, len(qualifying) + 1)

    # Rename team column to a stable output name.
    if team_col is not None and team_col != "team_id":
        qualifying.rename(columns={team_col: "team_id"}, inplace=True)
    elif team_col is None:
        qualifying["team_id"] = np.nan

    # Stable output column order — matches the docstring contract.
    cols = [
        "rank", "defender_id", "defender_name", "team_id",
        "possessions_targeted",
        "raw_PPP_against", "expected_PPP_against",
        "DTI_def", "DTI_def_per100",
    ]
    return qualifying[cols]


# ---------------------------------------------------------------------------
# Layer 3 — DTI_hunt (per-offensive-player, the "hunter skill" leaderboard)
# ---------------------------------------------------------------------------

def compute_dti_hunt(
    poss_df_with_dti: pd.DataFrame,
    min_hunting_possessions: int = 150,
    is_targeted_col: str = "is_targeted",
) -> pd.DataFrame:
    """
    Aggregate Layer 1 to per-offensive-player — the "hunter skill"
    leaderboard.

    "Hunting" possessions are those flagged by the ingest as intentional
    routing at the target defender — switch-hunts, called ISOs at the
    weakest defender, drag screens at a specific match. If the ingest
    omits the flag entirely we fall back to a heuristic: a possession is
    a "hunt" if the target defender's DTI_def_per100 ranks in the top
    third of the season's defender pool (i.e. he is an above-baseline
    surrenderer).

    For each hunter h, restricting to hunting possessions:

        m_h                       = number of hunting possessions
        raw_PPP_when_hunting_h    = sum(points_scored_i) / m_h
        expected_PPP_baseline_h   = sum(baseline_PPP_i) / m_h
        DTI_hunt_h                = raw_PPP_when_hunting_h
                                    - expected_PPP_baseline_h
        DTI_hunt_per100_h         = DTI_hunt_h * 100

    Args:
        poss_df_with_dti: output of compute_dti_poss().
        min_hunting_possessions: minimum sample size to qualify. Default
            150 — calibrated against the typical playoff hunter usage
            (Brunson, Tatum, Luka all clear ~150 hunting possessions per
            playoff run).
        is_targeted_col: column flagging hunting possessions. If absent
            the function falls back to the "target defender ranks in
            the top 33% of DTI_def_per100" heuristic — surfaced in the
            output's `_hunting_flag_source` attribute for the runner to
            print.

    Returns:
        DataFrame sorted by DTI_hunt_per100 descending (best hunters
        first) with columns:
            hunter_id, hunter_name, team_id,
            possessions_hunting, raw_PPP_when_hunting,
            expected_PPP_baseline, DTI_hunt, DTI_hunt_per100, rank
    """
    required = {
        "hunter_id", "hunter_name", "defender_id",
        "points_scored", "baseline_PPP", "DTI_poss",
    }
    missing = required - set(poss_df_with_dti.columns)
    if missing:
        raise KeyError(
            f"poss_df_with_dti missing required columns: {sorted(missing)}"
        )

    df = poss_df_with_dti.copy()

    # Resolve the hunting filter.
    if is_targeted_col in df.columns:
        hunting_mask = df[is_targeted_col].fillna(False).astype(bool)
        flag_source = f"column:{is_targeted_col}"
    else:
        # Fallback heuristic: top-third surrenderers are the "hunt-worthy"
        # defenders; possessions targeting them count as hunts.
        per_def = df.groupby("defender_id", observed=True).agg(
            poss=("DTI_poss", "size"),
            dti=("DTI_poss", "mean"),
        )
        per_def = per_def[per_def["poss"] >= 30]
        if per_def.empty:
            hunting_mask = pd.Series(False, index=df.index)
        else:
            cutoff = per_def["dti"].quantile(0.67)
            hunt_defs = set(per_def.index[per_def["dti"] >= cutoff])
            hunting_mask = df["defender_id"].isin(hunt_defs)
        flag_source = "fallback:top-third-surrenderers"

    hunt_df = df[hunting_mask].copy()

    weights = (
        hunt_df["possessions_used"].astype(float).fillna(1.0)
        if "possessions_used" in hunt_df.columns
        else pd.Series(1.0, index=hunt_df.index)
    )
    hunt_df["_w"] = weights

    team_col = (
        "offense_team_id" if "offense_team_id" in hunt_df.columns
        else "team_id" if "team_id" in hunt_df.columns
        else None
    )

    group_cols: List[str] = ["hunter_id", "hunter_name"]
    if team_col is not None:
        group_cols.append(team_col)

    grouped = hunt_df.groupby(group_cols, dropna=False, observed=True)
    agg = grouped.agg(
        possessions_hunting=("_w", "sum"),
        points_when_hunting=("points_scored", lambda s: float(np.sum(
            s.astype(float).to_numpy() * hunt_df.loc[s.index, "_w"].to_numpy()
        ))),
        expected_points_baseline=("baseline_PPP", lambda s: float(np.sum(
            s.astype(float).to_numpy() * hunt_df.loc[s.index, "_w"].to_numpy()
        ))),
    ).reset_index()

    agg = agg[agg["possessions_hunting"] > 0].copy()
    agg["raw_PPP_when_hunting"] = (
        agg["points_when_hunting"] / agg["possessions_hunting"]
    )
    agg["expected_PPP_baseline"] = (
        agg["expected_points_baseline"] / agg["possessions_hunting"]
    )
    agg["DTI_hunt"] = agg["raw_PPP_when_hunting"] - agg["expected_PPP_baseline"]
    agg["DTI_hunt_per100"] = agg["DTI_hunt"] * PER_100_SCALE

    qualifying = agg[
        agg["possessions_hunting"] >= float(min_hunting_possessions)
    ].copy()
    qualifying.sort_values("DTI_hunt_per100", ascending=False, inplace=True)
    qualifying.reset_index(drop=True, inplace=True)
    qualifying["rank"] = np.arange(1, len(qualifying) + 1)

    if team_col is not None and team_col != "team_id":
        qualifying.rename(columns={team_col: "team_id"}, inplace=True)
    elif team_col is None:
        qualifying["team_id"] = np.nan

    cols = [
        "rank", "hunter_id", "hunter_name", "team_id",
        "possessions_hunting",
        "raw_PPP_when_hunting", "expected_PPP_baseline",
        "DTI_hunt", "DTI_hunt_per100",
    ]
    out = qualifying[cols]
    # Attach the flag source so the runner can report it.
    out.attrs["hunting_flag_source"] = flag_source
    return out


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_against_known_targets(
    dti_def_df: pd.DataFrame,
    known_targets: Optional[Dict[str, Dict[str, str]]] = None,
    top_n: int = 30,
) -> pd.DataFrame:
    """
    Spot-check: do the named 2026 playoff hunt-targets land in the top N
    of the DTI_def leaderboard?

    Defaults to KNOWN_TARGETS_2026 (Booker, Mitchell, Jokic, KAT, Conley,
    Nesmith) from the OptGap master dossier.

    Args:
        dti_def_df: output of compute_dti_def() (sorted by DTI_def_per100
            descending).
        known_targets: dict mapping player name to {team, context}. If
            None, the module-level KNOWN_TARGETS_2026 is used.
        top_n: leaderboard depth to check against. Default 30.

    Returns:
        DataFrame with one row per known target:
            player_name, expected_team, in_top_n, observed_rank,
            observed_DTI_def_per100, observed_possessions_targeted,
            note
    """
    targets = known_targets or KNOWN_TARGETS_2026
    if "defender_name" not in dti_def_df.columns:
        raise KeyError("dti_def_df must have 'defender_name' column")

    head = dti_def_df.head(top_n).copy()
    head_names = head["defender_name"].astype(str).tolist()
    head_lookup = {
        name: dti_def_df[dti_def_df["defender_name"] == name].iloc[0]
        for name in head_names
    }

    rows = []
    for name, meta in targets.items():
        in_top = name in head_lookup
        if in_top:
            row = head_lookup[name]
            rows.append({
                "player_name": name,
                "expected_team": meta.get("team", ""),
                "in_top_n": True,
                "observed_rank": int(row["rank"]),
                "observed_DTI_def_per100": float(row["DTI_def_per100"]),
                "observed_possessions_targeted": float(
                    row["possessions_targeted"]
                ),
                "note": meta.get("context", ""),
            })
        else:
            # Check whether the player is present at all (just below the
            # cutoff) for diagnostic purposes.
            full = dti_def_df[dti_def_df["defender_name"] == name]
            if not full.empty:
                row = full.iloc[0]
                rows.append({
                    "player_name": name,
                    "expected_team": meta.get("team", ""),
                    "in_top_n": False,
                    "observed_rank": int(row["rank"]),
                    "observed_DTI_def_per100": float(row["DTI_def_per100"]),
                    "observed_possessions_targeted": float(
                        row["possessions_targeted"]
                    ),
                    "note": meta.get("context", "")
                            + " | OUTSIDE TOP N — check sample.",
                })
            else:
                rows.append({
                    "player_name": name,
                    "expected_team": meta.get("team", ""),
                    "in_top_n": False,
                    "observed_rank": np.nan,
                    "observed_DTI_def_per100": np.nan,
                    "observed_possessions_targeted": np.nan,
                    "note": meta.get("context", "")
                            + " | NOT FOUND on leaderboard (below min sample).",
                })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Convenience IO
# ---------------------------------------------------------------------------

def load_possessions(parquet_path: Path | str) -> pd.DataFrame:
    """Load the ingest's possession-level parquet."""
    return pd.read_parquet(parquet_path)


def load_baseline(parquet_path: Path | str) -> pd.DataFrame:
    """Load the ingest's action-type baseline parquet."""
    return pd.read_parquet(parquet_path)


@dataclass
class DTILeaderboards:
    """Bundle of the three DTI layers."""
    poss: pd.DataFrame
    defender: pd.DataFrame
    hunter: pd.DataFrame


def compute_all_layers(
    poss_df: pd.DataFrame,
    baseline_df: pd.DataFrame,
    min_targeted_possessions: int = 200,
    min_hunting_possessions: int = 150,
) -> DTILeaderboards:
    """End-to-end convenience: poss + baseline -> all three layers."""
    poss_dti = compute_dti_poss(poss_df, baseline_df)
    def_lb = compute_dti_def(
        poss_dti, min_targeted_possessions=min_targeted_possessions
    )
    hunt_lb = compute_dti_hunt(
        poss_dti, min_hunting_possessions=min_hunting_possessions
    )
    return DTILeaderboards(poss=poss_dti, defender=def_lb, hunter=hunt_lb)
