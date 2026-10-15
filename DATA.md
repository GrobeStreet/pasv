# Data: what is bundled and how to regenerate the rest

## Bundled
- `data/pasv_v01_2025_team_aggregate.csv`: the team-aggregate PASV v0.1 input (see CHANGELOG for the r ≈ 0.81 note).
- `npss/data/npss_panel.json`: the full NPSS panel, 1,131 player-seasons, 2017–2025. NPSS reproduces end to end from this file.
- `results/`: Study 1 outputs (`study1_summary.txt`, `study1_player_scores.csv`, within-player confirmations).

## Not bundled: Study 1 possession parquets
`code/run_study1.py` reads two files from a sibling directory `../dti_data/`:

| File | Contents |
|---|---|
| `poss_v3_2024-25_Regular_Season.parquet` | 284,382 possessions; 219,527 field-goal attempts (calibration) |
| `poss_v3_LINEUPS_2024-25_Playoffs.parquet` | held-out playoff possessions with on-floor lineups; 14,377 attempts |

### Regenerating them
Both are built from the NBA's public stats endpoints through `nba_api` (`leaguegamefinder`, `playbyplayv3`, `boxscoretraditionalv3`):

```bash
pip install -r requirements.txt nba_api
python3 code/dti_ingest_v3.py           # regular-season possessions -> ../dti_data/poss_v3_2024-25_Regular_Season.parquet
python3 code/dti_ingest_v3_lineups.py   # playoff possessions with lineups -> ../dti_data/poss_v3_LINEUPS_2024-25_Playoffs.parquet
python3 code/run_study1.py              # writes results/study1_summary.txt and results/study1_player_scores.csv
```

Notes:
- The ingest is slow (one request per game, rate-limited) and depends on the NBA endpoints staying stable.
- `clock` in the parquets is the game clock, not the shot clock (see `code/pasv_per_shot.py`).
- A frozen source manifest with file hashes is not yet committed. Until it is, a rebuild can be checked against the counts above and the printed values in `results/study1_summary.txt`.
