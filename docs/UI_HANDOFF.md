# Bàn giao giao diện WorldCup Stats ’26

Trang **Overview** giữ nguyên cấu trúc dữ liệu và chuỗi ảnh; toàn bộ giao diện dùng hệ
đen/trắng tối giản, chữ mảnh khổ lớn và các vạch ngang dài. Matches, Teams, Players,
Compare, ML Analytics và Best XI dùng cùng hệ biên tập nền tối; các màu trạng thái chỉ
được giữ khi chúng mang ý nghĩa dữ liệu. Hình học sân bóng được vẽ bằng CSS nên giao
diện không phụ thuộc font, ảnh hoặc video ngoài.

Giữ đủ Overview, Matches, Teams, Players, Compare (đường dẫn tương thích), ML Analytics,
Best XI và Match Detail, cùng bảng dữ liệu, biểu đồ, bộ lọc và chức năng tải CSV có sẵn.

## Khởi chạy trên Windows

Môi trường đã tạo tại `.venv` với Python 3.12. Chạy `./start-dashboard.ps1`.
Địa chỉ chuẩn của bản bàn giao là `http://127.0.0.1:8520/`.
Trong `.streamlit/config.toml`, sidebar multipage và toolbar mặc định đã tắt
(`showSidebarNavigation=false`, `toolbarMode=minimal`) để không hiện menu cũ khi tải.

Máy mới: tạo môi trường Python 3.12 rồi cài `pip install -r requirements-lock.txt`
để dùng đúng các phiên bản đã kiểm tra. Dữ liệu trong `data/` phải được giữ cùng dự án.

## Kiểm tra

```powershell
.venv/Scripts/python.exe tests/ui_smoke.py
.venv/Scripts/python.exe -m compileall -q src/app tests
.venv/Scripts/python.exe -m pip check
```

Đã kiểm tra tải 7 trang, đổi các selectbox và chạy cả 4 chế độ Best XI.
Đã xem trực tiếp trang Matches, kiểm tra cuộn, chuyển trang và xác nhận Overview không
nạp lớp giao diện XNRGY. Các điểm gãy responsive có quy tắc riêng cho tablet và mobile.
Không phát hiện lỗi trong các kịch bản này; không phải cam kết mọi tổ hợp dữ liệu đều không lỗi.
Ràng buộc đội hình quá chặt có thể không có nghiệm và ứng dụng sẽ thông báo.

## Lỗi được sửa khi chạy thử

- Thư mục gốc của các trang con sai một cấp, làm mất đường dẫn dữ liệu Best XI/PCA.
- Chưa ghép ngày sinh và cụm chiến thuật vào dữ liệu chọn Best XI.
- Tuổi U23 được tính theo ngày khai mạc 11/06/2026.
- Ngân sách người dùng chọn bị giới hạn ngầm xuống 200 triệu euro.
- Cập nhật thành phần nhúng PCA sang API iframe hiện hành.

Nội dung và kết quả giải đấu trong bộ dữ liệu hiện có được giữ lại;
phạm vi bàn giao này không bao gồm kiểm chứng nguồn dữ liệu bóng đá.

## Hệ giao diện XNRGY và chuyển động

- Bỏ emoji trang trí, thay cờ màu bằng mã quốc gia; icon SVG nét mảnh dùng chung,
  lấy màu từ chữ để hiển thị đen/trắng đồng nhất.
- Tiêu đề và khối nội dung hiện dần theo vị trí cuộn, phát lại khi đi ra rồi quay vào
  vùng nhìn; nền hero dùng hình học đơn sắc và hai dòng chữ tách lớp.
- Menu có hiệu ứng chữ trượt khi hover, nút có chuyển tiếp, thanh mảnh báo tiến độ cuộn.
- Chuyển giữa các trang dữ liệu dùng màn phủ đen/trắng; menu, tab, nút và thẻ dữ liệu
  có chuyển động hover đồng bộ.
- Không chặn thao tác wheel/touch hay thêm thư viện JavaScript. Trình duyệt không hỗ trợ
  scroll timelines vẫn hiển thị đầy đủ nội dung. Chế độ giảm chuyển động của hệ điều hành
  tự tắt hiệu ứng. Bảng, bộ lọc và biểu đồ giữ thao tác gốc.
- Đã chạy lại 24 kịch bản kiểm tra sau thay đổi icon và nhãn chọn chế độ.

## Matches và Match Detail

Hai trang này dùng hệ trình bày riêng lấy cảm hứng từ lịch đua biên tập và chuyển động
nhiều lớp của Palomino. Hero có lưới, vòng tròn và các đường mảnh chuyển ở các
tốc độ khác nhau theo cuộn; nội dung vẫn cuộn tự nhiên và không dùng JavaScript can thiệp
wheel/touch.

- `/matches` hiển thị toàn bộ lịch theo lưới hai cột, có lọc vòng đấu, đội, trạng thái,
  tìm theo đội/thành phố/sân và lọc trận bất thường. Cả thẻ là liên kết bàn phím truy cập được.
- `/match_detail?match_id=<id>` là URL cố định cho từng trận. Refresh, Back và liên kết
  trận trước/sau giữ đúng `match_id`.
- Chi tiết gồm hero tỷ số, tổng quan, so sánh thống kê, timeline, đội hình, hiệu suất cầu thủ,
  facts, sân và điều hướng trận. Dữ liệu thiếu hiển thị trạng thái rỗng thay vì số liệu giả.
- Mã xử lý dữ liệu nằm tại `src/app/match_data.py`, HTML trình bày tại
  `src/app/match_ui.py`, CSS tại `src/app/match_experience.css`, và trang chi tiết tại
  `src/app/pages/7_match_detail.py`.
- Smoke test có thêm ID hợp lệ/không tồn tại, trạng thái Upcoming và tìm kiếm Mexico.

## Photo Story, cờ và chân dung cầu thủ

- Mỗi route dùng photo-story-shell với một hero riêng; Overview có thêm ba chương lịch sử
  và reel tóm tắt bốn khung. Khi cuộn, ảnh giữ trong viewport còn chữ trượt theo tiến độ.
- Các hero và chương ảnh nằm trong `src/app/static/`; Streamlit phục vụ qua `/app/static/`.
- CSS dùng chung nằm trong src/app/photo_story.css, component và bộ tra ảnh nằm trong
  src/app/media_ui.py.
- Cờ lấy theo mã FIFA từ endpoint ảnh chính thức. Chân dung cầu thủ được ánh xạ theo tên
  từ PlayerPicture.PictureUrl trong các JSON FIFA đã có sẵn trong dự án. Tên có dấu,
  tên đệm và biến thể tên ngắn được chuẩn hóa trước khi tra.
- Nếu một cầu thủ không có ảnh nguồn, giao diện giữ khung initials nên bố cục không vỡ.
  Ảnh hồ sơ dùng nguồn FIFA độ phân giải cao 1440×1920 và tải eager; thẻ danh sách
  vẫn dùng biến thể 720×960 tải lười để giữ tốc độ. Cờ và ảnh đang nhìn thấy được
  trình duyệt ưu tiên tải.
- prefers-reduced-motion tắt toàn bộ transform liên quan tới cuộn. Breakpoint mobile
  chuyển tiêu đề về một cột, không gây tràn ngang.

## Giao diện thống nhất cho các trang phân tích

- `src/app/unified_pages.css` đưa Teams, Players, Compare, ML Analytics và Best XI về
  cùng hệ biên tập nền đen của Overview và Matches.
- Lớp này quản lý nhịp tiêu đề, dải KPI, thẻ hồ sơ, bộ lọc, tab, bảng dữ liệu và hiệu ứng
  xuất hiện theo cuộn. Toàn bộ logic Python, dữ liệu và thao tác hiện có được giữ nguyên.
- `navigation.py` tải theme bảng cho mọi route, giao diện thống nhất sau XNRGY và tải lớp photo story cuối cùng để
  hero toàn màn hình cùng thanh điều hướng nổi luôn có cùng cách hiển thị trên mọi trang.

## Rà soát độ rõ tiêu đề bảng

- Mọi bảng đều đi qua `table_ui.data_table`, vì vậy chỉ cần một lớp theme để kiểm soát độ tương phản.
- Streamlit GlideDataEditor vẽ header trên một canvas riêng; các biến `--gdg-text-header`, nền header và font header
  được đặt ở mức dùng chung, đồng thời canvas header có lớp tương phản riêng để tiêu đề cột không bị alpha
  `fadedText60` của Streamlit làm mờ trong các tab đã mở lâu.
- Header dùng chữ 14px, semi-bold, màu sáng rõ; nền và đường kẻ vẫn giữ hệ đen/trắng tối giản.
- Sorting, selection, search, fullscreen, tải CSV và các cột ảnh không bị thay đổi.
- Đã kiểm tra lại Overview, Matches, Teams, Players, ML Analytics, Best XI và Match Detail sau khi chỉnh.

## Visual chapters và chuyển cảnh monochrome

- Overview có ba chương lịch sử dọc và bốn khung tóm tắt. Các trang dữ liệu còn lại giữ một
  hero riêng, để nội dung trượt lên và che phần ảnh theo tiến độ cuộn.
- Sprite ảnh màu nằm tại `src/app/static/football-story-grid-v1.png`; nội dung chữ của
  từng chương thay đổi theo ngữ cảnh Teams, Players, Compare, ML, Best XI hoặc Matches.
- Chuyển route dùng hai mảng đen/trắng rời màn hình theo hướng đối nghịch. Reduced motion
  tắt transform và giữ nội dung ở trạng thái tĩnh, không ảnh hưởng chức năng.
