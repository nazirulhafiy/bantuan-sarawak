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


def long_date(iso_date: str) -> str:
    checked = datetime.strptime(iso_date, "%Y-%m-%d")
    return f"{checked.day} {checked.strftime('%B %Y')}"


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
            if not scheme.get("unspecified"):
                raise SystemExit(f"{scheme_id} needs an unspecified note")
        elif not amounts:
            raise SystemExit(f"{scheme_id} needs at least one amount")
        if not scheme.get("paragraphs"):
            raise SystemExit(f"{scheme_id} needs paragraphs")
        if not scheme.get("links"):
            raise SystemExit(f"{scheme_id} needs an official link")
        for link in scheme["links"]:
            check_official_url(link["url"], scheme_id)
    for group in site["groups"]:
        for link in group.get("links", []):
            check_official_url(link["url"], group["id"])
    for desk in site.get("desks", []):
        check_official_url(desk["url"], desk["name"])


def check_official_url(url: str, owner: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in OFFICIAL_HOSTS:
        raise SystemExit(f"Unofficial or invalid URL for {owner}: {url}")


def render_links(links: list[dict], class_name: str = "sources") -> str:
    items = "\n".join(
        "        <li><a href=\"{url}\" target=\"_blank\" rel=\"noopener noreferrer\">{label}</a></li>".format(
            url=esc(link["url"]),
            label=esc(link["label"]),
        )
        for link in links
    )
    return f"""      <ul class="{class_name}">
{items}
      </ul>"""


def render_scheme(scheme: dict) -> str:
    level = scheme["level"]
    level_word = "State" if level == "STATE" else "Federal"
    basis = scheme["amount_basis"]
    parts = [
        f"""    <article class="scheme" id="{esc(scheme['id'])}" data-level="{level.lower()}" data-amount-basis="{esc(basis)}">
      <header class="scheme-head">
        <p class="scheme-kicker">
          <span class="level level-{level.lower()}">{level_word}</span>
          <span class="scheme-short">{esc(scheme['short'])}</span>
        </p>
        <h3>{esc(scheme['title'])}</h3>
      </header>"""
    ]
    if basis == "attachment":
        parts.append('      <p class="basis">On an attachment</p>')
    if basis == "none":
        parts.append(f'      <p class="unspecified">{esc(scheme["unspecified"])}</p>')
    else:
        amounts = "\n".join(f"        <li>{esc(amount)}</li>" for amount in scheme["amounts"])
        parts.append(f"      <ul class=\"amount-list\">\n{amounts}\n      </ul>")
    if scheme.get("amount_note"):
        parts.append(f'      <p class="amount-note">{esc(scheme["amount_note"])}</p>')
    paragraphs = "\n".join(f"        <p>{esc(paragraph)}</p>" for paragraph in scheme["paragraphs"])
    parts.append(f"      <div class=\"scheme-copy\">\n{paragraphs}\n      </div>")
    parts.append('      <h4 class="sources-title">Official pages</h4>')
    parts.append(render_links(scheme["links"]))
    parts.append("    </article>")
    return "\n".join(parts)


def render_groups(site: dict, schemes: list[dict]) -> str:
    blocks = []
    for group in site["groups"]:
        grouped = [scheme for scheme in schemes if scheme["group"] == group["id"]]
        cards = "\n".join(render_scheme(scheme) for scheme in grouped)
        extra = ""
        if group.get("links"):
            extra = (
                '        <h3 class="group-sources-title">Pages checked for this group</h3>\n'
                + render_links(group["links"], "sources group-sources")
            )
        blocks.append(
            f"""    <section class="group" id="{esc(group['id'])}" aria-labelledby="group-{esc(group['id'])}">
      <header class="group-head">
        <h2 id="group-{esc(group['id'])}">{esc(group['title'])}</h2>
        <p>{esc(group['intro'])}</p>
{extra}
      </header>
      <div class="scheme-list">
{cards}
      </div>
    </section>"""
        )
    return "\n".join(blocks)


def render_jump(site: dict, schemes: list[dict]) -> str:
    links = []
    for group in site["groups"]:
        count = sum(scheme["group"] == group["id"] for scheme in schemes)
        links.append(
            f'<a href="#{esc(group["id"])}">{esc(group["title"])} '
            f'<span class="jump-count">{count}</span></a>'
        )
    return f"""    <nav class="jump" aria-label="On this page">
      <p class="jump-title">On this page</p>
      <div class="jump-links">
        {' '.join(links)}
      </div>
    </nav>"""


def render_filter(schemes: list[dict]) -> str:
    state_count = sum(scheme["level"] == "STATE" for scheme in schemes)
    federal_count = sum(scheme["level"] == "FEDERAL" for scheme in schemes)
    return f"""    <section class="level-filter" aria-labelledby="level-filter-title" data-level-filter hidden>
      <p class="level-filter-title" id="level-filter-title">Show</p>
      <div class="level-filter-options">
        <button type="button" class="level-filter-button is-active" data-level-filter-value="all" aria-pressed="true">All <span class="level-filter-count">{len(schemes)}</span></button>
        <button type="button" class="level-filter-button" data-level-filter-value="state" aria-pressed="false">State <span class="level-filter-count">{state_count}</span></button>
        <button type="button" class="level-filter-button" data-level-filter-value="federal" aria-pressed="false">Federal <span class="level-filter-count">{federal_count}</span></button>
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
      <p>Independent directory. Figures checked {esc(long_date(site['checked']))}. The Sarawak government does not run this site.</p>
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
      <p class="updated"><span class="updated-label">Checked</span> <time datetime="{esc(site['checked'])}">{esc(checked_label(site['checked']))}</time> <span class="updated-count">{len(schemes)} schemes</span></p>
    </header>
{render_jump(site, schemes)}
{render_filter(schemes)}
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
      <p class="about-lede">An independent list of state and federal assistance, with official links only. Amounts were checked on 4 October 2026.</p>
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
