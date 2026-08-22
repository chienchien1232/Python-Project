# ML Features bổ sung

Các module này thêm 4 chức năng vào project:

1. Player clustering — KMeans, chạy riêng theo nhóm vị trí GK/DF/MF/FW.
2. Player similarity — cosine similarity trên feature vector đã chuẩn hóa, trả về Top-K cầu thủ tương đồng.
3. Team clustering — aggregate thống kê `match_team_stats.csv` theo đội, kết hợp FIFA ranking/Elo.
4. Anomaly detection — Isolation Forest, chạy theo nhóm vị trí.

## Chạy

Từ thư mục root của project:

```bash
pip install -r requirements.txt
python -m src.run_ml_pipeline
```

Hoặc:

```bash
python src/run_ml_pipeline.py
```

Tham số:

```bash
python -m src.run_ml_pipeline --top-k 10 --player-min-k 2 --player-max-k 6 --team-min-k 2 --team-max-k 8
```

Kết quả nằm tại:

```text
data/processed/ml_results/
```

## Sử dụng riêng từng chức năng

```bash
python -m src.Player_Analysis.player_clustering
python -m src.Player_Analysis.player_similarity --top-k 10
python -m src.Team_Analysis.team_clustering
python -m src.Player_Analysis.anomaly_detection
```

## Gọi từ Python

```python
from src.Player_Analysis.player_clustering import find_similar_players

similar = find_similar_players(player_id=123, top_k=10)
print(similar)
```

Thiết kế sử dụng đường dẫn tương đối từ root package, nên dataset cố định tại `data/processed/csv` vẫn hoạt động.
