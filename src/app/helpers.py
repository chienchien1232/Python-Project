# -*- coding: utf-8 -*-
"""Ket noi DB dung chung cho cac trang Streamlit."""
import os
import sqlite3

import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "data", "db", "wc2026_full.db")
ANALYTICS = os.path.join(ROOT, "data", "processed", "analytics")


@st.cache_resource
def get_conn():
    if not os.path.exists(DB):
        st.error("Chưa có database! Chạy lệnh: python src/db/build_db.py")
        return None
    return sqlite3.connect(DB, check_same_thread=False)


def q(sql, params=None):
    con = get_conn()
    if con is None:
        return pd.DataFrame()
    return pd.read_sql(sql, con, params=params or [])
