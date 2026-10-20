"""Shared validation for published scheme source labels (data/schemes.json)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SCHEMES = DATA / "schemes.json"
ALLOWED_SOURCES = DATA / "allowed-sources.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_allowed_sources(path: Path = ALLOWED_SOURCES) -> set[str]:
    payload = load_json(path)
    if not isinstance(payload, list) or not payload:
        raise ValueError("data/allowed-sources.json must be a non-empty JSON array")
    allowed: set[str] = set()
    for entry in payload:
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError("allowed sources must be non-empty strings")
        name = entry.strip()
        if name in allowed:
            raise ValueError(f"duplicate allowed source: {name}")
        allowed.add(name)
    return allowed


def validate_scheme_source(scheme: dict, allowed_sources: set[str]) -> list[str]:
    """Return errors for one scheme's source link label."""
    errs: list[str] = []
    if not isinstance(scheme, dict):
        return ["scheme must be an object"]
    eid = scheme.get("id") or "<missing-id>"
    links = scheme.get("links")
    if not isinstance(links, list) or len(links) != 1:
        errs.append(f"{eid}: needs exactly one source link")
        return errs

    link = links[0]
    if not isinstance(link, dict):
        errs.append(f"{eid}: source link must be an object")
        return errs

    label = link.get("label")
    if label is None or (isinstance(label, str) and not label.strip()):
        errs.append(f"{eid}: source label is required")
    elif not isinstance(label, str):
        errs.append(f"{eid}: source label must be a string")
    elif label not in allowed_sources:
        errs.append(
            f"{eid}: source label {label!r} is not in data/allowed-sources.json"
        )
    elif label != label.strip() or "  " in label:
        errs.append(f"{eid}: source label has leading/trailing or doubled spaces")

    return errs


def validate_collection(
    schemes: list,
    allowed_sources: set[str] | None = None,
) -> list[str]:
    """Validate every published scheme's source label."""
    if allowed_sources is None:
        allowed_sources = load_allowed_sources()
    if not isinstance(schemes, list):
        return ["schemes.json must be a JSON array"]

    errs: list[str] = []
    seen_ids: set[str] = set()
    for index, scheme in enumerate(schemes):
        if not isinstance(scheme, dict):
            errs.append(f"schemes[{index}]: must be an object")
            continue
        eid = scheme.get("id")
        if isinstance(eid, str) and eid:
            if eid in seen_ids:
                errs.append(f"{eid}: duplicate id")
            seen_ids.add(eid)
        errs.extend(validate_scheme_source(scheme, allowed_sources))
    return errs
