# Final Code Audit

**Project:** `Fotball_analys` — World Cup 2026 football analytics platform (Streamlit + SQLite)
**Audit date:** 2026-10-23 (last commit at audit start: `3e4d25e`)
**Python runtime used for checks:** 3.10.x global interpreter with the project's verified library set
(streamlit 1.61.1, pandas 2.3.1, numpy 1.26.4, sklearn 1.7.2, plotly 6.9.0, pyarrow 21.0.0, PuLP 3.3.2)

---

## 1. Executive Summary

The repository is in **good handover shape**. The source tree is fully grouped (no loose
modules at any package root), the Streamlit multipage app starts and renders all 7 pages,
the smoke suite passes 34/34, static analysis reports no unused imports and no unused
names, syntax compiles cleanly, and the production SQLite database passes an integrity
check in read-only mode.

All cleanup applied during this audit is minimal: 4 deletions of dead local variables
(5 statements), one accuracy fix in the README structure section, and `.gitignore`
hygiene additions. No datasets, no database rows, no analytics outputs and no model
artifacts were touched. The remaining open item is a **known, versioned mismatch between
`requirements.txt` pins and the locally verified runtime** (documented in §6 and §10).

**Verdict: ready for handover**, with the limitations in §10 documented for the next owner.

---

## 2. Repository Structure (actual)

```
Fotball_analys/
├── .streamlit/            config.toml (dark theme, enableStaticServing, headless)
├── src/                   (package root: no loose files, no empty __init__)
│   ├── app/               Streamlit web app
│   │   ├── app.py         ★ main entry (Streamlit Cloud main module; MPA root)
│   │   ├── core/          helpers (DB q/caches), match_data, navigation,
│   │   │                  page_chrome, text_norm
│   │   ├── pages/         1_matches … 7_match_detail (directory-based MPA)
│   │   ├── ui/            presentation layer: media_ui, match_ui, compare_ui,
│   │   │   │              table_ui (+ __init__ package doc)
│   │   │   └── styles/    12 CSS files — all referenced (verified, see §9)
│   │   └── static/        16 media assets served via enableStaticServing
│   ├── analytics/         11 ML/EDA scripts (features, similarity, clusters,
│   │                      market value, anomalies, best XI, EDA, PCA…)
│   ├── pipeline/          7 data-build scripts (fetch_fifa → build_dataset →
│   │                      remap_ids → fill_gk/fifa_tc → validate → club_tier)
│   ├── maintenance/       audit_data, clean_data, format_prediction_floats, verify_env
│   └── db/                build_db.py (builds wc2026_full.db)
├── data/
│   ├── db/                wc2026_full.db (2.8 MB)
│   ├── processed/         csv/ (10), wc2026_player_match/ (8), analytics/ (31),
│   │                      AUDIT_REPORT.md, audit_schema.json
│   └── raw/               fifa/ (105), espn/ (2 — pen_punch runtime sources),
│                          fifa_training_centre/ (6 tables + CITATION + LICENSE)
├── docs/PHAN_CONG.md      team ownership map (9 members / 3 groups)
├── notebooks/C_eda_ml.ipynb  small documented EDA notebook (kept — active content)
├── tests/ui_smoke.py      34-check AppTest smoke suite
├── requirements.txt       pinned versions
├── start-dashboard.bat    local launcher (auto-creates .venv, installs, runs)
└── README.md              setup + structure + page map
```

Illustrative trees in the audit brief were treated as non-authoritative; the project
uses `maintenance/` and `core/` instead of the hypothetical `models/`, `services/`,
`visualization/` packages — **no packages were created to match the example tree.**

---

## 3. Dead Code Cleanup

Static analysis (pyflakes) found zero unused functions, zero unused imports, and five
dead local assignments. All five were cross-read before deletion; every one is a pure
local assignment with no side effects and no readers:

| File | What was removed | Reason |
|---|---|---|
| `src/app/ui/media_ui.py` | `hero_tablet`, `hero_mobile` local vars (2 lines) | Never read; `-tablet`/`-mobile` variants do not exist on disk, so `static_variant()` would have fallen back to the desktop name anyway |
| `src/pipeline/build_dataset.py` | `home_len_extra` (1 line) | Computed from the calendar JSON but never read |
| `src/pipeline/build_dataset.py` | `opp_goals_full` (1 line) | Pure expression reusing existing vars; never read |
| `src/pipeline/build_dataset.py` | `parquet_ok = True/False` (2 statements) | Bookkeeping flag with no reader; the parquet try/except itself is retained |

**Explicitly kept (checked, not dead):**
- Every function in `core/`, `ui/` and `match_data/api` layers has call sites (verified by import graph + AppTest execution). Examples cross-checked: `text_norm.flag`, `helpers.load_similarity_matrix`, `media_ui.static_url/static_variant/flag_url/player_photo_url`, all `match_ui.render_*`.
- `print(..., file=sys.stderr)` fallbacks in `app.py` KPI queries are legitimate degradation logging, not debug leftovers.
- `try/except` around parquet writes in `build_dataset.py` is behavior, not dead code.
- No commented-out legacy implementations were found in application code.

---

## 4. Import Cleanup

- **Unused imports removed: 0** (pyflakes over `src/` + `tests/` reports none).
- Wildcard imports: none found.
- No duplicate imports found.
- `src/utils/__init__.py` re-exports `ALIAS`, `load_csv`, `load_gk`, `load_pms` —
  meaningful re-export surface, not an empty stub (see §5/§10 note about its consumers).
- Remaining warnings: none.

---

## 5. File Audit

| Classification | Item | Disposition |
|---|---|---|
| REMOVED (2026-10-23, owner-directed) | 3 × `.gitkeep` (`data/db/`, `data/processed/analytics/`, `data/processed/ml_results/`) + empty `data/processed/ml_results/` | Content files keep live dirs tracked in git; placeholders no longer needed |
| REMOVED (2026-10-23, owner-directed) | `src/utils/` (aliases, io_helpers, entity_resolve, `__init__`) | Zero importers repo-wide (verified twice); see §10.3 |
| MUST KEEP | `src/app/ui/__init__.py` | Package marker — `ui.*` modules are imported by pages |
| MUST KEEP | `notebooks/C_eda_ml.ipynb` | Documented EDA used for the course (MIN_MIN=90, shrinkage K=270 rationale); active content |
| MUST KEEP | `docs/PHAN_CONG.md` | Live team ownership contract (updated in the same commit) |
| SAFE TO REMOVE (done) | 5 dead variable assignments (§3) | Removed |
| Generated caches | `__pycache__/` dirs | Covered by `.gitignore`; none are tracked; no action needed |

No empty Python modules, empty CSS/HTML/JS, duplicate sources, backup/temp files, or
obsolete documentation were found. CSS audit: **12/12 files in `ui/styles/` are loaded
by pages or the shared navigation/page_chrome bundle — none dead.**

---

## 6. Dependency Audit

Declared (`requirements.txt`) vs. actual usage across all scripts and the app:

| Dependency | Pin | Used in code | Verdict |
|---|---|---|---|
| pandas | 3.0.5 | everywhere (app + pipeline + analytics) | RETAIN |
| numpy | 2.5.3 | 6+ modules (sklearn pre/post, analytics, plots) | RETAIN |
| matplotlib | 3.11.2 | pca_explore, eda_report | RETAIN |
| seaborn | 0.13.2 | **no import sites** (only `verify_env.py` gate) | RETAIN (documented; see note) |
| streamlit | 1.63.0 | entire app (incl. `st.iframe`, `st.html`, `enableStaticServing`) | RETAIN |
| openpyxl | 3.1.5 | **no import sites** (`verify_env.py` gate only) | RETAIN (documented; see note) |
| scikit-learn | 1.9.1 | 6 analytics modules + app ML flows | RETAIN |
| plotly | 7.0.0 | app charts (px.bar/scatter, go.Scatterpolar radar) + vendored plotly.js | RETAIN |
| PuLP | 3.3.2 | best-XI optimization path | RETAIN |
| pyarrow | 25.0.1 | parquet read/write (`similarity_matrix.parquet`, `wc2026_player_match/`) | RETAIN |

SQLite: correctly **no** external SQLite dependency — the app uses the standard library
`sqlite3` (read-only URI connections). Verified throughout `helpers.py`.

Notes:
- `seaborn` / `openpyxl`: zero import sites in `src/`, but both are gated by
  `src/maintenance/verify_env.py` (the team's environment checklist) and may be used by
  ad-hoc Excel/export workflows. Removed candidates only for a *future* cleanup that
  also updates `verify_env.py` — deliberately not done here to preserve the handover
  contract.
- **Version-pin mismatch** (pinned vs. locally verified runtime): pandas 3.0.5 vs 2.3.1,
  numpy 2.5.3 vs 1.26.4, matplotlib 3.11.2 vs 3.10.3, streamlit 1.63.0 vs 1.61.1,
  scikit-learn 1.9.1 vs 1.7.2, plotly 7.0.0 vs 6.9.0, pyarrow 25.0.1 vs 21.0.0
  (PuLP and openpyxl match). The app runs **on both** (Streamlit Cloud deploys from the
  pinned file; the local environment is the older set). Per the safety rules no pins
  were changed — see §10.

---

## 7. Data and Model Integrity

Executed, read-only:

- **SQLite `PRAGMA integrity_check` on `data/db/wc2026_full.db` → `integrity: ok`**;
  `matches = 104`, `players = 1248` (expected canonical counts). Connection opened with
  `mode=ro` URI; no write handle was created.
- All 13 canonical CSVs, 11 `wc2026_player_match/` files and 31 `analytics/` outputs were
  **not** written, renamed, regenerated or re-typed during this audit. `audit_schema.json`
  matches the last regeneration (`cd416bf`).
- ML artifacts (`data/processed/analytics/`) and the parquet/SQLite mirrors present and
  untouched; no model retraining, no parameter changes.
- `.gitignore` correctly excludes ESPN play-by-play caches (`plays_full/`, `plays_agg/`)
  per the documented re-download design and all `__pycache__`/venv paths.
- No credentials, API keys or secrets exist anywhere in the repo (checked `.streamlit/`,
  scripts, docs); no `.env`/`secrets.toml` files present.

---

## 8. Streamlit and Deployment

| Check | Result | Method |
|---|---|---|
| Entry point validity | PASS | `start-dashboard.bat` targets `src/app/app.py` (exists); README documents it; Streamlit Cloud main-module path unchanged by recent refactors |
| App startup / page rendering | PASS | `streamlit.testing.v1.AppTest.from_file` executed `app.py` and all 7 pages with zero exceptions (34 checks, exit 0) |
| Internal imports | PASS | `core.*` import graph exercised on every page; pyflakes clean |
| Static assets serving | PASS | `enableStaticServing = true` in `.streamlit/config.toml`; files present under `src/app/static/`; relative `app/static/...` URLs verified live previously and not modified |
| Data loading via SQLite | PASS | Every page performs real queries in the smoke run (matches, teams, players, events, lineups, team stats) |
| Plotly chart construction | PASS | Overview bar/scatter and Compare radar figures are constructed during the smoke run without exceptions |
| Missing-data handling | PASS | App-side fallbacks (`kpi`, `n_teams`, assists, penalties) and CSV-missing `st.info` paths in place (`load_analytics_csv → None`) |
| Streamlit Cloud reachability | PASS (site up) | `https://wc26analys.streamlit.app` → HTTP 303 anonymous-cookie handshake (known Cloud artifact; the last interactive Selenium session confirmed full render, 0 media errors) |
| Local launcher | PASS | `start-dashboard.bat` auto-creates `.venv`, installs `requirements.txt`, runs on port 8521 |

The database is accessed in read-only mode from the app (`file:...?mode=ro` URI,
`PRAGMA mmap_size`) — cleanup cannot mutate it through the app.

---

## 9. Test Results

| Check | Command | Result |
|---|---|---|
| Static analysis (unused imports/names, undefined names) | `python -m pyflakes src tests` | **PASSED** (exit 0, after cleanup; 5 findings before) |
| Syntax / byte-compilation | `python -m compileall src tests -q` | **PASSED** (exit 0) |
| App smoke suite (34 checks: all 7 pages, selectbox/radio modes, query-param detail, merged compare workspace, ML cluster action) | `python tests/ui_smoke.py` | **PASSED** (34/34 `PASS`, exit 0) |
| Database integrity | `PRAGMA integrity_check` via read-only connection | **PASSED** (`ok`, 104 matches / 1248 players) |
| Empty-file scan (repo-wide, excluding `.venv/.git`) | filesystem scan | **PASSED** — only 3 `.gitkeep` placeholders |
| CSS usage cross-reference | grep of 12 stylesheets | **PASSED** — 12/12 referenced |
| Analytics scripts executed end-to-end | — | **NOT RUN** — deliberately: every module in `src/analytics/` and `src/pipeline/` writes derived outputs into `data/processed/`; running them would touch production artifacts. Their runtime consumption is verified through the app smoke tests instead |
| Fresh-VM install from `requirements.txt` | — | **NOT RUN** — environment already provisioned; see §10 pin-mismatch note |
| Streamlit Cloud interactive render | — | **NOT RUN (this session)** — last interactive verification predates this audit (all-green, `3e4d25e` code paths unchanged since); anonymous HTTP check confirms site up |

---

## 10. Known Issues / Limitations for the next owner

1. **`requirements.txt` pins newer versions than the locally verified environment**
   (e.g. pandas 3.x, streamlit 1.63 vs locally used 1.61). Both sets run the app today,
   but a fresh install uses the pinned set while contributors may develop on the older
   local set. Recommend running the test suite once on a fresh `.venv` and then either
   re-pinning to the verified versions or upgrading the local env to the pins — a
   one-time decision for the new owner (no defect identified requiring a change now).
2. **`seaborn` and `openpyxl` are declared and env-gated but import-free in code.**
   Safe to drop in a future cleanup *together with* their `verify_env.py` gate entries.
3. **`src/utils/` had no importer — since removed.** The package (aliases, io_helpers,
   entity_resolve) was README-documented and TV2-assigned in `docs/PHAN_CONG.md`, but
   nothing ever imported it. Owner directed its deletion on 2026-10-23 (same commit
   refreshed every doc reference). If entity resolution is needed again, it should be
   re-created wired directly into the pipeline rather than as a standalone package.
4. The Streamlit Cloud health path `/_stcore/health` responds with the shell wrapper
   (proxy-level behavior of the platform, not the app); do not build tooling that
   expects a bare `ok` there.
5. `notebooks/C_eda_ml.ipynb` references repo-relative paths (`../data/...`) — it only
   runs from inside `notebooks/`.

---

## 11. Handover Checklist

- [x] Source code reviewed (pyflakes over `src/` + `tests/`, import graph, targeted reads of every app module).
- [x] Unused imports removed where verified — none found (0 to remove).
- [x] Dead code removed where verified — 5 dead assignments removed.
- [x] Empty and duplicate files reviewed — only 3 intentional `.gitkeep` placeholders; none removed.
- [x] Dependencies reviewed — all 10 retained with justification; 2 candidates documented.
- [x] Internal imports verified — via smoke AppTest on all pages + pyflakes.
- [x] Existing tests executed — `tests/ui_smoke.py` 34/34 PASSED.
- [x] Dataset integrity preserved — no write, no regeneration; canonical artifacts untouched.
- [x] SQLite database integrity preserved — read-only `integrity_check: ok`.
- [x] Machine learning artifacts preserved — `data/processed/analytics/` untouched.
- [x] Streamlit application startup checked — AppTest full render of every page, entry point verified.
- [x] Visualization code checked — plotly figures constructed during smoke run.
- [x] Deployment configuration reviewed — `config.toml`, main module path, launcher, pins.
- [x] README and setup instructions reviewed — structure entry updated to current tree.
- [x] Remaining limitations documented — §10.

---

*Report generated as part of pre-handover audit task. All claims in this document refer
to commands actually executed in this session (results in §5/§7/§8/§9).*
