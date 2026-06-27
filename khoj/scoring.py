"""
The fit scorer.

This is a faithful, auditable encoding of the Senior AI Engineer JD. The JD is
unusually direct about what it wants and what it considers a trap, so the scorer
is rule-based and transparent rather than a black box. Every candidate gets a
final score in [0, 1] and a structured breakdown that the reasoning layer turns
into plain English.

Design principles, straight from the JD:
  - Career-history evidence outweighs the skills list. Someone who built a
    recommendation system at a product company beats someone who merely lists
    "RAG" as a skill.
  - Skills are trust-weighted by endorsements, time used, and assessment score,
    so lazy keyword stuffing earns almost nothing.
  - The named disqualifiers (off-role titles, pure services careers, job hopping,
    vision/speech-only, pure research) apply real penalties.
  - Behavioral signals modify the fit as a multiplier: a perfect profile that is
    inactive and unreachable is, for hiring, not actually available.
"""

import re
from datetime import date

from . import lexicons as L
from .honeypot import detect as detect_honeypot

REF_DATE = date(2026, 6, 17)

# Specific skill terms that count as relevant to this role. Matched on word
# boundaries so short tokens never produce false hits (no "ml" inside "html",
# no "search" inside "research").
_RELEVANT_SKILL_TERMS = sorted({
    "nlp", "natural language processing", "machine learning", "deep learning",
    "embedding", "embeddings", "retrieval", "information retrieval", "ranking",
    "learning to rank", "recommendation", "recommender", "recsys", "semantic search",
    "vector search", "vector database", "llm", "llms", "language model", "rag",
    "transformer", "transformers", "fine-tuning", "finetuning", "lora", "qlora",
    "peft", "faiss", "milvus", "pinecone", "weaviate", "qdrant", "opensearch",
    "elasticsearch", "bm25", "hnsw", "pgvector", "vespa", "sentence transformers",
    "bge", "e5", "xgboost", "lightgbm", "mlflow", "feature engineering", "mlops",
    "personalization", "search relevance",
}, key=len, reverse=True)
_REL_RE = re.compile(r"(?<![a-z])(" + "|".join(re.escape(t) for t in _RELEVANT_SKILL_TERMS) + r")(?![a-z])")


def _is_relevant_skill(name):
    return bool(_REL_RE.search(name))

NON_TECH = {
    "business analyst", "hr manager", "mechanical engineer", "accountant",
    "project manager", "customer support", "operations manager", "content writer",
    "sales executive", "civil engineer", "graphic designer", "marketing manager",
}

WEIGHTS = {"career": 0.40, "skill_trust": 0.22, "title": 0.18, "experience": 0.20}


from .match import hits as _hits  # word-boundary matching, not naive substring


def _history_text(cand):
    """Only the DEMONSTRATED work: career-history titles and descriptions.

    The summary is deliberately excluded. The dataset's decoys stuff retrieval
    and ranking keywords into aspirational summary lines ("looking to grow into
    ranking") while their actual roles are classification or analytics. Scoring
    evidence on the career history only is what separates real builders from
    keyword-stuffing analysts.
    """
    parts = []
    for r in cand.get("career_history", []):
        parts.append((r.get("title") or "").lower())
        parts.append((r.get("description") or "").lower())
    return " ".join(parts)


def _summary_text(cand):
    p = cand.get("profile", {})
    return ((p.get("summary") or "") + " " + (p.get("headline") or "")).lower()


JUNIOR_MARKERS = ("junior", "intern", "trainee", "fresher", "entry level", "entry-level")
SENIOR_MARKERS = ("senior", "staff", "principal", "lead", "head of", "director")


def _title_score(cand):
    t = (cand.get("profile", {}).get("current_title") or "").lower()
    relevant = any(g in t for g in L.GOOD_TITLES)
    # An explicit junior title is a weak fit for a senior founding-team role,
    # no matter how on-topic the rest of the title reads.
    if any(j in t for j in JUNIOR_MARKERS):
        return (0.45 if relevant else 0.25), "junior-level title for a senior role"
    if relevant:
        if any(sm in t for sm in SENIOR_MARKERS):
            return 1.0, "senior, directly-relevant title"
        return 0.9, "directly-relevant title"
    if any(a in t for a in L.ADJACENT_TITLES):
        return 0.55, "adjacent title, needs career evidence"
    if any(n in t for n in NON_TECH):
        return 0.08, "off-role title for an AI engineering job"
    return 0.30, "unrelated technical title"


def _career_evidence(history_text):
    """Score demonstrated retrieval/ranking/ML work from the career history."""
    ml = _hits(history_text, L.CORE_ML)
    infra = _hits(history_text, L.VECTOR_INFRA)
    embed = _hits(history_text, L.EMBED_MODELS)
    evals = _hits(history_text, L.EVAL_TERMS)
    prod = _hits(history_text, L.PRODUCTION)
    plain = _hits(history_text, L.PLAIN_IR)   # plain-language retrieval/ranking work
    raw = (1.0 * len(ml) + 1.6 * len(infra) + 1.6 * len(embed) + 1.2 * len(evals)
           + 0.4 * len(prod) + 1.6 * len(plain))
    # Normalize so the full stack (retrieval + vector infra + embeddings + eval)
    # separates from partial evidence rather than everyone saturating at 1.0.
    # The JD wants to tell great from good, so resolution at the top matters.
    score = min(1.0, raw / 9.0)
    return score, {"ml": sorted(ml), "infra": sorted(infra), "embed": sorted(embed),
                   "eval": sorted(evals), "production": bool(prod), "plain": sorted(plain)}


def _skill_trust(cand):
    signals = cand.get("redrob_signals", {}) or {}
    assess = signals.get("skill_assessment_scores", {}) or {}
    trusted = []
    stuffed = 0
    seen = set()
    for s in cand.get("skills", []):
        name = (s.get("name") or "").lower()
        seen.add(name)
        if not _is_relevant_skill(name):
            continue
        endorse = min((s.get("endorsements", 0) or 0) / 20.0, 1.0)
        dur = min((s.get("duration_months", 0) or 0) / 24.0, 1.0)
        a = assess.get(s.get("name"))
        a = (a / 100.0) if isinstance(a, (int, float)) and not isinstance(a, bool) else None
        if a is None:
            trust = 0.5 * endorse + 0.5 * dur
        else:
            trust = 0.35 * endorse + 0.30 * dur + 0.35 * a
        if trust < 0.12:
            stuffed += 1
        else:
            trusted.append((s.get("name"), round(trust, 2)))
    # A passed Redrob assessment is the strongest proof of real ability, so credit
    # a relevant, well-scored assessment even when the skill is not in the list.
    for skill_name, raw in assess.items():
        nm = (skill_name or "").lower()
        if nm in seen or not _is_relevant_skill(nm):
            continue
        if isinstance(raw, (int, float)) and not isinstance(raw, bool) and raw >= 60:
            trusted.append((skill_name, round(0.4 * (raw / 100.0), 2)))
    # de-saturated like career evidence: a deep, well-endorsed skill set should
    # outrank a thin one rather than both capping at 1.0
    score = min(1.0, sum(t for _, t in trusted) / 5.0)
    return score, trusted, stuffed


def _experience_fit(yoe):
    if 6 <= yoe <= 8:
        return 1.0
    if 5 <= yoe < 6 or 8 < yoe <= 9:
        return 0.85
    if 4 <= yoe < 5 or 9 < yoe <= 11:
        return 0.6
    if 3 <= yoe < 4 or 11 < yoe <= 13:
        return 0.35
    return 0.15


def _companies(cand):
    out = [(cand.get("profile", {}).get("current_company") or "").lower()]
    for r in cand.get("career_history", []):
        out.append((r.get("company") or "").lower())
    return out


def score_candidate(cand, ablate=None):
    """Return a dict: final score plus the full breakdown for reasoning.

    ablate (optional) neutralizes one signal so the evaluation harness can
    measure how much that signal contributes. It does not affect normal scoring.
    """
    is_hp, hp_reasons = detect_honeypot(cand)

    profile = cand.get("profile", {})
    yoe = float(profile.get("years_of_experience", 0) or 0)
    history_text = _history_text(cand)
    summary_text = _summary_text(cand)

    title, title_note = _title_score(cand)
    career, career_detail = _career_evidence(history_text)
    skill_trust, trusted_skills, n_stuffed = _skill_trust(cand)
    exp = _experience_fit(yoe)

    if ablate == "career":
        career = 0.5
    elif ablate == "skill":
        skill_trust = 0.5
    elif ablate == "title":
        title = 0.5
    elif ablate == "experience":
        exp = 0.5

    core = (WEIGHTS["career"] * career + WEIGHTS["skill_trust"] * skill_trust
            + WEIGHTS["title"] * title + WEIGHTS["experience"] * exp)

    penalties = []
    mult = 1.0

    # keyword stuffer: off-role title carrying a pile of AI skills
    current_title = (profile.get("current_title") or "").lower()
    if any(n in current_title for n in (NON_TECH | set(L.OFFROLE_TITLES))) \
            and len(trusted_skills) + n_stuffed >= 4:
        mult *= 0.15
        penalties.append("AI skills listed under a non-technical role (keyword stuffer)")

    # analyst decoy: templated tell phrases plus NO substantive retrieval evidence.
    # Genuine builders always have infra, embedding, eval, or plain-language
    # retrieval work in their history; decoys only name-drop bare ML keywords. We
    # gate on that substantive evidence rather than a keyword count, so a decoy
    # that name-drops many ML words across several roles still cannot escape, and
    # a real builder with moderate evidence is never wrongly demoted.
    tells = _hits(summary_text, L.ANALYST_TELL)
    # Substantive evidence is a vector DB, an embedding model, an evaluation
    # framework, or two-plus plain-language retrieval phrases. A single shallow
    # mention ("ranking system") is not enough: the decoys name-drop exactly one
    # while genuine builders show eval/infra/embedding and several plain phrases.
    substantive = (career_detail["infra"] or career_detail["embed"]
                   or career_detail["eval"] or len(career_detail["plain"]) >= 2)
    if tells and not substantive:
        mult *= 0.5
        penalties.append("aspirational AI keywords without demonstrated retrieval/ranking work")

    # pure services career with no product-company experience
    comps = _companies(cand)
    blob = " ".join(comps)
    has_services = any(f in blob for f in L.SERVICES_FIRMS)
    has_product = any(f in blob for f in L.PRODUCT_FIRMS)
    if has_services and not has_product:
        mult *= 0.7
        penalties.append("entire career at services/consulting firms")
    elif has_product:
        mult *= 1.05

    # title-chaser: genuine rapid hopping only. The JD distrusts switching every
    # ~1.5 years; we trigger below 16-month average and penalize mildly, so real
    # builders with a couple of shorter stints are not destroyed.
    roles = cand.get("career_history", [])
    if len(roles) >= 4:
        avg_dur = sum(r.get("duration_months", 0) or 0 for r in roles) / len(roles)
        if avg_dur < 16:
            mult *= 0.8
            penalties.append(f"job-hopping pattern (avg tenure {avg_dur:.0f} months)")

    # vision/speech/robotics focus without NLP/IR. Reads the career history only
    # (the skills list is noisy) and is waived by ANY genuine retrieval/ranking
    # evidence, so a ranking builder who happens to list an image skill is spared.
    cv = _hits(history_text, L.CV_SPEECH_ROBOTICS)
    nlpir = _hits(history_text, L.NLP_IR)
    if len(cv) >= 2 and not nlpir and not career_detail.get("plain"):
        mult *= 0.5
        penalties.append("vision/speech/robotics focus without NLP or retrieval")

    # pure research, no production
    research = _hits(history_text, {"research", "phd", "academic", "publication", "thesis"})
    if research and not career_detail["production"] and career < 0.3:
        mult *= 0.65
        penalties.append("research background with no production evidence")

    if ablate == "penalties":
        mult = 1.0
    fit = max(0.0, min(1.0, core * mult))

    behavioral, beh_notes = _behavioral(cand)
    location, loc_note = _location(cand)
    if ablate == "behavioral":
        behavioral = 1.0
    elif ablate == "location":
        location = 1.0

    final = fit * behavioral * location
    if is_hp and ablate != "honeypot":
        final = 0.0

    return {
        "candidate_id": cand.get("candidate_id"),
        "final": round(final, 6),
        "is_honeypot": is_hp,
        "honeypot_reasons": hp_reasons,
        "components": {
            "career_evidence": round(career, 3),
            "skill_trust": round(skill_trust, 3),
            "title": round(title, 3),
            "experience": round(exp, 3),
            "behavioral": round(behavioral, 3),
            "location": round(location, 3),
            "core": round(core, 3),
            "penalty_mult": round(mult, 3),
        },
        "detail": {
            "title_note": title_note, "career": career_detail,
            "trusted_skills": trusted_skills, "n_stuffed": n_stuffed,
            "penalties": penalties, "beh_notes": beh_notes, "loc_note": loc_note,
            "yoe": yoe,
        },
    }


def _behavioral(cand):
    s = cand.get("redrob_signals", {}) or {}
    last = s.get("last_active_date")
    try:
        y, m, d = (last or "2024-01-01").split("-")
        days = (REF_DATE - date(int(y), int(m), int(d))).days
    except (ValueError, AttributeError):
        days = 999
    if days <= 30:
        recency = 1.0
    elif days <= 90:
        recency = 0.8
    elif days <= 180:
        recency = 0.55
    else:
        recency = 0.3
    resp = float(s.get("recruiter_response_rate", 0) or 0)
    otw = 1.0 if s.get("open_to_work_flag") else 0.0
    icr = float(s.get("interview_completion_rate", 0) or 0)
    # A gentle modifier, not a dominant factor. The signals doc calls these a
    # "modifier on top of skill-match"; reachability refines the ranking among
    # qualified people rather than overriding qualification.
    m = 0.72 + 0.16 * recency + 0.07 * resp + 0.03 * otw + 0.02 * icr
    notice = s.get("notice_period_days", 0) or 0
    if notice > 90:
        m *= 0.97
    m = max(0.7, min(1.0, m))
    notes = {"days_since_active": days, "open_to_work": bool(s.get("open_to_work_flag")),
             "response_rate": resp, "notice_period_days": notice}
    return m, notes


def _location(cand):
    p = cand.get("profile", {})
    loc = (p.get("location") or "").lower()
    country = (p.get("country") or "").lower()
    relocate = bool((cand.get("redrob_signals") or {}).get("willing_to_relocate"))
    if country == "india":
        # The JD prefers Pune/Noida but is explicit that it is flexible and
        # welcomes candidates across Indian metros, so a non-hub Indian city is
        # barely nudged, not penalized. The real divide is India vs overseas.
        if any(h in loc for h in L.INDIA_HUBS):
            return 1.0, f"in {p.get('location')}"
        return 0.99, f"India ({p.get('location')})"
    if relocate:
        return 0.85, f"{p.get('location')}, willing to relocate"
    return 0.75, f"{p.get('location')}, no India base and not flagged to relocate"
