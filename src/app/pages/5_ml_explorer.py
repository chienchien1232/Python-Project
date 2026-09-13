# -*- coding: utf-8 -*-
"""WorldCup Stats '26 - Machine Learning Analytics Explorer."""
import os
import sys
import html as html_lib

import pandas as pd
import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys_path = os.path.join(ROOT, "src")
app_path = os.path.join(ROOT, "src", "app")
for p in [app_path, sys_path]:
    if p not in sys.path:
        sys.path.insert(0, p)

from helpers import load_analytics_csv  # noqa: E402
from media_ui import flag_image, render_photo_story  # noqa: E402

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ML Analytics Explorer | WorldCup Stats '26",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)
# First paint must be dark so page switches never flash white.
st.markdown("<style>html,body,.stApp,#root{background:#050505 !important;color-scheme:dark}</style>", unsafe_allow_html=True)

# ── Inject custom CSS ──────────────────────────────────────────────────────────
css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def clean_name(val):
    if not isinstance(val, str):
        return str(val) if val is not None else ""
    return (
        val.replace("Adrin", "Adrian")
           .replace("Andrs", "Andres")
           .replace("Damin", "Damian")
           .replace("Curaao", "Curacao")
           .replace("Cte d'Ivoire", "Côte d'Ivoire")
           .replace("Trkiye", "Türkiye")
           .replace("Lionel Andrs Messi", "Lionel Messi")
           .replace("Rodrigo Rodri", "Rodri")
           .replace("Kylian Mbappe", "Kylian Mbappé")
    )


# ── Top Navigation Bar ────────────────────────────────────────────────────────
from navigation import render_navigation
from table_ui import data_table
render_navigation('ML Analytics')

render_photo_story(
    "MACHINE LEARNING ENGINE / 2026",
    "PATTERNS.",
    "BENEATH PLAY.",
    "Clusters, projections and anomalies drawn from every tournament performance.",
    index="ML LAB",
    page="ml",
)

# ── Hero Section ──────────────────────────────────────────────────────────────
st.markdown(
    '<div class="wc-hero-wrapper" style="margin-bottom:20px">'
    '<div class="wc-hero-badge-row">'
    '<div class="wc-hero-badge"><span class="wc-badge-dot"></span>MACHINE LEARNING ENGINE</div>'
    '<div class="wc-hero-dates">K-MEANS CLUSTERING · 2D PCA · OUTLIER DETECTION</div>'
    '</div>'
    '<div class="wc-hero-title" style="font-size:52px;margin-bottom:10px">'
    '<span class="title-white">ADVANCED ML</span>'
    '<span class="title-lime">ANALYTICS.</span>'
    '</div>'
    '<div class="wc-hero-desc" style="max-width:760px;margin-bottom:16px">'
    'Unsupervised machine learning exploration of tournament data. Discover player tactical roles through K-Means clustering, '
    'explore high-dimensional feature spaces via 2D Principal Component Analysis (PCA), and detect anomalous match performances.'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)
# ── ML Explorer Tabs ──────────────────────────────────────────────────────────
st.markdown(
    '<div class="ml-workspace-intro" id="ml-workspace">'
    '<span>ML WORKSPACE / 03 TOOLS</span>'
    '<h2>Three models.<br>One workspace.</h2>'
    '</div>',
    unsafe_allow_html=True,
)
t1, t2, t3 = st.tabs([
    " Tactical Role Clustering",
    " 2D PCA Embedding Map",
    " Statistical Anomaly Detection"
])


# ==============================================================================
# TAB 1: CLUSTERING
# ==============================================================================
with t1:
    st.markdown("<div class='section-header' style='font-size:20px;margin-top:0'>K-Means Tactical Role Definitions</div>", unsafe_allow_html=True)

    st.markdown(
        """
        The **K-Means Clustering** pipeline evaluates **18 normalized Per-90 tactical metrics** per player to discover genuine on-pitch functional profiles beyond nominal lineup positions:

        *  **Finisher / Goal Scorer**: High shot volume, top-tier conversion rate, and elite box presence.
        *  **Playmaker / Chance Creator**: Elite shot-creating actions, key passes, crosses, and foul drawing.
        *  **Ball Progressor**: High-volume passing, progressive passes, and line-breaking progression.
        *  **Defensive Anchor**: High tackle volume, interceptions, ball recoveries, and aerial clearances.
        *  **Box-to-Box All-Rounder**: Balanced distribution across progressive, creative, and defensive actions.
        """
    )

    # ── Shared ML helpers (logic ported from the original explorer) ──
    METRIC_FRIENDLY = {
        "goals_p90": "Goals scored",
        "assists_p90": "Assists (pass leading to a goal)",
        "shots_p90": "Shot attempts",
        "shots_on_target_p90": "Shots on target",
        "passes_p90": "Passes made",
        "accurate_passes_p90": "Passes completed",
        "crosses_p90": "Crosses (wing passes into the box)",
        "tackles_p90": "Tackles (stopping the ball carrier)",
        "interceptions_p90": "Interceptions (cutting passes)",
        "clearances_p90": "Clearances (kicking the ball away)",
        "blocks_p90": "Blocks",
        "recoveries_p90": "Ball recoveries",
        "duels_won_p90": "1-v-1 duels won",
        "aerial_duels_won_p90": "Aerial duels won (headers)",
        "dribbles_attempted_p90": "Dribbles attempted",
        "fouls_committed_p90": "Fouls committed",
        "fouls_won_p90": "Fouls won",
        "offsides_p90": "Offsides",
    }
    KEY_METRICS = ["goals_p90", "shots_p90", "passes_p90", "tackles_p90",
                   "clearances_p90", "dribbles_attempted_p90"]
    ROLE_METRICS = {
        "Finisher / Goal Scorer": ["goals_p90", "shots_on_target_p90", "shots_p90"],
        "Playmaker / Chance Creator": ["assists_p90", "crosses_p90", "dribbles_attempted_p90"],
        "Ball Progressor": ["passes_p90", "accurate_passes_p90"],
        "Defensive Player": ["tackles_p90", "interceptions_p90", "clearances_p90", "blocks_p90"],
        "Defensive Anchor": ["tackles_p90", "interceptions_p90", "clearances_p90", "blocks_p90"],
        "Box-to-Box / All-rounder": KEY_METRICS,
        "Box-to-Box All-Rounder": KEY_METRICS,
    }

    def ratio_text(ratio):
        if ratio >= 1.05:
            return f"{ratio:.1f}× avg", "#ffffff"
        if ratio <= 0.95:
            return f"{round((1 - ratio) * 100)}% below avg", "#8a8f98"
        return "≈ tournament avg", "#8a8f98"

    st.markdown(
        '<style>'
        '.ml-role-card{background:#0e0e0e;border:0;border-top:1px solid rgba(255,255,255,0.18);border-bottom:1px solid rgba(255,255,255,0.10);border-radius:0;'
        'padding:18px;margin-bottom:16px;}'
        '.ml-panel-head{display:flex;align-items:center;gap:9px;font-size:14px;font-weight:800;'
        'letter-spacing:1.2px;color:#f3f2ed;text-transform:uppercase;margin-bottom:12px;flex-wrap:wrap;}'
        '.ml-dot{width:8px;height:8px;border-radius:50%;background:#f2f1ec;flex:0 0 auto;}'
        '.ml-year{margin-left:auto;font-size:10px;font-weight:600;letter-spacing:1px;color:#6b7280;white-space:nowrap;}'
        '.ml-role-head{display:flex;align-items:center;gap:12px;margin-bottom:6px;}'
        '.ml-role-num{display:grid;place-items:center;width:40px;height:40px;flex:0 0 auto;'
        'border:1px solid rgba(242,241,236,0.5);border-radius:8px;color:#f2f1ec;'
        'font-size:15px;font-weight:900;}'
        '.ml-role-title{font-size:19px;font-weight:800;color:#fff;line-height:1.15;}'
        '.ml-role-sub{font-size:11.5px;color:#8a8f98;font-weight:600;}'
        '.ml-known{font-size:12px;color:#8a8f98;margin-bottom:10px;}'
        '.ml-known b{color:#e8e8e3;}'
        '.ml-traits{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);'
        'border-radius:8px;padding:10px 12px;margin-bottom:10px;}'
        '.ml-traits-title{font-size:10.5px;font-weight:800;color:#8a8f98;letter-spacing:1px;'
        'text-transform:uppercase;margin-bottom:6px;}'
        '.ml-traits ul{margin:0;padding-left:16px;font-size:12.5px;color:#e8e8e3;line-height:1.7;}'
        '.ml-bar-row{margin:7px 0;}'
        '.ml-bar-top{display:flex;justify-content:space-between;font-size:11.5px;margin-bottom:3px;}'
        '.ml-bar-top span:first-child{color:#8a8f98;}'
        '.ml-bar-track{height:8px;background:rgba(255,255,255,0.06);border-radius:4px;position:relative;}'
        '.ml-bar-avg{position:absolute;left:50%;top:-1px;bottom:-1px;width:2px;background:rgba(255,255,255,0.35);}'
        '.ml-bar-fill{position:absolute;left:0;top:0;bottom:0;border-radius:4px;opacity:0.85;}'
        '.ml-group-row{display:flex;align-items:center;gap:10px;min-width:0;'
        'padding:8px 2px;border-bottom:1px solid rgba(255,255,255,0.08);}'
        '.ml-group-row .media-flag{flex:0 0 auto;}'
        '.ml-group-name{font-size:13.5px;font-weight:700;color:#fff;'
        'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}'
        '.ml-group-team{font-size:11.5px;color:#8a8f98;white-space:nowrap;}'
        '.ml-group-pos{background:rgba(255,255,255,0.10);color:#fff;border-radius:5px;'
        'padding:1px 7px;font-size:10.5px;font-weight:800;white-space:nowrap;}'
        '.ml-group-val{margin-left:auto;font-size:13.5px;font-weight:800;color:#fff;white-space:nowrap;}'
        '.ml-group-val small{font-size:10px;color:#8a8f98;font-weight:600;margin-left:4px;}'
        '</style>',
        unsafe_allow_html=True,
    )

    @st.dialog("Tactical group — players", width="large")
    def show_group_players(role, players_df, metric_col, metric_label):
        top = players_df.sort_values(metric_col, ascending=False).head(20)
        rows = ""
        for _, prow in top.iterrows():
            p_team = clean_name(str(prow["team"]))
            rows += (
                '<div class="ml-group-row">'
                f'{flag_image(p_team, class_name="media-flag is-small")}'
                f'<span class="ml-group-name">{html_lib.escape(clean_name(str(prow["player_name"])))}</span>'
                f'<span class="ml-group-team">{html_lib.escape(p_team)}</span>'
                f'<span class="ml-group-pos">{html_lib.escape(str(prow["position"]))}</span>'
                f'<span class="ml-group-val">{float(prow[metric_col]):.2f}<small>{html_lib.escape(metric_label)}</small></span>'
                '</div>'
            )
        st.markdown(
            f'<div style="font-size:12.5px;color:#8a8f98;margin-bottom:12px">'
            f'Standout metric: <b style="color:#fff">{html_lib.escape(metric_label)}</b> · '
            f'showing top 20 of <b style="color:#e8e8e3">{len(players_df)}</b> players, '
            f'sorted by that metric</div>' + rows,
            unsafe_allow_html=True,
        )

    clus_all = load_analytics_csv("player_clusters.csv")
    if clus_all is not None and "cluster_label" in clus_all.columns:
        clus_all["player_id"] = clus_all["player_id"].astype(str)
        clus_all["player_name"] = clus_all["player_name"].apply(clean_name)
        clus_all["team"] = clus_all["team"].apply(clean_name)
    else:
        clus_all = None

    def cluster_label_for(cluster_id):
        if clus_all is not None:
            hit = clus_all[clus_all["cluster"] == cluster_id]
            if not hit.empty and "cluster_label" in hit.columns:
                return str(hit["cluster_label"].mode().iloc[0])
        return f"Cluster {int(cluster_id)}"

    def group_frame_for(role, positions):
        if clus_all is None:
            return pd.DataFrame()
        return clus_all[(clus_all["cluster_label"] == role) & (clus_all["position"].isin(positions))]

    def role_card(role, n_pl, top_pl, bullets_html, bars_html, number):
        return (
            f'<div class="ml-role-card">'
            f'<div class="ml-role-head"><div class="ml-role-num">{number:02d}</div>'
            f'<div><div class="ml-role-title">{html_lib.escape(role)}</div>'
            f'<div class="ml-role-sub">{n_pl} players in this group</div></div></div>'
            f'<div class="ml-known">Known for: <b>{html_lib.escape(top_pl)}</b></div>'
            f'<div class="ml-traits"><div class="ml-traits-title">What this group does most / least</div>'
            f'<ul>{bullets_html}</ul></div>'
            f'{bars_html}'
            f'</div>'
        )

    def build_bars(r, metric_cols, pop_mean):
        bars_html = ""
        for m in KEY_METRICS:
            if m not in metric_cols or pop_mean.get(m, 0) <= 0:
                continue
            ratio = float(r[m]) / pop_mean[m]
            txt, clr = ratio_text(ratio)
            width = min(ratio * 100, 200) / 2
            bars_html += (
                f'<div class="ml-bar-row">'
                f'<div class="ml-bar-top"><span>{METRIC_FRIENDLY[m]}</span>'
                f'<span style="color:{clr};font-weight:700">{txt}</span></div>'
                f'<div class="ml-bar-track"><div class="ml-bar-avg"></div>'
                f'<div class="ml-bar-fill" style="width:{width:.1f}%;background:{clr}"></div>'
                f'</div></div>'
            )
        return bars_html

    def build_bullets(r, metric_cols, pop_mean, pop_std):
        z = {m: (float(r[m]) - pop_mean[m]) / pop_std[m] for m in metric_cols}
        top2 = sorted(z, key=z.get, reverse=True)[:2]
        low1 = min(z, key=z.get)
        bullets = []
        for m in top2:
            if z[m] >= 0.25 and pop_mean[m] > 0:
                bullets.append(f"<b>{METRIC_FRIENDLY[m]}</b> — {ratio_text(float(r[m]) / pop_mean[m])[0]}")
        if low1 and z[low1] <= -0.25 and pop_mean[low1] > 0:
            bullets.append(f"<b>{METRIC_FRIENDLY[low1]}</b> — {ratio_text(float(r[low1]) / pop_mean[low1])[0]}")
        if not bullets:
            bullets.append("No extreme tendency — an all-round profile")
        return "".join(f"<li>{b}</li>" for b in bullets), z

    # ── Outfield roles ──
    prof_out = load_analytics_csv("cluster_profile_outfield.csv")
    if prof_out is not None:
        st.markdown(
            "<div style='background:#0e0e0e;border:0;border-top:1px solid rgba(255,255,255,0.18);"
            "border-bottom:1px solid rgba(255,255,255,0.10);border-radius:0;padding:14px 18px;margin-bottom:18px;font-size:13.5px;"
            "color:#8a8f98;line-height:1.65'>"
            "<b style='color:#fff'>What am I looking at?</b> Think of grouping classmates by "
            "personality — the machine read every player's stats and automatically grouped similar "
            "playing styles together. <b style='color:#fff'>No human labeled them.</b> Each card "
            "below is one group: the numbers are that group's average <b style='color:#fff'>per "
            "90 minutes on the pitch</b>, and every bar compares the group with the tournament "
            "average (the white tick = 100% = exactly average)."
            "</div>",
            unsafe_allow_html=True,
        )

        metric_cols = [c for c in prof_out.columns
                       if c not in ("cluster", "cluster_label", "n_players", "top_players")]
        pf = load_analytics_csv("player_features.csv")
        pop_mean, pop_std, has_avg = None, None, False
        if pf is not None and not pf.empty:
            pf_out = pf[(pf["minutes"] >= 90) & (pf["position"].isin(["DEF", "MID", "FWD"]))]
            if not pf_out.empty:
                pop_mean = pf_out[metric_cols].mean()
                pop_std = pf_out[metric_cols].std()
                pop_std = pop_std.where(pop_std > 0, 1.0)
                has_avg = True

        card_cols = st.columns(2)
        for i, (_, r) in enumerate(prof_out.iterrows()):
            role = cluster_label_for(r.get("cluster", i))
            grp = group_frame_for(role, ["DEF", "MID", "FWD"])
            n_pl = len(grp)
            top_pl = "; ".join(grp.sort_values("minutes", ascending=False).head(3)["player_name"].tolist()) if not grp.empty else "-"
            if has_avg:
                bullets_html, z = build_bullets(r, metric_cols, pop_mean, pop_std)
                bars_html = build_bars(r, metric_cols, pop_mean)
                sig = ROLE_METRICS.get(role, KEY_METRICS)
                standout = max([m for m in sig if m in z], key=lambda m: z[m]) if any(m in z for m in sig) else KEY_METRICS[0]
            else:
                bullets_html = "<li>Population average unavailable.</li>"
                bars_html = ""
                standout = KEY_METRICS[0]
            standout_label = METRIC_FRIENDLY.get(standout, standout).split(" (")[0] + " / 90 min"
            card_html = role_card(role, n_pl, top_pl, bullets_html, bars_html, i + 1)
            with card_cols[i % 2]:
                st.markdown(card_html, unsafe_allow_html=True)
                if st.button("View players in this group", key=f"ml_cluster_{int(r.get('cluster', i))}"):
                    if not grp.empty and standout in grp.columns:
                        show_group_players(role, grp, standout, standout_label)
                    else:
                        st.info("Player list not available for this group.")

        st.markdown("<div class='section-header' style='font-size:18px'>Full Metrics Table — All 18 Indicators</div>", unsafe_allow_html=True)
        tbl = prof_out.copy()
        if "cluster_label" not in tbl.columns:
            tbl["cluster_label"] = [cluster_label_for(c) for c in tbl["cluster"]]
        tbl = tbl[["cluster_label"] + metric_cols].copy()
        tbl = tbl.rename(columns={"cluster_label": "Role", **{m: METRIC_FRIENDLY[m] for m in metric_cols}})
        data_table(tbl, width="stretch", label="Cluster centroid index")
        st.caption("per 90 = average per 90 minutes on the pitch · 'Role' is the machine-found group name (K-Means cluster).")

    # ── Goalkeeper roles ──
    prof_gk = load_analytics_csv("cluster_profile_gk.csv")
    if prof_gk is not None and not prof_gk.empty:
        st.markdown("<div class='section-header' style='font-size:18px'>Goalkeeper Cluster Centroids Breakdown</div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:#0e0e0e;border:0;border-top:1px solid rgba(255,255,255,0.18);"
            "border-bottom:1px solid rgba(255,255,255,0.10);border-radius:0;padding:14px 18px;margin-bottom:18px;font-size:13.5px;"
            "color:#8a8f98;line-height:1.65'>"
            "<b style='color:#fff'>And the goalkeepers?</b> They are grouped separately, by "
            "how they keep the ball out of the net — some stop a higher share of everything "
            "they face, others see very little action across the tournament. Same rule as "
            "above: the white tick on every bar = the tournament average for goalkeepers."
            "</div>",
            unsafe_allow_html=True,
        )
        gk_df = None
        if clus_all is not None:
            gk_df = clus_all[clus_all["position"] == "GK"]
        GK_FRIENDLY = {"saves_p90": "Saves / 90 min", "save_pct": "Save %"}
        gk_cards = st.columns(2)
        for i, (_, r) in enumerate(prof_gk.iterrows()):
            grp = gk_df[gk_df["cluster"] == r.get("cluster", i)] if gk_df is not None and "cluster" in gk_df.columns else (gk_df if gk_df is not None else pd.DataFrame())
            if not grp.empty and "cluster_label" in grp.columns:
                role = str(grp["cluster_label"].mode().iloc[0])
            else:
                role = f"Goalkeeper Cluster {i}"
            if gk_df is not None and not gk_df.empty:
                gm = gk_df[["saves_p90", "save_pct"]].mean()
                gs = gk_df[["saves_p90", "save_pct"]].std()
                gs = gs.where(gs > 0, 1.0)
                z = {m: (float(r[m]) - gm[m]) / gs[m] for m in ("saves_p90", "save_pct")}
                bullets = []
                for m in ("saves_p90", "save_pct"):
                    if abs(z[m]) >= 0.25 and gm[m] > 0:
                        bullets.append(f"<b>{GK_FRIENDLY[m]}</b> — {ratio_text(float(r[m]) / gm[m])[0]}")
                if not bullets:
                    bullets.append("No extreme tendency vs other goalkeepers")
                bars_html = ""
                for m in ("saves_p90", "save_pct"):
                    if gm[m] <= 0:
                        continue
                    ratio = float(r[m]) / gm[m]
                    txt, clr = ratio_text(ratio)
                    width = min(ratio * 100, 200) / 2
                    bars_html += (
                        f'<div class="ml-bar-row">'
                        f'<div class="ml-bar-top"><span>{GK_FRIENDLY[m]}</span>'
                        f'<span style="color:{clr};font-weight:700">{txt}</span></div>'
                        f'<div class="ml-bar-track"><div class="ml-bar-avg"></div>'
                        f'<div class="ml-bar-fill" style="width:{width:.1f}%;background:{clr}"></div>'
                        f'</div></div>'
                    )
            else:
                role, grp = f"Goalkeeper Cluster {i}", pd.DataFrame()
                bullets = ["Goalkeeper list not available."]
                bars_html = ""
            n_pl = len(grp) if grp is not None else 0
            top_pl = "; ".join(grp.sort_values("minutes", ascending=False).head(3)["player_name"].tolist()) if grp is not None and not grp.empty else "-"
            standout = "save_pct"
            with gk_cards[i % 2]:
                st.markdown(
                    f'<div class="ml-role-card">'
                    f'<div class="ml-role-head"><div class="ml-role-num">G{i + 1}</div>'
                    f'<div><div class="ml-role-title">{html_lib.escape(role)}</div>'
                    f'<div class="ml-role-sub">{n_pl} goalkeepers in this group</div></div></div>'
                    f'<div class="ml-known">Known for: <b>{html_lib.escape(top_pl)}</b></div>'
                    f'<div class="ml-traits"><div class="ml-traits-title">Signature vs average goalkeeper</div>'
                    f'<ul>{"".join(f"<li>{b}</li>" for b in bullets)}</ul></div>'
                    f'{bars_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button("View goalkeepers in this group", key=f"ml_gk_{i}"):
                    if grp is not None and not grp.empty:
                        show_group_players(role, grp, standout, GK_FRIENDLY[standout])
                    else:
                        st.info("Goalkeeper list not available.")

        st.markdown("<div class='section-header' style='font-size:18px'>Full GK Metrics Table</div>", unsafe_allow_html=True)
        gk_tbl = prof_gk[["saves_p90", "save_pct"]].copy()
        gk_tbl = gk_tbl.rename(columns={"saves_p90": "Saves / 90 min", "save_pct": "Save %"})
        data_table(gk_tbl, width="stretch", label="Goalkeeper centroid index")
        st.caption("Save % = share of shots on target saved · Saves / 90 min = saves per 90 minutes on the pitch.")


# ==============================================================================
# TAB 2: PCA MAP
# ==============================================================================
with t2:
    st.markdown("<div class='section-header' style='font-size:20px;margin-top:0'> 2D PCA Dimensionality Projection</div>", unsafe_allow_html=True)
    st.markdown("Interactive 2D Principal Component Analysis embedding showing similarity and clustering separation across all tournament players.")

    html_p = os.path.join(ROOT, "data", "processed", "analytics", "pca_interactive.html")
    if os.path.exists(html_p):
        import re as _re

        @st.cache_data(show_spinner=False)
        def pca_html_self_contained() -> str:
            with open(html_p, encoding="utf-8") as f:
                html_doc = f.read()
            # Inline Plotly JS so the map renders even when the plot.ly CDN
            # is unreachable from the viewer's browser.
            js_path = os.path.join(ROOT, "src", "app", "static", "plotly-3.7.0.min.js")
            if os.path.exists(js_path):
                with open(js_path, encoding="utf-8") as f:
                    plotly_js = f.read()
                html_doc, n = _re.subn(
                    r'<script\s+src="https://cdn\.plot\.ly/[^"]*"[^>]*></script>',
                    lambda _m: "<script>" + plotly_js + "</script>",
                    html_doc,
                    count=1,
                )
                if n == 0:
                    html_doc = html_doc.replace(
                        "</head>", "<script>" + plotly_js + "</script></head>", 1,
                    )
            return html_doc

        html_bytes = pca_html_self_contained()
        # Retheme the stored Plotly export at render time so the frame uses
        # the same dark editorial canvas as the surrounding analytics page.
        html_bytes = html_bytes.replace(
            "<head>",
            '<head><style>html,body{margin:0;background:#0e0e0e!important;color:#f1f0eb}</style>',
            1,
        )
        html_bytes = (
            html_bytes
            .replace('"paper_bgcolor":"white"', '"paper_bgcolor":"#0e0e0e"')
            .replace('"plot_bgcolor":"#E5ECF6"', '"plot_bgcolor":"#0e0e0e"')
            .replace('"color":"#2a3f5f"', '"color":"#b0b0aa"')
            .replace('"gridcolor":"white"', '"gridcolor":"#2d2d2d"')
            .replace('"linecolor":"white"', '"linecolor":"#555555"')
            .replace('"zerolinecolor":"white"', '"zerolinecolor":"#555555"')
        )
        with st.container(border=True):
            st.markdown(
                '<div class="ml-panel-head"><span class="ml-dot"></span>'
                'PLAYER SIMILARITY MAP<span class="ml-year">/ 2026</span></div>',
                unsafe_allow_html=True,
            )
            st.iframe(html_bytes, height=620, width="stretch", tab_index=-1)
        st.caption("Each point represents a tournament player · Color corresponds to ML cluster role · Hover to view player details")
    else:
        st.info("PCA interactive plot file not found. Run `python src/analytics/pca_explore.py` to generate the embedding.")

    # ── What drives each axis: loadings + extremes (existing pipeline outputs) ──
    loadings = load_analytics_csv("pca_loadings.csv")
    pcs = load_analytics_csv("player_pcs.csv")
    if loadings is not None and not loadings.empty:
        metric_col = loadings.columns[0]
        with st.container(border=True):
            st.markdown(
                '<div class="ml-panel-head"><span class="ml-dot"></span>'
                'WHAT DRIVES EACH AXIS<span class="ml-year">PC1 / PC2 LOADINGS</span></div>'
                '<div style="font-size:12.5px;color:#8a8f98;margin-bottom:12px">'
                'Bars show how strongly each per-90 metric pulls players along the axis. '
                'Longer bar = stronger influence on that direction of the map.</div>',
                unsafe_allow_html=True,
            )
            load_cols = st.columns(2)
            for j, pc in enumerate(["PC1", "PC2"]):
                if pc not in loadings.columns:
                    continue
                top_load = loadings[[metric_col, pc]].copy()
                top_load["abs"] = top_load[pc].abs()
                top_load = top_load.sort_values("abs", ascending=False).head(8)
                bars = ""
                mx = max(top_load["abs"].max(), 1e-9)
                for _, lrow in top_load.iterrows():
                    w = abs(float(lrow[pc])) / mx * 100
                    clr = "#f2f1ec" if float(lrow[pc]) < 0 else "#a6a6a0"
                    bars += (
                        f'<div class="ml-bar-row">'
                        f'<div class="ml-bar-top"><span>{METRIC_FRIENDLY.get(str(lrow[metric_col]), str(lrow[metric_col]))}</span>'
                        f'<span style="font-weight:700;color:{clr}">{float(lrow[pc]):+.2f}</span></div>'
                        f'<div class="ml-bar-track"><div class="ml-bar-fill" style="width:{w:.1f}%;background:{clr}"></div>'
                        f'</div></div>'
                    )
                with load_cols[j % 2]:
                    st.markdown(f'<div style="font-size:13px;font-weight:800;color:#fff;margin-bottom:8px">{pc} — TOP DRIVERS</div>' + bars,
                                unsafe_allow_html=True)
    if pcs is not None and not pcs.empty:
        pcs["player_name"] = pcs["player_name"].apply(clean_name)
        pcs["team"] = pcs["team"].apply(clean_name)
        with st.container(border=True):
            st.markdown(
                '<div class="ml-panel-head"><span class="ml-dot"></span>'
                'PLAYERS AT THE EDGES<span class="ml-year">PC EXTREMES</span></div>'
                '<div style="font-size:12.5px;color:#8a8f98;margin-bottom:12px">'
                'Most extreme players on each axis — the archetypes anchoring the corners of the map.</div>',
                unsafe_allow_html=True,
            )
            ext_cols = st.columns(2)
            for j, pc in enumerate(["PC1", "PC2"]):
                if pc not in pcs.columns:
                    continue
                lo = pcs.nsmallest(4, pc)[["player_name", "position", "team", pc]].copy()
                hi = pcs.nlargest(4, pc)[["player_name", "position", "team", pc]].copy()
                lo.columns = hi.columns = ["Player", "Pos", "Team", pc]
                with ext_cols[j % 2]:
                    st.markdown(f'<div style="font-size:12px;font-weight:800;color:#8a8f98;margin:6px 0">◀ LOW {pc}</div>',
                                unsafe_allow_html=True)
                    data_table(lo, width="stretch", label=f"Low {pc} extremes")
                    st.markdown(f'<div style="font-size:12px;font-weight:800;color:#8a8f98;margin:6px 0">HIGH {pc} ▶</div>',
                                unsafe_allow_html=True)
                    data_table(hi, width="stretch", label=f"High {pc} extremes")


# ==============================================================================
# TAB 3: ANOMALY DETECTION
# ==============================================================================
with t3:
    st.markdown("<div class='section-header' style='font-size:20px;margin-top:0'>Statistical Outliers &amp; Anomalous Match Performances</div>", unsafe_allow_html=True)
    st.markdown("Performances with statistical z-score deviations exceeding $|Z| > 2.3$ relative to positional baseline distributions.")

    anom = load_analytics_csv("anomalies.csv")
    if anom is not None and not anom.empty:
        anom["player_name"] = anom["player_name"].apply(clean_name)
        anom["team"] = anom["team"].apply(clean_name)

        disp_anom = anom.copy()
        rename_dict = {
            "player_name": "Player",
            "position": "Pos",
            "team": "Team",
            "minutes": "Mins",
            "total_goals": "Goals",
            "goals_p90": "Goals/90",
            "nguyen_nhan": "Statistical Anomaly Reason (Z-Score)"
        }
        disp_anom = disp_anom.rename(columns=rename_dict)
        disp_cols = [c for c in ["Player", "Pos", "Team", "Mins", "Goals", "Goals/90", "Statistical Anomaly Reason (Z-Score)"] if c in disp_anom.columns]

        data_table(disp_anom[disp_cols], width="stretch", label="Statistical anomaly index")
        st.caption("σ represents standard deviation units away from the positional player cohort average.")
    else:
        st.info("Run `python src/analytics/detect_anomalies.py` to compute anomaly thresholds.")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:12.5px;padding:20px 0;border-top:1px solid rgba(255,255,255,0.06)'>"
    "WorldCup Stats '26 Analytics Platform &nbsp;·&nbsp; Data powered by FIFA, ESPN &amp; official match records &nbsp;·&nbsp; Built with Python &amp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
