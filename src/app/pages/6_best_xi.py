# -*- coding: utf-8 -*-
"""Trang 6 — Best XI & Analytics Score (doc output tu Nhóm B)."""
import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, "..")
from helpers import ANALYTICS

st.title("⭐ Best XI & Analytics Score")

xi_p = os.path.join(ANALYTICS, "best_xi.csv")
sc_p = os.path.join(ANALYTICS, "analytics_scores.csv")

tab1, tab2 = st.tabs(["🏆 Đội hình tiêu biểu", "📊 Analytics Score"])
with tab1:
    if not os.path.exists(xi_p):
        st.warning("Nhóm B chưa chạy analytics suite.\n\n"
                   "Lệnh: `python src/analytics/build_features.py` rồi "
                   "`python src/analytics/analytics_score.py`, "
                   "`python src/analytics/best_xi.py`")
    else:
        xi = pd.read_csv(xi_p)
        st.dataframe(xi, use_container_width=True, hide_index=True)
        bench_p = os.path.join(ANALYTICS, "best_xi_bench.csv")
        if os.path.exists(bench_p):
            st.subheader("Dự bị")
            st.dataframe(pd.read_csv(bench_p), use_container_width=True,
                         hide_index=True)

with tab2:
    if not os.path.exists(sc_p):
        st.info("Chưa có analytics_scores.csv — Nhóm B chạy analytics_score.py.")
    else:
        sc = pd.read_csv(sc_p)
        pos = st.selectbox("Vị trí", ["Tất cả", "GK", "DEF", "MID", "FWD"])
        show = sc if pos == "Tất cả" else sc[sc["position"] == pos]
        st.dataframe(show.head(50), use_container_width=True, hide_index=True)
