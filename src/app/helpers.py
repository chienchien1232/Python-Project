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
    """Run a read-only SQL query. Results are cached; each caller gets a copy."""
    key = tuple(params) if params else ()
    return _q_cached(sql, key).copy()


@st.cache_data(ttl=600, show_spinner=False)
def _q_cached(sql, params_key):
    con = get_conn()
    if con is None:
        return pd.DataFrame()
    return pd.read_sql(sql, con, params=list(params_key) if params_key else [])


def load_analytics_csv(filename):
    """Doc output cua Nhóm B tu data/processed/analytics/. Tra None neu thieu."""
    result = _load_analytics_csv_cached(filename)
    return result.copy() if result is not None else None


@st.cache_data(ttl=600, show_spinner=False)
def _load_analytics_csv_cached(filename):
    path = os.path.join(ANALYTICS, filename)
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


@st.cache_data(ttl=600, show_spinner=False)
def _similarity_matrix_cached():
    path = os.path.join(ANALYTICS, "similarity_matrix.parquet")
    if not os.path.exists(path):
        return None
    return pd.read_parquet(path)


def load_similarity_matrix():
    """Similarity matrix (cached); each caller gets a copy. None if missing."""
    result = _similarity_matrix_cached()
    return result.copy() if result is not None else None
