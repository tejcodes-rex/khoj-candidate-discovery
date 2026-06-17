"""
Job description understanding.

The brief asks for interpreting "complex, nuanced job descriptions" and reading
the implicit asks, not just the keywords. We turn a JD into a structured spec:
must-have and nice-to-have skills (canonicalized), an experience band, a
seniority level, and a set of intent flags mined from the prose (for example,
"we care more about what you have shipped than where you studied" sets a
pedigree-agnostic flag that the Hidden-Gem engine reads).

A model-based extractor can replace the rule layer behind the same interface;
the deterministic rules below guarantee the pipeline runs fully offline.
"""

import re

from . import skills
from .text import normalize_text

_SENIORITY = {
    "intern": 0, "junior": 1, "associate": 1, "mid": 2, "senior": 3,
    "lead": 4, "staff": 4, "principal": 5,
}

# phrases that signal the employer explicitly de-emphasizes pedigree
_PEDIGREE_AGNOSTIC = [
    "care more about", "matter less", "matters less", "regardless of",
    "where you studied", "pedigree", "what you have built", "what you have shipped",
    "actually shipped", "not only people who have read",
]
_HANDS_ON = ["hands-on", "hands on", "not a manager", "builder", "builders"]


def parse(job):
    """Return a structured requirement spec from a job dict."""
    desc = job.get("description", "")
    norm = normalize_text(desc)

    must = skills.canonical_set(job.get("must_have"))
    nice = skills.canonical_set(job.get("nice_to_have"))

    # mine extra skills mentioned in the prose
    for canon in skills.FAMILY:
        if canon in norm and canon not in must:
            nice.add(canon)

    seniority_str = (job.get("seniority") or "").lower()
    seniority = 2
    for k, v in _SENIORITY.items():
        if k in seniority_str or k in norm:
            seniority = max(seniority if k in seniority_str else 0, v)
            if k in seniority_str:
                break

    pedigree_agnostic = any(p in desc.lower() for p in _PEDIGREE_AGNOSTIC)
    hands_on = any(p in desc.lower() for p in _HANDS_ON)

    return {
        "job_id": job.get("job_id"),
        "title": job.get("title", ""),
        "must_have": sorted(must),
        "nice_to_have": sorted(nice - must),
        "must_families": sorted(f for f in skills.families(must) if f),
        "min_experience_years": int(job.get("min_experience_years", 0) or 0),
        "seniority": seniority,
        "pedigree_agnostic": pedigree_agnostic,
        "hands_on": hands_on,
        "query_text": normalize_text(
            job.get("title", "") + ". " + desc + " " +
            " ".join(job.get("must_have", []) or []) + " " +
            " ".join(job.get("nice_to_have", []) or [])
        ),
    }
