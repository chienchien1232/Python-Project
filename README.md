# 🏆 World Cup Data Analytics & Web App

Dự án phân tích dữ liệu chuyên sâu bóng đá World Cup (FBref Mini) tích hợp các mô hình Machine Learning để khám phá cấu trúc dữ liệu, tìm kiếm cầu thủ tương đồng, phân cụm lối chơi và định giá chuyển nhượng.

---

## 🛠️ Hướng dẫn cài đặt & Thiết lập môi trường (Setup)

Đối với các thành viên trong nhóm sau khi `clone` hoặc `pull` code mới nhất từ GitHub về máy, hãy thực hiện theo các bước dưới đây để chạy dự án:

### Bước 1: Kéo code mới nhất từ Git
Mở Terminal / Command Prompt tại thư mục dự án và chạy:
```bash
git pull origin main
```

### Bước 2: Tạo và kích hoạt môi trường ảo (venv)
Trên Windows:
```bash
python -m venv venv
venv\Scripts\activate
```
Trên macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt các thư viện phụ thuộc (Dependencies)
Sau khi đã kích hoạt môi trường ảo, chạy lệnh sau để cài đặt toàn bộ thư viện cần thiết từ file `requirements.txt`:
```bash
pip install -r requirements.txt
```

> Chỉ làm BƯỚC 2 & 3 ĐÚNG 1 LẦN DUY NHẤT (Khi mới clone/setup dự án):
> - Bước 2 (Tạo venv): Chỉ cần tạo môi trường ảo một lần duy nhất trên máy.
> - Bước 3 (pip install): Chỉ cần cài đặt gói thư viện một lần duy nhất.
Fotball_analys/
├── data/
│   ├── processed/
│   │   ├── csv/                              # ⛔ CHUẨN — không ai đụng          [CẢ NHÓM đọc]
│   │   ├── wc2026_player_match/              # [ĐÃ CÓ] sản phẩm hiện tại         [A1 quản lý]
│   │   ├── analytics/                        # 🟡 MỚI — output ML                [B]
│   │   │   ├── player_features.csv           #     feature store                 [B]
│   │   │   ├── team_features.csv             #                                    [B]
│   │   │   ├── player_clusters.csv           #     3.1                           [B]
│   │   │   ├── similarity_matrix.parquet     #     3.2                           [B]
│   │   │   ├── anomalies.csv                 #     3.4                           [B]
│   │   │   ├── team_clusters.csv             #     3.3                           [B]
│   │   │   ├── analytics_scores.csv          #     3.6a                          [B]
│   │   │   ├── market_value_model.pkl        #     3.6b                          [B]
│   │   │   └── best_xi.csv                   #     3.7                           [B]
│   │   ├── AUDIT_REPORT.md                   # [ĐÃ CÓ]
│   │   └── DATA_DICTIONARY.md                # 🟡 MỚI — hợp đồng cột feature      [B viết, cả nhóm duyệt]
│   │
│   ├── db/
│   │   └── wc2026_full.db                    # 🔵 MỚI — DB cho web               [A1]
│   │
│   └── raw/                                  # [ĐÃ CÓ] nguyên trạng
│       ├── fifa/                             #                                   [A1 tái tạo được]
│       ├── espn/                             #                                   [A1]
│       ├── fifa_training_centre/             #                                   [A1]
│       └── csv_original/                     # backup                            [A1]
│
├── src/
│   ├── __init__.py                           # [ĐÃ CÓ]
│   ├── pipeline/                             # 🔴 KHU VỰC A1 (data engineering)
│   │   ├── fetch_fifa.py                     #     B1 tải FIFA API               [A1]
│   │   ├── build_dataset.py                  #     B2 dựng pms/gk                [A1]
│   │   ├── remap_wc2026_ids.py               #     B3 chuẩn hóa ID               [A1]
│   │   ├── fill_gk_final.py                  #     B4 GK backfill ESPN           [A1]
│   │   ├── fill_fifa_tc.py                   #     B5 FIFA TC backfill           [A1]
│   │   └── validate_dataset.py               #     B6 validation                 [A1]
│   │
│   ├── db/                                   # 🔵 KHU VỰC A1
│   │   └── build_db.py                       #     ETL csv → wc2026_full.db      [A1]
│   │                                         #     (+ --check, views, index)
│   │
│   ├── app/                                  # 🟢 KHU VỰC A2
│   │   ├── app.py                            #     shell Streamlit + get_conn()  [A2]
│   │   ├── style.css                         #                                    [A2]
│   │   └── pages/
│   │       ├── 1_overview.py                 #     KPI + lịch giải               [A2]
│   │       ├── 2_matches.py                  #     lọc trận + timeline           [A2]
│   │       ├── 3_players.py                  #     hồ sơ cầu thủ per-90          [A2]
│   │       ├── 4_teams.py                    #     đội tuyển (+ cụm B nếu có)    [A2]
│   │       ├── 5_goalkeepers.py              #     bảng GK                       [A2]
│   │       └── 6_best_xi.py                  #     đọc output của B              [A2]
│   │
│   ├── analytics/                            # 🟣 KHU VỰC B
│   │   ├── common.py                         #     loader + per-90               [B]
│   │   ├── build_features.py                 #     feature store                 [B]
│   │   ├── pca_explore.py                    #     3.5 PCA                       [B]
│   │   ├── player_clusters.py                #     3.1 KMeans                    [B]
│   │   ├── player_similarity.py              #     3.2 cosine top-K              [B]
│   │   ├── detect_anomalies.py               #     3.4 IsolationForest           [B]
│   │   ├── team_clusters.py                  #     3.3 team styles               [B]
│   │   ├── analytics_score.py                #     3.6a                          [B]
│   │   ├── market_value.py                   #     3.6b (+ disclaimer)           [B]
│   │   └── best_xi.py                        #     3.7 formation builder         [B]
│   │
│   ├── utils/                                # 🟡 CHUNG
│   │   ├── aliases.py                        #     alias tên đội/cầu thủ         [A1 khởi tạo]
│   │   └── io_helpers.py                     #     load/save CSV chuẩn           [A1]
│   │
│   ├── audit_data.py                         # [ĐÃ CÓ] tiện ích audit            [A1]
│   ├── clean_data.py                         # [ĐÃ CÓ] fix csv (idempotent)      [A1]
│   ├── format_prediction_floats.py           # [ĐÃ CÓ] format ML files           [A1]
│   ├── verify_env.py                         # [ĐÃ CÓ] check môi trường          [CHUNG]
│   ├── data_loader.py / utils.py / web.py    # placeholder rỗng → xóa khi dọn    [—]
│   └── __init__.py                           # package marker
│
├── notebooks/
│   ├── A1_schema_check.ipynb                 # ERD + query mẫu DB                [A1]
│   ├── A2_chart_lab.ipynb                    # thử nghiệm biểu đồ plotly         [A2]
│   └── B_feature_exploration.ipynb           # EDA features trước khi ML         [B]
│
├── docs/                                     # 📄 HỢP ĐỒNG CẢ NHÓM
│   ├── PLAN.md                               # plan tổng + checklist milestone   [cả nhóm duyệt]
│   ├── PLAN_NHOM_A.md                        # phân công chi tiết A1/A2          [A1+A2]
│   ├── db_schema.md                          # schema wc2026_full.db             [A1 viết → A2 duyệt]
│   ├── feature_dictionary.md                 # ~25 cột feature + công thức       [B viết → cả nhóm duyệt]
│   └── api_convention.md                     # quy ước app ↔ analytics           [A2+B]
│
├── assets/                                   # wireframe/mockup web              [A2]
├── requirements.txt                          # + streamlit, plotly               [A1 cập nhật]
├── README.md                                 # hướng dẫn chạy 2 lệnh chuẩn       [cả nhóm]
└── .gitignore                                # đã loại plays_full/plays_agg      [ĐÃ CÓ]