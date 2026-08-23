# -*- coding: utf-8 -*-
"""Trang 3 — Cầu thủ: tìm kiếm + hồ sơ từng trận."""
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, "..")
from helpers import q

st.title("👤 Cầu thủ")

name = st.text_input("Tìm theo tên:", "")
if name:
    rows = q("""SELECT * FROM player_match_stats
                WHERE player_name LIKE ? ORDER BY match_id""", (f"%{name}%",))
    if rows.empty:
        st.info("Không tìm thấy cầu thủ.")
    else:
        info = rows.iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.write(f"**{info['player_name']}**")
        c2.write(f"Vị trí: {info['position']} · #{info['shirt_number']}")
        c3.write(f"Đội: {info['player_team']} · {info['nationality'] or '-'}")

        show = [c for c in ["match_id", "opponent_team", "minutes_played", "goals",
                            "assists", "shots", "shots_on_target", "passes",
                            "accurate_passes", "pass_accuracy", "tackles",
                            "interceptions", "clearances", "fouls_committed",
                            "fouls_won", "offsides", "yellow_cards", "red_cards"]
                if c in rows.columns]
        sub = rows[show].rename(columns={
            "match_id": "Trận", "opponent_team": "Đối thủ",
            "minutes_played": "Phút", "goals": "Bàn", "assists": "KT",
            "shots": "Sút", "shots_on_target": "Sút trúng đích",
            "passes": "Chuyền", "accurate_passes": "Chuyền chính xác",
            "pass_accuracy": "% chuyền", "tackles": "Tắc bóng",
            "interceptions": "Cắt bóng", "clearances": "Phá bóng",
            "fouls_committed": "Phạm lỗi", "fouls_won": "Được hưởng",
            "offsides": "Việt vị", "yellow_cards": "Thẻ vàng",
            "red_cards": "Thẻ đỏ"})
        st.dataframe(sub, use_container_width=True, hide_index=True)
else:
    st.info("Nhập tên cầu thủ (ví dụ: RANGEL, MESSI, MBAPPÉ...)")
