# Kien truc du an WorldCup Stats '26

```plaintext
                    +-------------------+
                    |  data/raw/fifa    |  calendar.json + match_*.json (FIFA API)
                    +---------+---------+
                              | src/pipeline/build_dataset.py
                              v
+----------------+  +--------------------------+  +------------------------+
| data/processed |  | src/db/build_db.py       |  | data/db/wc2026_full.db |
| /csv/*.csv     +->+ (dims + facts + views,   +->+ (SQLite duy nhat cho  |
| (source chuan) |  |  enrich attendance)      |  |  web dashboard)        |
+----------------+  +--------------------------+  +-----------+------------+
                                                           |
                    +--------------------------+           |
                    | src/analytics/*.py       |           | read-only SQL
                    | eda -> features ->       |           | (helpers.q, cache)
                    | cluster/similarity/PCA/  |           |
                    | anomaly/score/value/XI   |           |
                    +------------+-------------+           |
                                 | CSV/parquet v           v
                                 +------------------>+-----------+
                                                      | src/app/  |
                                                      | app.py +  |
                                                      | pages/1-7 |
                                                      +-----------+
```

## Luong du lieu

1. **Thu thap** (`src/pipeline/fetch_fifa.py`): tai calendar + chi tiet tran.
2. **Dung dataset** (`build_dataset.py`, `fill_fifa_tc.py`, `fill_gk_final.py`,
   `remap_wc2026_ids.py`, `validate_dataset.py`): ra `wc2026_player_match/`.
3. **Len DB** (`src/db/build_db.py`): ra `data/db/wc2026_full.db`.
4. **ML** (`src/analytics/`, chay theo README dung thu tu): ra
   `data/processed/analytics/*.csv|*.parquet|*.png|*.html`.
5. **Hien thi** (`src/app/`): chi doc DB + file analytics (khong ghi).

## Quy uoc

- `helpers.q()` / `load_analytics_csv()` cache 600s, tra ban copy.
- `text_norm.py`: chuan hoa ten + ma doi dung chung.
- `page_chrome.py`: boilerplate trang (config + CSS + footer).
- Market value la ESTIMATE counterfactual (xem `market_value_validation.csv`).

## Quy uoc noi thuc the (entity resolution) — BAT BUOC cho moi join moi

- Dung `src/utils/entity_resolve.py`: blocking `(nationality, birth_year +-1,
  position_group)` truoc, fuzzy `difflib` trong block, song song
  `ThreadPoolExecutor` (cam `joblib/loky` tren Windows).
- Chay offline 1 lan, ghi `data/processed/<ten>_bridge.csv`
  (`from_id,to_id,score,verified`) + `<ten>_conflicts.csv` de sua tay <5%.
- Web va ML **cam fuzzy runtime**: chi `pd.merge` tren bridge (ms).
- Khong scrape live (Cloudflare/ToS): dung dataset tinh/Kaggle/curated.
- Tien le: `id_mapping_fifa_to_csv.json` + `id_conflicts.json` (giữ nguyên).
