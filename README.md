# 🏆 World Cup Data Analytics & Web App

Dự án phân tích dữ liệu chuyên sâu bóng đá World Cup (FBref Mini) tích hợp các mô hình Machine Learning để khám phá cấu trúc dữ liệu, tìm kiếm cầu thủ tương đồng, phân cụm lối chơi và định giá chuyển nhượng.

---

## 🛠️ Hướng dẫn cài đặt & Thiết lập môi trường (Setup)

Sau khi clone hoặc pull nhánh chien, chạy entrypoint duy nhất của bản bàn giao.

### Bước 1: Cập nhật mã nguồn
```bash
git pull origin chien
```

### Bước 2: Tạo môi trường ảo (máy mới)
Trên Windows:
```bash
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-lock.txt
```
Trên macOS / Linux:
```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
```

### Bước 3: Khởi chạy
```bash
.\start-dashboard.ps1
```

Mặc định mở tại http://127.0.0.1:8520/. Cấu hình Streamlit đã ẩn sidebar và
toolbar mặc định để menu MPA cũ không lóe lên khi tải trang.

## Cấu trúc giao diện

src/app/app.py là entrypoint duy nhất. Các trang hiện hành nằm trong src/app/pages/:

- 1_matches.py — lịch trận, lọc và liên kết Match Detail.
- 2_teams.py — thư mục đội tuyển, thống kê và lịch sử đối đầu.
- 3_players.py — thư mục cầu thủ, hồ sơ ảnh màu và workspace Compare.
- 4_compare.py — redirect tương thích tới /players?view=compare.
- 5_ml_explorer.py — PCA, phân cụm, bất thường và định giá.
- 6_best_xi.py — các chế độ đội hình Best XI.
- 7_match_detail.py — trang chi tiết trận theo match_id.

src/app/static/ chứa ảnh hero, các chương World Cup và bundle Plotly được tham chiếu
trực tiếp. Dữ liệu trong data/ phải được giữ nguyên khi bàn giao. requirements.txt
là danh sách phụ thuộc theo khoảng phiên bản; requirements-lock.txt là bộ phiên bản
đã dùng để kiểm tra bản cuối.

## Kiểm tra nhanh

    .\.venv\Scripts\python.exe tests/ui_smoke.py
    .\.venv\Scripts\python.exe -m compileall -q src tests
    .\.venv\Scripts\python.exe -m pip check
    git diff --check

Smoke test bao phủ Overview, Matches, Teams, Players/Compare, ML Analytics, Best XI,
Match Detail và trạng thái match hợp lệ/không tồn tại. Bảng, radar, bộ lọc, ảnh cầu thủ,
cờ và các liên kết hiện có giữ nguyên thao tác.

## Pipeline Machine Learning (chạy đúng thứ tự)

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

Bằng chứng thực nghiệm đi kèm output trong `data/processed/analytics/`:
`eda_corr/minutes_bins.csv` (căn cứ shrinkage K=270, downweight 0.5),
`cluster_tuning.csv` (silhouette + Davies-Bouldin + ARI),
`market_value_cv.csv` (GridSearchCV 5-fold phân tầng), `market_value_ablation.csv`
(team_win_pct 0.383 vs 0.383 — leakage không đáng kể),
`market_value_calibration.csv` (max raw ratio 23.5x nên phải scale),
`score_validation.csv`, `anomaly_tuning.csv`. Notebook EDA: `notebooks/C_eda_ml.ipynb`.
Market value là ESTIMATE counterfactual (thiếu ground truth sau giải), xem
`market_value_validation.csv` (MAE 53.5%, hit ±25% là 31.2%).

Sơ đồ kiến trúc và luồng dữ liệu: `docs/ARCHITECTURE.md`. Module dùng chung:
`src/app/text_norm.py` (chuẩn hóa tên + mã đội), `src/app/page_chrome.py`
(boilerplate trang: config + CSS + footer).

## Phát triển

CSS giao diện được tách theo trách nhiệm: style.css cho nền chung, photo_story.css
cho hero/chuyển cảnh, table_theme.css cho bảng, match_experience.css cho Matches và
Match Detail, cùng các lớp unified_pages.css, xnrgy.css, best_xi.css. Component HTML
và ánh xạ ảnh dùng chung nằm trong media_ui.py, table_ui.py, match_ui.py và
compare_ui.py. Các lớp đều tôn trọng prefers-reduced-motion và không can thiệp
wheel/touch.
