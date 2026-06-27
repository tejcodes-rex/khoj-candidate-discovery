"""
Internal evaluation against our independent gold labeler.

The competition hides the ground truth, so this is the closest we can get to
measuring ranking quality before submitting. It computes the exact official
composite (0.50*NDCG@10 + 0.30*NDCG@50 + 0.15*MAP + 0.05*P@10) of our ranking
against gold tiers from khoj/goldlabel.py, and ablates each signal to show how
much it contributes. A signal that, when removed, drops the composite is a signal
that is earning its place.

    python evaluate_internal.py --candidates ./candidates.jsonl

Honest caveat: agreement with our own gold is not proof of agreement with the
hidden ground truth. Both are faithful readings of the same JD. This measures
internal consistency and lets us tune systematically instead of by guesswork.
"""

import argparse
import gzip
import io
import json
import math

from khoj.scoring import score_candidate
from khoj.goldlabel import gold_tier

ABLATIONS = [None, "career", "skill", "title", "experience", "behavioral",
             "location", "penalties", "honeypot"]


def _iter(path):
    op = (lambda p: io.TextIOWrapper(gzip.open(p, "rb"), encoding="utf-8")) if str(path).endswith(".gz") \
        else (lambda p: open(p, "r", encoding="utf-8"))
    with op(path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def dcg(gains):
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def ndcg_at_k(ranked_tiers, ideal_tiers, k):
    idcg = dcg(ideal_tiers[:k])
    return (dcg(ranked_tiers[:k]) / idcg) if idcg > 0 else 0.0


def average_precision(ranked_tiers, total_relevant):
    if total_relevant == 0:
        return 0.0
    hits = 0
    s = 0.0
    for i, t in enumerate(ranked_tiers, 1):
        if t >= 3:
            hits += 1
            s += hits / i
    return s / total_relevant


def composite(ranking_ids, gold, ideal_tiers, total_relevant):
    ranked = [gold[cid] for cid in ranking_ids]
    ndcg10 = ndcg_at_k(ranked, ideal_tiers, 10)
    ndcg50 = ndcg_at_k(ranked, ideal_tiers, 50)
    mapv = average_precision(ranked, total_relevant)
    p10 = sum(1 for t in ranked[:10] if t >= 3) / 10
    comp = 0.50 * ndcg10 + 0.30 * ndcg50 + 0.15 * mapv + 0.05 * p10
    return comp, ndcg10, ndcg50, mapv, p10


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default="./candidates.jsonl")
    ap.add_argument("--depth", type=int, default=2000, help="ranking depth kept for metrics")
    args = ap.parse_args()

    gold = {}
    scores = {ab: [] for ab in ABLATIONS}
    tiers = []
    for cand in _iter(args.candidates):
        cid = cand["candidate_id"]
        gold[cid] = gold_tier(cand)
        tiers.append(gold[cid])
        for ab in ABLATIONS:
            scores[ab].append((score_candidate(cand, ablate=ab)["final"], cid))

    ideal = sorted(tiers, reverse=True)
    total_rel = sum(1 for t in tiers if t >= 3)

    dist = {t: tiers.count(t) for t in range(6)}
    print(f"gold tier distribution: {dist}")
    print(f"relevant (tier 3+): {total_rel}\n")
    print(f"{'variant':<14}{'composite':>10}{'NDCG@10':>9}{'NDCG@50':>9}{'MAP':>7}{'P@10':>7}")

    base = None
    for ab in ABLATIONS:
        ranked = sorted(scores[ab], key=lambda x: (-x[0], x[1]))[: args.depth]
        ids = [cid for _, cid in ranked]
        comp, n10, n50, mapv, p10 = composite(ids, gold, ideal, total_rel)
        label = "FULL" if ab is None else f"- {ab}"
        if ab is None:
            base = comp
            drop = ""
        else:
            drop = f"   ({comp - base:+.3f})"
        print(f"{label:<14}{comp:>10.3f}{n10:>9.3f}{n50:>9.3f}{mapv:>7.3f}{p10:>7.3f}{drop}")

    print("\nNumbers in parentheses show the composite change when a signal is removed.")
    print("A negative change means the signal is helping.")


if __name__ == "__main__":
    main()
