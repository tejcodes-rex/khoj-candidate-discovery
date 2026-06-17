"""
Offline evaluation.

Accuracy is a stated requirement, so we measure it with named metrics and report
lift against two baselines that represent what most teams will ship:

  keyword   rank by raw must-have keyword overlap only (a glorified filter)
  semantic  rank by embedding similarity only (the default everyone builds)
  khoj      the full two-stage signal-aware engine

Metrics: NDCG@k, Recall@k, MRR, Precision@k, plus our own Hidden-Gem Recovery@k,
which measures how many of the strong-fit, low-pedigree candidates each system
surfaces in the top k. That last one is the number that tells the story: the
keyword and semantic baselines bury the gems, Khoj recovers them.
"""

import math

from . import signals
from .data_io import searchable_document
from .text import TfidfSpace


def dcg(relevances):
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances))


def ndcg_at_k(ranked_ids, qrel, k):
    gains = [qrel.get(cid, 0) for cid in ranked_ids[:k]]
    ideal = sorted(qrel.values(), reverse=True)[:k]
    idcg = dcg(ideal)
    return (dcg(gains) / idcg) if idcg > 0 else 0.0


def recall_at_k(ranked_ids, qrel, k):
    relevant = {cid for cid, g in qrel.items() if g > 0}
    if not relevant:
        return 0.0
    hit = sum(1 for cid in ranked_ids[:k] if cid in relevant)
    return hit / len(relevant)


def precision_at_k(ranked_ids, qrel, k):
    if k == 0:
        return 0.0
    return sum(1 for cid in ranked_ids[:k] if qrel.get(cid, 0) > 0) / k


def mrr(ranked_ids, qrel):
    for i, cid in enumerate(ranked_ids, 1):
        if qrel.get(cid, 0) > 0:
            return 1.0 / i
    return 0.0


def hidden_gem_recovery_at_k(ranked_ids, gem_ids, k):
    if not gem_ids:
        return 0.0
    return sum(1 for cid in ranked_ids[:k] if cid in gem_ids) / len(gem_ids)


# ---- baselines --------------------------------------------------------------

def keyword_ranking(spec, candidates):
    """A filter-style baseline: order by must-have keyword overlap, then nice."""
    must = set(spec["must_have"])
    nice = set(spec["nice_to_have"])
    scored = []
    for c in candidates:
        sk = set(c["skills"])
        score = len(sk & must) * 2 + len(sk & nice)
        scored.append((c["candidate_id"], score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [cid for cid, _ in scored]


def semantic_ranking(spec, candidates):
    """Embedding-only baseline: the default build everyone ships."""
    space = TfidfSpace().fit(
        [searchable_document(c) for c in candidates],
        [c["candidate_id"] for c in candidates],
    )
    return [cid for cid, _ in space.query(spec["query_text"])]


def evaluate_all(spec, candidates, ranker, qrel, k=10):
    """Return a metrics table for keyword, semantic, and khoj systems."""
    gem_ids = {c["candidate_id"] for c in candidates
               if c.get("_archetype") in ("gem_be", "gem_ml") and qrel.get(c["candidate_id"], 0) > 0}

    kw = keyword_ranking(spec, candidates)
    sem = semantic_ranking(spec, candidates)
    khoj_full = [r["candidate_id"] for r in ranker.rank(spec, top_k=len(candidates))]

    def row(ranked):
        return {
            "ndcg@k": round(ndcg_at_k(ranked, qrel, k), 3),
            "recall@k": round(recall_at_k(ranked, qrel, k), 3),
            "precision@k": round(precision_at_k(ranked, qrel, k), 3),
            "mrr": round(mrr(ranked, qrel), 3),
            "gem_recovery@k": round(hidden_gem_recovery_at_k(ranked, gem_ids, k), 3),
        }

    return {
        "k": k,
        "n_gems": len(gem_ids),
        "keyword": row(kw),
        "semantic": row(sem),
        "khoj": row(khoj_full),
    }
