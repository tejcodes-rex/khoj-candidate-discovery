"""
An independent gold relevance labeler.

The competition hides the ground truth, so we build our own faithful proxy to
measure and tune against. This labeler is deliberately structured differently
from the scorer: where the scorer is a weighted continuous formula, this is a
hard tiered checklist read straight off the job description and the archetype
structure we found in the data. Because the two are independent formalizations of
the same JD, their agreement is informative rather than circular, and the places
they disagree are exactly where we look for bugs.

Tiers follow the challenge's scheme: 0 (irrelevant, includes honeypots and traps)
up to 5 (the ideal hire). "Relevant" in the official metrics is tier 3+.
"""

from datetime import date

from . import lexicons as L
from .honeypot import detect as detect_honeypot
from .match import hits as _mhits
from .scoring import _history_text, _summary_text, NON_TECH, JUNIOR_MARKERS

REF = date(2026, 6, 17)

# Archetype read from the templated summary opening.
OFFROLE_ARCH = "Professional with"
GENERIC_DEV_ARCH = "Software engineer with"


def _archetype(cand):
    s = (cand.get("profile", {}).get("summary") or "").strip()
    if s.startswith(OFFROLE_ARCH):
        return "offrole"
    if s.startswith(GENERIC_DEV_ARCH):
        return "generic_dev"
    if s.startswith("Software / data professional"):
        return "data_adjacent"
    if s.startswith(("Data scientist / ML", "Machine learning engineer", "Senior AI engineer",
                     "AI engineer", "Applied")):
        return "core_ml"
    return "other"


def _has(text, terms):
    return bool(_mhits(text, terms))


def gold_tier(cand):
    """Return an integer relevance tier 0..5 for this candidate."""
    if detect_honeypot(cand)[0]:
        return 0

    p = cand.get("profile", {})
    title = (p.get("current_title") or "").lower()
    arch = _archetype(cand)
    ctext = _history_text(cand)            # DEMONSTRATED work only, not the summary
    stext = _summary_text(cand)
    yoe = float(p.get("years_of_experience", 0) or 0)

    # Hard zeros: off-role people and generic developers with no ML at all.
    if arch == "offrole" or any(n in title for n in NON_TECH):
        return 0
    ml_terms = {"machine learning", "ml", "nlp", "deep learning", "embedding",
                "ranking", "retrieval", "recommendation", "recsys", "llm"}
    if arch == "generic_dev" and not _has(ctext, ml_terms):
        return 0

    # Build up evidence points for genuine AI/ML candidates, from the career
    # history (so aspirational summary keywords earn nothing).
    pts = 0
    retrieval = _has(ctext, {"retrieval", "ranking", "recommendation", "recsys",
                             "personalization", "relevance", "semantic search"}) \
        or _has(ctext, L.PLAIN_IR)
    if retrieval:
        pts += 2
    if _has(ctext, set(L.VECTOR_INFRA) | set(L.EMBED_MODELS) | {"embedding", "embeddings"}):
        pts += 1
    if _has(ctext, set(L.EVAL_TERMS)):
        pts += 1
    # Analyst decoy: aspirational tell in summary and no real retrieval history.
    if _has(stext, L.ANALYST_TELL) and not retrieval:
        return min(2, 2 if arch == "core_ml" else 1)
    comps = " ".join([(p.get("current_company") or "").lower()] +
                     [(r.get("company") or "").lower() for r in cand.get("career_history", [])])
    product = any(f in comps for f in L.PRODUCT_FIRMS)
    services_only = any(f in comps for f in L.SERVICES_FIRMS) and not product
    if product:
        pts += 1
    if 5 <= yoe <= 9:
        pts += 1
    elif 4 <= yoe <= 11:
        pts += 0  # acceptable but not ideal

    sig = cand.get("redrob_signals", {}) or {}
    try:
        la = sig.get("last_active_date", "2024-01-01").split("-")
        days = (REF - date(int(la[0]), int(la[1]), int(la[2]))).days
    except (ValueError, AttributeError):
        days = 999
    reachable = days <= 60 and float(sig.get("recruiter_response_rate", 0) or 0) >= 0.4 \
        and sig.get("open_to_work_flag", False)
    if reachable:
        pts += 1
    loc = (p.get("location") or "").lower()
    if (p.get("country") or "").lower() == "india" or sig.get("willing_to_relocate"):
        if any(h in loc for h in L.INDIA_HUBS) or (p.get("country") or "").lower() == "india":
            pts += 1

    # Disqualifier caps, straight from the JD.
    cap = 5
    cv = _has(ctext, L.CV_SPEECH_ROBOTICS)
    nlpir = _has(ctext, L.NLP_IR)
    if cv and not nlpir:
        cap = min(cap, 1)
    if any(j in title for j in JUNIOR_MARKERS):
        cap = min(cap, 2)
    if services_only:
        cap = min(cap, 1)
    if ("research" in ctext or "phd" in ctext) and not _has(ctext, L.PRODUCTION) and not retrieval:
        cap = min(cap, 1)
    roles = cand.get("career_history", [])
    if len(roles) >= 4 and sum(r.get("duration_months", 0) or 0 for r in roles) / len(roles) < 18:
        cap = min(cap, 3)

    # Map points (0..7) to a tier, then apply the cap.
    if pts >= 7:
        tier = 5
    elif pts >= 6:
        tier = 4
    elif pts >= 4:
        tier = 3
    elif pts >= 3:
        tier = 2
    elif pts >= 2:
        tier = 1
    else:
        tier = 0

    if arch in ("core_ml",) and tier < 1 and not (cv and not nlpir):
        tier = 1  # a core ML profile is at least marginally relevant
    return min(tier, cap)
