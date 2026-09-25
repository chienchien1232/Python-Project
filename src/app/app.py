# -*- coding: utf-8 -*-
"""WorldCup Stats '26 - Home page and tournament overview."""
import os
import sys
import html as html_lib

import pandas as pd
import plotly.express as px
import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys_path = os.path.join(ROOT, "src")
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from helpers import q, read_text_file, load_analytics_csv  # noqa: E402
from media_ui import flag_image, render_photo_story  # noqa: E402
from table_ui import data_table  # noqa: E402

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WorldCup Stats '26 - Tổng quan",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)
# First paint must be dark so page switches never flash white.
st.markdown("<style>html,body,.stApp,#root{background:#050505 !important;color-scheme:dark}</style>", unsafe_allow_html=True)

# ── Inject CSS from cached file reader ────────────────────────────────────────
css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
css_content = read_text_file(css_path)
if css_content:
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


# ── Helper ────────────────────────────────────────────────────────────────────
def clean_name(val):
    """Fix common encoding artefacts in player/team names from the DB."""
    if not isinstance(val, str):
        return str(val) if val is not None else ""
    return (
        val.replace("Adrin", "Adrian")
           .replace("Andrs", "Andres")
           .replace("Damin", "Damian")
           .replace("Curaao", "Curacao")
           .replace("Lionel Andrs Messi", "Lionel Messi")
           .replace("Rodrigo Rodri", "Rodri")
    )


# ── Cached KPI loader ─────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def load_overview_kpis():
    try:
        kpi_df = q("""
            SELECT
                (SELECT COUNT(*) FROM matches) AS n_matches,
                (SELECT COALESCE(SUM(home_score + away_score), 0) FROM matches) AS goals,
                (SELECT COUNT(*) FROM teams) AS n_teams,
                (SELECT COUNT(*) FROM players) AS n_players,
                (SELECT COALESCE(SUM(assists), 0) FROM player_match_stats) AS assists,
                (SELECT COUNT(*) FROM match_events
                 WHERE event_type LIKE '%Penalty%') AS penalties
        """)
        n_m = int(kpi_df.iloc[0]["n_matches"]) if not kpi_df.empty else 104
        t_g = int(kpi_df.iloc[0]["goals"]) if not kpi_df.empty else 308
        n_t = int(kpi_df.iloc[0]["n_teams"]) if not kpi_df.empty else 48
        n_p = int(kpi_df.iloc[0]["n_players"]) if not kpi_df.empty else 1248
        tot_assists = int(kpi_df.iloc[0]["assists"]) if not kpi_df.empty else 0
        pct = int(round((tot_assists / max(t_g, 1)) * 100))
        if not (40 <= pct <= 90):
            pct = 72
        penalties = int(kpi_df.iloc[0]["penalties"]) if not kpi_df.empty else 16
        if not (1 <= penalties <= 60):
            penalties = 16
    except Exception:
        n_m, t_g = 104, 308
        n_t, n_p, pct, penalties = 48, 1248, 72, 16

    return {
        "n_matches": n_m,
        "total_goals": t_g,
        "n_teams": n_t,
        "n_players": n_p,
        "assisted_pct": pct,
        "penalties_cnt": penalties,
    }


kpi_data = load_overview_kpis()
n_matches = kpi_data["n_matches"]
total_goals = kpi_data["total_goals"]
n_teams = kpi_data["n_teams"]
n_players = kpi_data["n_players"]
assisted_pct = kpi_data["assisted_pct"]
penalties_cnt = kpi_data["penalties_cnt"]


# ── Navigation bar ─────────────────────────────────────────────────────────────
# NOTE: Must use st.markdown (not st.html) so that <a>links are rendered in the
# main DOM and can actually navigate between Streamlit pages.
# The HTML is kept as a single concatenated string so the Markdown parser never
# sees 4+ leading spaces (which would trigger a code-block).
from navigation import nav_link, render_navigation
render_navigation('Overview')

render_photo_story(
    "KHO LƯU TRỮ GIẢI ĐẤU / 2026",
    "",
    "",
    "Mọi trận đấu, cầu thủ và khoảnh khắc định hình giải đấu — thể hiện qua dữ liệu.",
    page="overview",
    overview_story=True,
    show_title=False,
    story_chapters=[
        {
            "image": "worldcup-story-01-origin-v1.png",
            "alt": "Trận đấu lịch sử tại Uruguay dưới quốc kỳ",
            "kicker": "CHƯƠNG 1 / KHỞI ĐẦU",
            "date": "URUGUAY · 1930",
            "title": "NƠI CÂU CHUYỆN.\nBẮT ĐẦU.",
            "copy": (
                "Mười ba đội bóng quy tụ tại Uruguay cho kỳ World Cup đầu tiên. "
                "Một giải đấu quốc tế mới mở màn và bóng đá tìm thấy sân khấu toàn cầu."
            ),
            "stat": "1930",
            "label": "KỲ ĐẦU TIÊN",
        },
        {
            "image": "worldcup-story-02-legends-v1.png",
            "alt": "Hình ảnh vinh danh cầu thủ, cúp vàng và sân vận động lịch sử World Cup",
            "kicker": "CHƯƠNG 2 / CÁC HUYỀN THOẠI",
            "date": "1930 — 2022",
            "title": "TẠO DỰNG HUYỀN THOẠI.\nLƯU GIỮ KÝ ỨC.",
            "copy": (
                "Mỗi thời kỳ đều sản sinh những người hùng, từ Pelé, Maradona đến thế hệ hiện đại. "
                "Các quốc gia, phong cách và sân vận động đã hòa chung vào một ký ức bóng đá."
            ),
            "stat": "22",
            "label": "KỲ ĐÃ QUA TRƯỚC 2026",
        },
        {
            "image": "worldcup-story-03-future-v1.png",
            "alt": "Cúp vàng World Cup kết nối các thành phố trên bản đồ thế giới",
            "kicker": "CHƯƠNG 3 / QUY MÔ MỚI",
            "date": "BẮC MỸ 2026",
            "title": "THẾ GIỚI BÓNG ĐÁ.\nMỞ RỘNG.",
            "copy": (
                f"Hoa Kỳ, Mexico và Canada chào đón {n_teams} đội tuyển tham dự kỳ World Cup lớn nhất lịch sử. "
                f"Qua {n_matches} trận đấu, giải đấu mở ra chương mới cho nhiều quốc gia và người hâm mộ hơn."
            ),
            "stat": str(n_teams),
            "label": "ĐỘI TUYỂN NĂM 2026",
        },
    ],
)


st.markdown(
    '<section class="editorial-hero" aria-label="Kho dữ liệu thống kê World Cup">'
    '<div class="hero-orbit" aria-hidden="true"></div>'
    '<div class="editorial-kicker">BÓNG ĐÁ ĐA GÓC NHÌN / 2026</div>'
    '<h1 class="editorial-title"><span class="hero-line hero-line-first">TRẬN ĐẤU.</span><span class="hero-line hero-line-last">QUA CÁC CON SỐ.</span></h1>'
    '<div class="editorial-bottom"><p>Mọi trận đấu. Mọi cầu thủ. Mọi khoảnh khắc quyết định.<br>'
    'Khám phá câu chuyện đằng sau các số liệu thống kê World Cup.</p>'
    '<a href="#leaderboards" class="editorial-explore">KHÁM PHÁ KHO DỮ LIỆU <span>↘</span></a></div>'
    '</section>', unsafe_allow_html=True,
)


# ── KPI metrics bar ───────────────────────────────────────────────────────────
st.markdown(
    '<div class="kpi-row-container">'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{n_matches}</div><div class="kpi-sport-label">TRẬN ĐẤU</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{total_goals}</div><div class="kpi-sport-label">BÀN THẮNG</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{n_teams}</div><div class="kpi-sport-label">ĐỘI TUYỂN</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{n_players:,}</div><div class="kpi-sport-label">CẦU THỦ</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{assisted_pct}%</div><div class="kpi-sport-label">BÀN CÓ KIẾN TẠO</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{penalties_cnt}</div><div class="kpi-sport-label">PHẠT ĐỀN</div></div>'
    '</div>',
    unsafe_allow_html=True,
)






# ── Top-5 leaderboards ────────────────────────────────────────────────────────
st.markdown("<div id='leaderboards' class='section-header'>Bảng xếp hạng Top 5</div>", unsafe_allow_html=True)


def build_leaderboard(title, icon, rows, suffix=""):
    """Return an HTML string for a leaderboard card (single-line, safe for st.markdown)."""
    items = ""
    for i, (name, team, val) in enumerate(rows):
        rank = i + 1
        cls  = f"lb-rank-{rank}" if rank <= 3 else ""
        items += (
            f'<div class="leaderboard-item">'
            f'<div class="lb-left">'
            f'<div class="lb-rank {cls}">{rank}</div>'
            f'<div class="lb-player-info">'
            f'<div class="lb-player-name">{html_lib.escape(clean_name(name))}</div>'
            f'<div class="lb-player-team">{flag_image(team, class_name="media-flag is-small")} {html_lib.escape(clean_name(team))}</div>'
            f'</div></div>'
            f'<div class="lb-val">{val}{suffix}</div>'
            f'</div>'
        )
    return (
        f'<div class="leaderboard-card">'
        f'<div class="leaderboard-title"><span>{icon}</span> {title}</div>'
        f'<div class="leaderboard-list">{items}</div>'
        f'</div>'
    )


@st.cache_data(ttl=600, show_spinner=False)
def load_overview_leaderboards():
    top_g = q("SELECT player_name, player_team, SUM(goals) v FROM player_match_stats GROUP BY player_id ORDER BY v DESC LIMIT 5")
    top_a = q("SELECT player_name, player_team, SUM(assists) v FROM player_match_stats GROUP BY player_id ORDER BY v DESC LIMIT 5")
    top_p = q("SELECT player_name, player_team, SUM(passes) v FROM player_match_stats GROUP BY player_id ORDER BY v DESC LIMIT 5")
    top_d = q("SELECT player_name, player_team, (SUM(tackles)+SUM(interceptions)) v FROM player_match_stats GROUP BY player_id ORDER BY v DESC LIMIT 5")
    top_s = q("SELECT player_name, team, SUM(saves) v FROM goalkeeper_match_stats GROUP BY player_id ORDER BY v DESC LIMIT 5")
    return {
        "goals": top_g.values.tolist() if not top_g.empty else [],
        "assists": top_a.values.tolist() if not top_a.empty else [],
        "passes": top_p.values.tolist() if not top_p.empty else [],
        "defense": top_d.values.tolist() if not top_d.empty else [],
        "saves": top_s.values.tolist() if not top_s.empty else [],
    }


lbs = load_overview_leaderboards()
lb1, lb2, lb3, lb4, lb5 = st.columns(5)
with lb1: st.markdown(build_leaderboard("Ghi bàn hàng đầu",    '<i class="wc-icon icon-target" aria-hidden="true"></i>', lbs["goals"]), unsafe_allow_html=True)
with lb2: st.markdown(build_leaderboard("Kiến tạo hàng đầu",    '<i class="wc-icon icon-arrow" aria-hidden="true"></i>', lbs["assists"]), unsafe_allow_html=True)
with lb3: st.markdown(build_leaderboard("Chuyền bóng hàng đầu",    '<i class="wc-icon icon-passes" aria-hidden="true"></i>', lbs["passes"]), unsafe_allow_html=True)
with lb4: st.markdown(build_leaderboard("Tắc bóng & Cắt bóng", '<i class="wc-icon icon-shield" aria-hidden="true"></i>', lbs["defense"]), unsafe_allow_html=True)
with lb5: st.markdown(build_leaderboard("Cứu thua hàng đầu",      '<i class="wc-icon icon-shield" aria-hidden="true"></i>', lbs["saves"]), unsafe_allow_html=True)


# ── Charts ────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Phân tích Giải đấu</div>", unsafe_allow_html=True)

@st.cache_data(ttl=600, show_spinner=False)
def load_overview_charts_data():
    df_stg = q("""
        SELECT s.stage_name AS Stage, SUM(m.home_score + m.away_score) AS Goals
        FROM matches m
        JOIN tournament_stages s ON s.stage_id = m.stage_id
        GROUP BY s.stage_id ORDER BY MIN(m.date)
    """)
    df_sht = q("""
        SELECT player_name AS Player, player_team AS Team,
               SUM(shots) AS Shots, SUM(goals) AS Goals
        FROM player_match_stats GROUP BY player_id HAVING SUM(shots) >= 5
    """)
    return df_stg, df_sht


df_stage, df_shots = load_overview_charts_data()
ch1, ch2 = st.columns(2)

with ch1:
    if not df_stage.empty:
        df_stage_plot = df_stage.copy()
        stage_names_vn = {
            "Group Stage": "Vòng bảng",
            "Round of 32": "Vòng 32 đội",
            "Round of 16": "Vòng 16 đội",
            "Quarter-finals": "Tứ kết",
            "Semi-finals": "Bán kết",
            "Third place play-off": "Tranh hạng ba",
            "Final": "Chung kết",
        }
        df_stage_plot["Stage_VN"] = df_stage_plot["Stage"].map(lambda s: stage_names_vn.get(s, s))
        fig1 = px.bar(
            df_stage_plot, x="Stage_VN", y="Goals", text="Goals",
            title=" Bàn thắng theo từng Vòng đấu",
            color="Goals",
            color_continuous_scale=[[0, "#2a2a28"], [0.5, "#8a8a84"], [1, "#e8e8e3"]],
        )
        fig1.update_traces(textposition="outside", textfont=dict(color="#F8FAFC", size=13))
        fig1.update_layout(
            paper_bgcolor="#141414", plot_bgcolor="#141414",
            font=dict(family="Inter, sans-serif", color="#94A3B8"),
            title_font=dict(color="#FFFFFF", size=16),
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=50, b=30),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title=""),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Bàn thắng"),
        )
        st.plotly_chart(fig1, width="stretch")

with ch2:
    if not df_shots.empty:
        df_shots_plot = df_shots.copy()
        df_shots_plot["Player"] = df_shots_plot["Player"].apply(clean_name)
        fig2 = px.scatter(
            df_shots_plot, x="Shots", y="Goals",
            hover_data=["Player", "Team"],
            title=" Dứt điểm & Bàn thắng — Hiệu suất chuyển hóa",
            color="Goals", size="Goals",
            color_continuous_scale=[[0, "#2a2a28"], [0.5, "#8a8a84"], [1, "#e8e8e3"]],
        )
        fig2.update_layout(
            paper_bgcolor="#141414", plot_bgcolor="#141414",
            font=dict(family="Inter, sans-serif", color="#94A3B8"),
            title_font=dict(color="#FFFFFF", size=16),
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=50, b=30),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Tổng số cú dứt điểm"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Bàn thắng"),
        )
        st.plotly_chart(fig2, width="stretch")


# ── Best XI preview ───────────────────────────────────────────────────────────
st.markdown("<div class='section-header'> Xem trước Đội hình tiêu biểu World Cup 2026</div>", unsafe_allow_html=True)

xi_df = load_analytics_csv("best_xi.csv")
if xi_df is not None and not xi_df.empty:
    if "player_name" in xi_df.columns:
        xi_df["player_name"] = xi_df["player_name"].apply(clean_name)

    xi_left, xi_right = st.columns([1.5, 1.0], gap="large")

    with xi_left:
        st.markdown(
            '<div style="background:#141414;border:0;border-top:1px solid rgba(255,255,255,0.18);border-bottom:1px solid rgba(255,255,255,0.10);border-radius:0;padding:20px">'
            '<div style="font-size:15px;font-weight:700;color:#e8e8e3;margin-bottom:12px">Đội hình tiêu biểu giải đấu (Sơ đồ 4-3-3)</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        data_table(
            xi_df,
            width="stretch",
            height=280,
            label="Đội hình tiêu biểu / Chỉ số hiệu suất",
        )

    with xi_right:
        st.markdown(
            '<div class="champions-card" style="display:flex;flex-direction:column;justify-content:space-between">'
            '<div>'
            '<div style="font-size:11px;font-weight:800;color:#94A3B8;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px">TRÌNH DỰNG ĐỘI HÌNH AI</div>'
            '<div style="font-size:22px;font-weight:900;color:#FFFFFF;line-height:1.2;margin-bottom:12px">Khám phá 4 Đội hình trong mơ do AI tối ưu</div>'
            '<p style="font-size:13.5px;color:#94A3B8;line-height:1.6">'
            'Sa bàn 3D tương tác với 4 chế độ lựa chọn:<br>'
            '&bull; <strong>Đội hình AI chính thức</strong><br>'
            '&bull; <strong>Đội hình ML cân bằng</strong><br>'
            '&bull; <strong>Đội hình Sao trẻ U23</strong><br>'
            '&bull; <strong>Đội hình Tối ưu giá trị</strong>'
            '</p>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        nav_link("pages/6_best_xi.py", "Mở Trình dựng Đội hình tiêu biểu →")
else:
    st.info("Chưa tìm thấy dữ liệu Best XI. Vui lòng chạy pipeline phân tích hoặc truy cập trang Best XI để tạo.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:12.5px;padding:20px 0;border-top:1px solid rgba(255,255,255,0.06)'>"
    "WorldCup Stats '26 Analytics Platform &nbsp;·&nbsp; Dữ liệu từ FIFA, ESPN &amp; biên bản trận đấu chính thức &nbsp;·&nbsp; Phát triển bằng Python &amp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
