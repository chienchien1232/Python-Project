"""Editorial presentation around Streamlit's native interactive dataframes."""
from html import escape
from numbers import Integral
from typing import Any

import streamlit as st

def data_table(
    data: Any = None,
    width: Any = "stretch",
    height: Any = "auto",
    *,
    label: str = "Data index",
    **kwargs: Any,
) -> Any:
    """Add a small index heading and roomier rows without replacing the grid.

    All dataframe options and its return value are passed through, including
    column configuration, selection callbacks, keys, and explicit row heights.
    Counting uses only an existing concrete shape; it never materializes a lazy
    dataframe or modifies the supplied records.
    """
    shape = getattr(data, "shape", None)
    # Pandas Styler stores the original dataframe in .data.
    if shape is None and type(data).__module__.startswith("pandas.io.formats.style"):
        shape = getattr(data.data, "shape", None)

    counts = ""
    if isinstance(shape, tuple) and len(shape) >= 2 and all(
        isinstance(value, Integral) for value in shape[:2]
    ):
        rows, columns = shape[:2]
        counts = (
            '<span class="data-table-count">'
            f'<span>{rows:,} {"record" if rows == 1 else "records"}</span>'
            '<span class="data-table-divider" aria-hidden="true">/</span>'
            f'<span>{columns:,} {"field" if columns == 1 else "fields"}</span>'
            "</span>"
        )

    if label or counts:
        st.html(
            '<div class="data-table-meta">'
            f'<span class="data-table-label">{escape(label)}</span>{counts}'
            "</div>"
        )

    kwargs.setdefault("row_height", 44)
    kwargs.setdefault("hide_index", True)
    return st.dataframe(data, width=width, height=height, **kwargs)
