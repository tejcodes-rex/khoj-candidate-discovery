# Khoj

**The discovery engine that finds what filters miss.**

Khoj is an intelligent candidate discovery system built for the India Runs Data and AI Challenge. It does not filter resumes. It reads a nuanced job description, understands what the role actually needs, and ranks an entire pool of messy, real-world profiles by genuine fit, surfacing the high-potential candidates that keyword search and even plain semantic search leave at the bottom.

It runs end to end on any laptop with no GPU and no network, in milliseconds per query.

---

## Why this exists

Recruiters drown in profiles and lean on keyword filters that reward the obvious candidate and bury the hidden gem: the self-taught backend engineer from a tier-three college who quietly rebuilt a payments service to handle five times the traffic, the data scientist who shipped a real ranking system but never wrote it in the words a filter is scanning for.

Khoj is built around that exact gap. It treats discovery as a ranking problem over three families of signal, and it explains every decision it makes.

## What it does

1. **Reads the job, not just the keywords.** A job description is parsed into a structured requirement spec: must-have skills, nice-to-have skills, an experience band, a seniority level, and intent flags mined from the prose (for example, a description that says it cares more about what you have shipped than where you studied switches on a pedigree-agnostic mode).

2. **Survives messy data.** Profiles arrive unstandardized: junk casing, missing fields, duplicates, Hinglish and regional-language fragments. The ingestion layer canonicalizes all of it into one clean shape, folds common Hinglish to keywords so multilingual profiles still contribute signal, and drops near-duplicates.

3. **Ranks on three signal families, the way the brief asks.**
   - **Relevance** decides who can do the job: semantic similarity to the role plus skill-ontology coverage of the requirements and the experience band.
   - **Signals** decide who to call first among the qualified: career trajectory (how fast someone is climbing), behavioral intent (how reachable and likely-to-move they are), and the Hidden-Gem potential score.
   Signals refine relevance multiplicatively, so a high-intent but unqualified profile can never crowd out a qualified one.

4. **Finds the hidden gems.** The potential score measures demonstrated impact and trajectory against surface pedigree. When someone looks far stronger than their credentials suggest, Khoj flags them and boosts them, with the reason attached.

5. **Explains itself.** Every ranked candidate ships with a score breakdown, the skills that matched, the must-haves still missing, and plain-language evidence for the trajectory, intent, and potential calls.

## Architecture

```
Messy profiles ─▶ Ingest + normalize ─▶ Feature + signal extraction ─▶ Semantic index
                                                                              │
Job description ─▶ JD understanding (structured spec) ────────────────────────┤
                                                                              ▼
                                            Stage 1: fast semantic retrieval (top N)
                                                                              │
                                                                              ▼
                              Stage 2: relevance x (trajectory + intent + hidden-gem)
                                                                              │
                                   ┌──────────────────────┬───────────────────┤
                                   ▼                      ▼                   ▼
                            explainability         (fairness audit)     ranked shortlist
```

The semantic backend is pluggable. The default is a dependency-free TF-IDF space so anyone can clone and run instantly. A sentence-transformer backend slots in behind the same interface when extra accuracy is wanted. The same is true for the index (exact cosine for small pools, approximate-nearest-neighbour for scale) and the JD parser (rule-based by default, model-based optional).

## Repository layout

```
khoj/            the engine
  text.py        normalization, multilingual folding, TF-IDF + cosine
  skills.py      skill ontology and canonicalization
  data_io.py     loading, canonicalization, dedup, and the real-data adapter point
  jd.py          job-description understanding
  signals.py     trajectory, intent, and hidden-gem potential
  rank.py        two-stage retrieve and rerank
  evaluate.py    NDCG, Recall, Precision, MRR, and Hidden-Gem Recovery vs baselines
scripts/
  make_synthetic.py   the synthetic Indian profile generator
data/
  raw/           input profiles, jobs, relevance labels
  output/        ranked shortlists (JSON and CSV)
run.py           end-to-end runner
```

## Run it

```bash
python scripts/make_synthetic.py     # build the sample dataset
python run.py                        # rank all jobs, write shortlists, print evaluation
python run.py --job JOB001 --topk 15 # a single role, larger shortlist
```

Outputs land in `data/output/` as both JSON (full detail with evidence) and CSV (recruiter-ingest ready).

## Results on the sample data

The sample includes the case recruiters actually struggle with: keyword-stuffed but stagnant profiles that look great on text alone, and rising hidden gems who write themselves in shorthand ("node", "k8s", "recsys") with sparse, sometimes Hinglish summaries. Measured against the two baselines most systems ship, a naive keyword filter and a semantic-only ranker, averaged across the two roles:

| System | NDCG@10 | Precision@10 | Hidden-Gem Recovery@10 |
|---|---|---|---|
| keyword filter | 0.71 | 1.00 | 0.00 |
| semantic only | 0.67 | 1.00 | 0.00 |
| **Khoj** | **0.85** | **1.00** | **0.56** |

The number that matters: both baselines recover zero hidden gems. The keyword filter cannot tell that "k8s" means Kubernetes, and semantic search ranks the sparse-text gem far below the buzzword-stuffed profile. Khoj recovers half to two-thirds of the hidden gems while also lifting overall ranking quality by 19 to 33%, and it does it in under two milliseconds per query. Signals refine relevance rather than override it, so precision stays at 1.00 the whole way.

## Connecting the real dataset

Point the loader at the official file and write one adapter function in `khoj/data_io.py` that maps the source columns to the canonical candidate shape. Nothing downstream changes. The output format is configured in `run.py` to match the required submission schema.

## Status

Working end to end: ingestion, multilingual normalization, JD understanding, two-stage ranking, hidden-gem detection, explainability, evaluation against baselines, and ranked-shortlist output. Active work: the sentence-transformer backend, the recruiter demo interface, the fairness audit report, and the learning-to-rank reranker trained on labeled data.
