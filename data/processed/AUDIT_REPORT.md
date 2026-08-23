# AUDIT REPORT — World Cup 2026 Dataset (`data/processed/csv/`)

Ngày audit: 2026-08-23 · Phạm vi: 13 file CSV · Nguyên tắc: **sửa tối thiểu, giữ nguyên cấu trúc**
Backup bản gốc (trước mọi sửa đổi): `data/raw/csv_original/` (13 file)

---

## 1. Dataset overview

| Nhóm | File | Vai trò |
|---|---|---|
| Dimension | `teams.csv` (48), `tournament_stages.csv` (7), `venues.csv` (16), `squads_and_players.csv` (1248) | Master data |
| Fact-match | `matches.csv` (104), `matches_detailed.csv` (104), `match_team_stats.csv` (208) | 1 dòng / trận (team_stats: 2 dòng / trận) |
| Fact-event | `match_events.csv` (601), `match_lineups.csv` (5408) | Sự kiện & đội hình theo trận |
| Player agg | `player_stats.csv` (1248) | Thống kê cả giải theo cầu thủ |
| ML derived | `match_prediction_features{,_X}.csv`, `match_prediction_targets_y.csv` (104 mỗi file) | Bộ dữ liệu train đã sinh |

Sơ đồ quan hệ xác nhận đúng như giả định đề bài:
`teams → squads_and_players → player_stats`; `matches → {lineups, events, team_stats, detailed, prediction_features}`; lookup `stages`, `venues`.

## 2–3. Schema & Primary Keys

Toàn bộ cột đã ở dạng lowercase snake_case — **không cần rename** (mục 11: 0).

| File | PK (đã kiểm chứng UNIQUE 100%) |
|---|---|
| teams / tournament_stages / venues / squads_and_players / player_stats / matches / match_prediction_* | id tương ứng |
| match_lineups | `lineup_id`; đồng thời `(match_id, player_id)` unique |
| match_team_stats | `(match_id, team_id)` |
| match_events | `event_id` |

Kiểu dữ liệu suy diễn: IDs/counts = int; % và rating = numeric; date = YYYY-MM-DD chuẩn 100%.

## 4. Foreign key relationships

20/20 ràng buộc FK kiểm tra **OK, 0 vi phạm**, gồm: matches→teams/stages/venues; lineups→matches/squads/teams; events→matches/squads/teams; team_stats→matches/teams; squads→teams; player_stats→squads/teams; prediction→matches/teams/stages/venues; `matches.player_of_the_match_id → squads`.
Coverage ngược: 104/104 trận có lineups, team_stats, detailed, prediction; **4 trận không có events** (mục 14).

## 5. Cross-file inconsistencies found

1. `kickoff_time_utc` không phải UTC thật (lệch tới nhiều giờ so với lịch chính thức FIFA) — ảnh hưởng `matches`, `matches_detailed`, (và bản copy trong 3 file ML).
2. Boolean 2 hệ: `is_knockout` dùng `True/False` (text) vs `is_starting_xi` dùng `0/1`.
3. Cột `date` là ngày local, sau khi chuẩn UTC giờ sẽ lệch ngày nếu không đồng bộ → đã xử lý cùng lúc.
4. Không có: trùng ID giữa các file, trùng trận, đội/cầu thủ 2 ID, sai vị trí GK/DEF/MID/FWD (thống nhất 3 file).

## 6. Missing values (đáng chú ý)

| File.cột | Thiếu | Xử lý |
|---|---|---|
| player_stats.shots / shots_on_target / average_rating | 100% | Giữ NULL — cột khung cho tương lai, KHÔNG gán 0 |
| player_stats.clean_sheets / saves / goals_conceded | 88% | Đúng ngữ nghĩa: chỉ GK có giá trị |
| player_stats.data_source | 209 (16,7%) | Giữ NULL, không đoán (mục 14) |
| matches(.detailed).home/away_penalty_score | 97% | Đúng: chỉ loạt luân lưu mới có |
| matches_detailed.home/away_goalkeeper | 12 (toàn knock-out) | Giữ NULL — flag |
| match_team_stats.player_of_the_match | 50% | Giữ NULL — flag |

## 7. Duplicate records

0 true duplicate trên toàn bộ 13 file (kể cả key phức hợp). Trùng tên bình thường hóa ("aliahmed", "mc") là 2+ cầu thủ khác người/khác đội hoặc artifact chuẩn hóa — **không phải lỗi dữ liệu**.

## 8. Invalid records

Kiểm tra logic bóng đá: home≠away ✓, tỉ số ≥ 0 ✓, XI luôn = 11/đội/trận (208/208) ✓, không cầu thủ nào đá cho 2 đội trong 1 trận ✓, minutes ∈ [0,130] ✓, phút sự kiện hợp lệ ✓, event.team == team của player trong lineup ✓, tổng bàn theo events == tỉ số 104/104 ✓, goals(events) == goals(player_stats) từng cầu thủ ✓, SoT ≤ Shots (cả cấp player & team) ✓.

## 9. Changes made (tối thiểu — value-level, 0 thay đổi cấu trúc)

| # | Thay đổi | Lý do |
|---|---|---|
| 1 | `tournament_stages.is_knockout`: 7 giá trị `True/False` → `1/0` | Thống nhất 1 hệ boolean toàn dataset |
| 2 | `matches.kickoff_time_utc`: 104/104 giờ → UTC thật | Giá trị sai so với nguồn chính thức; derive an toàn từ `data/raw/fifa/calendar.json` |
| 3 | `matches.date`: 42/104 → ngày UTC tương ứng | Tránh mâu thuẫn date↔time phát sinh sau fix #2 |
| 4 | `matches_detailed`: giống #2+#3 (91 giờ + 42 ngày) | Nhất quán giữa 2 file trận |

Script: `src/clean_data.py` (idempotent). Audit script: `src/audit_data.py`.

## 10. Files NOT modified

`squads_and_players.csv`, `player_stats.csv`, `teams.csv`, `venues.csv`, `match_lineups.csv`, `match_events.csv`, `match_team_stats.csv`,
**3 file ML** `match_prediction_features{,_X}.csv`, `match_prediction_targets_y.csv` (derived datasets — không đụng theo yêu cầu mục 5).
Lưu ý: 3 file ML vẫn chứa kickoff/date cũ — nếu retrai mô hình cần quyết định riêng có đồng bộ hay không.

## 11–13. Renames / Types / ID-fixes

- Cột renamed: **0** (đã snake_case chuẩn sẵn).
- Kiểu dữ liệu: boolean thống nhất về `0/1` int (mục 9#1); còn lại đã chuẩn.
- ID inconsistencies fixed: **0** — không phát hiện xung đột ID nào giữa các file.

## 14. Unresolved problems (flag, không tự fix)

1. **4 trận không có event nào**: #13, #47, #69, #96 — đều 0-0. Nguồn gốc bộ events này không ghi substitution/VAR/shootout đầy đủ (chỉ Goal/Assist/Card/OG/Penalty-shootout). Khuyến nghị thay bằng events từ nguồn FIFA đã tải (`data/raw/fifa/`, 1824 sự kiện đầy đủ hơn).
2. `player_stats` thiếu hoàn toàn shots/rating; 209 dòng không rõ data_source.
3. 12 GK knock-out + 104 POTM ở team_stats trống.
4. Encoding: tên UTF-8 chuẩn (nghi ngờ mojibake ban đầu chỉ là lỗi hiển thị console — đã xác minh bằng hexdump).

0c. **[Chuẩn hóa ID cho `data/processed/wc2026_player_match/`]** Theo quy ước *file CSV là chuẩn*: toàn bộ `player_id` trong 4 file (player_match_stats, goalkeeper_match_stats, match_events, players) đã đổi từ FIFA IdPlayer (vd 485070) sang ID chuẩn CSV 1–1248. Mapping 1:1 đầy đủ 1248/1248 (ghép theo đội + tên; phần dư ghép theo vị trí; lưu tại `id_mapping_fifa_to_csv.json`). `match_id` vốn đã chuẩn (1–104). `players.csv` giữ thêm cột `fifa_player_id` để truy vết nguồn. **Flag:** 2 nhóm không phân biệt được ở nguồn chuẩn — Scotland 3 tiền vệ tên hỏng "Mc" (290/293/309, gán theo thứ tự ID), Jordan 1 ca lệch cả tên lẫn vị trí giữa 2 nguồn (FIFA Ibrahim Sadeh vs csv #1016 Ali Hasan Mohammad, map theo loại trừ) — chi tiết `id_conflicts.json`. Lưu ý: nếu chạy lại `build_dataset.py` phải chạy tiếp `remap_wc2026_ids.py` để chuẩn hóa ID. Phát hiện phụ: file GK từng bị đặt nhầm `goalkeeper_match_stats.csv.csv`, đã đổi về đúng tên.

0d. **[Backfill GK stats]** 6 cột GK rỗng: `saves` + `shots_faced` đã fill cho 212/212 dòng GK thi đấu từ ESPN API (`site.api.espn.com`, per-player stats; nguồn ghi `+espn.com`). `penalty_saves/punches/high_claims/errors` không nguồn nào công bố → giữ NULL. `goals_conceded_on_pitch` GIỮ giá trị suy luận nội bộ (theo khoảng phút trên sân): đối chiếu chéo 208 GK với ESPN phát hiện 4 sai lệch, kiểm chứng bằng dữ kiện bàn thắng xác nhận **4/4 phía ta đúng** (2 ca ESPN đếm nhầm bàn cả trận cho GK thay người chỉ chơi 30'/2', 2 ca số liệu ESPN lỗi). 415 dòng dự bị không ra sân để trống theo thiết kế.

0e. **[De-dup + fill `player_match_stats`]** Đã xóa 3 file trùng trong `wc2026_player_match/` (`matches`, `match_events`, `players` + parquet tương ứng; SQLite rebuild còn 2 bảng) — FK toàn vẹn sau xóa, mọi ID tham chiếu về chuẩn CSV. Fill missing: `date_of_birth`+`nationality` 100% từ CSV chuẩn (squads/teams); từ ESPN per-player (join khóa match_id+home/away+số áo, khớp 5323/5323): `fouls_committed`, `fouls_won`, `shots`, `shots_on_target` = 100%, `offsides` 88%. Cross-check với giá trị sẵn có: assists lệch 86 ca (tiêu chí attribution khác nguồn — giữ giá trị sofascore đã validate), yellow_cards lệch 2 ca (giữ giá trị FIFA). **34 cột vẫn rỗng** (xG/xA/passes/duels/touches/big_chances...) — không nguồn công khai truy cập được, giữ NULL theo nguyên tắc.

0f. **[Săn mọi nguồn cho GK stats]** Kết quả rà soát TOÀN BỘ nguồn cho 6 cột GK: (1) `penalty_saves` — giải có **0 quả phạt đền bị cản phá trong 90'+ET'** (16 penalty đều ghi/trượt); 5 pha cản phá chỉ xảy ra ở loạt luân lưu → đã tách riêng `shootout_saves_reference.json`, không trộn vào cột; giá trị 0 là sự kiện thực tế, fill đủ 627/627. (2) `punches` — lấy từ play-by-play ESPN core API + commentary: chỉ 2 pha punch được ghi nhận toàn giải (trận 20, 33), còn lại = 0 thực tế; fill đủ. (3) `minutes_played` NULL cuối cùng (3 ô) — lấy từ `match_lineups.csv` chuẩn. (4) `high_claims` & `errors`: **không nguồn công khai nào ghi nhận** (FIFA API ✗, ESPN roster ✗, core plays ✗ không có type, commentary ✗, Sofascore chặn mạng, FBref không công bố cấp trận & vi phạm ToS nếu scrape) → giữ NULL vĩnh viễn trừ khi có nguồn Opta trả phí. Nguồn phụ trợ lưu tại `data/raw/espn/plays_full/` (104 file play-by-play đầy đủ ~1.3k events/trận).

0g. **[Fill missing `player_match_stats` — vòng cuối]** (1) `minutes_played`: điền nốt 154 ô từ `match_lineups.csv` chuẩn → cột đầy đủ 100%. (2) 2041 dòng dự bị không ra sân: điền giá trị 0 thực tế cho mọi cột hành động. (3) Đã thử khai thác play-by-play ESPN core API (~135k events, lọc period+sort) để tính tackles/interceptions/clearances/crosses/key_passes/dribbles/dispossessed/xG... nhưng phát hiện endpoint **chỉ trả 400 sự kiện đầu/trận** (phân trang & lọc type bị bỏ qua phía items) → độ phủ ~25-55% → **LOẠI vì undercount sẽ biến dạng dữ liệu**; raw giữ lại `data/raw/espn/plays_agg/` chỉ dùng tham khảo. Kết quả cuối: các cột có nguồn = 100%; **34 cột advanced vẫn NULL cho 3282 dòng cầu thủ thi đấu** (xG/xA/passes/duels/touches/...) — chỉ Opta/FBref-level mới có, chưa truy cập được hợp pháp từ máy.

0h. **[FIFA Training Centre — lấp 15 cột advanced]** Nguồn phát hiện mới: Kaggle `heshamelalamy47/worldcup-2026-open-data` (tải được không cần auth, 5.2MB) — cấu trúc hóa **báo cáo sau trận chính thức FIFA Training Centre** với 21 bảng: match_appearances 5392 dòng, in-possession distributions, out-of-possession, attempts_at_goal... Đã map 104/104 trận (team-pair+date) và điền vào `player_match_stats` cho 3280/3282 dòng cầu thủ thi đấu: `passes`, `accurate_passes`, `pass_accuracy`, `crosses`, `accurate_crosses`, `dribbles_attempted`, `tackles`, `tackles_won`, `interceptions`, `clearances`, `blocks`, `recoveries`, `aerial_duels_won`, `duels_won` = **100%**; `shots_off_target` + `blocked_shots` từ outcomes của attempts table (=100% cho played); `offsides` còn 215 ô (đã zero phần phút=0). 2 dòng còn thiếu (Rashford/Toney vào sân 96' trận chung kết) không có trong báo cáo FIFA TC → NULL. FBref cross-check: **403 cứng kể cả webfetch** → bỏ qua có căn cứ. Vẫn NULL: xg/xa, big_chances*, touches*, long_balls/through_balls, chances_created, duels(total), aerial_duels(total), successful_dribbles, dispossessed, possession_lost, errors_leading_to_* — chỉ Opta/SkillCorner trả phí mới có.

0i. **[Schema: xóa cột trống theo yêu cầu]** 18 cột không mang thông tin (mọi giá trị chỉ là rỗng/0-dự-bị: xg, xa, big_chances*, touches*, key_passes, long_balls*, through_balls, chances_created, duels(total), aerial_duels(total), successful_dribbles, dispossessed, possession_lost, errors_leading_to_*) đã bị xóa khỏi `player_match_stats.csv` theo lệnh trực tiếp của chủ sở hữu — schema 79→61 cột; parquet/SQLite đồng bộ. Nếu sau này có nguồn Opta-level, có thể thêm lại từ pipeline.

0j. **[Chuẩn hóa tên cầu thủ]** Toàn bộ `player_name` trong `player_match_stats` (5153 dòng) + `goalkeeper_match_stats` (608 dòng) đã đổi từ kiểu FIFA "Raul RANGEL" (HOA, không dấu) về **định dạng chuẩn của CSV gốc**: Title Case có đầy đủ dấu ("José Raúl Rangel") — join chính xác theo player_id, 0 dòng lệch. Đồng thời khôi phục delimiter dấu phẩy cho 2 file bị Excel lưu thành `;`. Backup: `csv_original/wc2026_before_name_fix/`.

0k. **[Cleanup dự án]** Đã xóa: `src/tmp_*.py` (rác agent), `src/main.py` (scraper cũ, theo lựa chọn chủ sở hữu), `downloaded_files/`, `data/raw/espn/plays/` (bản 400-events lỗi thời). Giữ nguyên placeholder rỗng (`data_loader/utils/web/__init__`) theo ý chủ sở hữu. Viết lại `validate_dataset.py`: phạm vi mới gồm PK/FK 10 file CSV chuẩn + pms/gk ↔ chuẩn + goals==scores + minutes numeric — **TOÀN BỘ PASS**. FINAL_REPORT.txt sinh lại phản ánh đúng hiện trạng.

## Cấu trúc code cuối cùng (src/)
```
fetch_fifa.py            # B1: tải raw FIFA API (104 trận)
build_dataset.py         # B2: dựng wc2026_player_match (FIFA ids)
remap_wc2026_ids.py      # B3: chuẩn hóa ID theo csv (bắt buộc chạy sau B2)
fill_gk_final.py         # B4: backfill GK stats từ ESPN
fill_fifa_tc.py          # B5: backfill passes/tackles/... từ FIFA TC
validate_dataset.py      # B6: validation cuối
audit_data.py            # tiện ích audit csv chuẩn
clean_data.py            # tiện ích fix kickoff/boolean (idempotent)
format_prediction_floats.py  # tiện ích format ML files
verify_env.py            # kiểm tra môi trường
data_loader.py / utils.py / web.py / __init__.py  # placeholder khung gốc
```

## 15. Recommendations

0b. **[ĐÃ GIẢI QUYẾT — re-audit `match_team_stats.csv`]** Kiểm tra chuyên sâu xác nhận: ID đánh số chính xác 100% (match_id đủ 1–104, không trùng/thiếu; mọi `(match_id, team_id)` thuộc đúng cặp home/away của trận; mỗi trận đúng 1 dòng home + 1 dòng away). Ô trống duy nhất: `player_of_the_match` 104/208 (theo thiết kế — chỉ ghi ở dòng đội có người nhận giải). **Lỗi possession đã được vá:** 24/104 trận có `possession_pct` hai đội cộng lại ≠ 100% (81–90%) → đã thay bằng giá trị chính thức từ ESPN (`site.api.espn.com`, 24 trận × 2 đội = 48 ô), đồng bộ `data_source` của 48 dòng đó thành `...+espn.com`. Toàn bộ cột `possession_pct` chuẩn hóa 1 chữ số thập phân (ROUND_HALF_UP). Sau vá: **104/104 trận tổng possession = 100.0**.


1. Thay `match_events.csv` bằng bản tổng hợp từ FIFA raw (đã có sẵn) để đủ substitution/VAR/shootout-miss.
2. Bổ sung `player_match_stats` từ `data/processed/wc2026_player_match/player_match_stats.parquet` (5323 dòng, đã build & validate): **có thể sinh nội bộ** minutes_played/goals/assists/cards/starter/captain; **cần nguồn ngoài** shots/passes/xG/xA/duels/touches/GK-detail (FIFA API không công bố; Sofascore/ESPN bị chặn mạng tại máy hiện tại).
3. Khi retrai ML: đồng bộ lại cột date/kickoff của 3 file prediction với core, hoặc tách feature thời gian ra pipeline riêng.
4. Thêm `data_source`/`last_verified` cho các dòng player_stats còn thiếu khi có nguồn xác nhận.
5. Giữ nguyên backup `data/raw/csv_original/` làm snapshot bất biến.
