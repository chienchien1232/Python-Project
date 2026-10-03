"""Chuan hoa ten + ma doi tuyen dung chung toan bo trang Streamlit.

Gom 6 ban `clean_name` va 4 ban `FLAGS`/`flag()` tung copy-paste o cac page
(match_data, compare_ui, app, 2/3/5/6_*.py) ve mot noi duy nhat de sua 1 cho.
Ban chuan lay theo match_data (xu ly None/NaN + du bo dau day du nhat).
"""
from __future__ import annotations

from typing import Any

import pandas as pd

FLAGS = {
    "Algeria": "DZ", "Argentina": "AR", "Australia": "AU", "Austria": "AT",
    "Belgium": "BE", "Bosnia and Herzegovina": "BA", "Brazil": "BR",
    "Cabo Verde": "CV", "Canada": "CA", "Colombia": "CO", "Congo DR": "CD",
    "Croatia": "HR", "Curaçao": "CW", "Czechia": "CZ", "Côte d'Ivoire": "CI",
    "Ecuador": "EC", "Egypt": "EG", "England": "ENG", "France": "FR",
    "Germany": "DE", "Ghana": "GH", "Haiti": "HT", "IR Iran": "IR",
    "Iraq": "IQ", "Japan": "JP", "Jordan": "JO", "Mexico": "MX",
    "Morocco": "MA", "Netherlands": "NL", "New Zealand": "NZ", "Norway": "NO",
    "Panama": "PA", "Paraguay": "PY", "Portugal": "PT", "Qatar": "QA",
    "Saudi Arabia": "SA", "Scotland": "SCO", "Senegal": "SN",
    "South Africa": "ZA", "South Korea": "KR", "Spain": "ES", "Sweden": "SE",
    "Switzerland": "CH", "Tunisia": "TN", "Türkiye": "TR", "USA": "US",
    "Uruguay": "UY", "Uzbekistan": "UZ",
}


def clean_name(value: Any) -> str:
    """Sua loi encoding ten cau thu/doi (Adrin->Adrian, ...)."""
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return ""
    text = str(value)
    return (
        text.replace("Adrin", "Adrian")
        .replace("Andrs", "Andres")
        .replace("Damin", "Damian")
        .replace("Curaao", "Curacao")
        .replace("Cte d'Ivoire", "Côte d'Ivoire")
        .replace("Trkiye", "Türkiye")
        .replace("Lionel Andrs Messi", "Lionel Messi")
        .replace("Rodrigo Rodri", "Rodri")
        .replace("Kylian Mbappe", "Kylian Mbappé")
    )


def flag(team_name: Any) -> str:
    """Ma doi rut gon (2 ky tu) de hien thi, mac dinh '—'."""
    return FLAGS.get(clean_name(team_name), "—")
