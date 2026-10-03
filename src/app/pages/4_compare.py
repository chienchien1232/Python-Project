"""Compatibility redirect for the former standalone Compare page."""
import streamlit as st
from streamlit.errors import StreamlitPageNotFoundError

from page_chrome import setup_page

setup_page("Players & Compare | WorldCup Stats '26")

# Client-side redirect (no full reload) into the merged compare workspace.
try:
    st.switch_page("pages/3_players.py", query_params={"view": "compare"})
except StreamlitPageNotFoundError:
    st.markdown(
        '<a href="/players?view=compare" target="_self" style="color:inherit;font:700 12px Arial;letter-spacing:.12em">'
        'OPEN PLAYER COMPARISON →</a>',
        unsafe_allow_html=True,
    )
