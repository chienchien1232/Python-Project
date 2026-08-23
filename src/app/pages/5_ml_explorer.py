# -*- coding: utf-8 -*-
"""TAB ML ADVANCED EXPLORER - Clustering / PCA / Anomaly."""
import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, "..")
from helpers import q, load_analytics_csv  # noqa: E402

st.title("🧠 ML Advanced Explorer")

t1, t2, t3 = st.tabs(["🔗 Player Clustering",
                      "🗺️ PCA Map", "⚡ Anomaly Detection"])

# ---------- Sub-tab 1: Clustering ----------
with t1:
    st.subheader("Giải thích đặc trưng các cụm lối chơi")
    st.markdown("""
    Mô hình **K-Means** tự học từ 18 chỉ số Per-90 và chia cầu thủ thành
    các nhóm vai trò thực tế:

    | Cụm | Đặc trưng nổi bật |
    |---|---|
    | 🎯 Finisher / Goal Scorer | Bàn & sút trúng đích/90 vượt trội |
    | 🧠 Playmaker / Chance Creator | Kiến tạo, tạt bóng, bị phạm lỗi |
    | 🚀 Ball Progressor | Thể tích chuyền bóng cao |
    | 🛡️ Defensive Player | Tắc bóng, cắt bóng, phá bóng |
    | ⚖️ Box-to-Box / All-rounder | Không lệch mạnh về nhóm nào |
    """)

    prof_out = load_analytics_csv("cluster_profile_outfield.csv")
    if prof_out is not None:
        st.markdown("**Centroid trung bình các cụm cầu thủ ngoài sân:**")
        st.dataframe(prof_out, use_container_width=True, hide_index=True)

    clus = load_analytics_csv("player_clusters.csv")
    if clus is not None and "cluster_label" in clus.columns:
        sel_c = st.selectbox("Xem cầu thủ tiêu biểu của cụm:",
                             sorted(clus["cluster_label"].dropna().unique()))
        members = clus[clus["cluster_label"] == sel_c]\
            .sort_values("minutes", ascending=False).head(10)
        st.dataframe(
            members[["player_name", "position", "team", "minutes"]],
            use_container_width=True, hide_index=True)

# ---------- Sub-tab 2: PCA Map ----------
with t2:
    st.subheader("PCA Map — khám phá cấu trúc dữ liệu")
    html_p = os.path.join("..", "..", "data", "processed", "analytics",
                          "pca_interactive.html")
    if os.path.exists(os.path.abspath(html_p)):
        with open(os.path.abspath(html_p), encoding="utf-8") as f:
            html_bytes = f.read()
        import streamlit.components.v1 as components
        components.html(html_bytes, height=620, scrolling=True)
        st.caption("Mỗi chấm = 1 cầu thủ · Màu = cụm ML · Hover để xem chi tiết")
    else:
        st.warning("Chạy `python src/analytics/pca_explore.py` để tạo PCA map.")

# ---------- Sub-tab 3: Anomaly ----------
with t3:
    st.subheader("Anomalous Performance")
    anom = load_analytics_csv("anomalies.csv")
    if anom is None or anom.empty:
        st.warning("Chạy `python src/analytics/detect_anomalies.py`.")
    else:
        show = anom.rename(columns={
            "player_name": "Cầu thủ", "position": "VT", "team": "Đội",
            "minutes": "Phút", "total_goals": "Bàn",
            "nguyen_nhan": "Nguyên nhân (z-score)"})
        if "goals_p90" in show.columns:
            show = show.rename(columns={"goals_p90": "Bàn/90"})
        st.dataframe(show, use_container_width=True, hide_index=True)
        st.caption("σ = độ lệch chuẩn so với mặt bằng chung của cùng vị trí.")
