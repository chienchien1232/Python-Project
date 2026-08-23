# 📋 PLAN DỰ ÁN — FIFA World Cup 2026 Analytics

## Thành viên & vai trò
| Người | Vai trò | Khu vực sở hữu | Nhánh git |
|---|---|---|---|
| **A1** | Database Engineer | `src/pipeline/`, `src/db/`, `src/utils/`, `data/db/` | `chien` (trực tiếp) |
| **A2** | Web Developer | `src/app/**`, `assets/`, `notebooks/A2_*` | `web` → PR vào `chien` |
| **B** | ML/Analytics | `src/analytics/`, `notebooks/B_*` | `analytics` → PR vào `chien` |

⛔ Cấm: đụng `data/processed/csv/` (nguồn sự thật) và khu vực của người khác.
✅ Giao điểm: A2 đọc `data/db/wc2026_full.db` · B xuất ra `data/processed/analytics/`.

## Checklist
### Người A1
- [x] `docs/db_schema.md`
- [x] `src/db/build_db.py` (ETL + index + views + --check)
- [x] Build `wc2026_full.db` (CHECK: PASS)
- [ ] Hỗ trợ query hiệu chỉnh khi A2 cần

### Người A2
- [x] `src/app/app.py` + `helpers.py` + 6 trang
- [ ] CSS polish + test end-to-end + PR nhánh `web`

### Người B
- [x] `common.py` + `build_features.py` → feature store
- [x] 3.5 PCA · 3.1 Clustering · 3.2 Similarity · 3.4 Anomaly · 3.3 Team · 3.6 Score/MV · 3.7 Best XI
- [ ] Chạy toàn bộ suite, ghi kết quả vào `data/processed/analytics/`

## Lệnh chuẩn
```bash
python src/db/build_db.py            # A1: tạo DB cho web
python src/analytics/build_features.py   # B: feature store
python src/analytics/pca_explore.py      # rồi lần lượt các script 3.x
streamlit run src/app/app.py             # A2: dashboard
```
