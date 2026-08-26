# -*- coding: utf-8 -*-
"""WorldCup Stats '26 - SPA shell: st.navigation, chuyen tab khong reload, khong sidebar."""
import os

import streamlit as st

st.set_page_config(page_title="WorldCup Stats '26", page_icon="⚽", layout="wide", initial_sidebar_state="collapsed")

# CSS toan cuc (inject 1 lan)
_css = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
if os.path.exists(_css):
    with open(_css, "r", encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

home = st.Page("views/0_home.py", title="Overview", url_path="home", default=True)
matches = st.Page("views/1_matches.py", title="Matches", url_path="matches")
teams = st.Page("views/2_teams.py", title="Teams", url_path="teams")
players = st.Page("views/3_players.py", title="Players", url_path="players")
compare = st.Page("views/4_compare.py", title="Compare", url_path="compare")
ml = st.Page("views/5_ml_explorer.py", title="ML Analytics", url_path="ml_explorer")
best_xi = st.Page("views/6_best_xi.py", title="Best XI", url_path="best_xi")

pg = st.navigation([home, matches, teams, players, compare, ml, best_xi],
                   position="hidden")

# ── Top bar: 1 hang cao - brand + 7 tab co icon + search ──
_cols = st.columns([1.75, 1.06, 1.0, 0.98, 1.02, 1.0, 1.18, 1.0])
with _cols[0]:
    st.markdown('<div class="wc-brand">WorldCup <span class="wc-brand-badge">Stats &#39;26</span></div>', unsafe_allow_html=True)
_NAV = [(home, "Overview"), (matches, "Matches"), (teams, "Teams"),
           (players, "Players"), (compare, "Compare"), (ml, "ML Analytics"),
           (best_xi, "Best XI")]
for _c, (_pgo, _label) in zip(_cols[1:8], _NAV):
    with _c:
        st.page_link(_pgo, label=_label)

pg.run()
