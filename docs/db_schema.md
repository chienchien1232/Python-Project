# Schema — wc2026_full.db

## Dimensions
| Bảng | PK | Cột chính |
|---|---|---|
| teams | team_id | team_name, fifa_code, group_letter, confederation, fifa_ranking_pre_tournament, elo_rating, manager_name |
| players | player_id | player_name, position, club_team, market_value_eur, caps, date_of_birth, height_cm |
| venues | venue_id | stadium_name, city, country, capacity |
| tournament_stages | stage_id | stage_name, is_knockout(0/1) |
| referees | referee_id | referee_name |

## Facts
| Bảng | PK | FK | Ghi chú |
|---|---|---|---|
| matches | match_id | home/away_team_id→teams, stage_id, venue_id, referee_id | 104 trận |
| matches_detailed | match_id | — | bản denormalized có tên |
| match_events | event_id | match_id→matches, player_id→players, team_id | bàn/thẻ/VAR |
| match_lineups | lineup_id | match_id, player_id, team_id | 1 dòng/cầu thủ/trận |
| match_team_stats | (match_id, team_id) | cả hai | possession, shots... |
| player_match_stats | (match_id, player_id) | cả hai + pms.player_team là tên | sản phẩm ML 61 cột |
| goalkeeper_match_stats | (match_id, player_id) | như trên | 14 cột GK |
| player_stats_tournament | player_id | →players | thống kê cả giải |

## Views
- `v_player_totals` — tổng kết per-player (dùng cho bảng xếp hạng web)
- `v_goalkeepers` — chỉ dòng GK đá chính

## Quy ước
- Tất cả snake_case, giữ nguyên tên cột CSV gốc
- Boolean dạng 0/1 · ngày YYYY-MM-DD · phút thi đấu số nguyên (NULL = không rõ)
