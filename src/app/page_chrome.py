"""Boilerplate trang Streamlit dung chung (config + first-paint + CSS + footer).

Gom 8 ban copy `set_page_config` + first-paint dark + nap `style.css` + footer
o app.py va pages/*.py ve mot cho. Moi page van tu goi render_navigation
rieng sau setup_page().
"""
from __future__ import annotations

import os

import streamlit as st

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

FOOTER_DEFAULT = (
    "<div style='text-align:center;color:#64748b;font-size:12.5px;padding:20px 0;"
    "border-top:1px solid rgba(255,255,255,0.06)'>"
    "WorldCup Stats '26 Analytics Platform &nbsp;·&nbsp; Data powered by FIFA, "
    "ESPN &amp; official match records &nbsp;·&nbsp; Built with Python &amp; Streamlit"
    "</div>"
)

FOOTER_MATCH = (
    "<div style='text-align:center;color:#686865;font-size:10px;letter-spacing:.08em;"
    "padding:24px 0;border-top:1px solid #292929'>"
    "WORLDCUP STATS '26 &nbsp;·&nbsp; MATCH CALENDAR &nbsp;·&nbsp; FIFA 2026 DATA ARCHIVE"
    "</div>"
)


def setup_page(page_title: str) -> None:
    """Cau hinh trang + first-paint den + nap style.css (giong he 8 page cu)."""
    st.set_page_config(
        page_title=page_title,
        page_icon="◉",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    # First paint must be dark so page switches never flash white.
    st.markdown(
        "<style>html,body,.stApp,#root{background:#050505 !important;color-scheme:dark}</style>",
        unsafe_allow_html=True,
    )
    css_path = os.path.join(APP_ROOT, "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def footer(variant: str = "default") -> None:
    """Chan trang thong nhat (default | match)."""
    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
    st.markdown(FOOTER_MATCH if variant == "match" else FOOTER_DEFAULT,
                unsafe_allow_html=True)
