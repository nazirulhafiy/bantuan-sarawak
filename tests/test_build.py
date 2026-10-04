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
        for scheme in self.schemes:
            card = article(self.home, scheme["id"])
            word = "State" if scheme["level"] == "STATE" else "Federal"
            self.assertIn(f'class="level level-{scheme["level"].lower()}"', card)
            self.assertIn(f">{word}</span>", card)
            self.assertIn(scheme["title"], card)
            for link in scheme["links"]:
                self.assertIn(link["url"], card)
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
        self.assertIn("What changed in the 4 October 2026 check", self.home)
        self.assertIn("25 May 2026", self.home)
        self.assertIn("independent", self.about.casefold())
        self.assertIn("4 October 2026", self.about)
        self.assertIn("does not run", self.about)
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
        bwe = article(self.home, "bwe")
        self.assertIn("RM600 a month", bwe)
        self.assertIn("RM500", bwe)
        self.assertIn("Use RM600", bwe)
        self.assertIn('data-level="federal"', article(self.home, "ppr"))
        self.assertIn('data-level="federal"', article(self.home, "nextgen"))
        self.assertIn('data-level="federal"', article(self.home, "budi"))
        self.assertIn("25%", article(self.home, "electricity"))
        self.assertIn("50%", article(self.home, "rental"))
        self.assertIn("IGPS", self.home)
        self.assertIn("selected courses", article(self.home, "ftes").casefold())

    def test_ringgit_figures_are_on_the_allowlist(self):
        found = {value.replace(",", "") for value in re.findall(r"RM\s*([0-9][0-9,]*)", self.home + self.about)}
        self.assertTrue(found)
        self.assertEqual(found - ALLOWED_RM, set())


if __name__ == "__main__":
    unittest.main()
