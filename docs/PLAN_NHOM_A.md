# PLAN NHÓM A — Data/DB & Web (A1 + A2)

## A1 — Database Engineer
- [x] `docs/db_schema.md` — schema 5 dim + 8 fact + 2 views
- [x] `src/db/build_db.py` — ETL từ csv/ chuẩn → `data/db/wc2026_full.db`
      (PK/FK/index/views `v_player_totals`, `v_goalkeepers`, cờ `--check`)
- [x] Build DB — **CHECK: PASS** toàn bộ bảng khớp CSV nguồn
- [ ] Hỗ trợ query hiệu chỉnh khi A2 cần

## A2 — Web Developer
- [x] `src/app/app.py` (Trang chủ Tổng quan: KPI + vua phá lưới + bàn theo ngày)
- [x] `src/app/helpers.py` (get_conn + q)
- [x] `src/app/pages/2_matches.py` (lọc đội/vòng + timeline sự kiện)
- [x] `pages/3_players.py` (tra cứu cầu thủ per-match)
- [x] `pages/4_teams.py` (thành tích + thống kê + cụm ML nếu có)
- [x] `pages/5_goalkeepers.py` (xếp hạng GK)
- [x] `pages/6_best_xi.py` (đọc output Nhóm B, fallback cảnh báo)
- [ ] CSS polish + test end-to-end + PR nhánh `web`

## Chạy thử
```bash
python src/db/build_db.py          # A1 đã chạy - PASS
streamlit run src/app/app.py       # A2 demo
```
