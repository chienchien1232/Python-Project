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
    page_title="Phân Tích Máy Học ML | WorldCup Stats '26",
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
    "TRUNG TÂM PHÂN TÍCH MÁY HỌC / 2026",
    "QUY LUẬT.",
    "ẨN SAU TRẬN ĐẤU.",
    "Phân cụm, phép chiếu và các dị biệt dữ liệu được trích xuất từ mọi màn trình diễn tại giải đấu.",
    index="PHÒNG LAB ML",
    page="ml",
)

# ── Hero Section ──────────────────────────────────────────────────────────────
st.markdown(
    '<div class="wc-hero-wrapper" style="margin-bottom:20px">'
    '<div class="wc-hero-badge-row">'
    '<div class="wc-hero-badge"><span class="wc-badge-dot"></span>HỆ THỐNG PHÂN TÍCH MÁY HỌC</div>'
    '<div class="wc-hero-dates">PHÂN CỤM K-MEANS · GIẢM CHIỀU 2D PCA · PHÁT HIỆN DỊ BIỆT (OUTLIER)</div>'
    '</div>'
    '<div class="wc-hero-title" style="font-size:52px;margin-bottom:10px">'
    '<span class="title-white">PHÂN TÍCH</span>'
    '<span class="title-lime">MÁY HỌC ML.</span>'
    '</div>'
    '<div class="wc-hero-desc" style="max-width:760px;margin-bottom:16px">'
    'Khám phá dữ liệu giải đấu bằng máy học không giám sát. Tìm hiểu các vai trò chiến thuật thực tế qua thuật toán K-Means, '
    'quan sát không gian thuộc tính đa chiều với Phân tích Thành phần Chính (PCA 2D), và phát hiện những màn trình diễn đột biến dị thường.'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)
# ── ML Explorer Tabs ──────────────────────────────────────────────────────────
st.markdown(
    '<div class="ml-workspace-intro" id="ml-workspace">'
    '<span>KHÔNG GIAN ML / 03 CÔNG CỤ</span>'
    '<h2>Ba mô hình.<br>Một không gian phân tích.</h2>'
    '</div>',
    unsafe_allow_html=True,
)
t1, t2, t3 = st.tabs([
    " Phân cụm Vai trò Chiến thuật",
    " Bản đồ Nhúng 2D PCA",
    " Phát hiện Trận đấu Dị biệt"
])


# ==============================================================================
# TAB 1: CLUSTERING
# ==============================================================================
with t1:
    st.markdown("<div class='section-header' style='font-size:20px;margin-top:0'>Định Nghĩa Vai Trò Chiến Thuật K-Means</div>", unsafe_allow_html=True)

    st.markdown(
        """
        Quy trình **Phân cụm K-Means** đánh giá **18 chỉ số chiến thuật chuẩn hóa mỗi 90 phút** của từng cầu thủ để khám phá vai trò thi đấu thực tế trên sân thay vì chỉ nhìn vào vị trí đăng ký danh nghĩa:

        *  **Sát thủ vòng cấm / Cầu thủ săn bàn**: Tần suất dứt điểm cao, tỷ lệ chuyển hóa cơ hội thượng thừa và chiếm lĩnh khu vực 16m50.
        *  **Nhạc trưởng kiến thiết / Cầu thủ tạo cơ hội**: Số pha tạo đột biến dẫn tới dứt điểm vượt trội, đường chuyền quyết định, tạt bóng và câu lỗi chiến thuật.
        *  **Tiền vệ tịnh tiến bóng**: Khối lượng chuyền bóng lớn, chuyền tịnh tiến xuyên tuyến đưa bóng lên phía trước.
        *  **Mỏ neo phòng ngự**: Tranh chấp tay đôi, đánh chặn, thu hồi bóng và không chiến giải nguy xuất sắc.
        *  **Tiền vệ con thoi toàn diện (Box-to-Box)**: Đóng góp cân bằng giữa tịnh tiến bóng, sáng tạo cơ hội và hỗ trợ phòng ngự.
        """
    )

    # ── Shared ML helpers (logic ported from the original explorer) ──
    METRIC_FRIENDLY = {
        "goals_p90": "Bàn thắng ghi được",
        "assists_p90": "Kiến tạo thành bàn",
        "shots_p90": "Dứt điểm",
        "shots_on_target_p90": "Dứt điểm trúng đích",
        "passes_p90": "Số đường chuyền",
        "accurate_passes_p90": "Chuyền bóng chính xác",
        "crosses_p90": "Tạt bóng vào vòng cấm",
        "tackles_p90": "Tắc bóng cản phá",
        "interceptions_p90": "Cắt đường chuyền",
        "clearances_p90": "Phá bóng giải nguy",
        "blocks_p90": "Chặn cú sút / đường chuyền",
        "recoveries_p90": "Thu hồi bóng",
        "duels_won_p90": "Thắng tranh chấp 1-đối-1",
        "aerial_duels_won_p90": "Thắng không chiến (đánh đầu)",
        "dribbles_attempted_p90": "Nỗ lực rê dắt bóng",
        "fouls_committed_p90": "Phạm lỗi",
        "fouls_won_p90": "Bị phạm lỗi (kiếm lỗi)",
        "offsides_p90": "Việt vị",
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
            return f"Gấp {ratio:.1f}× TB", "#ffffff"
        if ratio <= 0.95:
            return f"Thấp hơn {round((1 - ratio) * 100)}% so với TB", "#8a8f98"
        return "≈ mức trung bình giải", "#8a8f98"

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

    @st.dialog("Nhóm chiến thuật — danh sách cầu thủ", width="large")
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
            f'Chỉ số nổi bật: <b style="color:#fff">{html_lib.escape(metric_label)}</b> · '
            f'hiển thị top 20 trong tổng số <b style="color:#e8e8e3">{len(players_df)}</b> cầu thủ, '
            f'sắp xếp theo chỉ số này</div>' + rows,
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
        return f"Nhóm {int(cluster_id)}"

    def group_frame_for(role, positions):
        if clus_all is None:
            return pd.DataFrame()
        return clus_all[(clus_all["cluster_label"] == role) & (clus_all["position"].isin(positions))]

    def role_card(role, n_pl, top_pl, bullets_html, bars_html, number):
        return (
            f'<div class="ml-role-card">'
            f'<div class="ml-role-head"><div class="ml-role-num">{number:02d}</div>'
            f'<div><div class="ml-role-title">{html_lib.escape(role)}</div>'
            f'<div class="ml-role-sub">{n_pl} cầu thủ trong nhóm này</div></div></div>'
            f'<div class="ml-known">Tiêu biểu: <b>{html_lib.escape(top_pl)}</b></div>'
            f'<div class="ml-traits"><div class="ml-traits-title">Đặc trưng nổi bật nhất / ít nhất của nhóm</div>'
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
            bullets.append("Không có xu hướng cực đoan — phong cách thi đấu toàn diện")
        return "".join(f"<li>{b}</li>" for b in bullets), z

    # ── Outfield roles ──
    prof_out = load_analytics_csv("cluster_profile_outfield.csv")
    if prof_out is not None:
        st.markdown(
            "<div style='background:#0e0e0e;border:0;border-top:1px solid rgba(255,255,255,0.18);"
            "border-bottom:1px solid rgba(255,255,255,0.10);border-radius:0;padding:14px 18px;margin-bottom:18px;font-size:13.5px;"
            "color:#8a8f98;line-height:1.65'>"
            "<b style='color:#fff'>Ý nghĩa bảng này là gì?</b> Tương tự như phân loại học sinh theo "
            "tính cách — mô hình tự động đọc toàn bộ thống kê của mọi cầu thủ và gom các cầu thủ có phong "
            "cách thi đấu tương đồng vào cùng một nhóm. <b style='color:#fff'>Hoàn toàn không có sự can thiệp thủ công.</b> Mỗi thẻ "
            "bên dưới là một nhóm: các con số thể hiện mức trung bình của nhóm <b style='color:#fff'>mỗi "
            "90 phút trên sân</b>, và thanh biểu đồ so sánh nhóm đó với trung bình toàn bộ giải đấu "
            "(vạch trắng = 100% = ngang bằng trung bình giải)."
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
                bullets_html = "<li>Chưa có dữ liệu trung bình giải.</li>"
                bars_html = ""
                standout = KEY_METRICS[0]
            standout_label = METRIC_FRIENDLY.get(standout, standout).split(" (")[0] + " / 90 phút"
            card_html = role_card(role, n_pl, top_pl, bullets_html, bars_html, i + 1)
            with card_cols[i % 2]:
                st.markdown(card_html, unsafe_allow_html=True)
                if st.button("Xem danh sách cầu thủ nhóm này", key=f"ml_cluster_{int(r.get('cluster', i))}"):
                    if not grp.empty and standout in grp.columns:
                        show_group_players(role, grp, standout, standout_label)
                    else:
                        st.info("Chưa có danh sách cầu thủ cho nhóm này.")

        st.markdown("<div class='section-header' style='font-size:18px'>Bảng Đầy Đủ 18 Chỉ Số Chiến Thuật</div>", unsafe_allow_html=True)
        tbl = prof_out.copy()
        if "cluster_label" not in tbl.columns:
            tbl["cluster_label"] = [cluster_label_for(c) for c in tbl["cluster"]]
        tbl = tbl[["cluster_label"] + metric_cols].copy()
        tbl = tbl.rename(columns={"cluster_label": "Vai trò chiến thuật", **{m: METRIC_FRIENDLY[m] for m in metric_cols}})
        data_table(tbl, width="stretch", label="Chỉ mục trọng tâm phân cụm")
        st.caption("mỗi 90 phút = trung bình mỗi 90 phút thi đấu trên sân · 'Vai trò chiến thuật' là tên nhóm do mô hình K-Means phát hiện.")

    # ── Goalkeeper roles ──
    prof_gk = load_analytics_csv("cluster_profile_gk.csv")
    if prof_gk is not None and not prof_gk.empty:
        st.markdown("<div class='section-header' style='font-size:18px'>Phân Tích Cụm Trọng Tâm Của Thủ Môn</div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:#0e0e0e;border:0;border-top:1px solid rgba(255,255,255,0.18);"
            "border-bottom:1px solid rgba(255,255,255,0.10);border-radius:0;padding:14px 18px;margin-bottom:18px;font-size:13.5px;"
            "color:#8a8f98;line-height:1.65'>"
            "<b style='color:#fff'>Còn các thủ môn thì sao?</b> Thủ môn được phân cụm riêng biệt, theo "
            "cách họ bảo vệ khung thành — một số cản phá tỷ lệ bóng trúng đích cao, một số khác ít "
            "phải hoạt động hơn suốt giải đấu. Quy tắc so sánh tương tự như trên: vạch trắng trên mỗi "
            "thanh = mức trung bình của toàn bộ thủ môn tại giải đấu."
            "</div>",
            unsafe_allow_html=True,
        )
        gk_df = None
        if clus_all is not None:
            gk_df = clus_all[clus_all["position"] == "GK"]
        GK_FRIENDLY = {"saves_p90": "Cứu thua / 90 phút", "save_pct": "Tỷ lệ cứu thua %"}
        gk_cards = st.columns(2)
        for i, (_, r) in enumerate(prof_gk.iterrows()):
            grp = gk_df[gk_df["cluster"] == r.get("cluster", i)] if gk_df is not None and "cluster" in gk_df.columns else (gk_df if gk_df is not None else pd.DataFrame())
            if not grp.empty and "cluster_label" in grp.columns:
                role = str(grp["cluster_label"].mode().iloc[0])
            else:
                role = f"Nhóm Thủ Môn {i}"
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
                    bullets.append("Không có xu hướng chênh lệch lớn so với thủ môn khác")
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
                role, grp = f"Nhóm Thủ Môn {i}", pd.DataFrame()
                bullets = ["Chưa có danh sách thủ môn."]
                bars_html = ""
            n_pl = len(grp) if grp is not None else 0
            top_pl = "; ".join(grp.sort_values("minutes", ascending=False).head(3)["player_name"].tolist()) if grp is not None and not grp.empty else "-"
            standout = "save_pct"
            with gk_cards[i % 2]:
                st.markdown(
                    f'<div class="ml-role-card">'
                    f'<div class="ml-role-head"><div class="ml-role-num">G{i + 1}</div>'
                    f'<div><div class="ml-role-title">{html_lib.escape(role)}</div>'
                    f'<div class="ml-role-sub">{n_pl} thủ môn trong nhóm này</div></div></div>'
                    f'<div class="ml-known">Tiêu biểu: <b>{html_lib.escape(top_pl)}</b></div>'
                    f'<div class="ml-traits"><div class="ml-traits-title">Đặc trưng so với trung bình thủ môn toàn giải</div>'
                    f'<ul>{"".join(f"<li>{b}</li>" for b in bullets)}</ul></div>'
                    f'{bars_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Xem danh sách thủ môn nhóm này", key=f"ml_gk_{i}"):
                    if grp is not None and not grp.empty:
                        show_group_players(role, grp, standout, GK_FRIENDLY[standout])
                    else:
                        st.info("Chưa có danh sách thủ môn.")

        st.markdown("<div class='section-header' style='font-size:18px'>Bảng Đầy Đủ Chỉ Số Thủ Môn</div>", unsafe_allow_html=True)
        gk_tbl = prof_gk[["saves_p90", "save_pct"]].copy()
        gk_tbl = gk_tbl.rename(columns={"saves_p90": "Cứu thua / 90 phút", "save_pct": "Tỷ lệ cứu thua %"})
        data_table(gk_tbl, width="stretch", label="Chỉ mục trọng tâm thủ môn")
        st.caption("Tỷ lệ cứu thua % = phần trăm cú sút trúng đích được cản phá · Cứu thua / 90 phút = số lần cứu thua trung bình mỗi 90 phút trên sân.")


# ==============================================================================
# TAB 2: PCA MAP
# ==============================================================================
with t2:
    st.markdown("<div class='section-header' style='font-size:20px;margin-top:0'>Phép Chiếu Không Gian 2D Bằng PCA</div>", unsafe_allow_html=True)
    st.markdown("Bản đồ nhúng 2D Principal Component Analysis (PCA) tương tác trực quan hóa mức độ tương đồng và khoảng cách phân tách giữa mọi cầu thủ tại giải đấu.")

    html_p = os.path.join(ROOT, "data", "processed", "analytics", "pca_interactive.html")
    if os.path.exists(html_p):
        import re as _re

        @st.cache_data(show_spinner=False)
        def pca_html_self_contained() -> str:
            with open(html_p, encoding="utf-8") as f:
                html_doc = f.read()
            # Reference static Plotly script to avoid streaming 5MB string over WebSocket
            html_doc = _re.sub(
                r'<script\s+[^>]*src="https://cdn\.plot\.ly/[^"]*"[^>]*></script>',
                '<script src="/app/static/plotly-3.7.0.min.js"></script>',
                html_doc,
                count=1,
            )
            return html_doc

        html_bytes = pca_html_self_contained()
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
                'BẢN ĐỒ TƯƠNG ĐỒNG CẦU THỦ<span class="ml-year">/ 2026</span></div>',
                unsafe_allow_html=True,
            )
            st.iframe(html_bytes, height=620, width="stretch", tab_index=-1)
        st.caption("Mỗi điểm biểu thị một cầu thủ · Màu sắc tương ứng với cụm vai trò chiến thuật ML · Rê chuột để xem thông tin chi tiết của cầu thủ")
    else:
        st.info("Chưa tìm thấy tệp biểu đồ tương tác PCA. Hãy chạy lệnh `python src/analytics/pca_explore.py` để tạo bản đồ nhúng.")

    # ── What drives each axis: loadings + extremes (existing pipeline outputs) ──
    loadings = load_analytics_csv("pca_loadings.csv")
    pcs = load_analytics_csv("player_pcs.csv")
    if loadings is not None and not loadings.empty:
        metric_col = loadings.columns[0]
        with st.container(border=True):
            st.markdown(
                '<div class="ml-panel-head"><span class="ml-dot"></span>'
                'YẾU TỐ ĐỊNH HÌNH TRỤC TỌA<span class="ml-year">HỆ SỐ TẢI PC1 / PC2</span></div>'
                '<div style="font-size:12.5px;color:#8a8f98;margin-bottom:12px">'
                'Các thanh biểu thị mức độ mỗi chỉ số 90 phút chi phối vị trí của cầu thủ dọc theo trục tọa độ. '
                'Thanh dài hơn = ảnh hưởng mạnh hơn tới hướng đó của bản đồ.</div>',
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
                    st.markdown(f'<div style="font-size:13px;font-weight:800;color:#fff;margin-bottom:8px">{pc} — YẾU TỐ ẢNH HƯỞNG HÀNG ĐẦU</div>' + bars,
                                unsafe_allow_html=True)
    if pcs is not None and not pcs.empty:
        pcs["player_name"] = pcs["player_name"].apply(clean_name)
        pcs["team"] = pcs["team"].apply(clean_name)
        with st.container(border=True):
            st.markdown(
                '<div class="ml-panel-head"><span class="ml-dot"></span>'
                'CÁC CẦU THỦ Ở VỊ TRÍ BIÊN CỰC<span class="ml-year">CỰC TRỊ PC</span></div>'
                '<div style="font-size:12.5px;color:#8a8f98;margin-bottom:12px">'
                'Những cầu thủ có giá trị cực trị nhất trên mỗi trục — đại diện cho các phong cách định hình góc biên của bản đồ không gian.</div>',
                unsafe_allow_html=True,
            )
            ext_cols = st.columns(2)
            for j, pc in enumerate(["PC1", "PC2"]):
                if pc not in pcs.columns:
                    continue
                lo = pcs.nsmallest(4, pc)[["player_name", "position", "team", pc]].copy()
                hi = pcs.nlargest(4, pc)[["player_name", "position", "team", pc]].copy()
                lo.columns = hi.columns = ["Cầu thủ", "Vị trí", "Đội tuyển", pc]
                with ext_cols[j % 2]:
                    st.markdown(f'<div style="font-size:12px;font-weight:800;color:#8a8f98;margin:6px 0">◀ {pc} THẤP NHẤT</div>',
                                unsafe_allow_html=True)
                    data_table(lo, width="stretch", label=f"Cực trị {pc} thấp")
                    st.markdown(f'<div style="font-size:12px;font-weight:800;color:#8a8f98;margin:6px 0">{pc} CAO NHẤT ▶</div>',
                                unsafe_allow_html=True)
                    data_table(hi, width="stretch", label=f"Cực trị {pc} cao")


# ==============================================================================
# TAB 3: ANOMALY DETECTION
# ==============================================================================
with t3:
    st.markdown("<div class='section-header' style='font-size:20px;margin-top:0'>Phát Hiện Dị Biệt Thống Kê &amp; Màn Trình Diễn Bất Thường</div>", unsafe_allow_html=True)
    st.markdown("Các màn trình diễn có độ lệch chuẩn thống kê vượt ngưỡng $|Z| > 2.3$ so với phân phối chuẩn của các cầu thủ cùng vị trí thi đấu.")

    anom = load_analytics_csv("anomalies.csv")
    if anom is not None and not anom.empty:
        anom["player_name"] = anom["player_name"].apply(clean_name)
        anom["team"] = anom["team"].apply(clean_name)

        disp_anom = anom.copy()
        rename_dict = {
            "player_name": "Cầu thủ",
            "position": "Vị trí",
            "team": "Đội tuyển",
            "minutes": "Số phút",
            "total_goals": "Bàn thắng",
            "goals_p90": "Bàn thắng/90",
            "nguyen_nhan": "Lý do dị biệt thống kê (Z-Score)"
        }
        disp_anom = disp_anom.rename(columns=rename_dict)
        disp_cols = [c for c in ["Cầu thủ", "Vị trí", "Đội tuyển", "Số phút", "Bàn thắng", "Bàn thắng/90", "Lý do dị biệt thống kê (Z-Score)"] if c in disp_anom.columns]

        data_table(disp_anom[disp_cols], width="stretch", label="Chỉ mục dị biệt thống kê")
        st.caption("σ biểu thị số độ lệch chuẩn cách biệt so với mức trung bình của nhóm cầu thủ cùng vị trí.")
    else:
        st.info("Chạy lệnh `python src/analytics/detect_anomalies.py` để tính toán ngưỡng dị biệt thống kê.")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:12.5px;padding:20px 0;border-top:1px solid rgba(255,255,255,0.06)'>"
    "Nền tảng Phân tích WorldCup Stats '26 &nbsp;·&nbsp; Dữ liệu từ FIFA, ESPN &amp; biên bản thi đấu chính thức &nbsp;·&nbsp; Phát triển bằng Python &amp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
