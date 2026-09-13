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
    story_chapters: list[dict[str, str]] | None = None,
    show_title: bool = True,
) -> None:
    """Render a page-specific sticky hero and the optional Overview photo reel."""
    page_key = re.sub(r"[^a-z0-9-]", "", page.casefold().replace("_", "-")) or "overview"
    hero_assets = {
        "overview": ("hero-overview-fifa-2026-v1.png", "FIFA World Cup 2026 celebration with Cristiano Ronaldo and the World Cup trophy"),
        "matches": ("hero-matches-v1.png", "A match ball on the centre circle under stadium lights"),
        "teams": ("hero-teams-v1.png", "A national squad preparing together in the stadium tunnel"),
        "players": ("hero-players-v1.png", "Two football players facing each other under floodlights"),
        "ml": ("hero-ml-v1.png", "An overhead football tactics and analytics workspace"),
        "best-xi": ("hero-best-xi-v1.png", "A team dressing room ready for the starting eleven"),
        "match-detail": ("hero-match-detail-v1.png", "Two football players contesting the ball during a match"),
    }
    asset_name, alt_text = hero_assets.get(page_key, hero_assets["overview"])
    chapter_sets = {
        "NATIONAL": ("THE SQUAD", "THE BADGE", "THE PLAN", "THE CROWD"),
        "PLAYER": ("THE ARRIVAL", "THE TOUCH", "THE VISION", "THE MOMENT"),
        "HEAD-TO-HEAD": ("TWO SIDES", "THE DETAIL", "THE SHAPE", "THE EDGE"),
        "MACHINE": ("RAW SIGNAL", "THE FEATURE", "THE PATTERN", "THE OUTLIER"),
        "SQUAD OPTIMIZATION": ("THE POOL", "THE ROLE", "THE SHAPE", "THE ELEVEN"),
        "MATCH CALENDAR": ("ARRIVAL", "THE BALL", "THE PLAN", "MATCHDAY"),
    }
    chapters = next(
        (items for token, items in chapter_sets.items() if token in kicker.upper()),
        ("THE STAGE", "THE BALL", "THE PLAN", "ONE WORLD"),
    )
    scene_notes = (
        "Before the whistle / anticipation",
        "Technique under pressure / decisive detail",
        "Reading space / shaping the match",
        "Nations together / one tournament",
    )
    reel_panels = "".join(
        '<article class="editorial-reel-panel reel-panel-' + str(number) + '">'
        '<div class="editorial-reel-image" role="img" aria-label="' + escape(note) + '"></div>'
        '<div class="editorial-reel-shade" aria-hidden="true"></div>'
        '<div class="editorial-reel-caption"><span>0' + str(number) + ' / 04</span>'
        '<small>' + escape(note) + '</small><h2>' + escape(title) + '</h2></div></article>'
        for number, (title, note) in enumerate(zip(chapters, scene_notes), start=1)
    )

    chronicle_panels = ""
    story_items = (story_chapters or [])[:3]
    for number, chapter in enumerate(story_items, start=1):
        title_html = "<br>".join(escape(str(chapter.get("title", ""))).splitlines())
        chapter_image = str(chapter.get("image", ""))
        chronicle_panels += (
            '<article class="worldcup-chronicle-panel chronicle-panel-' + str(number) + '">'
            '<div class="worldcup-chronicle-frame">'
            '<div class="worldcup-chronicle-media"><img src="' + static_url(chapter_image)
            + '" alt="' + escape(str(chapter.get("alt", "World Cup story chapter")), quote=True) + '">'
            '</div><div class="worldcup-chronicle-copy">'
            '<header><span>THE WORLD CUP CHRONICLE</span><span>0' + str(number) + ' / 0'
            + str(len(story_items)) + '</span></header>'
            '<div class="worldcup-chronicle-body">'
            '<span class="worldcup-chronicle-kicker">' + escape(str(chapter.get("kicker", "CHAPTER"))) + '</span>'
            '<small>' + escape(str(chapter.get("date", ""))) + '</small>'
            '<h2>' + title_html + '</h2><p>' + escape(str(chapter.get("copy", ""))) + '</p>'
            '<div class="worldcup-chronicle-stat"><strong>' + escape(str(chapter.get("stat", number)))
            + '</strong><span>' + escape(str(chapter.get("label", "CHAPTER"))) + '</span></div>'
            '</div></div></div></article>'
        )
    story_class = " is-overview" if overview_story else " is-cover"
    # Order on Overview: hero → chronicle (3 history chapters) → reel.
    # Other pages render no story sections at all.
    story_html = ""
    if overview_story:
        if chronicle_panels:
            story_html += (
                '<section class="worldcup-chronicle" aria-label="Three chapters from World Cup history">'
                + chronicle_panels + '</section>'
            )
        story_html += (
            '<section class="editorial-reel" aria-label="Four visual tournament summary chapters">'
            '<div class="editorial-reel-stage">' + reel_panels + '</div></section>'
        )
    story_label = (line_one + " " + line_two).strip() or kicker
    title_markup = (
        '<h1><span>' + escape(line_one) + '</span><span>' + escape(line_two) + '</span></h1>'
        if show_title else ''
    )
    st.markdown(
        '<section class="photo-story-shell' + story_class + ' page-' + page_key + '" aria-label="' + escape(story_label) + '">'
        '<div class="photo-story-stage">'
        '<img class="photo-story-image" src="' + static_url(asset_name) + '" '
        'alt="' + escape(alt_text, quote=True) + '">'
        '<div class="photo-story-shade" aria-hidden="true"></div>'
        '<div class="photo-story-rule" aria-hidden="true"></div>'
        '<div class="photo-story-top"><span>' + escape(kicker) + '</span><span>' + escape(index) + '</span></div>'
        '<div class="photo-story-copy">'
        + title_markup
        + '<div class="photo-story-foot"><p>' + escape(description) + '</p>'
        '<span>SCROLL TO EXPLORE ↓</span></div></div>'
        '</div></section>' + story_html,
        unsafe_allow_html=True,
    )
