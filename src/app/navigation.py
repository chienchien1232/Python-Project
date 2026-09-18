"""Shared, accessible navigation and page-specific visual systems."""
from pathlib import Path
from urllib.parse import urlencode

import streamlit as st
from streamlit.errors import StreamlitPageNotFoundError

# Client-side destinations (resolved relative to the app entrypoint).
NAV_PAGES = (
    ("app.py", "Tổng quan"),
    ("pages/1_matches.py", "Trận đấu"),
    ("pages/2_teams.py", "Đội tuyển"),
    ("pages/3_players.py", "Cầu thủ"),
    ("pages/5_ml_explorer.py", "Phân tích ML"),
    ("pages/6_best_xi.py", "Đội hình tiêu biểu"),
)

# Plain-anchor fallback URLs (used only when page_link cannot resolve,
# e.g. standalone test runs; production always takes the widget path).
PAGE_URLS = {
    "app.py": "/",
    "pages/1_matches.py": "/matches",
    "pages/2_teams.py": "/teams",
    "pages/3_players.py": "/players",
    "pages/5_ml_explorer.py": "/ml_explorer",
    "pages/6_best_xi.py": "/best_xi",
    "pages/7_match_detail.py": "/match_detail",
}


def nav_link(path, label, disabled=False, query_params=None):
    """Page link that navigates client-side (no full reload, no white flash).

    Falls back to a plain anchor only when the Streamlit page registry
    cannot resolve the target (standalone script runs outside the MPA).
    """
    try:
        if query_params:
            st.page_link(path, label=label, disabled=disabled, query_params=query_params)
        else:
            st.page_link(path, label=label, disabled=disabled)
        return
    except StreamlitPageNotFoundError:
        pass
    url = PAGE_URLS.get(path, "/")
    if query_params:
        url += "?" + urlencode({k: str(v) for k, v in dict(query_params).items()})
    st.markdown(
        f'<a class="wc-nav-fallback" href="{url}" target="_self">{label}</a>',
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def _load_nav_css(is_xnrgy_page: bool) -> str:
    root = Path(__file__).resolve().parent
    css_parts = []
    for filename in ("table_theme.css", *(("xnrgy.css", "unified_pages.css") if is_xnrgy_page else ()), "photo_story.css"):
        p = root / filename
        if p.exists():
            css_parts.append(p.read_text(encoding="utf-8"))
    return "<style>" + "\n".join(css_parts) + "</style>"


def render_navigation(active):
    is_xnrgy_page = active not in ("Overview", "Tổng quan")
    st.html(_load_nav_css(is_xnrgy_page))


    edition = (
        '<span class="wc-edition">KHÁM PHÁ DỮ LIỆU <b>↗</b></span>' if is_xnrgy_page
        else '<span class="wc-edition">KHO LƯU TRỮ GIẢI ĐẤU ↗</span>'
    )
    slug = active.lower().replace(" ", "-")
    st.markdown(
        '<div class="xnrg-shell" data-page="' + slug + '">'
        '<span class="xnrg-page-index">WORLD CUP / 2026</span></div>'
        '<div class="wc-scroll-progress" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    # Client-side navbar: tabs + edition only (no brand text).
    # The marker scopes navbar CSS so in-content columns with page links
    # never inherit the pill-bar styling.
    st.markdown('<div class="vc-nav-anchor" aria-hidden="true">navbar</div>', unsafe_allow_html=True)
    nav_cols = st.columns([1, 1, 1, 1, 1, 1, 1.4], gap="small")
    alias_map = {
        "Overview": "Tổng quan",
        "Matches": "Trận đấu",
        "Teams": "Đội tuyển",
        "Players": "Cầu thủ",
        "ML Analytics": "Phân tích ML",
        "Best XI": "Đội hình tiêu biểu",
    }
    normalized_active = alias_map.get(active, active)
    for col, (path, label) in zip(nav_cols[:6], NAV_PAGES):
        is_current = (label == normalized_active)
        with col:
            if path == "app.py":
                # The main script is not resolvable via page_link, so the
                # home item stays a plain anchor (full reload only here).
                st.markdown(
                    f'<a class="wc-nav-home{" is-active" if is_current else ""}" '
                    f'href="/" target="_self">{label.upper()}</a>',
                    unsafe_allow_html=True,
                )
            else:
                nav_link(path, label.upper(), disabled=is_current)
    with nav_cols[6]:
        st.markdown(edition, unsafe_allow_html=True)
    # Scroll-direction watcher: hides the floating navbar when scrolling down,
    # reveals it when scrolling up. Runs inside a tiny collapsed component
    # iframe (markdown HTML cannot carry scripts/handlers) and only toggles a
    # CSS class on the navbar — listeners are passive, native touch, keyboard
    # and chart gestures are untouched. Placed after the nav so the
    # `.vc-nav-anchor + div` pill selector keeps matching the nav columns.
    st.iframe(
        """<script>(function(){var D=null;try{D=window.parent.document;}catch(e){return;}try{var fe=window.frameElement,c=fe&&fe.closest?fe.closest('div[data-testid="stElementContainer"]'):null;if(c)c.style.display="none";}catch(e){}if(!D||D.__vcNavInit)return;D.__vcNavInit=true;var last=0;function cur(){var m=D.querySelector('[data-testid="stMain"]');if(m&&m.scrollHeight>m.clientHeight+4)return m.scrollTop;var w=null;try{w=window.parent;}catch(e){}return (w&&w.scrollY)||D.documentElement.scrollTop||0;}function bar(){var a=D.querySelector(".vc-nav-anchor");if(!a||!a.closest)return null;var c=a.closest('div[data-testid="stElementContainer"]');return (c&&c.nextElementSibling)||null;}function onScroll(){var y=cur();if(y===last)return;var b=bar();if(y>140&&y>last+4){if(b)b.classList.add("vc-nav-hidden");}else if(y<last-4||y<=140){if(b)b.classList.remove("vc-nav-hidden");}last=y;}var m=D.querySelector('[data-testid="stMain"]');if(m)m.addEventListener("scroll",onScroll,{passive:true});try{window.parent.addEventListener("scroll",onScroll,{passive:true,capture:true});}catch(e){}})();</script>""",
        height=8,
        width="stretch",
        tab_index=-1,
    )
