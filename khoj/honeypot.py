"""
Honeypot and impossibility detection.

The pool seeds roughly eighty honeypots: profiles that are internally
impossible (the spec's own examples are "eight years at a company founded three
years ago" and "expert in ten skills with zero months used"). They are forced
to relevance tier 0 in the ground truth, and a submission with more than ten
percent honeypots in its top 100 is disqualified outright.

We do not try to be clever here. We apply conservative, near-certain
contradiction checks so that flagging a profile is essentially always correct.
A flagged candidate is pushed out of the shortlist entirely. The trust-weighted
skill scoring already starves these profiles of points on its own; this is the
explicit safety net on top of that.
"""

from datetime import date


def _parse(d):
    if not d or not isinstance(d, str):
        return None
    try:
        y, m, day = d.split("-")
        return date(int(y), int(m), int(day))
    except (ValueError, AttributeError):
        return None


def detect(cand):
    """Return (is_honeypot, list_of_reasons)."""
    reasons = []
    profile = cand.get("profile", {})
    yoe = float(profile.get("years_of_experience", 0) or 0)
    yoe_months = yoe * 12

    # 1. Claimed mastery of a skill never actually used. (We do NOT flag a skill
    # merely used longer than the paid career; people learn skills in school.)
    for s in cand.get("skills", []):
        prof = (s.get("proficiency") or "").lower()
        dur = s.get("duration_months", None)
        if prof in ("advanced", "expert") and dur == 0:
            reasons.append(f"claims {prof} '{s.get('name')}' with 0 months of use")

    # 2. Total tenure across roles exceeds the stated career length by years.
    total_role_months = sum(r.get("duration_months", 0) or 0 for r in cand.get("career_history", []))
    if total_role_months > yoe_months + 36:
        reasons.append(
            f"career history totals {total_role_months} months but stated experience is only {yoe:.1f} yrs"
        )

    # 3. A single role longer than the whole stated career (plus slack).
    today = date(2026, 6, 17)
    for r in cand.get("career_history", []):
        dur = r.get("duration_months", 0) or 0
        if dur > yoe_months + 24:
            reasons.append(f"role at {r.get('company')} lasts {dur} months but total experience is {yoe:.1f} yrs")
        start = _parse(r.get("start_date"))
        end = _parse(r.get("end_date"))
        if start and start > today:
            reasons.append(f"role at {r.get('company')} starts in the future ({r.get('start_date')})")
        if start and end and end < start:
            reasons.append(f"role at {r.get('company')} ends before it starts")
        if start and end:
            real_months = (end.year - start.year) * 12 + (end.month - start.month)
            if dur - real_months > 18:  # claimed far longer than the dates allow
                reasons.append(f"role at {r.get('company')} claims {dur} months but dates span {real_months}")

    # 3. Education that ends before it starts or in implausible years.
    for e in cand.get("education", []):
        sy, ey = e.get("start_year"), e.get("end_year")
        if isinstance(sy, int) and isinstance(ey, int) and ey < sy:
            reasons.append("education ends before it starts")

    return (len(reasons) > 0, reasons)
