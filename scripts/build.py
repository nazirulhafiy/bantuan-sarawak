#!/usr/bin/env python3
"""Build the Bantuan Sarawak static directory into dist/."""

from __future__ import annotations

import html
import json
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DIST = ROOT / "dist"
SITE_DIR = ROOT / "site"

# New Cloudflare Web Analytics site for bantuan.sarawak.news.
# Leave this empty until that site has its own token. The beacon is
# emitted only when the token is non-empty. Do not reuse ai.sarawak.news.
CLOUDFLARE_WEB_ANALYTICS_TOKEN = ""

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


def render_analytics_script(token: str = CLOUDFLARE_WEB_ANALYTICS_TOKEN) -> str:
    token = token.strip()
    if not token:
        return ""
    beacon = json.dumps({"token": token, "spa": True}, separators=(",", ":"))
    return (
        '<script defer src="https://static.cloudflareinsights.com/beacon.min.js" '
        f"data-cf-beacon='{beacon}'></script>"
    )


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


# Stroke glyphs for category headings. Each one is a different shape so the
# sections can be told apart. The heading text stays the accessible name.
GROUP_ICONS = {
    "household": (
        '<path d="M3.5 11 12 3.2 20.5 11"/>'
        '<path d="M6.2 10.2V21h11.6V10.2"/>'
        '<path d="M10 21v-6h4V21"/>'
    ),
    "student": (
        '<path d="M12 6.2C10.2 4.4 7 3.5 3.2 3.5v14.2c3.8.3 6.8 1.1 8.8 2.8"/>'
        '<path d="M12 6.2c1.8-1.8 5-2.7 8.8-2.7v14.2c-3.8.3-6.8 1.1-8.8 2.8"/>'
        '<path d="M12 6.2v14.3"/>'
    ),
    "housing": (
        '<path d="M1.2 12 7.9 4.4 12 12 16.1 4.4 22.8 12"/>'
        '<path d="M2.2 11.8V21h19.6V11.8"/>'
        '<path d="M5.4 21V15h5V21"/>'
        '<path d="M13.6 21V15h5V21"/>'
    ),
    "health": (
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M12 7.5v9M7.5 12h9"/>'
    ),
    "baby": (
        '<path d="M4.4 9.6C4.4 4.4 12 4.4 12 9.6"/>'
        '<path d="M2.8 9.6h14a1.8 1.8 0 0 1 1.8 1.8V13.8H2.8z"/>'
        '<path d="M17 10.4 21.2 4.2"/>'
        '<circle cx="6.8" cy="19.9" r="1.65"/>'
        '<circle cx="14.4" cy="19.9" r="1.65"/>'
    ),
    "business": (
        '<path d="M6 4.6h12L21.2 8.4H2.8z"/>'
        '<path d="M5.2 8.4V21h13.6V8.4"/>'
        '<path d="M9.2 21V12.6h5.6V21"/>'
    ),
    "welfare": (
        '<path d="M21 8.4c0-2.5-2.1-4.5-4.7-4.5-1.9 0-3.6 1.1-4.3 2.7C11.3 5 9.6 3.9 7.7 3.9 5.1 3.9 3 5.9 3 8.4 3 15.6 12 20.6 12 20.6S21 15.6 21 8.4z"/>'
    ),
}


def render_group_icon(group_id: str) -> str:
    try:
        body = GROUP_ICONS[group_id]
    except KeyError:
        raise SystemExit(f"No heading icon for group {group_id}") from None
    return (
        '<svg class="group-icon" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round">{body}</svg>'
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
      <div class="category-filter-options">
        {' '.join(buttons)}
      </div>
      <p class="visually-hidden" data-filter-status aria-live="polite">Showing all {len(schemes)} schemes</p>
    </section>"""


def render_header(site: dict, active: str) -> str:
    def link(page: str, href: str, label: str) -> str:
        current = ' aria-current="page"' if active == page else ""
        klass = "site-nav-link is-active" if active == page else "site-nav-link"
        return f'<a class="{klass}" href="{href}"{current}>{label}</a>'

    return f"""  <header class="bar">
    <span class="brand-lockup"><a class="brand" href="/">{esc(site['name'])}</a></span>
    <nav class="site-nav" id="primary-navigation" aria-label="Primary">
      {link("home", "/", "Home")}
      {link("about", "about.html", "About")}
    </nav>
    <span class="bar-rule-tail" aria-hidden="true"></span>
    <button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="primary-navigation" aria-label="Open navigation" title="Open navigation">
      <span></span><span></span><span></span>
    </button>
    <button class="theme-toggle" type="button" data-theme-toggle aria-label="Switch to dark mode" title="Switch to dark mode">
      <svg class="theme-icon-morph" aria-hidden="true" width="18" height="18" viewBox="0 0 24 24">
        <mask id="theme-toggle-moon-mask"><rect width="24" height="24" fill="#fff"></rect><circle cx="17" cy="7" r="7" fill="#000"></circle></mask>
        <circle class="theme-icon-moon" cx="12" cy="12" r="9" mask="url(#theme-toggle-moon-mask)"></circle>
        <circle class="theme-icon-sun" cx="12" cy="12" r="5"></circle>
        <g class="theme-icon-rays">
          <line x1="12" y1="1.6" x2="12" y2="3.8"></line><line x1="12" y1="20.2" x2="12" y2="22.4"></line>
          <line x1="1.6" y1="12" x2="3.8" y2="12"></line><line x1="20.2" y1="12" x2="22.4" y2="12"></line>
          <line x1="4.6" y1="4.6" x2="6.2" y2="6.2"></line><line x1="17.8" y1="17.8" x2="19.4" y2="19.4"></line>
          <line x1="4.6" y1="19.4" x2="6.2" y2="17.8"></line><line x1="17.8" y1="6.2" x2="19.4" y2="4.6"></line>
        </g>
      </svg>
    </button>
  </header>"""


def render_footer(site: dict, active: str) -> str:
    home_current = ' aria-current="page"' if active == "home" else ""
    about_current = ' aria-current="page"' if active == "about" else ""
    group_links = "\n".join(
        f'          <li><a class="site-footer-link" href="/#{esc(group["id"])}">{esc(group["title"])}</a></li>'
        for group in site["groups"]
    )
    return f"""  <footer class="site-footer">
    <div class="site-footer-main">
      <div class="site-footer-summary">
        <p class="site-footer-brand">{esc(site['name'])}</p>
        <p class="site-footer-note">An independent directory of Sarawak government assistance. Every scheme links to an official page. This website does not take applications.</p>
      </div>
      <nav aria-label="Explore" class="site-footer-nav">
        <h2>Explore</h2>
        <ul>
          <li><a class="site-footer-link" href="/"{home_current}>Home</a></li>
          <li><a class="site-footer-link" href="about.html"{about_current}>About</a></li>
        </ul>
        <h2 class="site-footer-categories-title">On this page</h2>
        <ul>
{group_links}
        </ul>
      </nav>
    </div>
    <div class="site-footer-bottom">
      <p>Built by <a class="site-footer-link site-footer-credit-link" href="https://hafiy.my" target="_blank" rel="noopener noreferrer">hafiy.my</a>, an independent publication. Not affiliated with the Sarawak Government.</p>
    </div>
  </footer>"""


def theme_boot() -> str:
    return """  <script>
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
  <meta property="og:site_name" content="{esc(site['name'])}" />
  <meta property="og:image" content="{esc(image)}" />
  <meta property="og:image:alt" content="Bantuan Sarawak, a directory of Sarawak government assistance" />
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
                    "name": site["name"],
                    "description": site["description"],
                    "inLanguage": "en",
                },
                {
                    "@type": "CollectionPage",
                    "@id": f"{url}#collection",
                    "url": url,
                    "name": site["title"],
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
      <h1>{esc(site['title'])}</h1>
      <p class="brief-deck">{esc(site['introduction'])}</p>
      <p class="updated"><span class="updated-label">Last updated</span> <time datetime="{esc(site['checked'])}">{esc(checked_label(site['checked']))}</time></p>
    </header>
{render_category_filter(site, schemes)}
{render_groups(site, schemes)}
  </main>
  <button class="back-to-top" type="button" data-back-to-top aria-label="Back to top" hidden><span class="back-to-top-label">Back to top</span> <span class="back-to-top-arrow" aria-hidden="true">↑</span></button>
{render_footer(site, "home")}
  {render_analytics_script()}
</body>"""
    return render_head(site, site["title"], site["description"], url, site["og_title"], structured) + "\n" + body + "\n</html>\n"


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
      <p class="about-eyebrow">About the directory</p>
      <h1>About Bantuan Sarawak</h1>
      <p class="about-lede">An independent list of state assistance, with official links only. Amounts were checked on 6 October 2026.</p>
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
{render_footer(site, "about")}
  {render_analytics_script()}
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


def build() -> None:
    site = load_json(DATA / "site.json")
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
