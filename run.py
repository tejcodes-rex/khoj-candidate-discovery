"""
Khoj end-to-end runner.

Usage:
    python run.py                 run all jobs, write outputs, print evaluation
    python run.py --job JOB001    run a single job
    python run.py --topk 15       shortlist size

Reads from data/raw, writes ranked shortlists to data/output, and prints an
evaluation table comparing Khoj against a keyword baseline and a semantic-only
baseline. Fully offline, no GPU, no network.
"""

import argparse
import json
import time
from pathlib import Path

from khoj import data_io, jd, evaluate
from khoj.rank import Ranker

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "output"
OUT.mkdir(parents=True, exist_ok=True)


def write_outputs(job_spec, ranked, topk):
    """Write the ranked shortlist in both JSON and CSV (predefined-format ready)."""
    job_id = job_spec["job_id"]
    payload = {
        "job_id": job_id,
        "job_title": job_spec["title"],
        "generated_by": "Khoj candidate discovery engine",
        "shortlist_size": len(ranked),
        "shortlist": ranked,
    }
    (OUT / f"shortlist_{job_id}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # CSV mirrors the columns a recruiting tool would ingest
    lines = ["rank,candidate_id,name,score,hidden_gem,semantic,requirement,"
             "trajectory,intent,potential,matched_skills,why"]
    for r in ranked:
        c = r["components"]
        why = (f"{r['evidence']['potential']}; {r['evidence']['intent']}").replace(",", ";")
        matched = "|".join(r["matched_skills"])
        lines.append(
            f"{r['rank']},{r['candidate_id']},\"{r['name']}\",{r['score']},"
            f"{int(r['hidden_gem'])},{c['semantic']},{c['requirement']},"
            f"{c['trajectory']},{c['intent']},{c['potential']},\"{matched}\",\"{why}\""
        )
    (OUT / f"shortlist_{job_id}.csv").write_text("\n".join(lines), encoding="utf-8")


def pct(new, old):
    if old == 0:
        return "n/a" if new == 0 else "+inf"
    return f"{(new - old) / old * 100:+.0f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", default=None)
    ap.add_argument("--topk", type=int, default=10)
    args = ap.parse_args()

    candidates, stats = data_io.load_profiles(RAW / "profiles.jsonl")
    jobs = data_io.load_jobs(RAW / "jobs.json")
    qrels = data_io.load_qrels(RAW / "qrels.json")

    print(f"Loaded {stats['loaded']} profiles, dropped {stats['deduped']} "
          f"near-duplicates, {len(candidates)} unique candidates.\n")

    t0 = time.perf_counter()
    ranker = Ranker(retrieve_n=60).fit(candidates)
    index_ms = (time.perf_counter() - t0) * 1000
    print(f"Indexed {len(candidates)} candidates in {index_ms:.0f} ms.\n")

    for job in jobs:
        if args.job and job["job_id"] != args.job:
            continue
        spec = jd.parse(job)

        t1 = time.perf_counter()
        ranked = ranker.rank(spec, top_k=args.topk)
        query_ms = (time.perf_counter() - t1) * 1000

        write_outputs(spec, ranked, args.topk)

        print("=" * 74)
        print(f"{job['job_id']}  {job['title']}")
        print(f"query latency: {query_ms:.1f} ms   "
              f"pedigree-agnostic JD: {spec['pedigree_agnostic']}")
        print("-" * 74)
        print(f"{'#':>2}  {'candidate':<11} {'score':>6}  gem  {'fit':>4} "
              f"{'traj':>4} {'intent':>6}  background")
        for r in ranked:
            gem = "GEM" if r["hidden_gem"] else "   "
            print(f"{r['rank']:>2}  {r['candidate_id']:<11} {r['score']:>6.3f}  "
                  f"{gem}  {r['components']['requirement']:>4.2f} "
                  f"{r['components']['trajectory']:>4.2f} "
                  f"{r['components']['intent']:>6.2f}  {r['education'][:34]}")

        m = evaluate.evaluate_all(spec, candidates, ranker, qrels.get(job["job_id"], {}),
                                  k=args.topk)
        print("-" * 74)
        print(f"evaluation @k={m['k']}   (planted hidden gems: {m['n_gems']})")
        print(f"{'system':<10} {'NDCG':>6} {'Recall':>7} {'Prec':>6} "
              f"{'MRR':>6} {'GemRecov':>9}")
        for name in ("keyword", "semantic", "khoj"):
            r = m[name]
            print(f"{name:<10} {r['ndcg@k']:>6.3f} {r['recall@k']:>7.3f} "
                  f"{r['precision@k']:>6.3f} {r['mrr']:>6.3f} {r['gem_recovery@k']:>9.3f}")
        print(f"khoj vs semantic  ->  NDCG {pct(m['khoj']['ndcg@k'], m['semantic']['ndcg@k'])}, "
              f"gem recovery {m['khoj']['gem_recovery@k']:.2f} vs {m['semantic']['gem_recovery@k']:.2f}")
        print(f"khoj vs keyword   ->  NDCG {pct(m['khoj']['ndcg@k'], m['keyword']['ndcg@k'])}, "
              f"gem recovery {m['khoj']['gem_recovery@k']:.2f} vs {m['keyword']['gem_recovery@k']:.2f}")
        print()

    print(f"Shortlists written to {OUT}")


if __name__ == "__main__":
    main()
