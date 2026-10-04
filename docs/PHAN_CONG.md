# PHÂN CÔNG NHÓM — WorldCup Stats '26 (9 thành viên / 3 nhóm)

> Điền tên vào cột Thành viên. Mỗi người chỉ sửa file thuộc nhóm mình.
> Schema DB, tên cột output analytics và contract `helpers.q` là bất biến —
> muốn đổi phải báo cả 3 nhóm trước.

## Nhóm 1 — Data & Database (3 người)

| Người | Vai trò | File sở hữu |
|---|---|---|
| TV1: ___Tùng___+ Thanh____ | Tìm raw data | `data/raw/`, `src/pipeline/fetch_fifa.py` (chỉ tải API/dataset tĩnh, cấm scrape live) |
| TV2: _____Thông_____ | Xử lý dữ liệu | `src/pipeline/build_dataset.py`, `fill_fifa_tc.py`, `fill_gk_final.py`, `remap_wc2026_ids.py`, `build_club_tier.py`, `src/clean_data.py`, `src/utils/`, `data/processed/csv/`, `data/processed/wc2026_player_match/` |
| TV3: __Giáp________ | DB + kiểm định | `src/db/build_db.py`, `src/pipeline/validate_dataset.py`, `src/audit_data.py`, `src/format_prediction_floats.py`, `src/verify_env.py`, `data/db/` |

Cam kết nhóm 1: `wc2026_full.db` đầy đủ (104 trận / 48 đội / 1039 cầu thủ),
CSV nguồn trong `data/processed/csv/` không được sửa sau khi chốt.

## Nhóm 2 — Web App + UI/Media (2 người)

| Người | Vai trò | File sở hữu |
|---|---|---|
| TV4: _____Đức_____ | Trang dữ liệu + nền tảng | `src/app/app.py`, `pages/1_matches.py`, `2_teams.py`, `7_match_detail.py`, `match_data.py`, `navigation.py`, `page_chrome.py`, `text_norm.py`, `start-dashboard.bat`, `tests/ui_smoke.py`, toàn bộ `*.css`, `media_ui.py`, `match_ui.py`, `src/app/static/` |
| TV5: ______Trung____ | Trang cầu thủ/ML/BestXI | `pages/3_players.py`, `4_compare.py`, `5_ml_explorer.py`, `6_best_xi.py`, `compare_ui.py`, `helpers.py`, `table_ui.py` |

Cam kết nhóm 2: smoke 34/34 PASS; web chỉ đọc DB + file analytics, không đọc
CSV trực tiếp, thiếu file thì cảnh báo không crash.

## Nhóm 3 — ML/Analytics (3 người)

| Người | Vai trò | File sở hữu |
|---|---|---|
| TV6: _________Chiến_ | Feature + clustering | `build_features.py`, `common.py`, `eda_report.py`, `notebooks/C_eda_ml.ipynb`, `player_clusters.py`, `team_clusters.py` |
| TV7: ___Mạnh_______ | Similarity/PCA/anomaly/score | `player_similarity.py`, `pca_explore.py`, `detect_anomalies.py`, `analytics_score.py` |
| TV8: _____Quốc Anh_____ | Value/XI + pipeline ML | `market_value.py`, `best_xi.py` (pipeline song song `Player_Analysis/`, `Team_Analysis/`, `ml_data.py`, `run_ml_pipeline.py` đã dọn đợt clean) |

Cam kết nhóm 3: output đúng schema `data/processed/analytics/` kèm file bằng chứng
(`eda_*`, `cluster_tuning.csv`, `market_value_cv/ablation/calibration.csv`,
`score_validation.csv`, `anomaly_tuning.csv`). `market_value` là ESTIMATE
(thiếu ground truth sau giải) — giữ disclaimer.

## Giao điểm giữa các nhóm

- Nhóm 2 đọc DB của nhóm 1 qua `helpers.q()` (cache 600s, trả bản copy).
- Nhóm 2 đọc output nhóm 3 qua `load_analytics_csv()` / `load_similarity_matrix()`.
- Nối thực thể mới: `src/utils/entity_resolve.py` (blocking + difflib +
  ThreadPool, cấm `joblib/loky`), bridge offline, cấm fuzzy runtime.

## Checklist bàn giao (chạy trước mọi buổi demo)

    .\.venv\Scripts\python.exe -m compileall -q src tests
    .\.venv\Scripts\python.exe -m pip check
    .\.venv\Scripts\python.exe tests/ui_smoke.py   # 34/34 PASS
    .\start-dashboard.bat                          # http://127.0.0.1:8520/

## Xác nhận

| Nhóm | Đại diện ký | Ngày |
|---|---|---|
| Nhóm 1 — Data | __________ | ____/____/________ |
| Nhóm 2 — Web | __________ | ____/____/________ |
| Nhóm 3 — ML | __________ | ____/____/________ |
