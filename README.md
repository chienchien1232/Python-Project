# 🏆 World Cup Data Analytics & Web App

Dự án phân tích dữ liệu chuyên sâu bóng đá World Cup tích hợp các mô hình Machine Learning
để khám phá cấu trúc dữ liệu, tìm kiếm cầu thủ tương đồng, phân cụm lối chơi và định giá
chuyển nhượng. Giao diện web đen/trắng tối giản, mono editorial, ảnh và video toàn màn hình.

---

## 1. Cài đặt & chạy (Setup)

### Điều kiện tiên quyết: Python 3.12 trở lên

### Bước 1: Cập nhật mã nguồn (Hoặc tải trực tiếp repo từ branch chien)
```bash
git clone -b chien https://github.com/chienchien1232/Python-Project.git
```

### Bước 2: Tạo môi trường ảo (máy mới, Python 3.12)
Trên Windows:
```bash
cd Python-Project
python -m venv .venv
.venv\Scripts\Python.exe -m pip install -r requirements.txt
```
Trên macOS / Linux:
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```
`requirements.txt` pin cứng đúng phiên bản đã kiểm tra (pandas 3.0.5, streamlit 1.63.0, ...).

### Bước 3: Khởi chạy
```bash
.\start-dashboard.bat
```

Mặc định mở tại http://127.0.0.1:8521/. Cấu hình Streamlit đã ẩn sidebar và
toolbar mặc định để menu MPA cũ không lóe lên khi tải trang.

---

## 2. Cấu trúc dự án

```plaintext
my_python_project/
├── data/               # raw (FIFA API) / processed (csv chuẩn, wc2026_player_match, analytics) / db
├── src/                # pipeline, db, analytics, app, utils
├── notebooks/          # C_eda_ml.ipynb (EDA phục vụ BTL)
├── tests/              # ui_smoke.py (34 kịch bản)
├── .gitignore
├── requirements.txt    # pin cứng phiên bản đã kiểm tra
├── start-dashboard.bat # entrypoint duy nhất (tự tạo .venv + cài + mở browser)
└── README.md           # file này
```

`src/app/app.py` là entrypoint duy nhất. Các trang trong `src/app/pages/`:

- 1_matches.py — lịch trận, lọc và liên kết Match Detail.
- 2_teams.py — thư mục đội tuyển, thống kê và lịch sử đối đầu.
- 3_players.py — thư mục cầu thủ, hồ sơ và workspace Compare.
- 4_compare.py — redirect tương thích tới /players?view=compare.
- 5_ml_explorer.py — PCA, phân cụm, bất thường và định giá.
- 6_best_xi.py — các chế độ đội hình Best XI.
- 7_match_detail.py — trang chi tiết trận theo match_id (`/match_detail?match_id=<id>`).

Module dùng chung: `src/app/text_norm.py` (chuẩn hóa tên + mã đội),
`src/app/page_chrome.py` (boilerplate trang: config + CSS + footer),
`src/app/utils/entity_resolve.py` (nối thực thể: blocking + difflib + ThreadPool).

## 3. Luồng dữ liệu & kiến trúc

```plaintext
data/raw/fifa ──build_dataset──▶ data/processed/csv ──build_db──▶ data/db/wc2026_full.db
        (FIFA API)          (nguồn sự thật)              (SQLite duy nhất cho web)
                                            │
data/processed/wc2026_player_match ──analytics──▶ data/processed/analytics/*.csv|parquet
                                            │
                        web chỉ ĐỌC DB + file analytics (không ghi)
                                            ▼
                              src/app/ (app.py + pages/1-7)
```

1. **Thu thập** (`src/pipeline/fetch_fifa.py`): tải calendar + chi tiết trận.
2. **Dựng dataset** (`build_dataset.py`, `fill_fifa_tc.py`, `fill_gk_final.py`,
   `remap_wc2026_ids.py`, `validate_dataset.py`): ra `wc2026_player_match/`.
3. **Lên DB** (`src/db/build_db.py`): ra `data/db/wc2026_full.db` (5 dim + 8 fact + views).
4. **ML** (`src/analytics/`, chạy đúng thứ tự mục 6): ra `data/processed/analytics/`.
5. **Hiển thị** (`src/app/`): chỉ đọc DB + file analytics.

Quy ước app ↔ analytics: web chỉ đọc `wc2026_full.db` và `data/processed/analytics/`;
thiếu file output thì hiện cảnh báo + lệnh chạy, KHÔNG crash. Mọi cột định danh dùng
`player_id/match_id/team_id`; tên chỉ để hiển thị.

Quy ước nối thực thể (bắt buộc cho mọi join mới): blocking
`(nationality, birth_year ±1, position_group)` trước, fuzzy `difflib` trong block,
song song `ThreadPoolExecutor` (cấm `joblib/loky` trên Windows). Chạy offline 1 lần,
ghi `data/processed/<ten>_bridge.csv` + `<ten>_conflicts.csv` để sửa tay <5%.
Web và ML cấm fuzzy runtime: chỉ `pd.merge` trên bridge. Không scrape live.

## 4. Schema DB — `data/db/wc2026_full.db`

Dimensions: `teams` (team_id; team_name, fifa_code, group_letter, confederation,
fifa_ranking_pre_tournament, elo_rating, manager_name), `players` (player_id;
player_name, position, club_team, market_value_eur, caps, date_of_birth, height_cm),
`venues` (venue_id; stadium_name, city, country, capacity),
`tournament_stages` (stage_id; stage_name, is_knockout 0/1),
`referees` (referee_id; referee_name).

Facts (104 trận): `matches`, `matches_detailed`, `match_events`, `match_lineups`,
`match_team_stats` (possession, shots...), `player_match_stats`,
`goalkeeper_match_stats`, `player_stats_tournament`.

Views: `v_player_totals`, `v_goalkeepers`. Quy ước: snake_case, boolean 0/1,
ngày YYYY-MM-DD, phút thi đấu số nguyên (NULL = không rõ).

## 5. Từ điển feature — `player_features.csv` (per-90, lọc ≥90 phút)

Mỗi cầu thủ 1 dòng. `*_p90 = tổng / (phút/90)` + bản shrinkage
`p90 × minutes/(minutes+270)` chống nhiễu mẫu nhỏ (K=270 ≈ 3 trận).
18 cặp `total_*`/`*_p90`: goals, assists, shots, shots_on_target, passes,
accurate_passes, crosses, tackles, interceptions, clearances, blocks, recoveries,
duels_won, aerial_duels_won, dribbles_attempted, fouls_committed, fouls_won, offsides.
`pass_accuracy_pct` = accurate/passes ×100 (NULL nếu 0 chuyền).
GK riêng `gk_features.csv`: saves, shots_faced, conceded, clean_sheets,
`save_pct`, `saves_p90`.

Không có trong dữ liệu (đừng hỏi model): xG/xA, key passes, big chances,
touches, through balls, heatmaps, thời hạn hợp đồng.

## 6. Pipeline Machine Learning (chạy đúng thứ tự)

    .\.venv\Scripts\python.exe src/analytics/eda_report.py
    .\.venv\Scripts\python.exe src/analytics/build_features.py
    .\.venv\Scripts\python.exe src/analytics/player_clusters.py
    .\.venv\Scripts\python.exe src/analytics/player_similarity.py
    .\.venv\Scripts\python.exe src/analytics/team_clusters.py
    .\.venv\Scripts\python.exe src/analytics/pca_explore.py
    .\.venv\Scripts\python.exe src/analytics/detect_anomalies.py
    .\.venv\Scripts\python.exe src/analytics/analytics_score.py
    .\.venv\Scripts\python.exe src/analytics/market_value.py
    .\.venv\Scripts\python.exe src/analytics/best_xi.py --formation 4-3-3

Phương pháp từng module (số liệu đã kiểm chứng khi chạy):

- **EDA** (`eda_report.py` + `notebooks/C_eda_ml.ipynb`): std `goals_p90` nhóm 0–90'
  gấp 3× nhóm 270–360' (căn cứ shrinkage); corr passes/accurate 0.974,
  duels/aerial 0.998 (căn cứ downweight 0.5).
- **Clustering** (`player_clusters.py`, K-Means + StandardScaler): k outfield 4–8,
  GK 2–5, chọn max silhouette (k=4, ARI ổn định 0.984); nhãn theo z-score centroid.
- **Similarity** (cosine trên z-score L2-norm, block theo vị trí, cross-pos = 0).
- **Team clustering** (K-Means 8 chỉ số/trận, k=3 theo silhouette 0.280).
- **PCA** (giữ 90% phương sai, PC1 25.4%; fit outfield rồi project GK).
- **Anomaly** (IsolationForest theo vị trí + luật cứng + lý do z-score;
  contamination 0.05; ~72 ca gồm Messi/Mbappé do luật bàn thắng).
- **Score** (percentile trong từng vị trí + ROLE_MIX; Spearman overall~output:
  DEF 0.891, MID 0.536, FWD 0.834 trên dữ liệu hiện tại).
- **Market value** (hồi quy log1p; GridSearchCV phân tầng theo vị trí, chọn
  Ridge theo MAE trên tập train; dự báo từng cầu thủ bằng cross-validation).
  Holdout 25%: R² log 0.405, MAE €11.8M, median absolute percentage error 59.7%;
  baseline median theo vị trí có MAE €15.3M. Đây là ước lượng giá trị trong
  dataset, không phải dự báo giá sau giải.
- **Best XI** (ILP PuLP max tổng overall_score + ràng buộc đội hình/ngân sách/quota).

Bằng chứng thực nghiệm đi kèm output: `eda_corr/minutes_bins.csv`,
`cluster_tuning.csv`, `market_value_cv.csv`, `market_value_holdout.csv`,
`score_validation.csv`, `anomaly_tuning.csv`, `club_tier_map.csv`.
**Market value là hồi quy mô tả giá trong dataset**; sai số holdout còn cao,
nên không dùng làm định giá chuyển nhượng hay dự báo giá tương lai.

## 7. Giao diện web

Đen/trắng tối giản, chữ khổ lớn, video/ảnh toàn màn hình. Overview: portal hero
WORLD CUP 2026 (ngày tổ chức, nhà vô địch, CTA) + film solo + khung 3 video
highlight lặp + KPI + leaderboard + Best XI preview. Các trang còn lại: Matches,
Teams, Players/Compare, ML Analytics, Best XI, Match Detail — bảng, radar, bộ lọc,
ảnh cầu thủ, cờ và liên kết giữ nguyên thao tác. Navbar trong suốt, ẩn khi cuộn
xuống, hiện khi cuộn lên. Tôn trọng `prefers-reduced-motion`, không can thiệp
wheel/touch.

Ràng buộc đội hình quá chặt có thể không có nghiệm và ứng dụng sẽ thông báo.
Phạm vi không bao gồm kiểm chứng nguồn dữ liệu bóng đá.

## 8. Kiểm tra nhanh

    .\.venv\Scripts\python.exe tests/ui_smoke.py
    .\.venv\Scripts\python.exe -m compileall -q src tests
    .\.venv\Scripts\python.exe -m pip check
    git diff --check

Smoke test 34 kịch bản: 7 trang, đổi selectbox, 4 chế độ Best XI,
match hợp lệ/không tồn tại, lọc và tìm kiếm.

## 9. Phát triển

CSS tách theo trách nhiệm: style.css (nền chung + navbar), photo_story.css
(hero/portal/film/chapters), table_theme.css (bảng), match_experience.css
(Matches + Match Detail), unified_pages.css, xnrgy.css, best_xi.css.
Component HTML và ánh xạ ảnh dùng chung: media_ui.py, table_ui.py, match_ui.py,
compare_ui.py. Không dùng `import *`; tên snake_case; hằng UPPER_SNAKE_CASE.
