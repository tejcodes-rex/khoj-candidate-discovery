"""
The signal layer. This is where Khoj earns its keep.

The brief names three data families and asks us to use all of them: profile
attributes, career metadata, and activity/behavioral signals. Most submissions
will use only the first. We compute the second and third explicitly, plus the
two ideas that win the track:

  trajectory   how fast and how far a career is climbing (career metadata)
  intent       likelihood the person is reachable and will move (behavioral)
  potential    demonstrated impact measured against surface pedigree, which is
               the Hidden-Gem signal: high potential with low pedigree is the
               candidate a keyword filter buries.

Every function returns a 0..1 score plus a short reason string so the result is
explainable end to end.
"""

import re

_SENIOR_WORDS = ["intern", "junior", "associate", "mid", "senior", "lead", "staff", "principal"]
_IMPACT = [
    r"\d+\s*x", r"\d+\s*%", r"p99", r"p95", r"latency", r"scale", r"scaled",
    r"throughput", r"reliability", r"end to end", r"owned", r"production",
    r"deployed", r"shipped", r"built", r"reduced", r"cut", r"improved",
    r"million", r"\bm\b", r"2m", r"5x",
]
_TIER1_BRANDS = ["google", "microsoft", "amazon", "flipkart", "razorpay",
                 "swiggy", "zomato", "atlassian"]
_TIER1_COLLEGE = ["iit", "bits", "iiit", "nit"]


def _level_of(title):
    t = title.lower()
    for i, w in enumerate(_SENIOR_WORDS):
        if w in t:
            return i
    return 1  # default to a junior-ish level when unstated


def trajectory(cand):
    """Career velocity: progression in level per year, plus role momentum."""
    exp = cand["experience"]
    if not exp:
        return 0.0, "no work history on file"
    levels = [_level_of(r.get("title", "")) for r in exp]
    span = max(1, cand["years_experience"])
    climb = max(levels) - min(levels)
    rate = climb / span  # levels gained per year
    # normalize: gaining roughly one level every 1.5 years is excellent
    score = min(1.0, rate / 0.66)
    if climb >= 2:
        reason = f"climbed {climb} seniority levels in {span} years"
    elif climb == 1:
        reason = f"steady progression over {span} years"
    else:
        reason = "flat trajectory so far"
    return round(score, 3), reason


def intent(cand):
    """Behavioral fit: is this person reachable and likely to move."""
    s = cand.get("signals") or {}
    last = s.get("last_active_days", 999)
    recency = max(0.0, 1.0 - min(last, 365) / 365.0)
    otw = 1.0 if s.get("open_to_work") else 0.0
    completeness = float(s.get("profile_completeness", 0.0) or 0.0)
    response = float(s.get("response_rate", 0.0) or 0.0)
    apps = min(1.0, (s.get("recent_applications", 0) or 0) / 8.0)
    score = 0.35 * recency + 0.25 * otw + 0.15 * completeness + 0.15 * response + 0.10 * apps
    if otw and last <= 7:
        reason = f"open to work, active {last} day(s) ago"
    elif last <= 30:
        reason = f"active {last} day(s) ago"
    else:
        reason = f"low recent activity ({last} days)"
    return round(min(1.0, score), 3), reason


def _impact_density(cand):
    text = " ".join([cand["summary"], cand["text_blob"]])
    hits = sum(1 for pat in _IMPACT if re.search(pat, text))
    return min(1.0, hits / 6.0)


def _pedigree(cand):
    """High when the candidate looks impressive on the surface."""
    edu = (cand["education"] or "").lower()
    college = 1.0 if any(b in edu for b in _TIER1_COLLEGE) else 0.0
    brands = 1.0 if any(b in " ".join(cand["employers"]) for b in _TIER1_BRANDS) else 0.0
    tier = {1: 1.0, 2: 0.5, 0: 0.3}.get(cand.get("city_tier", 0), 0.2)
    return 0.45 * college + 0.45 * brands + 0.10 * tier


def potential(cand):
    """
    The Hidden-Gem core. Demonstrated impact and trajectory measured against
    surface pedigree. A high score means this person looks far stronger than
    their credentials suggest, which is exactly who keyword filters miss.
    """
    impact = _impact_density(cand)
    traj, _ = trajectory(cand)
    demonstrated = 0.6 * impact + 0.4 * traj
    ped = _pedigree(cand)
    gem_delta = max(0.0, demonstrated - ped)  # potential beyond pedigree
    if demonstrated >= 0.5 and ped < 0.4:
        reason = "strong demonstrated impact with a non-traditional background"
    elif demonstrated >= 0.5:
        reason = "strong demonstrated impact"
    else:
        reason = "limited demonstrated impact so far"
    return {
        "demonstrated": round(demonstrated, 3),
        "pedigree": round(ped, 3),
        "gem_delta": round(gem_delta, 3),
        "reason": reason,
    }
