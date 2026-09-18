"""Compatibility redirect for the former standalone Compare page."""
import streamlit as st
from streamlit.errors import StreamlitPageNotFoundError

st.set_page_config(
    page_title="So Sánh Cầu Thủ & Đội Tuyển | WorldCup Stats '26",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# First paint must be dark so page switches never flash white.
st.markdown("<style>html,body,.stApp,#root{background:#050505 !important;color-scheme:dark}</style>", unsafe_allow_html=True)

# Client-side redirect (no full reload) into the merged compare workspace.
try:
    st.switch_page("pages/3_players.py", query_params={"view": "compare"})
except StreamlitPageNotFoundError:
    st.markdown(
        '<a href="/players?view=compare" target="_self" style="color:inherit;font:700 12px Arial;letter-spacing:.12em">'
        'MỞ SO SÁNH CẦU THỦ →</a>',
        unsafe_allow_html=True,
    )
