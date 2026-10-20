#!/usr/bin/env python3
"""Build the Bantuan Sarawak static directory into dist/."""

from __future__ import annotations

import html
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from kit.analytics_loader import (  # noqa: E402
    ANALYTICS_LOADER_ATTR,
    ANALYTICS_MAX_AGE,
    render_analytics_loader as kit_render_analytics_loader,
)
from kit.analytics_registry import AnalyticsRegistry, load_analytics  # noqa: E402
from kit.shell import NavItem, render_back_to_top, render_footer as kit_render_footer  # noqa: E402
from kit.shell import render_header as kit_render_header  # noqa: E402

DATA = ROOT / "data"
DIST = ROOT / "dist"
SITE_DIR = ROOT / "site"
ICON_DIR = ROOT / "assets" / "phosphor"
SITE_META_PATH = DATA / "site.json"

# Site title, tagline, description, and About lead live only in data/site.json.
SITE_COPY_FIELDS = ("title", "tagline", "description", "about_lead")

# Footer summary note (site-specific; longer than the short description).
FOOTER_BRAND_NOTE = (
    "An independent directory of Sarawak government assistance. Every scheme "
    "links to an official page. This website does not take applications."
)

FOOTER_CREDIT_HTML = (
    'Built by <a class="site-footer-link site-footer-credit-link" '
    'href="https://hafiy.my" target="_blank" rel="noopener noreferrer">hafiy.my</a>, '
    "an independent publication. Not affiliated with the Sarawak Government."
)


def analytics_registry() -> AnalyticsRegistry:
    return load_analytics()


# Resolved once at import for tests that still read module-level names.
_ANALYTICS = analytics_registry()
GA_MEASUREMENT_ID = _ANALYTICS.primary_ga4_id()
CLOUDFLARE_WEB_ANALYTICS_TOKEN = _ANALYTICS.primary_cf_token()
GA_PRODUCTION_HOSTS = _ANALYTICS.hostnames
GA_INTERNAL_COOKIE = _ANALYTICS.internal_cookie
GA_INTERNAL_COOKIE_MAX_AGE = ANALYTICS_MAX_AGE
LEGACY_INTERNAL_COOKIES = tuple(_ANALYTICS.legacy_internal_cookies)
ANALYTICS_SPA = _ANALYTICS.spa


def render_analytics_loader(registry: AnalyticsRegistry | None = None) -> str:
    """Emit the shared kit analytics loader from ``data/analytics.json``."""
    return kit_render_analytics_loader(registry if registry is not None else analytics_registry())


def render_ga_script() -> str:
    """Alias for the unified registry loader (GA4 + CF)."""
    return render_analytics_loader()


OFFICIAL_HOSTS = {
    "ukas.sarawak.gov.my",
    "www.sarawak.gov.my",
    "service.sarawak.gov.my",
    "welfare.sarawak.gov.my",
    "www.jkm.gov.my",
    "myys.yayasansarawak.org.my",
    "yayasansarawak.org.my",
    "meitd.sarawak.gov.my",
    "hdc.sarawak.gov.my",
    "mudenr.sarawak.gov.my",
    "www.sarawakenergy.com",
    "apply-sras.ireka.my",
    "kpwk.sarawak.gov.my",
    "isarawakcare.sarawak.gov.my",
    "jwks.sarawak.gov.my",
    "mficord.sarawak.gov.my",
    "www.kpkm.gov.my",
    "app-egam.kpkm.gov.my",
    "talikhidmat.sarawak.gov.my",
}

BANNED_PHRASES = (
    "wellbest",
    "spta",
    "siba",
    "gptp",
    "15 may",
    "48 months",
    "rm200 x",
    "rm200 ×",
    "rm200×",
    "i-gps",
)

FAVICON = (
    "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' "
    "viewBox='0 0 100 100'><text y='.9em' font-size='90'>🫶</text></svg>"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_site(path: Path = SITE_META_PATH) -> dict:
    """Load site meta and require title/tagline/description/about_lead."""
    if not path.is_file():
        raise SystemExit(f"missing site copy file: {path.relative_to(ROOT)}")
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise SystemExit("data/site.json must be an object")
    for field in SITE_COPY_FIELDS:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"data/site.json is missing {field}")
        payload[field] = value.strip()
    return payload


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def due_phrases(scheme: dict) -> list[str]:
    """Date phrases the builder wraps. A string, or a list when a card has more than one."""
    due = scheme.get("due")
    if due is None:
        return []
    scheme_id = scheme.get("id", "scheme")
    if isinstance(due, str):
        phrases = [due]
    elif isinstance(due, list):
        phrases = list(due)
    else:
        raise SystemExit(f"{scheme_id} due must be a date phrase or a list of them")
    if not phrases or any(not isinstance(phrase, str) or not phrase.strip() for phrase in phrases):
        raise SystemExit(f"{scheme_id} due must be a non-empty date phrase")
    if len(phrases) != len(set(phrases)):
        raise SystemExit(f"{scheme_id} repeats a due phrase")
    for phrase in phrases:
        if "<" in phrase or ">" in phrase:
            raise SystemExit(f"{scheme_id} due phrase cannot contain HTML")
    return phrases


def copy_blocks(scheme: dict) -> list[str]:
    blocks = list(scheme.get("paragraphs") or [])
    if scheme.get("amount_note"):
        blocks.append(scheme["amount_note"])
    return blocks


def render_text_with_due(text: str, phrases: list[str]) -> str:
    """Escape text and wrap each due phrase that appears in this block. One pill per phrase."""
    hits = []
    for phrase in phrases:
        start = text.find(phrase)
        if start < 0:
            continue
        if text.find(phrase, start + len(phrase)) >= 0:
            raise SystemExit(f"Due phrase appears more than once in one block: {phrase}")
        hits.append((start, phrase))
    hits.sort()
    parts = []
    cursor = 0
    for start, phrase in hits:
        if start < cursor:
            raise SystemExit(f"Due phrases overlap: {phrase}")
        parts.append(esc(text[cursor:start]))
        parts.append(f'<span class="due-date">{esc(phrase)}</span>')
        cursor = start + len(phrase)
    parts.append(esc(text[cursor:]))
    return "".join(parts)


def check_scheme_source(scheme: dict) -> None:
    scheme_id = scheme["id"]
    links = scheme.get("links")
    if not isinstance(links, list) or len(links) != 1:
        raise SystemExit(f"{scheme_id} needs exactly one source link")
    check_official_url(links[0]["url"], scheme_id)
    phrases = due_phrases(scheme)
    blocks = copy_blocks(scheme)
    for phrase in phrases:
        found = sum(block.count(phrase) for block in blocks)
        if found != 1:
            raise SystemExit(f"{scheme_id} due phrase must appear once in the copy: {phrase}")
        for amount in scheme.get("amounts") or []:
            if phrase in amount:
                raise SystemExit(f"{scheme_id} due phrase is also in an amount: {phrase}")


def checked_label(iso_date: str) -> str:
    checked = datetime.strptime(iso_date, "%Y-%m-%d")
    return f"{checked.strftime('%A').upper()}, {checked.day} {checked.strftime('%b %Y').upper()}"


def validate(site: dict, schemes: list[dict]) -> None:
    group_ids = [group["id"] for group in site["groups"]]
    if len(group_ids) != len(set(group_ids)):
        raise SystemExit("Duplicate group id in data/site.json")
    seen = set()
    for scheme in schemes:
        scheme_id = scheme["id"]
        if scheme_id in seen:
            raise SystemExit(f"Duplicate scheme id: {scheme_id}")
        seen.add(scheme_id)
        if scheme["group"] not in group_ids:
            raise SystemExit(f"{scheme_id} uses unknown group {scheme['group']}")
        if scheme["level"] not in {"STATE", "FEDERAL"}:
            raise SystemExit(f"{scheme_id} level must be STATE or FEDERAL")
        basis = scheme["amount_basis"]
        if basis not in {"page", "attachment", "none"}:
            raise SystemExit(f"{scheme_id} has unknown amount_basis")
        amounts = scheme.get("amounts") or []
        if basis == "none":
            if amounts:
                raise SystemExit(f"{scheme_id} is amount_basis none but has amounts")
            if not scheme.get("copy_ordered") and not scheme.get("unspecified"):
                raise SystemExit(f"{scheme_id} needs an unspecified note")
        elif not amounts:
            raise SystemExit(f"{scheme_id} needs at least one amount")
        if not scheme.get("paragraphs"):
            raise SystemExit(f"{scheme_id} needs paragraphs")
        check_scheme_source(scheme)
    for group in site["groups"]:
        if group["id"] not in GROUP_ICONS:
            raise SystemExit(f"No heading icon for group {group['id']}")
        for link in group.get("links", []):
            check_official_url(link["url"], group["id"])
    for desk in site.get("desks", []):
        check_official_url(desk["url"], desk["name"])


def check_official_url(url: str, owner: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in OFFICIAL_HOSTS:
        raise SystemExit(f"Unofficial or invalid URL for {owner}: {url}")


def render_links(links: list[dict], class_name: str = "sources", indent: str = "      ") -> str:
    items = "\n".join(
        f'{indent}  <li><a href="{esc(link["url"])}" target="_blank" rel="noopener noreferrer">{esc(link["label"])}</a></li>'
        for link in links
    )
    return f"""{indent}<ul class="{class_name}">
{items}
{indent}</ul>"""


def render_scheme(
    scheme: dict,
    show_level: bool = False,
    rank: int | None = None,
    category_title: str | None = None,
) -> str:
    level = scheme["level"]
    basis = scheme["amount_basis"]
    # Full-width title bar: optional rank and title share one black header strip;
    # amounts, copy, and Source sit in the body below on the card surface.
    head = ["      <header class=\"scheme-head\">"]
    if rank is not None and category_title:
        head.append(
            "        <span class=\"scheme-rank\""
            f' aria-label="Item {rank} in {esc(category_title)}">{rank}</span>'
        )
    if show_level:
        level_word = "State" if level == "STATE" else "Federal"
        head.append(
            "          <p class=\"scheme-kicker\">\n"
            f"            <span class=\"level level-{level.lower()}\">{level_word}</span>\n"
            "          </p>"
        )
    head.append(f"        <h3>{esc(scheme['title'])}</h3>")
    head.append("      </header>")
    body = []
    if basis == "attachment":
        body.append('        <p class="basis">On an attachment</p>')
    if basis == "none" and not scheme.get("copy_ordered"):
        body.append(f'        <p class="unspecified">{esc(scheme["unspecified"])}</p>')
    elif basis != "none":
        many = " many" if len(scheme["amounts"]) > 1 else ""
        amounts = "\n".join(f"          <li>{esc(amount)}</li>" for amount in scheme["amounts"])
        body.append(f'        <ul class="amount-list{many}">\n{amounts}\n        </ul>')
    phrases = due_phrases(scheme)
    if scheme.get("copy_ordered"):
        copy_items = list(scheme["paragraphs"])
        if scheme.get("amount_note"):
            copy_items.append(scheme["amount_note"])
        items = "\n".join(
            f"          <li>{render_text_with_due(paragraph, phrases)}</li>" for paragraph in copy_items
        )
        body.append(f'        <ol class="scheme-copy">\n{items}\n        </ol>')
    else:
        paragraphs = "\n".join(
            f"          <p>{render_text_with_due(paragraph, phrases)}</p>" for paragraph in scheme["paragraphs"]
        )
        body.append(f'        <div class="scheme-copy">\n{paragraphs}\n        </div>')
        if scheme.get("amount_note"):
            body.append(
                f'        <p class="amount-note">{render_text_with_due(scheme["amount_note"], phrases)}</p>'
            )
    if scheme["links"]:
        body.append('        <h4 class="sources-title">Source</h4>')
        body.append(render_links(scheme["links"], indent="        "))
    return (
        f'    <article class="scheme" id="{esc(scheme["id"])}" data-level="{level.lower()}" data-amount-basis="{esc(basis)}">\n'
        f"{chr(10).join(head)}\n"
        f'      <div class="scheme-body">\n'
        f"{chr(10).join(body)}\n"
        f"      </div>\n"
        f"    </article>"
    )


# Category headings use Phosphor Icons, duotone weight (MIT). The SVG files in
# assets/phosphor are inlined here so the page does not fetch an icon CDN.
# The heading text stays the accessible name; the glyph is decorative.
GROUP_ICONS = {
    "household": "basket",
    "student": "graduation-cap",
    "housing": "house",
    "health": "heartbeat",
    "baby": "baby",
    "business": "storefront",
    "welfare": "hand-heart",
}


def icon_inner(name: str, fill_class: str) -> str:
    path = ICON_DIR / f"{name}-duotone.svg"
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        raise SystemExit(f"Missing Phosphor icon {name}: {path}") from None
    start = raw.find(">")
    end = raw.rfind("</svg>")
    if start == -1 or end == -1 or 'opacity="0.2"' not in raw:
        raise SystemExit(f"Phosphor icon {name} is not a duotone SVG")
    inner = raw[start + 1 : end].strip()
    marker = 'opacity="0.2"'
    if inner.count(marker) != 1:
        raise SystemExit(f"Phosphor icon {name} should have one duotone fill")
    return inner.replace(marker, f'class="{fill_class}" opacity="0.2"', 1)


def render_group_icon(group_id: str) -> str:
    try:
        name = GROUP_ICONS[group_id]
    except KeyError:
        raise SystemExit(f"No heading icon for group {group_id}") from None
    inner = icon_inner(name, "group-icon-fill")
    return (
        '<span class="group-icon-tile">'
        f'<svg class="group-icon" data-icon="{esc(name)}" viewBox="0 0 256 256" '
        'width="24" height="24" aria-hidden="true" focusable="false" fill="currentColor">'
        f"{inner}</svg></span>"
    )


# Still decorative network in the home brief. Same inlining pattern as the
# ai.sarawak.news hero: one aria-hidden SVG, positioned in CSS, not animated.
# Nodes are the seven category tiles. Coordinates are the viewBox of that SVG.
BRIEF_NET_NODES = (
    ("housing", 48, 48),
    ("household", 154, 75),
    ("student", 206, 38),
    ("health", 230, 112),
    ("welfare", 240, 170),
    ("baby", 330, 24),
    ("business", 372, 112),
)
BRIEF_NET_EDGES = (
    ("housing", "household"),
    ("household", "student"),
    ("household", "health"),
    ("student", "health"),
    ("student", "baby"),
    ("health", "welfare"),
    ("baby", "business"),
    ("welfare", "business"),
)
BRIEF_NET_TAILS = (
    ("baby", 412, 6),
    ("business", 414, 156),
    ("welfare", 404, 210),
)


def render_brief_net() -> str:
    points = {group_id: (x, y) for group_id, x, y in BRIEF_NET_NODES}
    lines = []
    for left, right in BRIEF_NET_EDGES:
        x1, y1 = points[left]
        x2, y2 = points[right]
        lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>')
    for group_id, x2, y2 in BRIEF_NET_TAILS:
        x1, y1 = points[group_id]
        lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>')
    nodes = []
    for group_id, x, y in BRIEF_NET_NODES:
        name = GROUP_ICONS[group_id]
        inner = icon_inner(name, "brief-net-fill")
        nodes.append(
            f'<g transform="translate({x} {y})">'
            '<rect class="brief-net-tile" x="-16" y="-16" width="32" height="32" rx="8"/>'
            f'<svg class="brief-net-icon" data-icon="{esc(name)}" x="-11" y="-11" width="22" height="22" '
            'viewBox="0 0 256 256" aria-hidden="true" focusable="false" fill="currentColor">'
            f"{inner}</svg></g>"
        )
    return (
        '<svg class="brief-net" role="presentation" viewBox="0 0 420 230" '
        'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
        '<g class="brief-net-lines" fill="none" stroke="currentColor" stroke-width="1.15" stroke-linecap="round">'
        f"{''.join(lines)}</g>"
        f"{''.join(nodes)}</svg>"
    )


def render_groups(site: dict, schemes: list[dict]) -> str:
    show_level = any(scheme["level"] == "FEDERAL" for scheme in schemes)
    blocks = []
    for group in site["groups"]:
        grouped = [scheme for scheme in schemes if scheme["group"] == group["id"]]
        cards = "\n".join(
            render_scheme(scheme, show_level, index, group["title"])
            for index, scheme in enumerate(grouped, 1)
        )
        blocks.append(
            f"""    <section class="group" id="{esc(group['id'])}" aria-labelledby="group-{esc(group['id'])}">
      <header class="group-head">
        <h2 id="group-{esc(group['id'])}">{render_group_icon(group['id'])}<span>{esc(group['title'])}</span></h2>
      </header>
      <div class="scheme-list">
{cards}
      </div>
    </section>"""
        )
    return "\n".join(blocks)


def render_category_filter(site: dict, schemes: list[dict]) -> str:
    buttons = [
        f'<button type="button" class="category-filter-button is-active" data-section-filter="all" '
        f'data-filter-label="All schemes" aria-pressed="true">All '
        f'<span class="category-filter-count" aria-hidden="true">{len(schemes)}</span></button>'
    ]
    for group in site["groups"]:
        count = sum(scheme["group"] == group["id"] for scheme in schemes)
        if not count:
            continue
        buttons.append(
            f'<button type="button" class="category-filter-button" data-section-filter="{esc(group["id"])}" '
            f'data-filter-label="{esc(group["title"])}" aria-pressed="false">{esc(group["title"])} '
            f'<span class="category-filter-count" aria-hidden="true">{count}</span></button>'
        )
    return f"""    <section class="category-filter" aria-labelledby="category-filter-title" data-category-filter>
      <p class="category-filter-title" id="category-filter-title">Browse by category</p>
      <div class="category-filter-scroll" data-category-scroll>
        <div class="category-filter-options">
          {' '.join(buttons)}
        </div>
        <span class="category-filter-hint category-filter-hint-start" aria-hidden="true"><span class="category-filter-chevron"></span></span>
        <span class="category-filter-hint category-filter-hint-end" aria-hidden="true"><span class="category-filter-chevron"></span></span>
      </div>
      <p class="visually-hidden" data-filter-status aria-live="polite">Showing all {len(schemes)} schemes</p>
    </section>"""


def render_header(site: dict, active: str) -> str:
    return kit_render_header(
        brand_title=site["title"],
        brand_href="/",
        active=active,
        nav_items=(
            NavItem("home", "/", "Home"),
            NavItem("about", "about.html", "About"),
        ),
    )


def render_footer(site: dict, active: str) -> str:
    group_links = "\n".join(
        f'          <li><a class="site-footer-link" href="/#{esc(group["id"])}">{esc(group["title"])}</a></li>'
        for group in site["groups"]
    )
    categories = (
        '        <h2 class="site-footer-categories-title">Categories</h2>\n'
        f"        <ul>\n{group_links}\n        </ul>\n"
    )
    return kit_render_footer(
        brand_title=site["title"],
        brand_note=FOOTER_BRAND_NOTE,
        active=active,
        explore_items=(
            NavItem("home", "/", "Home"),
            NavItem("about", "about.html", "About"),
        ),
        extra_nav_html=categories,
        credit_html=FOOTER_CREDIT_HTML,
    )


def theme_boot() -> str:
    return """  <script>
    document.documentElement.classList.add("js");
    try {
      const storedTheme = localStorage.getItem("sarawak-theme");
      if (storedTheme === "dark" || (storedTheme !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
        document.documentElement.dataset.theme = "dark";
      }
    } catch (error) {}
  </script>"""


def render_head(site: dict, title: str, description: str, canonical: str, og_title: str, structured: str) -> str:
    image = f"{site['url']}social-card.png"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="{esc(description)}" />
  <meta name="robots" content="index,follow" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{esc(og_title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:url" content="{esc(canonical)}" />
  <meta property="og:site_name" content="{esc(site['title'])}" />
  <meta property="og:image" content="{esc(image)}" />
  <meta property="og:image:alt" content="{esc(site['short_name'])}, a directory of Sarawak government assistance" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(og_title)}" />
  <meta name="twitter:description" content="{esc(description)}" />
  <meta name="twitter:image" content="{esc(image)}" />
  <link rel="canonical" href="{esc(canonical)}" />
  <title>{esc(title)}</title>
  <script type="application/ld+json">{structured}</script>
{theme_boot()}
  <link rel="icon" href="{FAVICON}" />
  <link rel="stylesheet" href="style.css" />
  <script src="app.js" defer></script>
  {render_analytics_loader()}
</head>"""


def json_ld(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_home(site: dict, schemes: list[dict]) -> str:
    url = site["url"]
    structured = json_ld(
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "WebSite",
                    "@id": f"{url}#website",
                    "url": url,
                    "name": site["title"],
                    "description": site["description"],
                    "inLanguage": "en",
                },
                {
                    "@type": "CollectionPage",
                    "@id": f"{url}#collection",
                    "url": url,
                    "name": site["tagline"],
                    "description": site["description"],
                    "isPartOf": {"@id": f"{url}#website"},
                    "dateModified": site["checked"],
                    "inLanguage": "en",
                },
                {
                    "@type": "ItemList",
                    "numberOfItems": len(schemes),
                    "itemListElement": [
                        {
                            "@type": "ListItem",
                            "position": index,
                            "name": scheme["title"],
                            "url": f"{url}#{scheme['id']}",
                        }
                        for index, scheme in enumerate(schemes, 1)
                    ],
                },
            ],
        }
    )
    body = f"""<body>
  <a class="skip-link" href="#content">Skip to content</a>
{render_header(site, "home")}
  <main id="content">
    <header class="brief">
      {render_brief_net()}
      <h1>{esc(site['tagline'])}</h1>
      <p class="brief-deck">{esc(site['description'])}</p>
      <p class="updated"><span class="updated-label">Last updated</span> <time datetime="{esc(site['checked'])}">{esc(checked_label(site['checked']))}</time></p>
    </header>
{render_category_filter(site, schemes)}
{render_groups(site, schemes)}
  </main>
{render_back_to_top()}
{render_footer(site, "home")}
</body>"""
    return render_head(site, site["og_title"], site["description"], url, site["og_title"], structured) + "\n" + body + "\n</html>\n"


def render_about(site: dict) -> str:
    url = f"{site['url']}about.html"
    sections = []
    for index, section in enumerate(site["about_sections"]):
        paragraphs = "\n".join(f"      <p>{esc(paragraph)}</p>" for paragraph in section["paragraphs"])
        sections.append(
            f"""    <section class="about-section" aria-labelledby="about-{esc(section['id'])}">
      <h2 id="about-{esc(section['id'])}">{esc(section['title'])}</h2>
{paragraphs}
    </section>"""
        )
    desks = "\n".join(
        f"""      <li>
        <strong>{esc(desk['name'])}</strong>
        <span>{esc(desk['detail'])}</span>
        <a href="{esc(desk['url'])}" target="_blank" rel="noopener noreferrer">{esc(desk['label'])}</a>
      </li>"""
        for desk in site["desks"]
    )
    structured = json_ld(
        {
            "@context": "https://schema.org",
            "@type": "AboutPage",
            "@id": f"{url}#about",
            "url": url,
            "name": site["about_seo_title"],
            "description": site["about_description"],
            "isPartOf": {"@id": f"{site['url']}#website"},
            "dateModified": site["checked"],
            "inLanguage": "en",
        }
    )
    body = f"""<body>
  <a class="skip-link" href="#content">Skip to content</a>
{render_header(site, "about")}
  <main id="content" class="about-page">
    <header class="about-hero">
      <h1>About {esc(site['short_name'])}</h1>
      <p class="about-lede">{esc(site['about_lead'])}</p>
    </header>
{chr(10).join(sections)}
    <section class="about-section" aria-labelledby="about-desks">
      <h2 id="about-desks">Official help desks</h2>
      <p>Questions about an application go to the office that runs the scheme. These desks are listed on official pages. This website does not answer applications.</p>
      <ul class="desks">
{desks}
      </ul>
    </section>
  </main>
{render_back_to_top()}
{render_footer(site, "about")}
</body>"""
    return (
        render_head(site, site["about_seo_title"], site["about_description"], url, site["about_seo_title"], structured)
        + "\n"
        + body
        + "\n</html>\n"
    )


def assert_safe(pages: list[str]) -> None:
    blob = "\n".join(pages).casefold()
    for phrase in BANNED_PHRASES:
        if phrase in blob:
            raise SystemExit(f"Banned phrase in build output: {phrase}")


def copy_site_fonts() -> None:
    source = SITE_DIR / "fonts"
    woff = source / "Geist-Variable.woff2"
    license_file = source / "OFL.txt"
    if not woff.is_file() or not license_file.is_file():
        raise SystemExit("site/fonts must contain Geist-Variable.woff2 and OFL.txt")
    target = DIST / "fonts"
    target.mkdir()
    shutil.copy2(woff, target / woff.name)
    shutil.copy2(license_file, target / license_file.name)


def copy_nav_marks() -> None:
    """Publish nav marks from the vendored kit (site/icons mirrors kit/assets/icons)."""
    icons_dist = DIST / "icons"
    icons_dist.mkdir()
    for mark_name in ("nav-mark-transparent.svg", "nav-mark-transparent-dark.svg"):
        kit_src = ROOT / "kit" / "assets" / "icons" / mark_name
        site_src = SITE_DIR / "icons" / mark_name
        if not kit_src.is_file():
            raise SystemExit(f"missing kit nav mark {kit_src.relative_to(ROOT)}")
        if not site_src.is_file():
            raise SystemExit(f"missing site nav mark {site_src.relative_to(ROOT)}")
        if kit_src.read_bytes() != site_src.read_bytes():
            raise SystemExit(
                f"site/icons/{mark_name} drifted from kit/assets/icons/{mark_name}; "
                "copy from kit or bump PIN + sync"
            )
        shutil.copy2(kit_src, icons_dist / mark_name)


def build() -> None:
    site = load_site()
    schemes = load_json(DATA / "schemes.json")
    validate(site, schemes)
    home = render_home(site, schemes)
    about = render_about(site)
    assert_safe([home, about])

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST / "index.html").write_text(home, encoding="utf-8")
    (DIST / "about.html").write_text(about, encoding="utf-8")
    (DIST / "style.css").write_text((SITE_DIR / "style.css").read_text(encoding="utf-8"), encoding="utf-8")
    (DIST / "app.js").write_text((SITE_DIR / "app.js").read_text(encoding="utf-8"), encoding="utf-8")
    shutil.copy2(SITE_DIR / "social-card.png", DIST / "social-card.png")
    copy_site_fonts()
    copy_nav_marks()
    (DIST / "schemes.json").write_text(json.dumps(schemes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (DIST / "CNAME").write_text((ROOT / "CNAME").read_text(encoding="utf-8"), encoding="utf-8")
    (DIST / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nSitemap: https://bantuan.sarawak.news/sitemap.xml\n",
        encoding="utf-8",
    )
    lastmod = site["checked"]
    urls = [site["url"], f"{site['url']}about.html"]
    entries = "\n".join(
        f"  <url>\n    <loc>{esc(url)}</loc>\n    <lastmod>{lastmod}</lastmod>\n  </url>" for url in urls
    )
    (DIST / "sitemap.xml").write_text(
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n"
        f"{entries}\n"
        "</urlset>\n",
        encoding="utf-8",
    )
    print(f"Built {DIST / 'index.html'} with {len(schemes)} schemes")


if __name__ == "__main__":
    build()
