"""
Khoj ranker, reproduce entrypoint.

    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Reads the 100,000-candidate pool, scores every candidate against the Senior AI
Engineer job description, and writes the validator-compliant top-100 CSV with a
grounded reasoning line for each pick.

CPU only, no network, no GPU. Two passes over the file keep peak memory low: the
first scores everyone and keeps only (score, id); the second pulls back just the
hundred finalists to attach reasoning. Runs in well under the five-minute budget.
"""

import argparse
import csv
import gzip
import io
import json
import sys
import time
from pathlib import Path

from khoj.scoring import score_candidate
from khoj.reasoning import make_reasoning


def _open(path):
    if str(path).endswith(".gz"):
        return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8")
    return open(path, "r", encoding="utf-8")


def _iter(path):
    with _open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default="./candidates.jsonl")
    ap.add_argument("--out", default="./submission.csv")
    ap.add_argument("--top", type=int, default=100)
    args = ap.parse_args()

    t0 = time.perf_counter()

    # Pass 1: score everyone, keep (rounded_score, candidate_id) only.
    # Dedup by candidate_id (keep first) so a duplicated input line can never
    # produce two rows with the same id, which the validator rejects.
    scored = []
    seen_ids = set()
    n = honeypots = dupes = 0
    for cand in _iter(args.candidates):
        cid = cand["candidate_id"]
        n += 1
        if cid in seen_ids:
            dupes += 1
            continue
        seen_ids.add(cid)
        s = score_candidate(cand)
        if s["is_honeypot"]:
            honeypots += 1
        scored.append((s["final"], cid))

    # Sort by rounded score descending, then candidate_id ascending. Rounding
    # before sorting guarantees the validator's tie-break rule holds exactly.
    scored.sort(key=lambda x: (-x[0], x[1]))
    top = scored[: args.top]
    top_ids = {cid for _, cid in top}
    pass1_ms = (time.perf_counter() - t0) * 1000

    # Pass 2: pull back just the finalists and attach reasoning.
    finalists = {}
    for cand in _iter(args.candidates):
        if cand["candidate_id"] in top_ids:
            finalists[cand["candidate_id"]] = cand
            if len(finalists) == len(top_ids):
                break

    rows = []
    hp_in_top = 0
    for rank, (score, cid) in enumerate(top, 1):
        cand = finalists[cid]
        s = score_candidate(cand)
        if s["is_honeypot"]:
            hp_in_top += 1
        rows.append({
            "candidate_id": cid,
            "rank": rank,
            "score": f"{score:.6f}",
            "reasoning": make_reasoning(cand, s, rank),
        })

    out = Path(args.out)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["candidate_id", "rank", "score", "reasoning"],
                           quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)

    total_ms = (time.perf_counter() - t0) * 1000
    print(f"Scored {n} candidates. Honeypots detected in pool: {honeypots}.")
    print(f"Top {len(top)} written to {out}.")
    print(f"Honeypots in top 100: {hp_in_top} (disqualified above 10).")
    print(f"Score range: rank 1 = {top[0][0]:.4f}, rank 100 = {top[-1][0]:.4f}.")
    print(f"Timing: pass1 {pass1_ms:.0f} ms, total {total_ms:.0f} ms.")
    if hp_in_top > 10:
        print("WARNING: honeypot rate exceeds the disqualification threshold.", file=sys.stderr)


if __name__ == "__main__":
    main()
