# -*- coding: utf-8 -*-
"""WorldCup Stats '26 - Machine Learning Analytics Explorer."""
import os
import sys
import html as html_lib

import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys_path = os.path.join(ROOT, "src")
app_path = os.path.join(ROOT, "src", "app")
for p in [app_path, sys_path]:
    if p not in sys.path:
        sys.path.insert(0, p)

from helpers import cfg_num, flag_img, icon_badge, load_analytics_csv

# ── Page configuration ────────────────────────────────────────────────────────


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


@st.dialog("Tactical group — players", width="large")
def show_group_players(role, players_df, metric_col, metric_label):
    """Cua so popup: cac cau thu thuoc nhom phong cach (ten + co + chi so noi bat)."""
    top = players_df.sort_values(metric_col, ascending=False).head(20)
    rows = ""
    for _, p in top.iterrows():
        p_team = clean_name(str(p["team"]))
        rows += (
            '<div class="stat-row" style="display:flex;align-items:center;justify-content:space-between;'
            'padding:8px 12px;background:rgba(255,255,255,0.02);'
            'border:1px solid var(--border-subtle);border-radius:10px;margin-bottom:6px">'
            '<div style="display:flex;align-items:center;gap:10px;min-width:0">'
            f'{flag_img(p_team, 16)}'
            f'<div style="font-size:13.5px;font-weight:700;color:#F8FAFC;'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
            f'{html_lib.escape(clean_name(str(p["player_name"])))}</div>'
            f'<div style="font-size:11.5px;color:#64748b">{html_lib.escape(p_team)}</div>'
            f'<span style="background:rgba(204,255,0,0.10);color:#ccff00;border-radius:6px;'
            f'padding:1px 7px;font-size:10.5px;font-weight:800">{html_lib.escape(str(p["position"]))}</span>'
            "</div>"
            f'<div style="font-size:13.5px;font-weight:800;color:#ccff00;white-space:nowrap">'
            f'{float(p[metric_col]):.2f}'
            f'<span style="font-size:10px;color:#64748b;font-weight:600;margin-left:4px">'
            f'{html_lib.escape(metric_label)}</span></div>'
            "</div>"
        )
    st.markdown(
        f'<div style="font-size:12.5px;color:#94a3b8;margin-bottom:12px">'
        f'Standout metric: <b style="color:#ccff00">{html_lib.escape(metric_label)}</b> · '
        f'showing top 20 of <b style="color:#E2E8F0">{len(players_df)}</b> players, '
        f'sorted by that metric</div>',
        unsafe_allow_html=True,
    )
    st.markdown(rows, unsafe_allow_html=True)


def ratio_text(ratio):
    """Dien dat de hieu: so voi trung binh giai (1.0 = dung trung binh)."""
    if ratio >= 1.05:
        return f"{ratio:.1f}× avg", "#ccff00"
    if ratio <= 0.95:
        return f"{round((1 - ratio) * 100)}% below avg", "#8b95a1"
    return "≈ tournament avg", "#94a3b8"


# ── Hero Section ──────────────────────────────────────────────────────────────
st.markdown(
    '<div class="wc-hero-wrapper" style="margin-bottom:20px">'
    '<div class="wc-hero-badge-row">'
    '<div class="wc-hero-badge"><span class="wc-badge-dot"></span> MACHINE LEARNING ENGINE</div>'
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
t1, t2, t3 = st.tabs(["Tactical Role Clustering", "2D PCA Embedding Map", "Statistical Anomaly Detection"])


# ==============================================================================
# TAB 1: CLUSTERING
# ==============================================================================
with t1:
    st.markdown(f"<div class='section-header' style='font-size:20px;margin-top:0'>{icon_badge('target')} K-Means Tactical Role Definitions</div>", unsafe_allow_html=True)
    
    st.markdown(
        """
        The **K-Means Clustering** pipeline evaluates **18 normalized Per-90 tactical metrics** per player to discover genuine on-pitch functional profiles beyond nominal lineup positions:
        
        * 🎯 **Finisher / Goal Scorer**: High shot volume, top-tier conversion rate, and elite box presence.
        * 🧠 **Playmaker / Chance Creator**: Elite shot-creating actions, key passes, crosses, and foul drawing.
        * 🚀 **Ball Progressor**: High-volume passing, progressive passes, and line-breaking progression.
        * 🛡️ **Defensive Anchor**: High tackle volume, interceptions, ball recoveries, and aerial clearances.
        * ⚖️ **Box-to-Box All-Rounder**: Balanced distribution across progressive, creative, and defensive actions.
        """
    )

    prof_out = load_analytics_csv("cluster_profile_outfield.csv")
    if prof_out is not None:
        st.markdown(f"<div class='section-header' style='font-size:18px'>{icon_badge('chart')} Outfield Cluster Centroids Breakdown</div>", unsafe_allow_html=True)

        st.markdown(
            "<div style='background:#111612;border:1px solid rgba(255,255,255,0.08);"
            "border-radius:12px;padding:14px 18px;margin-bottom:18px;font-size:13.5px;"
            "color:#94a3b8;line-height:1.65'>"
            "<b style='color:#F1F5F9'>What am I looking at?</b> Think of grouping classmates by "
            "personality — the machine read every player's stats and automatically grouped similar "
            "playing styles together. <b style='color:#F1F5F9'>No human labeled them.</b> Each card "
            "below is one group: the numbers are that group's average <b style='color:#F1F5F9'>per "
            "90 minutes on the pitch</b>, and every bar compares the group with the tournament "
            "average (the white tick = 100% = exactly average)."
            "</div>",
            unsafe_allow_html=True,
        )

        metric_cols = [c for c in prof_out.columns
                       if c not in ("cluster", "cluster_label", "n_players", "top_players")]
        KEY_METRICS = ["goals_p90", "shots_p90", "passes_p90", "tackles_p90",
                       "clearances_p90", "dribbles_attempted_p90"]
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
        ROLE_ICONS = {
            "Finisher / Goal Scorer": "target",
            "Playmaker / Chance Creator": "spark",
            "Ball Progressor": "rocket",
            "Defensive Player": "shield",
            "Box-to-Box / All-rounder": "scale",
        }
        # Chi so dac trung cho tung vai tro (popup hien chi so noi bat tu nhom nay)
        ROLE_METRICS = {
            "Finisher / Goal Scorer": ["goals_p90", "shots_on_target_p90", "shots_p90"],
            "Playmaker / Chance Creator": ["assists_p90", "crosses_p90",
                                           "dribbles_attempted_p90"],
            "Ball Progressor": ["passes_p90", "accurate_passes_p90"],
            "Defensive Player": ["tackles_p90", "interceptions_p90",
                                 "clearances_p90", "blocks_p90"],
            "Box-to-Box / All-rounder": KEY_METRICS,
        }

        # Trung binh toan giai (outfield, >=90 phut) lam moc so sanh 100%
        pf = load_analytics_csv("player_features.csv")
        pop_mean, pop_std, has_avg = None, None, False
        if pf is not None and not pf.empty:
            pf_out = pf[(pf["minutes"] >= 90) & (pf["position"].isin(["DEF", "MID", "FWD"]))]
            if not pf_out.empty:
                pop_mean = pf_out[metric_cols].mean()
                pop_std = pf_out[metric_cols].std()
                pop_std = pop_std.where(pop_std > 0, 1.0)
                has_avg = True

        # Danh sach cau thu theo nhom (outfield) cho popup
        clus_all = load_analytics_csv("player_clusters.csv")
        clus_out = None
        if clus_all is not None and "cluster_label" in clus_all.columns:
            clus_all["player_name"] = clus_all["player_name"].apply(clean_name)
            clus_all["team"] = clus_all["team"].apply(clean_name)
            clus_out = clus_all[clus_all["position"].isin(["DEF", "MID", "FWD"])]

        card_cols = st.columns(2)
        for i, (_, r) in enumerate(prof_out.iterrows()):
            role = str(r.get("cluster_label", f"Cluster {int(r.get('cluster', i))}"))
            icon = ROLE_ICONS.get(role, "ball")
            n_pl = int(r.get("n_players", 0))
            top_pl = clean_name(str(r.get("top_players", "-")))

            bullets = []
            if has_avg:
                z = {m: (float(r[m]) - pop_mean[m]) / pop_std[m] for m in metric_cols}
                top2 = sorted(z, key=z.get, reverse=True)[:2]
                low1 = min(z, key=z.get)
                for m in top2:
                    if z[m] >= 0.25 and pop_mean[m] > 0:
                        bullets.append(
                            f"<b>{METRIC_FRIENDLY[m]}</b> — "
                            f"{ratio_text(float(r[m]) / pop_mean[m])[0]}")
                if low1 and z[low1] <= -0.25 and pop_mean[low1] > 0:
                    bullets.append(
                        f"<b>{METRIC_FRIENDLY[low1]}</b> — "
                        f"{ratio_text(float(r[low1]) / pop_mean[low1])[0]}")
            if not bullets:
                bullets.append("No extreme tendency — an all-round profile")
            # Chi so noi bat = chi so z cao nhat TRONG nhom chi so dac trung cua vai tro
            sig = ROLE_METRICS.get(role, KEY_METRICS)
            if has_avg:
                standout = max([m for m in sig if m in z], key=lambda m: z[m])
            else:
                standout = max([m for m in sig if m in metric_cols],
                               key=lambda m: float(r[m]))

            bars_html = ""
            if has_avg:
                for m in KEY_METRICS:
                    if pop_mean.get(m, 0) <= 0:
                        continue
                    ratio = float(r[m]) / pop_mean[m]
                    txt, clr = ratio_text(ratio)
                    width = min(ratio * 100, 200) / 2
                    bars_html += (
                        f'<div style="margin:7px 0">'
                        f'<div style="display:flex;justify-content:space-between;'
                        f'font-size:11.5px;margin-bottom:3px">'
                        f'<span style="color:#94a3b8">{METRIC_FRIENDLY[m]}</span>'
                        f'<span style="color:{clr};font-weight:700">{txt}</span></div>'
                        f'<div style="height:8px;background:rgba(255,255,255,0.06);'
                        f'border-radius:999px;position:relative">'
                        f'<div style="position:absolute;left:50%;top:-1px;bottom:-1px;'
                        f'width:2px;background:rgba(255,255,255,0.35)"></div>'
                        f'<div style="position:absolute;left:0;top:0;bottom:0;'
                        f'width:{width:.1f}%;border-radius:999px;background:{clr};'
                        f'opacity:0.85"></div></div></div>'
                    )

            bullets_html = "".join(f"<li>{b}</li>" for b in bullets)
            card = (
                f'<div class="role-card">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
                f'{icon_badge(icon, 40, 22)}'
                f'<div><div style="font-family:var(--font-sport);font-size:19px;'
                f'font-weight:800;color:#FFFFFF;line-height:1.15">{html_lib.escape(role)}</div>'
                f'<div style="font-size:11.5px;color:#64748b;font-weight:600">'
                f'{n_pl} players in this group</div></div></div>'
                f'<div style="font-size:12px;color:#94a3b8;margin-bottom:10px">'
                f'Known for: <b style="color:#E2E8F0">{html_lib.escape(top_pl)}</b></div>'
                f'<div style="background:rgba(255,255,255,0.02);'
                f'border:1px solid rgba(255,255,255,0.06);border-radius:10px;'
                f'padding:10px 12px;margin-bottom:10px">'
                f'<div style="font-size:10.5px;font-weight:800;color:#64748b;'
                f'letter-spacing:1px;text-transform:uppercase;margin-bottom:6px">'
                f'What this group does most / least</div>'
                f'<ul style="margin:0;padding-left:16px;font-size:12.5px;color:#CBD5E1;'
                f'line-height:1.7">{bullets_html}</ul></div>'
                f'{bars_html}'
                f'</div>'
            )
            with card_cols[i % 2]:
                st.markdown(card, unsafe_allow_html=True)
                if st.button("View players in this group",
                             key=f"view_cluster_{int(r.get('cluster', i))}"):
                    if clus_out is not None and standout in clus_out.columns:
                        grp = clus_out[clus_out["cluster_label"] == role]
                        if not grp.empty:
                            show_group_players(
                                role, grp, standout,
                                METRIC_FRIENDLY[standout].split(" (")[0] + " / 90 min",
                            )
                        else:
                            st.info("No players found for this group.")
                    else:
                        st.info("Player list not available (run `python src/analytics/player_clusters.py`).")

        with st.expander("📋 Full metrics table — all 18 indicators (group averages, per 90 minutes)"):
            tbl = prof_out[["cluster_label", "n_players"] + metric_cols].copy()
            tbl = tbl.rename(columns={
                "cluster_label": "Role", "n_players": "Players",
                **{m: METRIC_FRIENDLY[m] for m in metric_cols},
            })
            st.dataframe(tbl, width="stretch", hide_index=True, column_config={c: cfg_num(c, "%.2f") for c in tbl.columns if c not in ("Role", "Players")})
            st.caption("per 90 = average per 90 minutes on the pitch · 'Role' is the "
                       "machine-found group name (K-Means cluster).")

    # ── 🧤 Goalkeeper Cluster Centroids Breakdown (GK được phân cụm riêng) ──
    clus = load_analytics_csv("player_clusters.csv")
    prof_gk = load_analytics_csv("cluster_profile_gk.csv")
    if prof_gk is not None and not prof_gk.empty:
        st.markdown(f"<div class='section-header' style='font-size:18px'>{icon_badge('glove')} Goalkeeper Cluster Centroids Breakdown</div>", unsafe_allow_html=True)

        st.markdown(
            "<div style='background:#111612;border:1px solid rgba(255,255,255,0.08);"
            "border-radius:12px;padding:14px 18px;margin-bottom:18px;font-size:13.5px;"
            "color:#94a3b8;line-height:1.65'>"
            "<b style='color:#F1F5F9'>And the goalkeepers?</b> They are grouped separately, by "
            "how they keep the ball out of the net — some stop a higher share of everything "
            "they face, others see very little action across the tournament. Same rule as "
            "above: the white tick on every bar = the tournament average for goalkeepers."
            "</div>",
            unsafe_allow_html=True,
        )

        gk_df = None
        if clus is not None and "cluster_label" in clus.columns:
            clus["player_name"] = clus["player_name"].apply(clean_name)
            clus["team"] = clus["team"].apply(clean_name)
            gk_df = clus[clus["position"] == "GK"]

        GK_FRIENDLY = {"saves_p90": "Saves / 90 min", "save_pct": "Save %"}
        gk_cards = st.columns(2)
        for i, (_, r) in enumerate(prof_gk.iterrows()):
            role = str(r.get("cluster_label", f"Cluster {int(r.get('cluster', i))}"))
            icon = "shield" if role == "Shot Stopper" else ("glove" if role == "Safe Hands" else "goal")
            n_pl = int(r.get("n_players", 0))
            top_pl = clean_name(str(r.get("top_players", "-")))

            bullets, bars_html = [], ""
            if gk_df is not None and not gk_df.empty:
                gm = gk_df[["saves_p90", "save_pct"]].mean()
                gs = gk_df[["saves_p90", "save_pct"]].std()
                gs = gs.where(gs > 0, 1.0)
                z = {m: (float(r[m]) - gm[m]) / gs[m] for m in ("saves_p90", "save_pct")}
                for m in ("saves_p90", "save_pct"):
                    if abs(z[m]) >= 0.25 and gm[m] > 0:
                        txt, _clr = ratio_text(float(r[m]) / gm[m])
                        bullets.append(f"<b>{GK_FRIENDLY[m]}</b> — {txt}")
                for m in ("saves_p90", "save_pct"):
                    if gm[m] <= 0:
                        continue
                    ratio = float(r[m]) / gm[m]
                    txt, clr = ratio_text(ratio)
                    width = min(ratio * 100, 200) / 2
                    bars_html += (
                        f'<div style="margin:7px 0">'
                        f'<div style="display:flex;justify-content:space-between;'
                        f'font-size:11.5px;margin-bottom:3px">'
                        f'<span style="color:#94a3b8">{GK_FRIENDLY[m]}</span>'
                        f'<span style="color:{clr};font-weight:700">{txt}</span></div>'
                        f'<div style="height:8px;background:rgba(255,255,255,0.06);'
                        f'border-radius:999px;position:relative">'
                        f'<div style="position:absolute;left:50%;top:-1px;bottom:-1px;'
                        f'width:2px;background:rgba(255,255,255,0.35)"></div>'
                        f'<div style="position:absolute;left:0;top:0;bottom:0;'
                        f'width:{width:.1f}%;border-radius:999px;background:{clr};'
                        f'opacity:0.85"></div></div></div>'
                    )
            if not bullets:
                bullets.append("No extreme tendency vs other goalkeepers")

            standout = "saves_p90" if role == "Shot Stopper" else "save_pct"
            card = (
                f'<div class="role-card">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
                f'{icon_badge(icon, 40, 22)}'
                f'<div><div style="font-family:var(--font-sport);font-size:19px;'
                f'font-weight:800;color:#FFFFFF;line-height:1.15">{html_lib.escape(role)}</div>'
                f'<div style="font-size:11.5px;color:#64748b;font-weight:600">'
                f'{n_pl} goalkeepers in this group</div></div></div>'
                f'<div style="font-size:12px;color:#94a3b8;margin-bottom:10px">'
                f'Known for: <b style="color:#E2E8F0">{html_lib.escape(top_pl)}</b></div>'
                f'<div style="background:rgba(255,255,255,0.02);'
                f'border:1px solid rgba(255,255,255,0.06);border-radius:10px;'
                f'padding:10px 12px;margin-bottom:10px">'
                f'<div style="font-size:10.5px;font-weight:800;color:#64748b;'
                f'letter-spacing:1px;text-transform:uppercase;margin-bottom:6px">'
                f'Signature vs average goalkeeper</div>'
                f'<ul style="margin:0;padding-left:16px;font-size:12.5px;color:#CBD5E1;'
                f'line-height:1.7">{"".join(f"<li>{b}</li>" for b in bullets)}</ul></div>'
                f'{bars_html}'
                f'</div>'
            )
            with gk_cards[i % 2]:
                st.markdown(card, unsafe_allow_html=True)
                if st.button("View goalkeepers in this group",
                             key=f"view_gk_{int(r.get('cluster', i))}"):
                    if gk_df is not None:
                        grp = gk_df[gk_df["cluster_label"] == role]
                        if not grp.empty:
                            show_group_players(role, grp, standout, GK_FRIENDLY[standout])
                        else:
                            st.info("No goalkeepers found for this group.")
                    else:
                        st.info("Goalkeeper list not available (run `python src/analytics/player_clusters.py`).")

        with st.expander("📋 Full GK metrics table (group averages)"):
            tbl = prof_gk[["cluster_label", "n_players", "saves_p90", "save_pct"]].copy()
            tbl = tbl.rename(columns={
                "cluster_label": "Role", "n_players": "Players",
                "saves_p90": "Saves / 90 min", "save_pct": "Save %",
            })
            st.dataframe(tbl, width="stretch", hide_index=True, column_config={c: cfg_num(c, "%.2f") for c in tbl.columns if c not in ("Role", "Players")})
            st.caption("Save % = share of shots on target saved · "
                       "Saves / 90 min = saves per 90 minutes on the pitch.")


# ==============================================================================
# TAB 2: PCA MAP
# ==============================================================================
with t2:
    st.markdown(f"<div class='section-header' style='font-size:20px;margin-top:0'>{icon_badge('map')} 2D PCA Dimensionality Projection</div>", unsafe_allow_html=True)
    st.markdown("Interactive 2D Principal Component Analysis embedding showing similarity and clustering separation across all tournament players.")
    
    html_p = os.path.join(ROOT, "data", "processed", "analytics", "pca_interactive.html")
    if os.path.exists(html_p):
        with open(html_p, encoding="utf-8") as f:
            html_bytes = f.read()
        import streamlit.components.v1 as components
        components.html(html_bytes, height=620, scrolling=True)
        st.caption("Each point represents a tournament player · Color corresponds to ML cluster role · Hover to view player details")
    else:
        st.info("PCA interactive plot file not found. Run `python src/analytics/pca_explore.py` to generate the embedding.")


# ==============================================================================
# TAB 3: ANOMALY DETECTION
# ==============================================================================
with t3:
    st.markdown(f"<div class='section-header' style='font-size:20px;margin-top:0'>{icon_badge('flame')} Statistical Outliers &amp; Anomalous Match Performances</div>", unsafe_allow_html=True)
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
        
        st.dataframe(disp_anom[disp_cols], width="stretch", hide_index=True, column_config={"Mins": cfg_num("Mins", "%.0f"), "Goals": cfg_num("Goals", "%.0f"),"Goals/90": cfg_num("Goals/90", "%.2f")})
        st.caption("σ = standard deviations from the positional average. + = above average, - = below average. Danh sách gồm cả cầu thủ bất thường TÍCH CỰC (siêu hình) và các trường hợp giảm form.")
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
