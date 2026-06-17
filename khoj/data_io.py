"""
Loading, canonicalization, and dedup of messy profiles.

This is the layer that absorbs the real-world mess described in the brief:
missing fields, junk casing, duplicate profiles, Hinglish, empty skills. It
turns whatever the source looks like into one canonical Candidate shape that the
rest of the pipeline relies on.

To swap in the official dataset, write a single adapter function here that maps
their columns to the canonical shape. Nothing downstream changes.
"""

import json
from pathlib import Path

from . import skills
from .text import normalize_text


def _years(experience):
    total = 0
    for r in experience or []:
        try:
            total += max(0, int(r.get("to", 0)) - int(r.get("from", 0)))
        except (TypeError, ValueError):
            continue
    return total


def canonicalize(raw):
    """Turn one raw profile into the canonical Candidate shape, defensively."""
    exp = raw.get("experience") or []
    skill_set = skills.canonical_set(raw.get("skills"))

    # Mine skills out of free text too, so under-tagged profiles are not penalized.
    blob = " ".join([
        raw.get("summary", "") or "",
        raw.get("headline", "") or "",
        " ".join((r.get("title", "") or "") + " " + (r.get("blurb", "") or "") for r in exp),
    ])
    norm_blob = normalize_text(blob)

    titles = [normalize_text(r.get("title", "")) for r in exp]
    employers = [(r.get("employer", "") or "").lower() for r in exp]

    return {
        "candidate_id": raw.get("candidate_id") or raw.get("id") or "",
        "name": (raw.get("name") or "").strip(),
        "headline": normalize_text(raw.get("headline", "")),
        "summary": normalize_text(raw.get("summary", "")),
        "location": raw.get("location") or "unknown",
        "city_tier": raw.get("city_tier", 0),
        "education": (raw.get("education") or "").strip(),
        "skills": sorted(skill_set),
        "skill_families": sorted(f for f in skills.families(skill_set) if f),
        "titles": titles,
        "employers": employers,
        "years_experience": _years(exp),
        "n_roles": len(exp),
        "experience": exp,
        "signals": raw.get("signals") or {},
        "text_blob": norm_blob,
        # carried through only for offline evaluation; never used in scoring
        "_archetype": raw.get("_archetype"),
    }


def searchable_document(cand):
    """The text a candidate is indexed and retrieved on."""
    parts = [
        cand["headline"], cand["summary"], cand["text_blob"],
        " ".join(cand["skills"]), " ".join(cand["titles"]),
        cand["education"].lower(),
    ]
    return " ".join(p for p in parts if p)


def _signature(cand):
    """Cheap near-duplicate signature: name plus top skills plus experience."""
    name = "".join(cand["name"].lower().split())
    return (name, tuple(cand["skills"][:5]), cand["years_experience"])


def load_profiles(path):
    """Load JSONL profiles, canonicalize, and drop near-duplicates."""
    raws = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                raws.append(json.loads(line))

    seen = {}
    dropped = 0
    for raw in raws:
        cand = canonicalize(raw)
        sig = _signature(cand)
        if sig in seen:
            dropped += 1
            continue
        seen[sig] = cand
    return list(seen.values()), {"loaded": len(raws), "deduped": dropped}


def load_jobs(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_qrels(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
