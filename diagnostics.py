"""
Diagnostics for the ranking, since the ground truth is hidden and there is no
leaderboard. We cannot measure NDCG directly, so we build confidence three other
ways:

  1. Composition: who is actually in our top 100 (titles, location, companies,
     experience, availability). It should look like the JD's ideal profile.
  2. Trap avoidance: a naive "rank by AI-keyword count" baseline is computed, and
     we show how many keyword stuffers, honeypots, and unreachable candidates it
     pulls into its top 100 that our system keeps out.
  3. Selectivity: the average of each scoring component in our top 100 versus the
     whole pool, showing every signal is doing work.

    python diagnostics.py --candidates ./candidates.jsonl
"""

import argparse
import collections
import gzip
import io
import json

from khoj.scoring import score_candidate, NON_TECH, _is_relevant_skill
from khoj.honeypot import detect as detect_honeypot
from khoj import lexicons as L


def _iter(path):
    op = (lambda p: io.TextIOWrapper(gzip.open(p, "rb"), encoding="utf-8")) if str(path).endswith(".gz") \
        else (lambda p: open(p, "r", encoding="utf-8"))
    with op(path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def naive_keyword_count(cand):
    """The trap baseline: count AI-relevant skills, ignore everything else."""
    return sum(1 for s in cand.get("skills", []) if _is_relevant_skill((s.get("name") or "").lower()))


def is_stuffer(cand):
    title = (cand.get("profile", {}).get("current_title") or "").lower()
    ai_skills = naive_keyword_count(cand)
    return any(n in title for n in NON_TECH) and ai_skills >= 4


def is_unreachable(cand):
    s = cand.get("redrob_signals", {}) or {}
    return (s.get("recruiter_response_rate", 1) or 0) < 0.1 or not s.get("open_to_work_flag", False)


def services_only(cand):
    comps = [(cand.get("profile", {}).get("current_company") or "").lower()]
    comps += [(r.get("company") or "").lower() for r in cand.get("career_history", [])]
    blob = " ".join(comps)
    return any(f in blob for f in L.SERVICES_FIRMS) and not any(f in blob for f in L.PRODUCT_FIRMS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default="./candidates.jsonl")
    ap.add_argument("--top", type=int, default=100)
    args = ap.parse_args()

    pool = []
    comp_sums = collections.defaultdict(float)
    n = 0
    for cand in _iter(args.candidates):
        s = score_candidate(cand)
        naive = naive_keyword_count(cand)
        pool.append((s["final"], cand["candidate_id"], naive, cand, s))
        for k, v in s["components"].items():
            comp_sums[k] += v
        n += 1

    ours = sorted(pool, key=lambda x: (-x[0], x[1]))[: args.top]
    naive_top = sorted(pool, key=lambda x: (-x[2], x[1]))[: args.top]

    def summarize(rows, label):
        titles = collections.Counter()
        india = stuffers = hp = unreach = svc = 0
        yoe = []
        resp = []
        for _, _, _, cand, s in rows:
            p = cand["profile"]
            titles[p["current_title"]] += 1
            if (p.get("country") or "").lower() == "india":
                india += 1
            if is_stuffer(cand):
                stuffers += 1
            if detect_honeypot(cand)[0]:
                hp += 1
            if is_unreachable(cand):
                unreach += 1
            if services_only(cand):
                svc += 1
            yoe.append(p.get("years_of_experience", 0))
            resp.append((cand.get("redrob_signals", {}) or {}).get("recruiter_response_rate", 0) or 0)
        print(f"\n== {label} (top {len(rows)}) ==")
        print(f"  India-based:        {india}/{len(rows)}")
        print(f"  keyword stuffers:   {stuffers}")
        print(f"  honeypots:          {hp}   (>10 = disqualified)")
        print(f"  unreachable:        {unreach}")
        print(f"  services-only:      {svc}")
        print(f"  mean experience:    {sum(yoe)/len(yoe):.1f} yrs")
        print(f"  mean response rate: {sum(resp)/len(resp):.2f}")
        print(f"  top titles:         {', '.join(f'{t}:{c}' for t,c in titles.most_common(6))}")

    print(f"Scored {n} candidates.")
    summarize(ours, "OUR RANKER")
    summarize(naive_top, "NAIVE keyword-count baseline (the trap)")

    print("\n== component selectivity (top 100 mean vs whole pool mean) ==")
    top_sums = collections.defaultdict(float)
    for _, _, _, _, s in ours:
        for k, v in s["components"].items():
            top_sums[k] += v
    for k in ("career_evidence", "skill_trust", "title", "experience", "behavioral", "location"):
        print(f"  {k:16s} top100={top_sums[k]/len(ours):.3f}   pool={comp_sums[k]/n:.3f}")


if __name__ == "__main__":
    main()
