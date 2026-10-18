# -*- coding: utf-8 -*-
"""Ket noi DB dung chung cho cac trang Streamlit."""
import os
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "data", "db", "wc2026_full.db")
ANALYTICS = os.path.join(ROOT, "data", "processed", "analytics")


def _read_conn():
    """Ket noi SQLite chi-doc moi lan query (an toan da-stream/thread: khong
    dung chung connection). mode=ro chan ghi; mmap cho phep doc file nhanh."""
    if not os.path.exists(DB):
        st.error("Chưa có database! Chạy lệnh: python src/db/build_db.py")
        return None
    uri = "file:///" + Path(DB).as_posix() + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.execute("PRAGMA mmap_size=268435456")
    return con


def q(sql, params=None):
    """Run a read-only SQL query. Results are cached; each caller gets a copy."""
    key = tuple(params) if params else ()
    return _q_cached(sql, key).copy()


@st.cache_data(ttl=600, show_spinner="Đang tải dữ liệu trận đấu...")
def _q_cached(sql, params_key):
    con = _read_conn()
    if con is None:
        return pd.DataFrame()
    try:
        return pd.read_sql(sql, con, params=list(params_key) if params_key else [])
    finally:
        con.close()


def load_analytics_csv(filename, dtype=None):
    """Doc output cua Nhóm B tu data/processed/analytics/. Tra None neu thieu.

    `dtype` (dict hoac None) chi truyen thang cho pandas; cache van 1 duong
    duy nhat qua `_load_analytics_csv_cached` (dict duoc dong bang thanh
    tuple de hash duoc cho st.cache_data).
    """
    frozen = tuple(sorted(dtype.items())) if dtype else None
    result = _load_analytics_csv_cached(filename, frozen)
    return result.copy() if result is not None else None


@st.cache_data(ttl=600, show_spinner="Đang tải kết quả phân tích...")
def _load_analytics_csv_cached(filename, dtype_key):
    path = os.path.join(ANALYTICS, filename)
    if not os.path.exists(path):
        return None
    return pd.read_csv(path, dtype=dict(dtype_key) if dtype_key else None)


@st.cache_data(ttl=600, show_spinner="Đang tải ma trận tương đồng...")
def _similarity_matrix_cached():
    path = os.path.join(ANALYTICS, "similarity_matrix.parquet")
    if not os.path.exists(path):
        return None
    return pd.read_parquet(path)


def load_similarity_matrix():
    """Similarity matrix (cached); each caller gets a copy. None if missing."""
    result = _similarity_matrix_cached()
    return result.copy() if result is not None else None
