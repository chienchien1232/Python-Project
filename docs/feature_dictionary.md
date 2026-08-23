# Feature Dictionary — player_features.csv (per-90, lọc ≥90 phút)

Mỗi cầu thủ 1 dòng. `*_p90 = tổng / (phút/90)`. Nguồn: `player_match_stats.csv`.

| Cột | Ý nghĩa | Ghi chú |
|---|---|---|
| player_id / player_name / position / team / nationality | định danh | position: GK/DEF/MID/FWD |
| matches / minutes | số trận, tổng phút | minutes dùng mẫu per-90 |
| total_* + *_p90 (18 cặp) | goals, assists, shots, shots_on_target, passes, accurate_passes, crosses, tackles, interceptions, clearances, blocks, recoveries, duels_won, aerial_duels_won, dribbles_attempted, fouls_committed, fouls_won, offsides | từ FIFA API + ESPN |
| pass_accuracy_pct | accurate/passes ×100 | NULL nếu 0 chuyền |

## gk_features.csv
| Cột | Công thức |
|---|---|
| saves / shots_faced / conceded / clean_sheets / starts / matches / minutes | tổng |
| save_pct | saves/(saves+conceded)×100 |
| saves_p90 | saves/(minutes/90) |

## Không có trong dữ liệu (đừng hỏi model)
xG/xA, key passes, big chances, touches, through balls, duels (tổng), heatmaps.
