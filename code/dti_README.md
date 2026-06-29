# DTI v0.1 — Ingest Pipeline README

**Status:** `Evidence` (substrate built, not yet wired to DTI compute notebook)
**Date:** 2026-06-13
**Files in this folder:**
- `dti_ingest.py` — the module (ingest functions)
- `run_dti_ingest.py` — the CLI runner
- `dti_README.md` — this file

This is the ingest substrate for the **Defender Targeting Index (DTI)**, the Lane 1 build defined in `OptGap_MASTER_Dossier_2026-06-13.md`. It pulls NBA possession-level play-by-play via the [PBPstats library](https://github.com/dblackrun/pbpstats) and emits a normalized possession-level parquet file. DTI itself (the per-defender "hunted PPP lift" computation) runs in a downstream notebook on this parquet.

---

## What gets ingested per possession

| Column | Type | Notes |
|---|---|---|
| `game_id` | str | stats.nba.com game id, e.g., `0042500401` |
| `period` | int | 1-4 + OTs |
| `possession_number` | int | pbpstats-assigned ordinal |
| `offensive_team_id`, `defensive_team_id` | int | NBA team ids |
| `offensive_player_ids`, `defensive_player_ids` | list[int] | the 5 on the court at the moment of the terminal event |
| `primary_action_type` | str | `iso` / `transition` / `putback` / `assisted_2` / `assisted_3` / `post_or_drive` / `turnover` / `free_throw` / `other` |
| `shot_outcome` | str | `made_2` / `made_3` / `missed_2` / `missed_3` / `turnover` / `foul_drawn_ft_trip` |
| `points` | int | points scored on the possession (FT trips credited via score-delta) |
| `shot_distance` | float | feet, from pbpstats `shot_data` |
| `shot_zone` | str | `at_rim` (<4 ft) / `short_mid` (<14 ft) / `long_mid` (<23 ft) / `corner_3` / `above_break_3` |
| `primary_offensive_player` | int | shooter / TOV player / FT shooter |
| `primary_defensive_player` | int | best-guess defender (see heuristic below) |
| `defender_heuristic` | str | which heuristic resolved the defender (stratify downstream) |
| `start_clock`, `end_clock`, `possession_start_type` | str | possession boundaries |
| `season`, `season_type`, `ingest_version`, `ingest_date` | str | provenance |

---

## How to run

```bash
# from .../Basketball Stats Book/pasv-sloan-repo/code/
python run_dti_ingest.py --season 2025-26 --season-type Playoffs
```

Flags:
- `--season`: e.g., `2025-26`, `2024-25`
- `--season-type`: `Regular Season` (default), `Playoffs`, or `Play In`
- `--out-dir`: defaults to `.../Basketball Stats Book/dti_data/`
- `--max-games N`: cap for smoke tests (e.g., `--max-games 5` for a 2-min dry-run)
- `--sleep-between-games`: default 0.6 sec — be conservative with stats.nba.com
- `--verbose`: DEBUG-level logging

Outputs:
- `dti_data/poss_level_<season>_<season_type>.parquet` — the main table
- `dti_data/expected_ppp_baseline_<season>_<season_type>.csv` — league-wide PPP by action type, used downstream
- `dti_data/pbpstats_response_cache/` — JSON cache so re-runs hit cache, not the API

---

## Runtime expectations

| Run | Game count | First-run time | Cached re-run |
|---|---|---|---|
| Smoke test (`--max-games 5`) | 5 | 2-5 min | <30 sec |
| Playoffs only | 60-105 | 8-20 min | 3-8 min |
| Full Regular Season | ~1,230 | 30-60 min | 12-25 min |
| Full season + playoffs combined | ~1,335 | 35-75 min | 15-30 min |

Time is dominated by stats.nba.com fetch latency and the 0.6-sec sleep between games. The actual extract+parse step is <5% of wall time.

**If stats.nba.com starts 429-ing,** bump `--sleep-between-games` to 1.5-2.0. The retry loop in `load_game_with_retries` will also back off exponentially up to 4 attempts.

---

## Known limitations (v0.1)

### 1. Primary defender resolution is a heuristic, not optical truth
We resolve the primary defender in this priority:
1. **Blocked shot** → the blocker (highest confidence).
2. **Shooting foul** at same clock as terminal event → the fouling defender.
3. **Same-index lineup pairing** → assume the Nth listed offensive player is guarded by the Nth listed defender. **This is crude and will be wrong often.** Downstream code should treat `defender_heuristic == "matchup_same_index_fallback"` as low confidence.
4. **Unresolved** → `primary_defensive_player = -1`. Downstream filters these out unless v0.2 layers optical tracking on top.

Expected resolution rate is roughly: 5-10% blocker, 10-20% shooting-foul, 50-70% same-index fallback, 5-15% unresolved. The high-confidence (blocker + foul) slice is ~15-30% of possessions and is the cleanest DTI signal in v0.1.

**v0.2 path:** wire in Second Spectrum or Synergy matchup data, or hand-label a sample for calibration.

### 2. Action-type tagging is event-derived, not Synergy-grade
PBPstats does NOT label P&R / iso / post-up natively. We approximate:
- `transition` = elapsed time on possession ≤ 8 sec
- `putback` = pbpstats `is_putback` flag
- `assisted_2` / `assisted_3` = pbpstats `is_assisted` flag + shot value
- `iso` = unassisted 2 from >4 ft
- `post_or_drive` = unassisted 2 at the rim (<4 ft)
- `turnover`, `free_throw`, `other` = terminal-event class

This is meaningfully less precise than Synergy's hand-tagged action types. Downstream DTI should not over-interpret distinctions between `iso` and `post_or_drive`.

### 3. The free-throw trip case is collapsed
A possession that ends on a foul drawn → FT trip gets `shot_outcome = "foul_drawn_ft_trip"` and `points` from the score-delta. We don't separately model the FT shooter from the player who drew the foul. Good enough for DTI v0.1; revisit if foul-hunting is its own framework lane (Lane 2 in the Optimization-Gap dossier).

### 4. nba_api fallback path is degraded
If pbpstats can't load the season (most likely cause: stats.nba.com schema change that pbpstats hasn't patched yet), the runner falls back to `nba_api.playbyplayv2`. The fallback path:
- Does NOT resolve matchup lineups
- Does NOT tag action types beyond `other`
- Does NOT compute defender at all (all `-1`)
- Only emits shot outcome + crude shot distance

This is the explicit "non-blocking degraded mode" so Bobby gets a non-empty parquet even on a bad API day. The runner logs this clearly. **If you see `ingest_version = v0.1-fallback` in the parquet, you're in the degraded mode.**

### 5. No game-clock context yet
We don't yet emit clutch-time flags, score margin context, or possession-end shot-clock. Easy to add in v0.2 (the events carry it; we just don't surface it).

---

## Stats.nba.com authentication

PBPstats hits the public `stats.nba.com` endpoints. In Bobby's local environment this should work without cookies. If it doesn't:

1. Open `https://stats.nba.com/` in a browser, accept the cookie banner, and let the page settle (this drops the required `nba_session` cookies).
2. If pbpstats still fails, check the [pbpstats issue tracker](https://github.com/dblackrun/pbpstats/issues) — the maintainer patches stats.nba.com schema changes within days, usually.
3. As a last resort: pin to an older pbpstats version with `pip install pbpstats==1.3.10`.

---

## What to do after the ingest finishes

The parquet is the substrate. The downstream compute (not in this folder) is:

```python
import pandas as pd
df = pd.read_parquet("dti_data/poss_level_2025-26_playoffs.parquet")

# 1. Restrict to high-confidence defender labels for v0.1
high_conf = df[df.defender_heuristic.isin(["blocker", "shooting_foul"])]

# 2. Compute per-defender PPP vs action-type baseline
baseline = pd.read_csv("dti_data/expected_ppp_baseline_2025-26_playoffs.csv")
# join on primary_action_type, compute actual_PPP_when_targeted - expected_PPP
# → that delta is the v0.1 DTI signal.
```

That compute notebook is the next build. This module just guarantees the substrate is clean and reproducible.

---

## Provenance

- Built: 2026-06-13
- Module version: `v0.1`
- pbpstats version pinned: latest from PyPI (currently 1.3.11)
- Source list for the design: `OptGap_MASTER_Dossier_2026-06-13.md`, `OptGap_Slice1_SwitchHunting_2026-06-13.md`, `PASV_Empirical_Validation_Plan_2026-06-05.md`
