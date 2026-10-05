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
        self.assertEqual(sum(len(scheme["links"]) for scheme in self.schemes), 29)
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
        self.assertIn("my-Yayasan", self.home)
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
        self.assertIn("4 October 2026", self.about)
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
        self.assertIn(">SUNDAY, 4 OCT 2026</time>", updated)
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
        baby_heading = re.search(
            r'<h2 id="group-baby">(<svg class="group-icon"[\s\S]*?</svg>)<span>New Baby</span></h2>',
            self.home,
        )
        self.assertIsNotNone(baby_heading)
        baby_icon = baby_heading.group(1)
        self.assertNotIn("<rect", baby_icon)
        self.assertEqual(baby_icon.count("<circle"), 2)
        self.assertIn('viewBox="0 0 24 24"', baby_icon)
        self.assertIn('width="22"', baby_icon)
        self.assertIn('height="22"', baby_icon)
        business_heading = re.search(
            r'<h2 id="group-business">(<svg class="group-icon"[\s\S]*?</svg>)<span>Small Business</span></h2>',
            self.home,
        )
        self.assertIsNotNone(business_heading)
        business_icon = business_heading.group(1)
        self.assertIn('M6 4.6h12L21.2 8.4H2.8z', business_icon)
        self.assertIn('M5.2 8.4V21h13.6V8.4', business_icon)
        self.assertIn('M9.2 21V12.6h5.6V21', business_icon)
        self.assertIn('viewBox="0 0 24 24"', business_icon)
        self.assertIn('stroke-width="2"', business_icon)
        self.assertNotIn('<circle', business_icon)
        self.assertNotIn('M3.5 5.5h17', business_icon)
        self.assertNotIn('M14.5 11.6H19.5V16.2H14.5z', business_icon)
        self.assertNotIn('M2 9.4h20', business_icon)
        housing_heading = re.search(
            r'<h2 id="group-housing">(<svg class="group-icon"[\s\S]*?</svg>)<span>Housing</span></h2>',
            self.home,
        )
        self.assertIsNotNone(housing_heading)
        housing_icon = housing_heading.group(1)
        self.assertNotIn("M16.2 5.2", housing_icon)
        self.assertIn("M1.2 12 7.9 4.4 12 12 16.1 4.4 22.8 12", housing_icon)
        household_icon = re.search(
            r'<h2 id="group-household">(<svg class="group-icon"[\s\S]*?</svg>)<span>Household</span></h2>',
            self.home,
        ).group(1)
        self.assertNotEqual(housing_icon, household_icon)
        self.assertIn("M3.5 11 12 3.2 20.5 11", household_icon)
        self.assertEqual(self.home.count('class="group-icon"'), len(self.site["groups"]))
        self.assertNotIn("group-icon", self.about)
        filter_row = re.search(
            r'<section class="category-filter"[\s\S]*?</section>',
            self.home,
        ).group(0)
        self.assertNotIn("<svg", filter_row)
        self.assertNotIn("group-icon", filter_row)
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
                rf'<h2 id="group-{group["id"]}">(<svg class="group-icon"[\s\S]*?</svg>)<span>{re.escape(group["title"])}</span></h2>',
                self.home,
            )
            self.assertIsNotNone(heading, group["id"])
            icon = heading.group(1)
            self.assertIn('aria-hidden="true"', icon)
            self.assertIn('stroke="currentColor"', icon)
            self.assertNotIn("<img", icon)
            self.assertNotIn("href=", icon)
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


if __name__ == "__main__":
    unittest.main()
