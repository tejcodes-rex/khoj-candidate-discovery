"""
The two-stage ranking engine.

Stage 1 (retrieve): fast semantic retrieval narrows the full pool to a candidate
set using the TF-IDF / embedding space. This is the part that has to be
lightning-fast at scale.

Stage 2 (rerank): a feature-rich, transparent scorer reorders the retrieved set
using requirement fit, career trajectory, behavioral intent, and the Hidden-Gem
potential boost. Every component score is kept so the result explains itself.

The weights below are a sensible, documented default. They are deliberately
readable rather than hidden inside a black box, and they can be replaced by a
learning-to-rank model trained on the qrels (see docs/METHODOLOGY.md) without
changing this interface.
"""

from . import signals
from .data_io import searchable_document
from .text import TfidfSpace

# Scoring is split in two on purpose.
#
# RELEVANCE answers "can this person do the job" and decides who is even allowed
# near the top. SIGNALS (trajectory, intent, hidden-gem potential) answer "among
# the people who can do the job, who should a recruiter call first" and act as a
# multiplicative refinement on top of relevance. Because the signal boost is
# scaled by relevance, a high-intent but unqualified profile can never crowd out
# a qualified one. This is what keeps ranking accuracy from regressing while the
# differentiators still do their job.
RELEVANCE = {
    "semantic": 0.45,      # embedding similarity to the JD
    "requirement": 0.55,   # must-have / nice-to-have coverage and experience band
}
SIGNAL = {
    "trajectory": 0.15,    # career velocity
    "intent": 0.15,        # behavioral, likelihood to move and respond
    "potential": 0.30,     # hidden-gem boost (amplified for pedigree-agnostic JDs)
}


class Ranker:
    def __init__(self, retrieve_n=50):
        self.space = TfidfSpace()
        self.candidates = []
        self.by_id = {}
        self.retrieve_n = retrieve_n

    def fit(self, candidates):
        self.candidates = candidates
        self.by_id = {c["candidate_id"]: c for c in candidates}
        docs = [searchable_document(c) for c in candidates]
        ids = [c["candidate_id"] for c in candidates]
        self.space.fit(docs, ids)
        return self

    # ---- stage 2 component scores -------------------------------------------

    @staticmethod
    def _requirement_fit(spec, cand):
        cand_sk = set(cand["skills"])
        cand_fam = set(cand["skill_families"])
        must = set(spec["must_have"])
        nice = set(spec["nice_to_have"])

        if must:
            direct = len(cand_sk & must) / len(must)
            fam = len(set(spec["must_families"]) & cand_fam) / max(1, len(spec["must_families"]))
            must_cov = 0.75 * direct + 0.25 * fam
        else:
            must_cov = 0.5
        nice_cov = (len(cand_sk & nice) / len(nice)) if nice else 0.0

        # experience band fit
        need = spec["min_experience_years"]
        have = cand["years_experience"]
        if need <= 0:
            exp_fit = 1.0
        elif have >= need:
            exp_fit = 1.0
        else:
            exp_fit = max(0.0, have / need)

        score = 0.6 * must_cov + 0.2 * nice_cov + 0.2 * exp_fit
        matched = sorted((cand_sk & (must | nice)))
        missing = sorted(must - cand_sk)
        return min(1.0, score), matched, missing

    def rank(self, spec, top_k=10):
        # ---- stage 1: retrieve
        retrieved = self.space.query(spec["query_text"], top_n=self.retrieve_n)
        sem = dict(retrieved)
        if not retrieved:
            return []
        max_sem = max(sem.values()) or 1.0

        # ---- stage 2: rerank
        results = []
        for cid, raw_sem in retrieved:
            cand = self.by_id[cid]
            semantic = raw_sem / max_sem
            req, matched, missing = self._requirement_fit(spec, cand)
            traj, traj_reason = signals.trajectory(cand)
            intent, intent_reason = signals.intent(cand)
            pot = signals.potential(cand)

            relevance = (RELEVANCE["semantic"] * semantic
                         + RELEVANCE["requirement"] * req)

            # hidden-gem boost is amplified when the JD explicitly de-emphasizes pedigree
            gem_w = SIGNAL["potential"] * (1.5 if spec.get("pedigree_agnostic") else 1.0)
            boost = (SIGNAL["trajectory"] * traj
                     + SIGNAL["intent"] * intent
                     + gem_w * pot["gem_delta"])

            # signals refine relevance; they cannot manufacture it from nothing
            score = relevance * (1.0 + boost)

            is_gem = pot["gem_delta"] >= 0.25 and pot["demonstrated"] >= 0.5 and req >= 0.4

            results.append({
                "candidate_id": cid,
                "name": cand["name"],
                "score": round(score, 4),
                "components": {
                    "semantic": round(semantic, 3),
                    "requirement": round(req, 3),
                    "trajectory": traj,
                    "intent": intent,
                    "potential": pot["gem_delta"],
                },
                "hidden_gem": is_gem,
                "matched_skills": matched,
                "missing_must_have": missing,
                "evidence": {
                    "trajectory": traj_reason,
                    "intent": intent_reason,
                    "potential": pot["reason"],
                    "demonstrated": pot["demonstrated"],
                    "pedigree": pot["pedigree"],
                },
                "education": cand["education"],
                "location": cand["location"],
                "years_experience": cand["years_experience"],
                "_archetype": cand.get("_archetype"),
            })

        results.sort(key=lambda r: r["score"], reverse=True)
        for i, r in enumerate(results[:top_k], 1):
            r["rank"] = i
        return results[:top_k]
