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
        no_source = {
            "skas",
            "electricity",
            "rental",
            "igps",
            "ipt-entry",
            "ftes",
            "hdras",
            "spektra-lite",
            "sri-pertiwi",
        }
        self.assertEqual({scheme["id"] for scheme in self.schemes if not scheme["links"]}, no_source)
        self.assertEqual(sum(len(scheme["links"]) for scheme in self.schemes), 22)
        for scheme in self.schemes:
            card = article(self.home, scheme["id"])
            word = "State" if scheme["level"] == "STATE" else "Federal"
            self.assertIn(f'class="level level-{scheme["level"].lower()}"', card)
            self.assertIn(f">{word}</span>", card)
            self.assertIn(scheme["title"], card)
            for link in scheme["links"]:
                self.assertIn(link["url"], card)
                self.assertIn('class="sources-title">Source</h4>', card)
            if scheme["links"]:
                self.assertIn('class="sources"', card)
            else:
                self.assertNotIn("sources-title", card)
                self.assertNotIn('class="sources"', card)
            if scheme["amount_basis"] == "none":
                self.assertNotIn('class="amount-list"', card)
                for amount in scheme.get("amounts") or []:
                    self.assertNotIn(amount, card)
            else:
                for amount in scheme["amounts"]:
                    self.assertIn(amount, card)

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
        self.assertNotIn("meitd.sarawak.gov.my", self.home)
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
        hdras = article(self.home, "hdras").casefold()
        self.assertNotIn("rm200", hdras)
        self.assertNotIn("48", hdras)
        efs = article(self.home, "efs")
        self.assertIn("1 January 2026", efs)
        self.assertIn("fully online", efs)
        self.assertNotIn("JPN", efs)
        skas_amounts = re.search(r'id="skas"[\s\S]*?<ul class="amount-list">([\s\S]*?)</ul>', self.home).group(1)
        self.assertIn("RM1,100", skas_amounts)
        self.assertIn("RM600", skas_amounts)
        self.assertIn("RM375", skas_amounts)
        self.assertNotIn("RM800", skas_amounts)
        self.assertNotIn("Use RM600", self.home)
        self.assertNotIn("state and federal", (self.home + self.about).casefold())
        self.assertIn("25%", article(self.home, "electricity"))
        self.assertIn("50%", article(self.home, "rental"))
        self.assertIn("IGPS", self.home)
        self.assertIn("selected courses", article(self.home, "ftes").casefold())

    def test_published_directory_is_state_only(self):
        self.assertEqual(len(self.schemes), 25)
        self.assertTrue(all(scheme["level"] == "STATE" for scheme in self.schemes))
        updated = re.search(r'<p class="updated">(.*?)</p>', self.home).group(1)
        self.assertIn(">Last updated</span>", updated)
        self.assertIn(">SUNDAY, 4 OCT 2026</time>", updated)
        self.assertNotIn("Checked", updated)
        self.assertNotIn("schemes", updated.casefold())
        self.assertNotIn("updated-count", self.home)
        deck = re.search(r'<p class="brief-deck">(.*?)</p>', self.home).group(1)
        self.assertEqual(deck, "A directory of state help for people in Sarawak.")
        self.assertNotIn('data-level="federal"', self.home)
        self.assertNotIn("level-filter", self.home)
        self.assertNotIn("data-level-filter", self.home)
        self.assertIn('<p class="category-filter-title" id="category-filter-title">Browse by category</p>', self.home)
        self.assertIn('data-category-filter', self.home)
        self.assertNotIn('data-category-filter hidden', self.home)
        self.assertNotRegex(self.home, r'<section class="category-filter"[^>]*\shidden')
        self.assertIn('data-section-filter="all"', self.home)
        self.assertIn("Showing all 25 schemes", self.home)
        self.assertNotIn("jump-links", self.home)
        self.assertNotIn("Household, senior and single adult", self.home + self.about)
        household = next(group for group in self.site["groups"] if group["id"] == "household")
        self.assertEqual(household["id"], "household")
        self.assertEqual(household["title"], "Household")
        welfare = next(group for group in self.site["groups"] if group["id"] == "welfare")
        self.assertEqual(welfare["id"], "welfare")
        self.assertEqual(welfare["title"], "Welfare")
        self.assertIn('id="group-welfare">Welfare</h2>', self.home)
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
            self.assertIn(f'id="group-{group["id"]}">{group["title"]}</h2>', self.home)
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
        self.assertIn("padding: 6px 8px;", css)
        self.assertIn("font-size: 11px;", css)
        self.assertIn("border-radius: 6px;", css)
        script = (self.dist / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("data-level-filter", script)
        self.assertNotIn("levelFilter", script)
        self.assertIn("data-category-filter", script)
        self.assertIn("Showing all ${visibleCount} schemes", script)

    def test_ringgit_figures_are_on_the_allowlist(self):
        found = {value.replace(",", "") for value in re.findall(r"RM\s*([0-9][0-9,]*)", self.home + self.about)}
        self.assertTrue(found)
        self.assertEqual(found - ALLOWED_RM, set())


if __name__ == "__main__":
    unittest.main()
