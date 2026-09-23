# 🏆 World Cup Data Analytics & Web App

Dự án phân tích dữ liệu chuyên sâu bóng đá World Cup (FBref Mini) tích hợp các mô hình Machine Learning để khám phá cấu trúc dữ liệu, tìm kiếm cầu thủ tương đồng, phân cụm lối chơi và định giá chuyển nhượng.

---

## 🛠️ Hướng dẫn cài đặt & Thiết lập môi trường (Setup)

### Điều kiện tiên quyết
    Python 3.12 trở lên
    git (hoặc tải repo về rồi giải nén)

### Bước 1: Cập nhật mã nguồn (Bỏ qua bước này nếu đã tải và giải nén trước đó)
```bash
git clone -b quoc_anh https://github.com/chienchien1232/Python-Project.git
```

### Bước 2: Tạo môi trường ảo (máy mới)
Trên Windows:
```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```
Trên macOS / Linux:
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### Bước 3: Khởi chạy

```bash
.\run_web.bat
```

Mặc định mở tại http://127.0.0.1:8520/ (Vui lòng đợi khoảng 1 phút). Cấu hình Streamlit đã ẩn sidebar và
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
chứa toàn bộ danh sách phụ thuộc và thư viện cần thiết để khởi chạy dự án.

## Kiểm tra nhanh

    .\.venv\Scripts\python.exe tests/ui_smoke.py
    .\.venv\Scripts\python.exe -m compileall -q src tests
    .\.venv\Scripts\python.exe -m pip check
    git diff --check

Smoke test bao phủ Overview, Matches, Teams, Players/Compare, ML Analytics, Best XI,
Match Detail và trạng thái match hợp lệ/không tồn tại. Bảng, radar, bộ lọc, ảnh cầu thủ,
cờ và các liên kết hiện có giữ nguyên thao tác.

## Phát triển

CSS giao diện được tách theo trách nhiệm: style.css cho nền chung, photo_story.css
cho hero/chuyển cảnh, table_theme.css cho bảng, match_experience.css cho Matches và
Match Detail, cùng các lớp unified_pages.css, xnrgy.css, best_xi.css. Component HTML
và ánh xạ ảnh dùng chung nằm trong media_ui.py, table_ui.py, match_ui.py và
compare_ui.py. Các lớp đều tôn trọng prefers-reduced-motion và không can thiệp
wheel/touch.
