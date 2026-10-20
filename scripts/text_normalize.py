#!/usr/bin/env python3
"""Shared text normalizer for source comparisons.

Copied from the fact-check stack (validate.py on the quote-checks branch) so
on-demand source checks can share the same folding rules without depending on
that PR landing first. Keep in sync when the normalizer changes there.
"""

from __future__ import annotations

import re
import unicodedata

EN_MONTHS = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}
MS_MONTHS = {
    "januari": "01",
    "februari": "02",
    "mac": "03",
    "april": "04",
    "mei": "05",
    "jun": "06",
    "julai": "07",
    "ogos": "08",
    "september": "09",
    "oktober": "10",
    "november": "11",
    "disember": "12",
}

RM_RE = re.compile(
    r"(?i)\bRM\s*([0-9]{1,3}(?:[,\s][0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)"
)
ISO_DATE_RE = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")
EN_DATE_RE = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(EN_MONTHS) + r")\s+(20\d{2})\b",
    re.I,
)
MS_DATE_RE = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(MS_MONTHS) + r")\s+(20\d{2})\b",
    re.I,
)


def normalize_text(text: str) -> str:
    """Normalize numbers, dates, dashes and whitespace for containment checks."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    # Fold Unicode hyphens/dashes to ASCII hyphen-minus. Include U+2010 (HYPHEN),
    # which NFKC may emit from U+2011 (NON-BREAKING HYPHEN), plus en/em dash,
    # figure dash, horizontal bar, and minus sign.
    for ch in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2015", "\u2212"):
        text = text.replace(ch, "-")
    # Collapse whitespace around hyphens: "non -commercial" / "pro - rated"
    text = re.sub(r"\s*-\s*", "-", text)
    # Drop spaces before punctuation: "2026 ." / "bill ," → "2026." / "bill,"
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    # Fold curly/smart quotes to ASCII so status-K patterns match snapshot wording
    for ch in ("\u2018", "\u2019", "\u201a", "\u201b", "\u2039", "\u203a"):
        text = text.replace(ch, "'")
    for ch in ("\u201c", "\u201d", "\u201e", "\u201f", "\u00ab", "\u00bb"):
        text = text.replace(ch, '"')
    text = text.lower()

    # Name aliases before other rewrites.
    # Use (?<!\w)/(?!\w) instead of \b so a leading quote on 'K' still matches.
    text = re.sub(r"\bs\s*pay\s*global\b", "spayglobal", text)
    text = re.sub(r"(?<!\w)status\s*['\"]?k['\"]?(?!\w)", "statusk", text)
    text = re.sub(r"['\"]k['\"]\s*status(?!\w)", "statusk", text)
    text = re.sub(r"['\"]?k['\"]?\s*identification\b", "statusk identification", text)
    text = re.sub(r"\bholding a ['\"]?k['\"]?(?!\w)", "statusk", text)
    text = re.sub(r"\bbearing the ['\"]?k['\"]?(?!\w)", "statusk", text)
    text = re.sub(r"\bhold ['\"]k['\"] status(?!\w)", "statusk", text)
    text = re.sub(r"\bwith status ['\"]?k['\"]?(?!\w)", "statusk", text)
    text = re.sub(r"\bwith ['\"]k['\"]\s*\(sarawak\)", "statusk", text)
    text = re.sub(r"\bdengan status ['\"]?k['\"]?(?!\w)", "statusk", text)
    text = re.sub(r"\bberstatus ['\"]?k['\"]?(?!\w)", "statusk", text)
    text = re.sub(r"['\"]k['\"]\s*\(sarawak\)", "statusk", text)
    text = re.sub(r"\bservice sarawak\b", "servicesarawak", text)
    text = re.sub(r"\bsarawak government portal\b", "servicesarawak", text)
    text = re.sub(r"\buniversity of technology sarawak\b", "uts", text)

    def rm_sub(m: re.Match[str]) -> str:
        raw = m.group(1)
        digits = re.sub(r"[,\s]", "", raw)
        if "." in digits:
            whole, frac = digits.split(".", 1)
            if set(frac) <= {"0"}:
                digits = whole
            else:
                digits = f"{whole}.{frac}"
        return f"rm{digits}"

    text = RM_RE.sub(rm_sub, text)

    def iso_sub(m: re.Match[str]) -> str:
        return f"date:{m.group(1)}-{m.group(2)}-{m.group(3)}"

    text = ISO_DATE_RE.sub(iso_sub, text)

    def en_sub(m: re.Match[str]) -> str:
        day = int(m.group(1))
        month = EN_MONTHS[m.group(2).lower()]
        return f"date:{m.group(3)}-{month}-{day:02d}"

    text = EN_DATE_RE.sub(en_sub, text)

    def ms_sub(m: re.Match[str]) -> str:
        day = int(m.group(1))
        month = MS_MONTHS[m.group(2).lower()]
        return f"date:{m.group(3)}-{month}-{day:02d}"

    text = MS_DATE_RE.sub(ms_sub, text)

    text = re.sub(r"\s+", " ", text)
    return text.strip()
