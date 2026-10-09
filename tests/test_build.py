import re
import unittest
from pathlib import Path

import scripts.build as build

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_RM = {
    "100",
    "200",
    "250",
    "300",
    "375",
    "400",
    "450",
    "500",
    "600",
    "800",
    "1000",
    "1100",
    "1169",
    "1198",
    "1200",
    "1236",
    "1298",
    "1500",
    "1800",
    "2500",
    "4556",
    "4849",
    "5000",
    "5001",
    "6000",
    "7000",
    "10000",
    "15000",
    "30000",
    "50000",
    "50400",
    "59220",
    "200000",
    "300000",
    "2618",
    "3720",
}

BANNED = ("wellbest", "spta", "siba", "gptp", "15 may", "48 months", "i-gps")


def article(html: str, scheme_id: str) -> str:
    match = re.search(
        rf'<article class="scheme" id="{scheme_id}"[\s\S]*?</article>',
        html,
    )
    if not match:
        raise AssertionError(f"missing article #{scheme_id}")
    return match.group(0)


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build.build()
        cls.dist = ROOT / "dist"
        cls.home = (cls.dist / "index.html").read_text(encoding="utf-8")
        cls.about = (cls.dist / "about.html").read_text(encoding="utf-8")
        cls.site = build.load_json(ROOT / "data" / "site.json")
        cls.schemes = build.load_json(ROOT / "data" / "schemes.json")

    def test_pages_and_assets(self):
        for name in ("index.html", "about.html", "style.css", "app.js", "robots.txt", "sitemap.xml", "CNAME", "social-card.png"):
            self.assertTrue((self.dist / name).is_file(), name)
        self.assertEqual((self.dist / "CNAME").read_text(encoding="utf-8").strip(), "bantuan.sarawak.news")
        self.assertEqual((ROOT / "CNAME").read_text(encoding="utf-8").strip(), "bantuan.sarawak.news")
        card = (self.dist / "social-card.png").read_bytes()
        self.assertEqual(card[12:16], b"IHDR")
        self.assertEqual(int.from_bytes(card[16:20], "big"), 1200)
        self.assertEqual(int.from_bytes(card[20:24], "big"), 630)

    def test_geist_font_is_self_hosted(self):
        source = ROOT / "site" / "fonts" / "Geist-Variable.woff2"
        license_source = ROOT / "site" / "fonts" / "OFL.txt"
        font = self.dist / "fonts" / "Geist-Variable.woff2"
        license_file = self.dist / "fonts" / "OFL.txt"
        self.assertTrue(source.is_file())
        self.assertEqual(font.read_bytes()[:4], b"wOF2")
        self.assertEqual(font.read_bytes(), source.read_bytes())
        self.assertGreater(font.stat().st_size, 1000)
        self.assertIn("SIL OPEN FONT LICENSE", license_file.read_text(encoding="utf-8"))
        self.assertEqual(license_file.read_text(encoding="utf-8"), license_source.read_text(encoding="utf-8"))
        css = (self.dist / "style.css").read_text(encoding="utf-8")
        self.assertNotIn("shadcn.io", css)
        face = re.search(r"@font-face \{([^}]+)\}", css).group(1)
        self.assertIn('font-family: "Geist"', face)
        self.assertIn('url("fonts/Geist-Variable.woff2")', face)
        self.assertIn("font-display: swap", face)
        self.assertIn("font-weight: 100 900", face)
        body = re.search(r"body \{([^}]+)\}", css).group(1)
        self.assertIn('"Geist"', body)
        self.assertIn("ui-sans-serif", body)
        self.assertIn("system-ui", body)
        self.assertIn("-apple-system", body)
        self.assertIn("sans-serif", body)

    def test_category_scroll_hint_does_not_cover_buttons(self):
        self.assertIn('data-category-scroll', self.home)
        self.assertIn('class="category-filter-hint category-filter-hint-end"', self.home)
        self.assertIn('class="category-filter-hint category-filter-hint-start"', self.home)
        filter_row = re.search(
            r'<section class="category-filter"[\s\S]*?</section>',
            self.home,
        ).group(0)
        self.assertNotIn("<svg", filter_row)
        self.assertEqual(filter_row.count("category-filter-count"), 8)
        self.assertEqual(
            filter_row.count('aria-hidden="true"'),
            filter_row.count("category-filter-count") + 2,
        )
        css = (self.dist / "style.css").read_text(encoding="utf-8")
        hint = re.search(r"\.category-filter-hint \{([^}]+)\}", css).group(1)
        self.assertIn("pointer-events: none", hint)
        self.assertIn("padding: 4px 20px 6px 0;", re.search(r"\.category-filter-options \{([^}]+)\}", css).group(1))
        script = (self.dist / "app.js").read_text(encoding="utf-8")
        self.assertIn("can-scroll-end", script)
        self.assertIn("can-scroll-start", script)

    def test_seo(self):
        for page, canonical in (
            (self.home, "https://bantuan.sarawak.news/"),
            (self.about, "https://bantuan.sarawak.news/about.html"),
        ):
            self.assertIn(f'<link rel="canonical" href="{canonical}"', page)
            self.assertIn('property="og:title"', page)
            self.assertIn('property="og:description"', page)
            self.assertIn('property="og:image" content="https://bantuan.sarawak.news/social-card.png"', page)
            self.assertIn('name="twitter:card" content="summary_large_image"', page)
            self.assertIn("<title>", page)
            self.assertIn('name="description"', page)
        self.assertIn("Sarawak government assistance, in one directory.", self.home)
        self.assertIn("🫶", self.home)
        self.assertIn("Sitemap: https://bantuan.sarawak.news/sitemap.xml", (self.dist / "robots.txt").read_text())
        sitemap = (self.dist / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("https://bantuan.sarawak.news/", sitemap)
        self.assertIn("https://bantuan.sarawak.news/about.html", sitemap)
        self.assertNotIn("skas.html", sitemap)

    def test_analytics_token_stays_empty(self):
        source = (ROOT / "scripts" / "build.py").read_text(encoding="utf-8")
        self.assertIn('CLOUDFLARE_WEB_ANALYTICS_TOKEN = ""', source)
        self.assertNotIn("cloudflareinsights", self.home)
        self.assertNotIn("cloudflareinsights", self.about)
        sample = build.render_analytics_script("example-token")
        self.assertIn("example-token", sample)
        self.assertIn("cloudflareinsights", sample)
        self.assertEqual(build.render_analytics_script(""), "")

    def test_every_scheme_is_labelled_and_linked(self):
        self.assertTrue(all(scheme["links"] for scheme in self.schemes))
        self.assertTrue(all(scheme["level"] in {"STATE", "FEDERAL"} for scheme in self.schemes))
        self.assertEqual(sum(len(scheme["links"]) for scheme in self.schemes), 24)
        self.assertTrue(all(len(scheme["links"]) == 1 for scheme in self.schemes))
        for scheme in self.schemes:
            card = article(self.home, scheme["id"])
            self.assertIn(f'data-level="{scheme["level"].lower()}"', card)
            self.assertNotIn("scheme-kicker", card)
            self.assertNotIn("scheme-short", card)
            self.assertNotIn(">State</span>", card)
            self.assertNotIn(">Federal</span>", card)
            self.assertIn(scheme["title"], card)
            self.assertIn('class="scheme-rank"', card)
            self.assertIn('class="scheme-head"', card)
            self.assertIn('class="scheme-body"', card)
            self.assertNotIn("scheme-title-row", card)
            self.assertLess(card.index('class="scheme-head"'), card.index('class="scheme-body"'))
            self.assertLess(card.index('class="scheme-rank"'), card.index("<h3>"))
            self.assertLess(card.index("<h3>"), card.index('class="scheme-body"'))
            self.assertLess(card.index('class="scheme-body"'), card.index('class="sources-title"'))
            self.assertIn('class="sources-title">Source</h4>', card)
            self.assertIn('class="sources"', card)
            for link in scheme["links"]:
                self.assertIn(link["url"], card)
            if scheme["amount_basis"] == "none":
                self.assertNotIn('class="amount-list"', card)
                for amount in scheme.get("amounts") or []:
                    self.assertNotIn(amount, card)
            else:
                many = " many" if len(scheme["amounts"]) > 1 else ""
                self.assertIn(f'class="amount-list{many}"', card)
                for amount in scheme["amounts"]:
                    self.assertIn(amount, card)
        federal = {
            "id": "sample",
            "level": "FEDERAL",
            "title": "Sample federal scheme",
            "amount_basis": "none",
            "unspecified": "None.",
            "paragraphs": ["A federal payment."],
            "links": [{"label": "Example", "url": "https://www.jkm.gov.my/"}],
        }
        shown = build.render_scheme(federal, show_level=True)
        self.assertIn('data-level="federal"', shown)
        self.assertIn('class="level level-federal"', shown)
        self.assertIn(">Federal</span>", shown)
        self.assertNotIn("scheme-short", shown)

    def test_groups_and_about(self):
        for group in self.site["groups"]:
            self.assertIn(f'id="{group["id"]}"', self.home)
            self.assertIn(group["title"], self.home)
            self.assertNotIn("intro", group)
            self.assertNotIn("links", group)
        for match in re.finditer(
            r'<header class="group-head">([\s\S]*?)</header>',
            self.home,
        ):
            self.assertNotRegex(match.group(1), r'<p[\s>]')
        self.assertNotIn("group-sources-title", self.home)
        self.assertNotIn("Pages checked for this group", self.home)
        self.assertNotIn("sources group-sources", self.home)
        self.assertNotIn(">my-Yayasan</a>", self.home)
        self.assertNotIn("Yayasan IPT", self.home)
        self.assertNotIn("Sri Pertiwi guidelines", self.home)
        self.assertNotIn("JWKS —", self.home)
        self.assertNotIn("JKMS —", self.home)
        self.assertNotIn(">KPWK</a>", self.home)
        self.assertIn('class="sources-title">Source</h4>', self.home)
        self.assertNotIn("Official pages", self.home)
        self.assertNotIn("news_view", self.home)
        self.assertNotIn("announcement_view", self.home)
        self.assertNotIn("isarawakcare.sarawak.gov.my", self.home)
        self.assertNotIn("Bantuan-IPT-ENG.pdf", self.home)
        self.assertNotIn("article_view/0/380", self.home)
        self.assertNotIn("faq_view", self.home)
        self.assertNotIn("webpage_view/117", self.home)
        self.assertNotIn("sla_view/319/757", self.home)
        self.assertIn("sla_view/0/821/", article(self.home, "skas"))
        ftes = article(self.home, "ftes")
        self.assertIn(
            "https://meitd.sarawak.gov.my/web/subpage/webpage_view/156",
            ftes,
        )
        self.assertIn("Ministry of Education, Innovation and Talent Development", ftes)
        self.assertNotIn(">MEITD</a>", ftes)
        self.assertNotIn("meitd.sarawak.gov.my/web/subpage/news_view", self.home)
        self.assertNotIn("sarawakenergy.com/media-info/media-releases", self.home)
        self.assertNotRegex(self.home, r'href="https://hdc\.sarawak\.gov\.my/?"')
        self.assertIn("independent", self.about.casefold())
        self.assertIn("6 October 2026", self.about)
        self.assertNotIn("4 October 2026", self.about)
        self.assertIn("does not run", self.about)
        footer_bottom = (
            '<div class="site-footer-bottom">\n'
            '      <p>Built by <a class="site-footer-link site-footer-credit-link" href="https://hafiy.my" '
            'target="_blank" rel="noopener noreferrer">hafiy.my</a>, an independent publication. '
            "Not affiliated with the Sarawak Government.</p>"
        )
        self.assertEqual(self.home.count('<footer class="site-footer">'), 1)
        self.assertEqual(self.about.count('<footer class="site-footer">'), 1)
        self.assertIn(footer_bottom, self.home)
        self.assertIn(footer_bottom, self.about)
        self.assertIn("official", self.about.casefold())

    def test_rejected_claims_stay_out(self):
        blob = (self.home + self.about).casefold()
        for phrase in BANNED:
            self.assertNotIn(phrase, blob)
        for scheme_id in ("rental", "hdras", "spektra-lite"):
            self.assertNotIn(f'id="{scheme_id}"', self.home)
        efs = article(self.home, "efs")
        self.assertIn("within 1 year", efs)
        self.assertIn("efs@sarawak.gov.my", efs)
        self.assertNotIn("1 January 2026", efs)
        self.assertNotIn("JPN", efs)
        skas = article(self.home, "skas")
        skas_amounts = re.search(r'<ul class="amount-list many">([\s\S]*?)</ul>', skas).group(1)
        self.assertIn("RM1,100", skas_amounts)
        self.assertIn("RM600", skas_amounts)
        self.assertIn("RM375", skas_amounts)
        self.assertNotIn("RM800", skas_amounts)
        self.assertNotIn("dedicated live page", skas.casefold())
        self.assertNotIn("10 March", skas)
        self.assertNotIn("25 May", skas)
        self.assertIn("10 November 2026", skas)
        self.assertIn('<ol class="scheme-copy">', skas)
        self.assertNotIn('class="amount-note"', skas)
        self.assertIn("Paid through S Pay Global for essential food.", skas)
        self.assertIn("single person with a disability", skas)
        self.assertNotIn("PWD", skas)
        electricity = article(self.home, "electricity")
        self.assertRegex(
            electricity,
            r'<ul class="amount-list">\s*<li>25% for domestic users',
        )
        self.assertIn('<ol class="scheme-copy">', electricity)
        self.assertNotIn("Use RM600", self.home)
        self.assertNotIn("state and federal", (self.home + self.about).casefold())
        self.assertNotIn("marked State", self.about)
        self.assertNotIn("older rates", self.about.casefold())
        self.assertNotIn("HDRAS", self.about)
        self.assertIn("25%", electricity)
        self.assertNotIn("not the SKAS payment", electricity)
        self.assertIn("28 February 2027", electricity)
        self.assertIn("IGPS", self.home)
        self.assertIn("selected courses", article(self.home, "ftes").casefold())

    def test_published_directory_is_state_only(self):
        self.assertEqual(len(self.schemes), 24)
        self.assertTrue(all(scheme["level"] == "STATE" for scheme in self.schemes))
        updated = re.search(r'<p class="updated">(.*?)</p>', self.home).group(1)
        self.assertIn(">Last updated</span>", updated)
        self.assertIn(">TUESDAY, 6 OCT 2026</time>", updated)
        self.assertNotIn("Checked", updated)
        self.assertNotIn("schemes", updated.casefold())
        self.assertNotIn("updated-count", self.home)
        deck = re.search(r'<p class="brief-deck">(.*?)</p>', self.home).group(1)
        self.assertEqual(deck, "Each scheme links to its source.")
        self.assertNotIn('data-level="federal"', self.home)
        self.assertNotIn("level-filter", self.home)
        self.assertNotIn("data-level-filter", self.home)
        self.assertIn('<p class="category-filter-title" id="category-filter-title">Browse by category</p>', self.home)
        self.assertIn('data-category-filter', self.home)
        self.assertNotIn('data-category-filter hidden', self.home)
        self.assertNotRegex(self.home, r'<section class="category-filter"[^>]*\shidden')
        self.assertIn('data-section-filter="all"', self.home)
        self.assertIn("Showing all 24 schemes", self.home)
        self.assertNotIn("jump-links", self.home)
        self.assertNotIn("Household, senior and single adult", self.home + self.about)
        household = next(group for group in self.site["groups"] if group["id"] == "household")
        self.assertEqual(household["id"], "household")
        self.assertEqual(household["title"], "Household")
        welfare = next(group for group in self.site["groups"] if group["id"] == "welfare")
        self.assertEqual(welfare["id"], "welfare")
        self.assertEqual(welfare["title"], "Welfare")
        self.assertIn('id="group-welfare">', self.home)
        self.assertIn(">Welfare</span></h2>", self.home)
        health = next(group for group in self.site["groups"] if group["id"] == "health")
        self.assertEqual(health["id"], "health")
        self.assertEqual(health["title"], "Senior Citizen")
        self.assertIn('id="health"', self.home)
        self.assertIn('id="group-health">', self.home)
        self.assertIn(">Senior Citizen</span></h2>", self.home)
        self.assertIn(
            'data-section-filter="health" data-filter-label="Senior Citizen"',
            self.home,
        )
        self.assertNotIn("Health and seniors", self.home + self.about)
        self.assertNotIn("M3.5 11 12 3.2 20.5 11", self.home)
        self.assertNotIn("M1.2 12 7.9 4.4 12 12 16.1 4.4 22.8 12", self.home)
        self.assertEqual(self.home.count('class="group-icon"'), len(self.site["groups"]))
        self.assertEqual(self.home.count('class="group-icon-tile"'), len(self.site["groups"]))
        self.assertNotIn("group-icon", self.about)
        self.assertNotIn("phosphoricons.com", self.home)
        self.assertNotIn("unpkg.com", self.home)
        filter_row = re.search(
            r'<section class="category-filter"[\s\S]*?</section>',
            self.home,
        ).group(0)
        self.assertNotIn("<svg", filter_row)
        self.assertNotIn("group-icon", filter_row)
        icon_names = {
            "household": "basket",
            "student": "graduation-cap",
            "housing": "house",
            "health": "heartbeat",
            "baby": "baby",
            "business": "storefront",
            "welfare": "hand-heart",
        }
        icon_markers = {
            "basket": "M232,88,216.93,201.06A8,8,0,0,1,209,208H47",
            "graduation-cap": "M251.76,88.94l-120-64",
            "house": "M219.31,108.68l-80-80",
            "heartbeat": "M72,144H32a8,8,0,0,1,0-16H67.72",
            "baby": "M92,140a12,12,0,1,1,12-12A12,12,0,0,1,92,140",
            "storefront": "M231.69,93.81,217.35,43.6",
            "hand-heart": "M230.33,141.06a24.34,24.34,0,0,0-18.61-4.77",
        }
        icons = []
        for group in self.site["groups"]:
            count = sum(scheme["group"] == group["id"] for scheme in self.schemes)
            self.assertGreater(count, 0)
            self.assertIn(
                f'data-section-filter="{group["id"]}" data-filter-label="{group["title"]}"',
                self.home,
            )
            self.assertIn(
                f'{group["title"]} <span class="category-filter-count" aria-hidden="true">{count}</span>',
                self.home,
            )
            heading = re.search(
                rf'<h2 id="group-{group["id"]}">(<span class="group-icon-tile"><svg class="group-icon"[\s\S]*?</svg></span>)<span>{re.escape(group["title"])}</span></h2>',
                self.home,
            )
            self.assertIsNotNone(heading, group["id"])
            icon = heading.group(1)
            name = icon_names[group["id"]]
            self.assertIn(f'data-icon="{name}"', icon)
            self.assertIn(icon_markers[name], icon)
            self.assertEqual(icon.count('opacity="0.2"'), 1)
            self.assertEqual(icon.count('class="group-icon-fill"'), 1)
            self.assertIn('aria-hidden="true"', icon)
            self.assertIn('fill="currentColor"', icon)
            self.assertIn('viewBox="0 0 256 256"', icon)
            self.assertIn('width="24"', icon)
            self.assertIn('height="24"', icon)
            self.assertNotIn("<img", icon)
            self.assertNotIn("href=", icon)
            self.assertNotIn("http", icon)
            icons.append(icon)
        self.assertEqual(len(icons), len(set(icons)))
        removed = {
            "ppr": "PPR",
            "nextgen": "Youth Agropreneur NextGen 2026",
            "budi": "BUDI Agri-Komoditi",
            "bwe": "Bantuan Warga Emas (BWE)",
            "bkk-child": "Bantuan Kanak-Kanak (BKK)",
            "epoku": "Elaun Pekerja Orang Kurang Upaya (EPOKU)",
            "btb": "Bantuan Orang Kurang Upaya Tidak Berupaya Bekerja (BTB)",
            "bpt": "Bantuan Penjagaan (BPT)",
            "bap": "Bantuan Anak Pelihara (BAP)",
            "bencana": "Bencana / Tabung Bantuan Segera",
        }
        backlog = (ROOT / "docs" / "federal-assistance-backlog.md").read_text(encoding="utf-8")
        for scheme_id, title in removed.items():
            self.assertNotIn(f'id="{scheme_id}"', self.home)
            self.assertIn(title, backlog)
            self.assertIn(f'"id": "{scheme_id}"', backlog)
        css = (self.dist / "style.css").read_text(encoding="utf-8")
        tile = re.search(r"\.group-icon-tile \{([^}]+)\}", css).group(1)
        self.assertIn("width: 36px;", tile)
        self.assertIn("height: 36px;", tile)
        self.assertIn("border-radius: 8px;", tile)
        self.assertIn("background: var(--group-icon-tile);", tile)
        self.assertIn("border: 1px solid var(--group-icon-border);", tile)
        self.assertIn("color: var(--ink);", tile)
        fill = re.search(r"\.group-icon-fill \{([^}]+)\}", css).group(1)
        self.assertIn("fill: var(--sarawak-yellow);", fill)
        self.assertIn("opacity: 1;", fill)
        dark_tile = re.search(r'html\[data-theme="dark"\] \.group-icon-tile \{([^}]+)\}', css).group(1)
        self.assertIn("color: var(--sarawak-yellow);", dark_tile)
        dark_fill = re.search(r'html\[data-theme="dark"\] \.group-icon-fill \{([^}]+)\}', css).group(1)
        self.assertIn("opacity: 0.2;", dark_fill)
        self.assertIn("--group-icon-tile: #fff6d2;", css)
        dark = re.search(r'html\[data-theme="dark"\] \{([^}]+)\}', css).group(1)
        self.assertIn("--group-icon-tile: rgba(247, 201, 72, 0.28);", dark)
        self.assertIn("--group-icon-border: rgba(247, 201, 72, 0.95);", dark)
        self.assertNotIn("level-filter", css)
        self.assertNotIn("jump-links", css)
        button = re.search(r"\.category-filter-button \{([^}]+)\}", css).group(1)
        self.assertIn("padding: 5px 6px;", button)
        self.assertIn("font-size: 9px;", button)
        self.assertIn("border-radius: 6px;", button)
        self.assertIn("line-height: 1.4;", button)
        page_amount = re.search(
            r'\.scheme\[data-amount-basis="page"\] \.amount-list li \{([^}]+)\}',
            css,
        ).group(1)
        self.assertIn("font-size: 16px;", page_amount)
        source_title = re.search(r"\.sources-title \{([^}]+)\}", css).group(1)
        self.assertIn("max-width: 100%;", source_title)
        self.assertIn("background: var(--sarawak-yellow);", source_title)
        self.assertIn("color: var(--sarawak-black);", source_title)
        self.assertIn("text-transform: uppercase;", source_title)
        self.assertIn("font-size: 12px;", source_title)
        source_link = re.search(r"\.sources a,[\s\S]*?font-size: ([0-9]+px);", css).group(1)
        self.assertEqual(source_link, "12px")
        self.assertIn("font-weight: 900;", source_title)
        self.assertIn("padding: 2px 6px;", source_title)
        title = re.findall(r"\.scheme-head > h3 \{([^}]+)\}", css)[-1]
        self.assertIn("background: transparent;", title)
        self.assertIn("color: #fff;", title)
        self.assertIn("font-size: 16px;", title)
        self.assertIn("font-weight: 700;", title)
        self.assertIn("letter-spacing: 0;", title)
        self.assertNotIn("letter-spacing: -.02em;", title)
        self.assertNotIn("text-transform", title)
        self.assertNotIn("scheme-title-row", css)
        scheme_head = re.search(r"\.scheme-head \{([^}]+)\}", css).group(1)
        self.assertIn("display: flex;", scheme_head)
        self.assertIn("gap: 0;", scheme_head)
        self.assertNotIn("gap: 0.5em;", scheme_head)
        rank_block = re.search(r"\.scheme-rank \{([^}]+)\}", css).group(1)
        self.assertNotIn("margin-right:", rank_block)
        self.assertIn("background: var(--sarawak-black);", scheme_head)
        self.assertIn(".scheme-rank {", css)
        rank = re.search(r"\.scheme-rank \{([^}]+)\}", css).group(1)
        self.assertIn("font-size: 16px;", rank)
        self.assertNotIn("width: 28px;", rank)
        self.assertNotIn(".scheme:has(.scheme-rank)", css)
        scheme_card = re.search(r"\.scheme \{([^}]+)\}", css).group(1)
        self.assertIn("padding: 0;", scheme_card)
        self.assertIn("overflow: hidden;", scheme_card)
        scheme_body = re.search(r"\.scheme-body \{([^}]+)\}", css).group(1)
        self.assertIn("padding: 16px 16px 12px;", scheme_body)
        self.assertIn('content: "•";', css)
        self.assertIn(".amount-list li::before", css)
        rank_after = re.search(r"\.scheme-rank::after \{([^}]+)\}", css).group(1)
        self.assertIn("\\00a0", rank_after)
        self.assertNotIn("·", rank_after)
        options = re.search(r"\.category-filter-options \{([^}]+)\}", css).group(1)
        self.assertIn("gap: 3px;", options)
        script = (self.dist / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("data-level-filter", script)
        self.assertNotIn("levelFilter", script)
        self.assertIn("data-category-filter", script)
        self.assertIn("Showing all ${visibleCount} schemes", script)

    def test_scheme_ranks_reset_per_category(self):
        household = article(self.home, "skas")
        electricity = article(self.home, "electricity")
        bkk = article(self.home, "bkk-ipt")
        self.assertIn('class="scheme-rank" aria-label="Item 1 in Household">1</span>', household)
        self.assertIn('class="scheme-rank" aria-label="Item 2 in Household">2</span>', electricity)
        self.assertIn('class="scheme-rank" aria-label="Item 1 in Students">1</span>', bkk)
        self.assertIn("https://myys.yayasansarawak.org.my/", bkk)
        self.assertNotIn("bantuan-pelajar-ke-ipt2", bkk)
        self.assertEqual(bkk.count("<li><a "), 1)
        laptop = article(self.home, "laptop")
        self.assertIn('<ol class="scheme-copy">', laptop)
        self.assertIn("A laptop is given in kind.", laptop)
        self.assertIn(
            "For a first-year diploma or bachelor student. Family income per person must be RM1,500 or below.",
            laptop,
        )
        self.assertNotIn("The page does not state a cash amount.", laptop)
        self.assertNotIn('class="unspecified"', laptop)
        self.assertIn("https://myys.yayasansarawak.org.my/", laptop)
        self.assertNotIn("bantuan-pelajar-ke-ipt2", laptop)
        self.assertEqual(laptop.count("<li><a "), 1)
        books = article(self.home, "book-voucher")
        self.assertIn("https://myys.yayasansarawak.org.my/", books)
        self.assertNotIn("bantuan-pelajar-ke-ipt2", books)
        self.assertEqual(books.count("<li><a "), 1)
        uniform = article(self.home, "school-uniform")
        self.assertIn("RM200 voucher", uniform)
        self.assertIn('<ol class="scheme-copy">', uniform)
        transport = article(self.home, "school-transport")
        self.assertIn("RM3,720", transport)
        self.assertIn('<ol class="scheme-copy">', transport)
        self.assertNotIn('class="amount-list"', transport)
        self.assertNotIn('class="unspecified"', transport)
        federal = {
            "id": "sample",
            "level": "FEDERAL",
            "title": "Sample federal scheme",
            "amount_basis": "none",
            "unspecified": "None.",
            "paragraphs": ["A federal payment."],
            "links": [{"label": "Example", "url": "https://www.jkm.gov.my/"}],
        }
        shown = build.render_scheme(federal, show_level=True)
        self.assertNotIn("scheme-rank", shown)

    def test_ringgit_figures_are_on_the_allowlist(self):
        found = {value.replace(",", "") for value in re.findall(r"RM\s*([0-9][0-9,]*)", self.home + self.about)}
        self.assertTrue(found)
        self.assertEqual(found - ALLOWED_RM, set())

    def test_one_source_full_agency_name_and_due_label(self):
        labels = {
            "skas": "Service Sarawak",
            "electricity": "Sarawak Energy",
            "bkk-ipt": "Yayasan Sarawak",
            "laptop": "Yayasan Sarawak",
            "book-voucher": "Yayasan Sarawak",
            "igps": "Yayasan Sarawak",
            "ipt-entry": "Yayasan Sarawak",
            "ftes": "Ministry of Education, Innovation and Talent Development",
            "school-uniform": "Yayasan Sarawak",
            "school-transport": "Yayasan Sarawak",
            "hdas": "Housing Development Corporation",
            "sras": "Housing Development Corporation",
            "spektra-permata": "Housing Development Corporation",
            "sri-pertiwi": "Ministry of Urban Development and Natural Resources",
            "schb": "Service Sarawak",
            "kgc": "Service Sarawak",
            "bik": "Service Sarawak",
            "bib": "Service Sarawak",
            "efs": "Kementerian Pembangunan Wanita, Kanak-Kanak dan Kesejahteraan Komuniti",
            "kirwas": "Jabatan Wanita dan Keluarga Sarawak",
            "smcs": "Service Sarawak",
            "geran-pelancaran": "Jabatan Kebajikan Masyarakat Sarawak",
            "ba": "Jabatan Kebajikan Masyarakat Sarawak",
            "bbb": "Jabatan Kebajikan Masyarakat Sarawak",
        }
        self.assertEqual({scheme["id"] for scheme in self.schemes}, set(labels))
        for scheme in self.schemes:
            card = article(self.home, scheme["id"])
            self.assertEqual(len(scheme["links"]), 1)
            self.assertEqual(scheme["links"][0]["label"], labels[scheme["id"]])
            self.assertEqual(card.count("<li><a "), 1)
            self.assertIn(f'>{labels[scheme["id"]]}</a>', card)
        self.assertNotIn("sla_view/211/846", self.home)
        self.assertNotIn("sla_view/211/729", self.home)
        self.assertIn("https://kpwk.sarawak.gov.my/web/subpage/webpage_view/100", article(self.home, "efs"))
        self.assertIn("https://jwks.sarawak.gov.my/web/subpage/webpage_view/182", article(self.home, "kirwas"))
        self.assertIn("https://myys.yayasansarawak.org.my/", article(self.home, "bkk-ipt"))
        self.assertIn("https://yayasansarawak.org.my/en/bantuan-pelajar-ke-ipt2/", article(self.home, "school-uniform"))

        due_cards = {
            "skas": ["10 November 2026", "mid-December 2026"],
            "electricity": ["28 February 2027"],
            "bkk-ipt": ["30 October 2026"],
            "laptop": ["30 October 2026"],
            "book-voucher": ["30 October 2026"],
        }
        for scheme_id, phrases in due_cards.items():
            card = article(self.home, scheme_id)
            for phrase in phrases:
                pill = f'<span class="due-date">{phrase}</span>'
                self.assertIn(pill, card)
                self.assertEqual(card.count(phrase), 1)
            self.assertIn('<ol class="scheme-copy">', card)
            self.assertLess(card.index("<li>"), card.index('class="due-date"'))
        skas = article(self.home, "skas")
        self.assertIn("The current phase is the payment on <span class=\"due-date\">10 November 2026</span>", skas)
        self.assertNotIn("10 March", skas)
        electricity = article(self.home, "electricity")
        self.assertIn("April–December 2026", electricity)
        self.assertIn("The current phase is the discount", electricity)
        books = article(self.home, "book-voucher")
        self.assertIn("Book Voucher Programme Phase 2, 2026", books)
        self.assertIn("RM1,500", books)
        self.assertNotIn("No income cap", books)
        laptop = article(self.home, "laptop")
        self.assertIn("Free Laptop Programme Phase 2, 2026", laptop)
        self.assertNotIn('class="due-date"', article(self.home, "igps"))
        self.assertNotIn('class="due-date"', article(self.home, "ba"))

        css = (self.dist / "style.css").read_text(encoding="utf-8")
        due = re.search(r"\.due-date \{([^}]+)\}", css).group(1)
        self.assertIn("display: inline;", due)
        self.assertIn("background: #d22630;", due)
        self.assertIn("color: #fff;", due)
        self.assertIn("font-size: inherit;", due)
        self.assertIn("font-weight: inherit;", due)

        with self.assertRaises(SystemExit):
            build.check_scheme_source(
                {
                    "id": "two-links",
                    "links": [
                        {"label": "One", "url": "https://www.jkm.gov.my/"},
                        {"label": "Two", "url": "https://www.jkm.gov.my/"},
                    ],
                    "paragraphs": ["A line."],
                }
            )
        with self.assertRaises(SystemExit):
            build.check_scheme_source(
                {
                    "id": "html-due",
                    "links": [{"label": "One", "url": "https://www.jkm.gov.my/"}],
                    "paragraphs": ["Closes <b>soon</b>."],
                    "due": "<b>soon</b>",
                }
            )
        with self.assertRaises(SystemExit):
            build.check_scheme_source(
                {
                    "id": "missing-due",
                    "links": [{"label": "One", "url": "https://www.jkm.gov.my/"}],
                    "paragraphs": ["No date here."],
                    "due": "30 October 2026",
                }
            )


if __name__ == "__main__":
    unittest.main()
