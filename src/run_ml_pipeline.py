from __future__ import annotations
import os
import sys
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from Player_Analysis.player_clustering import cluster_players
    from Player_Analysis.player_similarity import compute_player_similarity
    from Team_Analysis.team_clustering import cluster_teams
    from Player_Analysis.anomaly_detection import detect_player_anomalies
    from ml_data import ensure_result_dir
except ImportError:
    from Player_Analysis.player_clustering import cluster_players
    from Player_Analysis.player_similarity import compute_player_similarity
    from Team_Analysis.team_clustering import cluster_teams
    from Player_Analysis.anomaly_detection import detect_player_anomalies
    from ml_data import ensure_result_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Chạy toàn bộ 4 chức năng ML cho project World Cup."
    )
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--player-min-k", type=int, default=2)
    parser.add_argument("--player-max-k", type=int, default=6)
    parser.add_argument("--team-min-k", type=int, default=2)
    parser.add_argument("--team-max-k", type=int, default=8)
    parser.add_argument("--contamination", default="auto")
    args = parser.parse_args()

    try:
        contamination = float(args.contamination)
    except ValueError:
        contamination = args.contamination

    result_dir = ensure_result_dir()

    print("\n[1/4] Player clustering...")
    player_clusters = cluster_players(
        min_k=args.player_min_k,
        max_k=args.player_max_k,
    )
    player_clusters.to_csv(result_dir / "player_clusters.csv", index=False)

    print("\n[2/4] Player similarity...")
    similarities = compute_player_similarity(top_k=args.top_k)
    similarities.to_csv(result_dir / "player_similarity.csv", index=False)

    print("\n[3/4] Team clustering...")
    team_clusters = cluster_teams(
        min_k=args.team_min_k,
        max_k=args.team_max_k,
    )
    team_clusters.to_csv(result_dir / "team_clusters.csv", index=False)

    print("\n[4/4] Anomaly detection...")
    anomalies = detect_player_anomalies(contamination=contamination)
    anomalies.to_csv(result_dir / "player_anomalies.csv", index=False)

    print("\nPipeline completed.")
    print(f"Results directory: {result_dir}")
    print(f"Player clusters : {len(player_clusters):,} rows")
    print(f"Similarity      : {len(similarities):,} rows")
    print(f"Team clusters   : {len(team_clusters):,} rows")
    print(f"Anomalies       : {int(anomalies['is_anomaly'].sum()):,}")


if __name__ == "__main__":
    main()
