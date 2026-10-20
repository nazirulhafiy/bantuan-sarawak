#!/usr/bin/env python3
"""Fact-check scheme cards against sources/ snapshots.

Checks:
  (c) quotes — each amount, paragraph, and due line has a quote that appears
      (normalized) in the snapshot; numbers on the line appear in its quote;
      cap facts use an "or below" comparator; required facts are covered.
  (d) tokens — every RM figure, date, and key name on a card appears in the
      snapshot (normalized).

Exit 0 on success. Exit 1 and print FAIL lines on violation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMES_PATH = ROOT / "data" / "schemes.json"
SOURCES_DIR = ROOT / "sources"

# Keep in sync with scripts/snapshot_sources.py
URL_TO_SOURCE_ID: dict[str, str] = {
    "https://service.sarawak.gov.my/web/web/home/sla_view/0/821/": "skas",
    "https://www.sarawakenergy.com/media-info/announcements-publications/extension-of-electricity-discounts-for-sarawak-energy-account-holders-until-december-2026": "electricity",
    "https://myys.yayasansarawak.org.my/": "myys",
    "https://yayasansarawak.org.my/en/biasiswa-2/": "biasiswa",
    "https://meitd.sarawak.gov.my/web/subpage/webpage_view/156": "ftes",
    "https://yayasansarawak.org.my/en/bantuan-pelajar-ke-ipt2/": "bantuan-pelajar",
    "https://hdc.sarawak.gov.my/web/subpage/webpage_view/163": "hdas",
    "https://hdc.sarawak.gov.my/web/subpage/webpage_view/139": "sras",
    "https://hdc.sarawak.gov.my/web/subpage/webpage_view/127": "spektra-permata",
    "https://mudenr.sarawak.gov.my/web/attachment/show/?docid=U2JnN2NtQmNWZi9DWkhaYUlUMnhsdz09OjrhxKX9m6xObBhS-XQMz_Kf": "sri-pertiwi",
    "https://service.sarawak.gov.my/web/web/home/sla_view/0/742/": "schb",
    "https://service.sarawak.gov.my/web/web/home/sla_view/211/822": "kgc",
    "https://service.sarawak.gov.my/web/web/home/sla_view/211/847/": "bik",
    "https://service.sarawak.gov.my/web/web/home/sla_view/211/383/": "bib",
    "https://kpwk.sarawak.gov.my/web/subpage/webpage_view/100": "efs",
    "https://jwks.sarawak.gov.my/web/subpage/webpage_view/182": "kirwas",
    "https://service.sarawak.gov.my/web/web/home/sla_view/259/390": "smcs",
    "https://welfare.sarawak.gov.my/web/subpage/webpage_view/159": "geran-pelancaran",
    "https://welfare.sarawak.gov.my/web/subpage/webpage_view/130": "ba-bbb",
}

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
PERCENT_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*%")
ISO_DATE_RE = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")
EN_DATE_RE = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(EN_MONTHS) + r")\s+(20\d{2})\b",
    re.I,
)
MS_DATE_RE = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(MS_MONTHS) + r")\s+(20\d{2})\b",
    re.I,
)
# Soft relative windows still treated as date tokens when present on cards
REL_DATE_RE = re.compile(
    r"(?i)\b(mid-[a-z]+(?:\s+20\d{2})?|\d+\s+days|\d+\s+months?|\d+\s+years?|"
    r"within\s+\d+\s+year|within\s+\d+\s+months?)\b"
)

CAP_PHRASES = re.compile(
    r"(?i)(or below|or less|and below|and less|below|di bawah|ke bawah|dan ke bawah|"
    r"tidak melebihi|tidak melebih|melebih|not (?:be )?above|not exceed|"
    r"maximum of|up to|at or below|≤|<=)"
)

# Proper-name tokens that must be source-backed when they appear on a card.
KEY_NAME_RE = re.compile(
    r"\b(?:"
    r"S Pay Global|SPay Global|Sarawak Energy|Service Sarawak|"
    r"Sumbangan Tunai Rahmah|STR|Yayasan Sarawak|my-Yayasan|"
    r"Housing Development Corporation|HDC|Imbuhan Tetap Perumahan|"
    r"Swinburne|Curtin|UTS|i-CATS|SIHL|JKMS|iSarawakCare|SarawakPass|"
    r"Kenyalang Gold Card|Tariff D|Anak Sarawak|status K|"
    r"Ministry of Higher Education|Mutiara|Agrobank|SEDC|"
    r"Program Perumahan Rakyat|PPR"
    r")\b",
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
    # Collapse whitespace around hyphens: "non -commercial" / "pro - rated" → "non-commercial" / "pro-rated"
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


def extract_rm_tokens(text: str) -> set[str]:
    out: set[str] = set()
    for m in RM_RE.finditer(text):
        digits = re.sub(r"[,\s]", "", m.group(1))
        if "." in digits:
            whole, frac = digits.split(".", 1)
            if set(frac) <= {"0"}:
                digits = whole
        out.add(f"rm{digits}")
    return out


def extract_date_tokens(text: str) -> set[str]:
    norm = normalize_text(text)
    return set(re.findall(r"date:\d{4}-\d{2}-\d{2}", norm))


def extract_key_names(text: str) -> set[str]:
    """Return normalized key-name needles for snapshot containment."""
    out: set[str] = set()
    for m in KEY_NAME_RE.finditer(text):
        raw = m.group(0)
        # Skip ultra-short tokens that collide (UTS alone is handled via alias).
        if raw.lower() in {"uts", "str", "hdc", "ppr"}:
            # Still require them, but via normalize aliases / exact word in snap
            out.add(normalize_text(raw))
            continue
        out.add(normalize_text(raw))
    return out


def line_number_tokens(text: str) -> set[str]:
    """Numbers that must appear in the supporting quote (RM + plain integers with commas)."""
    tokens = extract_rm_tokens(text)
    for m in PERCENT_RE.finditer(text):
        tokens.add(f"pct{m.group(1)}")
    # Significant plain amounts like 10% deposit phrasing already covered; also
    # bare figures that sit next to RM context are in extract_rm_tokens.
    for m in re.finditer(r"\b(\d{1,3}(?:,\d{3})+|\d{4,})\b", text):
        digits = m.group(1).replace(",", "")
        # skip years
        if re.fullmatch(r"20\d{2}", digits):
            continue
        tokens.add(digits)
    tokens |= extract_date_tokens(text)
    return tokens


def quote_has_numbers(quote: str, line: str) -> bool:
    need = line_number_tokens(line)
    if not need:
        return True
    qn = normalize_text(quote)
    # Also accept percent spelled without % when line has 0%
    for tok in need:
        if tok.startswith("rm"):
            if tok not in qn and tok.replace("rm", "") not in qn:
                return False
        elif tok.startswith("pct"):
            num = tok[3:]
            if f"{num}%" not in quote.lower() and num not in qn:
                # allow "zero interest" for 0%
                if num == "0" and re.search(r"(?i)zero\s+interest", quote):
                    continue
                return False
        elif tok.startswith("date:"):
            if tok not in qn:
                return False
        else:
            if tok not in qn and f"rm{tok}" not in qn:
                return False
    return True


def source_id_for(scheme: dict) -> str:
    url = (scheme.get("links") or [{}])[0].get("url")
    if not url or url not in URL_TO_SOURCE_ID:
        raise KeyError(f"{scheme.get('id')}: unmapped source URL {url!r}")
    return URL_TO_SOURCE_ID[url]


def load_snapshot(source_id: str) -> str:
    path = SOURCES_DIR / f"{source_id}.txt"
    if not path.exists():
        raise FileNotFoundError(f"missing snapshot {path}")
    return path.read_text(encoding="utf-8")


def as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def validate_scheme(scheme: dict, *, require_quotes: bool = True) -> list[str]:
    """Return list of failure messages for one scheme."""
    fails: list[str] = []
    sid = scheme.get("id", "?")
    try:
        source_id = source_id_for(scheme)
        snap = load_snapshot(source_id)
    except (KeyError, FileNotFoundError) as exc:
        return [f"{sid}: {exc}"]

    snap_norm = normalize_text(snap)

    amounts = list(scheme.get("amounts") or [])
    paragraphs = list(scheme.get("paragraphs") or [])
    dues = as_list(scheme.get("due"))
    amount_quotes = list(scheme.get("amount_quotes") or [])
    paragraph_quotes = list(scheme.get("paragraph_quotes") or [])
    due_quotes = as_list(scheme.get("due_quotes"))
    facts = list(scheme.get("facts") or [])

    if require_quotes:
        if amounts and len(amount_quotes) != len(amounts):
            fails.append(
                f"{sid}: quote.missing — amount_quotes length {len(amount_quotes)} != amounts {len(amounts)}"
            )
        if len(paragraph_quotes) != len(paragraphs):
            fails.append(
                f"{sid}: quote.missing — paragraph_quotes length {len(paragraph_quotes)} != paragraphs {len(paragraphs)}"
            )
        if dues and len(due_quotes) != len(dues):
            fails.append(
                f"{sid}: quote.missing — due_quotes length {len(due_quotes)} != due {len(dues)}"
            )

    def check_pair(kind: str, index: int, line: str, quote: str | None) -> None:
        if not quote:
            if require_quotes:
                fails.append(f"{sid}: quote.missing — {kind}[{index}]")
            return
        if normalize_text(quote) not in snap_norm and quote not in snap:
            fails.append(
                f"{sid}: quote.not_in_snapshot — {kind}[{index}] {quote[:60]!r}"
            )
        if not quote_has_numbers(quote, line):
            fails.append(
                f"{sid}: quote.numbers — {kind}[{index}] numbers from {line!r} missing in quote"
            )

    for i, line in enumerate(amounts):
        q = amount_quotes[i] if i < len(amount_quotes) else None
        check_pair("amounts", i, line, q)
    for i, line in enumerate(paragraphs):
        q = paragraph_quotes[i] if i < len(paragraph_quotes) else None
        check_pair("paragraphs", i, line, q)
    for i, line in enumerate(dues):
        q = due_quotes[i] if i < len(due_quotes) else None
        check_pair("due", i, str(line), q)

    # Facts: caps need comparator; required facts must be covered by some quote.
    all_quotes = [q for q in amount_quotes + paragraph_quotes + due_quotes if q]
    for fact in facts:
        fid = fact.get("id", "?")
        kind = fact.get("kind")
        required = bool(fact.get("required", False))
        if kind == "cap":
            op = fact.get("op")
            if op != "<=":
                fails.append(f"{sid}: fact.comparator — {fid} cap requires op '<=' (got {op!r})")
                continue
            covered = False
            for q in all_quotes:
                if CAP_PHRASES.search(q):
                    val = fact.get("value")
                    qn = normalize_text(q)
                    if val is None or f"rm{val}" in qn or str(val) in qn:
                        covered = True
                        break
            if required and not covered:
                fails.append(f"{sid}: fact.uncovered — {fid} (cap <= not evidenced in quotes)")
        elif required:
            val = fact.get("value")
            needle = None
            if kind == "amount" and val is not None:
                needle = f"rm{val}"
            elif kind == "date" and val is not None:
                needle = normalize_text(str(val))
            elif kind == "eligibility":
                needle = normalize_text(str(fact.get("label") or val or fid))
            covered = False
            if needle:
                for q in all_quotes:
                    qn = normalize_text(q)
                    if needle in qn or (val is not None and str(val) in qn):
                        covered = True
                        break
            if needle and not covered:
                fails.append(f"{sid}: fact.uncovered — {fid}")

    # Token rule (d): RM figures, dates, key names on the card → snapshot
    card_bits = []
    card_bits.extend(amounts)
    card_bits.extend(paragraphs)
    card_bits.extend(str(d) for d in dues)
    if scheme.get("unspecified"):
        card_bits.append(str(scheme["unspecified"]))
    if scheme.get("amount_note"):
        card_bits.append(str(scheme["amount_note"]))
    card_bits.append(str(scheme.get("title") or ""))
    card_text = "\n".join(card_bits)

    for tok in extract_rm_tokens(card_text):
        if tok not in snap_norm:
            fails.append(f"{sid}: token.rm — {tok} not in snapshot {source_id}")
    for tok in extract_date_tokens(card_text):
        if tok not in snap_norm:
            # also allow relative windows that are not absolute calendar dates
            fails.append(f"{sid}: token.date — {tok} not in snapshot {source_id}")
    for name in extract_key_names(card_text):
        if name and name not in snap_norm:
            fails.append(f"{sid}: token.name — {name!r} not in snapshot {source_id}")

    return fails


def validate_schemes(
    schemes: list[dict],
    *,
    require_quotes: bool = True,
) -> list[str]:
    fails: list[str] = []
    for scheme in schemes:
        fails.extend(validate_scheme(scheme, require_quotes=require_quotes))
    return fails


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--schemes",
        type=Path,
        default=SCHEMES_PATH,
        help="path to schemes.json (default: data/schemes.json)",
    )
    parser.add_argument(
        "--allow-missing-quotes",
        action="store_true",
        help="skip quote presence checks (still runs token rule)",
    )
    parser.add_argument(
        "--skip-source-labels",
        action="store_true",
        help="skip data/allowed-sources.json label checks",
    )
    parser.add_argument(
        "--only",
        help="comma-separated scheme ids",
    )
    args = parser.parse_args(argv)

    schemes = json.loads(args.schemes.read_text(encoding="utf-8"))
    if args.only:
        wanted = {x.strip() for x in args.only.split(",")}
        schemes = [s for s in schemes if s["id"] in wanted]

    fails: list[str] = []

    if not args.skip_source_labels:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import schemes_lib as L  # noqa: WPS433

        allowed = L.load_allowed_sources()
        fails.extend(L.validate_collection(schemes, allowed))
        label_ok = not fails
    else:
        allowed = set()
        label_ok = True

    fails.extend(validate_schemes(schemes, require_quotes=not args.allow_missing_quotes))
    if fails:
        print("FAIL")
        for line in fails:
            print(line)
        return 1

    if label_ok and not args.skip_source_labels:
        print(
            f"OK: {len(schemes)} schemes; source labels in allowed set ({len(allowed)} names)"
        )
    print(f"PASS fact-check ({len(schemes)} schemes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
