# -*- coding: utf-8 -*-
"""Shared photographic storytelling, national flags, and FIFA player portraits."""
from __future__ import annotations

from functools import lru_cache
from html import escape
from pathlib import Path
import hashlib
import json
import re
import unicodedata
from urllib.parse import quote

import streamlit as st


APP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = APP_ROOT.parents[1]
FIFA_RAW = PROJECT_ROOT / "data" / "raw" / "fifa"


@lru_cache(maxsize=32)
def static_version(filename: str) -> str:
    """Cache-busting query string for bundled static assets.

    Browsers cache /app/static/* aggressively; appending the file mtime
    forces a fresh download whenever an image is replaced.
    """
    try:
        return str(int((APP_ROOT / "static" / filename).stat().st_mtime))
    except OSError:
        return "0"


def static_url(filename: str) -> str:
    safe_name = quote(str(filename), safe="")
    return f"/app/static/{safe_name}?v={static_version(filename)}"


def static_variant(filename: str, suffix: str) -> str:
    """Return a generated WebP variant when it exists, otherwise the source asset."""
    source = Path(filename)
    candidate = source.with_suffix("").name + suffix + ".webp"
    return candidate if (APP_ROOT / "static" / candidate).exists() else filename

TEAM_CODES = {
    "Algeria": "ALG", "Argentina": "ARG", "Australia": "AUS", "Austria": "AUT",
    "Belgium": "BEL", "Bosnia and Herzegovina": "BIH", "Brazil": "BRA",
    "Cabo Verde": "CPV", "Canada": "CAN", "Colombia": "COL", "Congo DR": "COD",
    "Croatia": "CRO", "Curaçao": "CUW", "Curacao": "CUW", "Czechia": "CZE",
    "Côte d'Ivoire": "CIV", "Cote d'Ivoire": "CIV", "Ecuador": "ECU",
    "Egypt": "EGY", "England": "ENG", "France": "FRA", "Germany": "GER",
    "Ghana": "GHA", "Haiti": "HAI", "IR Iran": "IRN", "Iraq": "IRQ",
    "Japan": "JPN", "Jordan": "JOR", "Mexico": "MEX", "Morocco": "MAR",
    "Netherlands": "NED", "New Zealand": "NZL", "Norway": "NOR", "Panama": "PAN",
    "Paraguay": "PAR", "Portugal": "POR", "Qatar": "QAT", "Saudi Arabia": "KSA",
    "Scotland": "SCO", "Senegal": "SEN", "South Africa": "RSA",
    "South Korea": "KOR", "Spain": "ESP", "Sweden": "SWE", "Switzerland": "SUI",
    "Tunisia": "TUN", "Türkiye": "TUR", "Turkey": "TUR", "USA": "USA",
    "Uruguay": "URU", "Uzbekistan": "UZB",
}

# Low-chroma national accents shared by the large Players portrait and the
# comparison cards. They are deliberately restrained so skin and kit colours
# remain accurate against the dark interface.
COUNTRY_PALETTES = {
    "ALG": ("#315b70", "#8a554e"), "ARG": ("#6fa9c8", "#e7dfcf"),
    "AUS": ("#3f695a", "#c5a85d"), "AUT": ("#7d3944", "#4c5660"),
    "BEL": ("#6d3039", "#b79a62"), "BIH": ("#406486", "#d0c9b8"),
    "BRA": ("#1c5a48", "#c4a35a"), "CAN": ("#8d3d46", "#d7d0c0"),
    "CIV": ("#b0783e", "#3f725f"), "COD": ("#426a83", "#b58a53"),
    "COL": ("#aa7f3d", "#315b70"), "CPV": ("#315b70", "#b8a46b"),
    "CRO": ("#537797", "#9a4a50"), "CZE": ("#95545a", "#4c6982"),
    "CUW": ("#3b6f83", "#c28d52"), "ECU": ("#a77d3c", "#385e70"),
    "EGY": ("#8f3f43", "#8d794a"), "ENG": ("#234b71", "#94424b"),
    "ESP": ("#8a3431", "#c49a55"), "FRA": ("#18365e", "#7b2630"),
    "GER": ("#4e555b", "#b7a68e"), "GHA": ("#395f4d", "#b68a45"),
    "HAI": ("#4f6388", "#9b4b57"), "IRN": ("#426c56", "#9a4e4e"),
    "IRQ": ("#416b56", "#b68d58"), "JOR": ("#4e6680", "#956071"),
    "JPN": ("#3b5b81", "#b04b51"), "KOR": ("#4a6882", "#ad4d53"),
    "KSA": ("#416b56", "#c1aa6b"), "MAR": ("#7c3947", "#3e6758"),
    "MEX": ("#34705b", "#9a4749"), "NED": ("#a86747", "#41677a"),
    "NOR": ("#3a5d80", "#93474e"), "NZL": ("#3e5f71", "#b6aa78"),
    "PAN": ("#496783", "#aa5960"), "PAR": ("#8d424a", "#416b79"),
    "POR": ("#76283b", "#355446"), "QAT": ("#765064", "#b39266"),
    "RSA": ("#3e6a58", "#b79854"), "SCO": ("#385d83", "#8f4650"),
    "SEN": ("#3a6b59", "#b29555"), "SUI": ("#8c3e46", "#4f6678"),
    "SWE": ("#4b6e82", "#b69b52"), "TUN": ("#8e4145", "#5c6571"),
    "TUR": ("#8d3f4a", "#496477"), "USA": ("#3f5f7d", "#99505a"),
    "URU": ("#4e7a8a", "#d0c5a8"), "UZB": ("#4a7185", "#b49a5c"),
    "DEFAULT": ("#456274", "#9a8f80"),
}


def _hex_rgb(value: str) -> str:
    value = value.lstrip("#")
    return ",".join(str(int(value[i : i + 2], 16)) for i in (0, 2, 4))


def country_palette(team_name: object) -> tuple[str, str, str, str, str]:
    """Return code, muted accent colours, and CSS-ready RGB triplets."""
    team = str(team_name or "")
    candidate = team.upper()
    code = candidate if candidate in COUNTRY_PALETTES else TEAM_CODES.get(team, "DEFAULT")
    primary, secondary = COUNTRY_PALETTES.get(code, COUNTRY_PALETTES["DEFAULT"])
    return code, primary, secondary, _hex_rgb(primary), _hex_rgb(secondary)


def _key(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", text.casefold())


def _short_key(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char)).casefold()
    parts = re.findall(r"[a-z0-9]+", text)
    return "".join((parts[0], parts[-1])) if len(parts) > 1 else "".join(parts)


def _tokens(value: object) -> list[str]:
    """Split a name into lowercase alphanumeric tokens.

    Also splits glued names such as ``RODRIGUESGarry`` (no space in source
    data) on camel-case boundaries so shirt-name matching still works.
    """
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", text)
    return re.findall(r"[a-z0-9]+", text.casefold())


def _description(value: object) -> str:
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and item.get("Description"):
                return str(item["Description"])
    return str(value or "")


@st.cache_data(show_spinner=False)
def _player_photo_maps() -> tuple[dict[str, str], dict[str, str]]:
    """Build exact name → URL plus unambiguous single-token → URL maps."""
    exact: dict[str, str] = {}
    token_urls: dict[str, set[str]] = {}
    for path in sorted(FIFA_RAW.glob("match_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for side in ("HomeTeam", "AwayTeam"):
            team = payload.get(side) or {}
            for player in team.get("Players") or []:
                picture = player.get("PlayerPicture") or {}
                url = picture.get("PictureUrl")
                if not url:
                    continue
                names = (
                    _description(player.get("PlayerName")),
                    _description(player.get("ShortName")),
                )
                for name in names:
                    if not name:
                        continue
                    exact.setdefault(_key(name), str(url))
                    exact.setdefault(_short_key(name), str(url))
                    for token in _tokens(name):
                        if len(token) >= 4:
                            token_urls.setdefault(token, set()).add(str(url))
    single = {token: next(iter(urls)) for token, urls in token_urls.items() if len(urls) == 1}
    return exact, single


def player_photo_url(player_name: object) -> str | None:
    """Resolve a FIFA portrait URL, tolerating full-legal-name variants.

    Match order: exact key → first+last short key → unambiguous single
    name token (last, first, then middle). Token matches only apply when
    the token identifies exactly one photo, so common surnames never map
    to the wrong player — they fall back to the generated avatar instead.
    """
    exact, single = _player_photo_maps()
    hit = exact.get(_key(player_name)) or exact.get(_short_key(player_name))
    if hit:
        return hit
    tokens = [t for t in _tokens(player_name) if len(t) >= 4]
    ordered = ([tokens[-1]] if tokens else []) + tokens[:1] + tokens[1:-1]
    for token in ordered:
        if token in single:
            return single[token]
    return None


def _portrait_fallback(player_name: object) -> str:
    """Create a colourful self-contained portrait for players without FIFA media."""
    name = str(player_name or "Player")
    initials = "".join(part[:1] for part in name.split()[:2]).upper() or "P"
    palettes = (
        ("#ff4d35", "#7a1026"), ("#22b8cf", "#123e7a"),
        ("#f4c542", "#b73b17"), ("#7c5cff", "#2c176f"),
        ("#31c48d", "#0c5b4b"), ("#ff6fae", "#71285d"),
    )
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    start, end = palettes[digest[0] % len(palettes)]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="640" viewBox="0 0 480 640">
    <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{start}"/><stop offset="1" stop-color="{end}"/></linearGradient></defs>
    <rect width="480" height="640" fill="url(#g)"/><circle cx="395" cy="92" r="150" fill="#fff" opacity=".1"/>
    <circle cx="240" cy="230" r="105" fill="#171717" opacity=".88"/><path d="M62 640c12-190 83-288 178-288s166 98 178 288" fill="#171717" opacity=".88"/>
    <text x="32" y="596" fill="#fff" font-family="Arial,sans-serif" font-size="50" font-weight="700" letter-spacing="4">{escape(initials)}</text>
    </svg>'''
    return "data:image/svg+xml," + quote(svg, safe="")


def flag_url(team_name: object = "", fifa_code: object = "") -> str:
    code = str(fifa_code or "").upper().strip()
    if not code or len(code) != 3:
        code = TEAM_CODES.get(str(team_name), "")
    return f"https://api.fifa.com/api/v3/picture/flags-sq-4/{code}" if code else ""


def flag_image(team_name: object, fifa_code: object = "", class_name: str = "media-flag") -> str:
    name = str(team_name or "Team")
    code = str(fifa_code or TEAM_CODES.get(name, "—")).upper()
    url = flag_url(name, fifa_code)
    image = (
        f'<img src="{escape(url, quote=True)}" alt="{escape(name)} flag" loading="lazy" '
        'referrerpolicy="no-referrer">'
        if url else ""
    )
    return (
        f'<span class="{escape(class_name, quote=True)}" aria-label="{escape(name)} flag">'
        f'<span>{escape(code)}</span>{image}</span>'
    )


def player_portrait(player_name: object, class_name: str = "player-portrait") -> str:
    name = str(player_name or "Player")
    initials = "".join(part[:1] for part in name.split()[:2]).upper() or "P"
    url = player_photo_url(name)
    fallback = _portrait_fallback(name)
    # The editorial Players profile has enough room to benefit from a 2x
    # source. Keep compact cards on the lighter 720x960 variant so a large
    # profile image does not make every table row slower to load.
    profile_portrait = any(
        token in class_name.split()
        for token in ("pp-profile-portrait", "h2h-profile-portrait")
    )
    transform_size = "height:1920,width:1440" if profile_portrait else "height:960,width:720"
    source = f"{url}?io=transform:fill,{transform_size}" if url else fallback
    loading = "eager" if profile_portrait else "lazy"
    image = (
        f'<img src="{escape(source, quote=True)}" alt="Portrait of {escape(name)}" '
        f'loading="{loading}" referrerpolicy="no-referrer" '
        f'onerror="this.onerror=null;this.src=\'{escape(fallback, quote=True)}\'">'
    )
    return (
        f'<span class="{escape(class_name, quote=True)}" aria-label="Portrait of {escape(name)}">'
        f'<span>{escape(initials)}</span>{image}</span>'
    )


def render_photo_story(
    kicker: str,
    line_one: str,
    line_two: str,
    description: str,
    *,
    index: str = "2026",
    page: str = "overview",
    overview_story: bool = False,
    show_title: bool = True,
) -> None:
    """Render the La Dolfina Jumping Overview experience or page-specific cover hero."""
    page_key = re.sub(r"[^a-z0-9-]", "", page.casefold().replace("_", "-")) or "overview"
    hero_assets = {
        "overview": ("images.webp", "FIFA World Cup 2026 tournament hero artwork"),
        "matches": ("hero-matches-v1.png", "A match ball on the centre circle under stadium lights"),
        "teams": ("hero-teams-v1.png", "A national squad preparing together in the stadium tunnel"),
        "players": ("hero-players-v1.png", "Two football players facing each other under floodlights"),
        "ml": ("hero-ml-v1.png", "An overhead football tactics and analytics workspace"),
        "best-xi": ("hero-best-xi-v1.png", "A team dressing room ready for the starting eleven"),
        "match-detail": ("hero-match-detail-v1.png", "Two football players contesting the ball during a match"),
    }
    asset_name, alt_text = hero_assets.get(page_key, hero_assets["overview"])

    if overview_story:
        # La Dolfina Jumping Inspired Architecture for Overview
        hero_desktop = static_variant(asset_name, "")
        hero_tablet = static_variant(asset_name, "-tablet")
        hero_mobile = static_variant(asset_name, "-mobile")

        # 1. Portal hero: WORLD CUP 2026 event identity (real DB dates).
        #    Title halves split on scroll; panels/du dots driven by JS.
        hero_html = (
            '<header class="portal page-overview" id="hero">'
            '<div class="portal-stage">'
            '<div class="portal-field">'
            '<picture class="portal-picture">'
            f'<source media="(max-aspect-ratio: 4 / 5)" srcset="{static_url(hero_mobile)}">'
            f'<source media="(max-aspect-ratio: 4 / 3)" srcset="{static_url(hero_tablet)}">'
            f'<img src="{static_url(hero_desktop)}" alt="{escape(alt_text, quote=True)}" '
            'class="portal-img" loading="eager" fetchpriority="high">'
            '</picture>'
            '<div class="portal-duo" aria-hidden="true"></div>'
            '<div class="portal-veil" aria-hidden="true"></div>'
            '<div class="portal-panel portal-left" aria-hidden="true"></div>'
            '<div class="portal-panel portal-right" aria-hidden="true"></div>'
            '<div class="portal-cup" aria-hidden="true">'
            f'<img src="{static_url("tải xuống.png")}" alt="" loading="eager" decoding="async">'
            '</div>'
            '<div class="portal-dates">'
            '<div><strong>11</strong><span>JUNE</span></div>'
            '<div class="portal-dates-sep">—</div>'
            '<div><strong>19</strong><span>JULY</span></div>'
            '</div>'
            '<div class="portal-event">'
            '<span class="portal-corner tl" aria-hidden="true"></span>'
            '<span class="portal-corner br" aria-hidden="true"></span>'
            'UNITED 2026 · USA — MEXICO — CANADA · 16 VENUES'
            '</div>'
            '<div class="portal-champ">'
            'FINAL · SPAIN 1 – 0 ARGENTINA · METLIFE STADIUM'
            '</div>'
            '<canvas class="portal-lines" aria-hidden="true"></canvas>'
            '<div class="portal-meta portal-meta-top"><span>WORLD CUP / 2026</span><span>THE DATA ARCHIVE</span></div>'
            '<div class="portal-meta portal-meta-bottom"><span>48 NATIONS · 104 MATCHES</span><span>SCROLL TO OPEN ↓</span></div>'
            '</div>'
            '</div>'
            '</header>'
        )

        st.markdown(hero_html, unsafe_allow_html=True)

        # 4. Companion Runtime Script for Native Smooth Anchors, Portal, and Film Reveals
        st.iframe(
            """<script>
(function() {
  var pWin = null;
  var pDoc = null;
  try {
    pWin = window.parent;
    pDoc = window.parent.document;
  } catch(e) {
    return;
  }
  if (!pDoc || !pWin) return;

  // Hide the host iframe container
  try {
    var fe = window.frameElement;
    if (fe) {
      var c = fe.closest('div[data-testid="stElementContainer"]') || fe.parentElement;
      if (c) c.style.display = 'none';
    }
  } catch(e) {}

  // 1. Native smooth anchor scrolling (no wheel hijack: Lenis removed —
  //    it fought Streamlit's scroll container and caused stutter).
  //    CSS `scroll-behavior: smooth` on .stMain handles the animation.
  //    No click handlers: default anchor jumps are left intact.

  // 2. Parallax Motion without sticky pinning.
  //     Single rAF-throttled pass: batch all reads first, then all writes,
  //     so scrolling never triggers forced synchronous layout (the stutter).
  //     Skipped entirely under prefers-reduced-motion.
  var reduceMotion = false;
  try {
    reduceMotion = pWin.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch(e) {}
  // 2. Film autoplay management is handled in section 6 below.

  // 3. Image Reveal via IntersectionObserver
  //     Under reduced-motion everything shows at once.
  //     Film cells / solo copy join the same one-shot reveal system.
  function initReveals() {
    try {
      if (!reduceMotion) pDoc.documentElement.classList.add('film-motion');
    } catch(e) {}
    var revealEls = pDoc.querySelectorAll('.film-cell, .film-solo-copy, .section-header, .kpi-sport-card, .leaderboard-card, .match-card-grid, div[data-testid="stDataFrame"]');
    if (!revealEls.length) return;

    if ('IntersectionObserver' in pWin && !reduceMotion) {
      var observer = new pWin.IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-revealed');
            observer.unobserve(entry.target);
          }
        });
      }, {
        rootMargin: '0px 0px -5% 0px',
        threshold: 0.12
      });

      revealEls.forEach(function(el) {
        observer.observe(el);
      });
    } else {
      revealEls.forEach(function(el) { el.classList.add('is-revealed'); });
    }
  }
  initReveals();
  setTimeout(initReveals, 500);

  // 4. Custom cursor removed (native cursor only).

  // 5. Motion gate: .portal-live is added ONLY when motion is allowed,
  //    so reduced-motion / no-JS renders show the finished page.
  var motionOk = false;
  try {
    motionOk = !reduceMotion;
  } catch(e) {}

  // 6. Film autoplay management: play only while visible, pause off-screen
  //    (saves battery/CPU with 5 looping videos); static poster frame
  //    under reduced-motion.
  function initFilms() {
    var vids = pDoc.querySelectorAll('.film-vid, .film-solo-vid');
    if (!vids.length) return;
    vids.forEach(function(v) {
      v.muted = true;
      if (reduceMotion) { try { v.pause(); } catch(e) {} return; }
    });
    if (reduceMotion || !('IntersectionObserver' in pWin)) return;
    var obs = new pWin.IntersectionObserver(function(entries) {
      entries.forEach(function(en) {
        var v = en.target;
        if (!v.isConnected) { obs.unobserve(v); return; }
        try {
          if (en.isIntersecting) { v.play(); }
          else { v.pause(); }
        } catch(e) {}
      });
    }, { threshold: 0.12 });
    vids.forEach(function(v) {
      if (v.__filmInit) return;
      v.__filmInit = true;
      obs.observe(v);
    });
  }
  initFilms();
  setTimeout(initFilms, 800);

  // 7. Portal hero bound to SCROLL POSITION (reversible both ways).
  //    Closed state is applied here (never in CSS) so no-JS stays open.
  var portalQueued = false;
  function portalProgress() {
    var hero = pDoc.querySelector('.portal');
    if (!hero) return -1;
    var rect = hero.getBoundingClientRect();
    var vh = pWin.innerHeight || 800;
    var travel = Math.max(rect.height - vh, 1);
    var p = -rect.top / travel;
    return Math.min(1, Math.max(0, p));
  }
  function updatePortal() {
    if (!motionOk || portalQueued) return;
    portalQueued = true;
    pWin.requestAnimationFrame(function() {
      portalQueued = false;
      var hero = pDoc.querySelector('.portal');
      if (!hero || !hero.classList.contains('portal-live')) return;
      var p = portalProgress();
      if (p < 0) return;
      var panels = hero.querySelectorAll('.portal-panel');
      var halves = hero.querySelectorAll('.portal-half');
      var img = hero.querySelector('.portal-img');
      var duo = hero.querySelector('.portal-duo');
      // Info copy + streak field fade out as the portal opens (nothing lingers).
      var fade = hero.querySelectorAll(
        '.portal-cup,.portal-lines,.portal-dates,.portal-event,.portal-champ,.portal-meta');
      for (var k = 0; k < fade.length; k++) {
        fade[k].style.opacity = Math.max(0, 1 - p * 1.6).toFixed(3);
      }
      if (panels[0]) panels[0].style.transform = 'translateX(' + (-p * 115).toFixed(2) + '%)';
      if (panels[1]) panels[1].style.transform = 'translateX(' + (p * 115).toFixed(2) + '%)';
      if (title) {
        title.style.transform = 'translateY(-50%) scale(' + (1 + p * 0.28).toFixed(3) + ')';
        title.style.letterSpacing = (6 - p * 16).toFixed(1) + 'px';
      }
      if (halves[0]) halves[0].style.transform = 'translateX(' + (-p * 55).toFixed(2) + '%)';
      if (halves[1]) halves[1].style.transform = 'translateX(' + (p * 55).toFixed(2) + '%)';
      if (img) img.style.transform = 'scale(' + (1.09 - p * 0.09).toFixed(3) + ')';
      if (duo) duo.style.opacity = (p * 0.28).toFixed(3);
    });
  }
  function initPortal() {
    var hero = pDoc.querySelector('.portal');
    if (!hero || !motionOk) return;
    hero.classList.add('portal-live');
    updatePortal();
  }
  if (!pWin.__portalBound) {
    pWin.__portalBound = true;
    pWin.addEventListener('scroll', updatePortal, { passive: true });
    var mainEl = pDoc.querySelector('[data-testid="stMain"]');
    if (mainEl) mainEl.addEventListener('scroll', updatePortal, { passive: true });
  }
  initPortal();
  setTimeout(initPortal, 800);

  // Hero streak-field canvas: light streaks travelling across the whole
  //    hero screen (static frame under reduced-motion; paused off-screen).
  function initCupLines() {
    var cv = pDoc.querySelector('.portal-lines');
    if (!cv || !cv.getContext || cv.__streakInit) return;
    cv.__streakInit = true;
    var ctx = cv.getContext('2d');
    var W = 0, H = 0, parts = [], targets = [], cup = { x: 0, y: 0, w: 120 };
    var running = true, drawn = false, t0 = 0;
    var BLUE = ['91,192,222', '46,139,192', '242,241,236'];
    var CYCLE = 9500;
    function size() {
      var r = cv.getBoundingClientRect();
      W = Math.max(320, Math.floor(r.width));
      H = Math.max(200, Math.floor(r.height));
      cv.width = W; cv.height = H;
    }
    function relRect(el) {
      var a = el.getBoundingClientRect(), b = cv.getBoundingClientRect();
      return { x: a.left - b.left, y: a.top - b.top, w: a.width, h: a.height };
    }
    function buildTargets() {
      targets = [];
      try {
        // No HTML title anymore: particles draw the words themselves.
        var off = pDoc.createElement('canvas');
        off.width = W; off.height = H;
        var o = off.getContext('2d');
        o.fillStyle = '#fff';
        o.textAlign = 'center';
        o.textBaseline = 'middle';
        var fs = Math.max(32, Math.round(H * 0.16));
        o.font = '600 ' + fs + 'px "Arial Narrow", Arial, sans-serif';
        o.fillText('WORLD CUP', W / 2, H * 0.70 - 30);
        o.fillText('2026', W / 2, H * 0.88 - 30);
        var img = o.getImageData(0, 0, W, H).data;
        var step = Math.max(2, Math.round(W / 320));
        for (var y = 0; y < H; y += step) {
          for (var x = 0; x < W; x += step) {
            if (img[((y * W) + x) * 4 + 3] > 128) targets.push([x, y]);
          }
        }
        while (targets.length > 1100) {
          targets = targets.filter(function(_, i) { return i % 2 === 0; });
        }
      } catch(e) { targets = []; }
      try {
        var cupEl = pDoc.querySelector('.portal-cup');
        if (cupEl) {
          var c = relRect(cupEl);
          cup = { x: c.x + c.w / 2, y: c.y + c.h / 2, w: Math.max(60, c.w) };
        }
      } catch(e) {}
    }
    function seed() {
      buildTargets();
      parts = [];
      var n = Math.max(targets.length, 120);
      for (var i = 0; i < n; i++) {
        var t = targets.length ? targets[i % targets.length] : [Math.random() * W, Math.random() * H];
        parts.push({
          x: Math.random() * W, y: Math.random() * H,
          tx: t[0], ty: t[1],
          ang: Math.random() * Math.PI * 2,
          rx: cup.w * (0.75 + Math.random() * 0.55),
          ry: cup.w * (0.32 + Math.random() * 0.12),
          sp: (0.004 + Math.random() * 0.010) * (Math.random() < 0.5 ? 1 : -1),
          ci: i % 3, a: 0.85 + Math.random() * 0.15,
          sz: 1.8, dl: Math.random() * 0.06
        });
      }
      t0 = pWin.performance ? pWin.performance.now() : Date.now();
    }
    function heroOpen() {
      try {
        if (typeof portalProgress === 'function' && portalProgress() > 0.2) return true;
      } catch(e) {}
      return false;
    }
    var lastT = 0, lastPhase = 0;
    function frame(now) {
      if (!running) { drawn = false; return; }
      if (!cv.isConnected) { running = false; drawn = false; return; }
      drawn = true;
      var nowMs = now || 0;
      var dt = Math.min(0.05, Math.max(0.001, (nowMs - (lastT || nowMs)) / 1000));
      lastT = nowMs;
      var phase = 1;
      if (t0) phase = ((nowMs - t0) % CYCLE) / CYCLE;
      if (phase < 0) phase += Math.ceil(-phase) + 1, phase = phase % 1;
      var open = heroOpen();
      if (open || !targets.length) {
        // Hero open (or no glyph targets): orbit only; refresh layout
        // only on cycle wrap so scrolling stays cheap.
        if (phase < lastPhase) { buildTargets(); seed(); }
        phase = 1;
      }
      lastPhase = phase;
      ctx.clearRect(0, 0, W, H);
      for (var i = 0; i < parts.length; i++) {
        var P = parts[i];
        var gx, gy, k;
        if (phase < 0.42 && !heroOpen()) {
          // Converge into the title glyphs (with per-dot delay).
          var lp = Math.min(1, Math.max(0, (phase - P.dl) / 0.3));
          var e = lp * lp * (3 - 2 * lp);
          gx = P.x + (P.tx - P.x) * Math.min(1, e * 1.15);
          gy = P.y + (P.ty - P.y) * Math.min(1, e * 1.15);
          k = 4;
        } else {
          // Released: wide sparse ellipse around the cup (fits the frame).
          P.ang += P.sp * (dt * 60);
          gx = cup.x + Math.cos(P.ang) * P.rx;
          gy = cup.y + Math.sin(P.ang) * P.ry;
          k = 2.2;
        }
        P.x += (gx - P.x) * Math.min(1, dt * k * 60 * 0.06 + 0.04);
        P.y += (gy - P.y) * Math.min(1, dt * k * 60 * 0.06 + 0.04);
        ctx.fillStyle = 'rgba(' + BLUE[P.ci] + ',' + P.a.toFixed(2) + ')';
        ctx.beginPath();
        ctx.arc(P.x, P.y, P.sz * 3.4, 0, Math.PI * 2);
        ctx.globalAlpha = 0.16;
        ctx.fill();
        ctx.globalAlpha = 0.4;
        ctx.beginPath();
        ctx.arc(P.x, P.y, P.sz * 2.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
        ctx.fillStyle = 'rgba(255,255,255,1)';
        ctx.beginPath();
        ctx.arc(P.x, P.y, P.sz, 0, Math.PI * 2);
        ctx.fill();
      }
      if (!reduceMotion) pWin.requestAnimationFrame(frame);
    }
    function kick() {
      size(); seed();
      if (reduceMotion) { running = true; frame(); running = false; return; }
      if (!drawn) frame();
    }
    size(); seed();
    if ('IntersectionObserver' in pWin) {
      new pWin.IntersectionObserver(function(es) {
        es.forEach(function(en) {
          running = en.isIntersecting;
          if (running) frame();
        });
      }, { threshold: 0.02 }).observe(cv);
    }
    pWin.addEventListener('resize', kick);
    kick();
  }
  initCupLines();
  setTimeout(initCupLines, 800);

  // 10. Streamlit re-renders replace canvas/DOM nodes, killing running
  //     loops bound to dead elements. Re-init (debounced) on DOM changes
  //     so effects never disappear after reruns or late image loads.
  var domTimer = null;
  function reinitDynamic() {
    initCupLines();
    initPortal();
    initFilms();
  }
  try {
    if ('MutationObserver' in pWin && pDoc.body) {
      new pWin.MutationObserver(function() {
        if (domTimer) pWin.clearTimeout(domTimer);
        domTimer = pWin.setTimeout(reinitDynamic, 600);
      }).observe(pDoc.body, { childList: true, subtree: true });
    }
  } catch(e) {}
})();
</script>""",
            # Hidden helper frame (its own container is display:none at runtime).
            # Height must be a positive int per Streamlit validation.
            height=8,
            width="stretch",
            tab_index=-1,
        )
        return

    # Default Cover Hero for other pages
    hero_markup = (
        f'<img class="photo-story-image" src="{static_url(asset_name)}" '
        f'alt="{escape(alt_text, quote=True)}">'
    )
    story_label = (line_one + " " + line_two).strip() or kicker
    title_markup = (
        f'<h1><span>{escape(line_one)}</span><span>{escape(line_two)}</span></h1>'
        if show_title else ''
    )

    st.markdown(
        f'<section class="photo-story-shell is-cover page-{page_key}" aria-label="{escape(story_label)}">'
        '<div class="photo-story-stage">'
        + hero_markup
        + '<div class="photo-story-shade" aria-hidden="true"></div>'
        '<div class="photo-story-rule" aria-hidden="true"></div>'
        f'<div class="photo-story-top"><span>{escape(kicker)}</span><span>{escape(index)}</span></div>'
        '<div class="photo-story-copy">'
        + title_markup
        + f'<div class="photo-story-foot"><p>{escape(description)}</p>'
        '<span>SCROLL TO EXPLORE ↓</span></div></div>'
        '</div></section>',
        unsafe_allow_html=True,
    )


def render_film_sections() -> None:
    """Render solo feature film + 3-in-1 highlight frame on Overview.

    Videos are local files in src/app/static (autoplay muted loop).
    Missing files fall back to poster images so the layout never breaks.
    """
    clips = [
        {"file": "15552725_3840_2160_30fps.mp4", "poster": "football-story-grid-v1.webp",
         "label": "AERIAL FILM", "alt": "Aerial stadium film"},
        {"file": "YTSave_YouTube_Media_e6a6lppWZkQ_Ferran-Torres-Goal-Spain-1-0-Argentina-FIFA-World-Cup-2026-FINAL_002_720p.mp4",
         "poster": "worldcup-story-02-legends-v1.webp",
         "label": "FINAL WINNER", "alt": "Ferran Torres final winning goal"},
        {"file": "YTSave_YouTube_Media_ihVQ60ftXMQ_Hyundai-Goal-of-the-Tournament-FINAL-WINNER-FIFA-World-Cup-2026_003_480p.mp4",
         "poster": "worldcup-story-03-future-v1.webp",
         "label": "GOAL OF THE TOURNAMENT", "alt": "Goal of the tournament winner"},
    ]
    cells = ""
    for c in clips:
        src = static_url(c["file"])
        cells += (
            '<div class="film-cell">'
            f'<video class="film-vid" muted loop autoplay playsinline preload="metadata" '
            f'poster="{static_url(c["poster"])}" aria-label="{escape(c["alt"])}">'
            f'<source src="{src}" type="video/mp4">'
            '</video>'
            f'<div class="film-cap">{escape(c["label"])}</div>'
            '</div>'
        )
    strip_html = (
        '<section class="film-solo" aria-label="Tournament story film">'
        '<video class="film-solo-vid" muted loop autoplay playsinline preload="metadata" '
        f'poster="{static_url("worldcup-story-01-origin-v1.webp")}" aria-label="The story of the 2026 FIFA World Cup">'
        '<source src="'
        + static_url("YTSave_YouTube_Media_BRv3KW-NIQc_ABSOLUTE-CINEMA-The-Story-Of-The-2026-FIFA-World-Cup_002_720p.mp4")
        + '" type="video/mp4">'
        '</video>'
        '<div class="film-solo-shade" aria-hidden="true"></div>'
        '<div class="film-solo-copy">'
        '<div class="film-kicker">ABSOLUTE CINEMA / 145 SECONDS</div>'
        '<h2>THE STORY OF<br>UNITED 2026.</h2>'
        '</div>'
        '</section>'
        '<section class="film-strip" aria-label="World Cup highlights">'
        '<h2 class="film-title">MOMENTS THAT<br>MOVED THE WORLD.</h2>'
        f'<div class="film-row film-row-3">{cells}</div>'
        '</section>'
    )

    st.markdown(strip_html, unsafe_allow_html=True)
