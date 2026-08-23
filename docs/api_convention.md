# API Convention — quy ước app ↔ analytics

1. **Nguồn đọc của web**: CHỈ `data/db/wc2026_full.db` (do A1 build) — không đọc CSV trực tiếp trong trang.
2. **Output của Nhóm B**: ghi vào `data/processed/analytics/` với tên cố định:
   - `player_features.csv`, `gk_features.csv`, `team_features.csv`
   - `player_clusters.csv`, `cluster_profile_*.csv`
   - `similarity_matrix.parquet`, `pca_loadings.csv`, `pca_biplot.png`
   - `anomalies.csv`, `analytics_scores.csv`
   - `best_xi.csv`, `best_xi_bench.csv`, `market_value_importance.csv`
3. Trang web khi thiếu file output → hiện cảnh báo + lệnh chạy tương ứng, KHÔNG crash.
4. Mọi cột định danh dùng player_id/match_id/team_id (chuẩn CSV); tên chỉ để hiển thị.
5. Thêm bảng/view mới cho web → A2 gửi yêu cầu, A1 bổ sung vào build_db.py + cập nhật db_schema.md.
