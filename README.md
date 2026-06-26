# Khoj — Intelligent Candidate Discovery

Ranking the top 100 candidates for Redrob's Senior AI Engineer role out of a pool of 100,000, for the India Runs Data and AI Challenge.

Khoj reads each candidate the way a careful engineer would read the job description: it weighs what people actually built over the keywords they listed, trusts skills only when the platform signals back them up, applies the disqualifiers the JD spells out, and discounts candidates who look great on paper but are not reachable. It runs in about 16 seconds on a laptop CPU with no network and no GPU.

## Reproduce the submission

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

That single command reads the candidate pool and writes a validator-compliant top-100 CSV. No pre-computation, no downloads, no API keys. Standard library only.

Validate it with the organizers' checker:

```bash
python validate_submission.py submission.csv     # prints "Submission is valid."
```

Or reproduce inside the same kind of sandboxed container Stage 3 uses (CPU only,
no network, nothing to install since the ranker is standard library only):

```bash
docker build -t khoj .
docker run --rm -v "$PWD":/data khoj --candidates /data/candidates.jsonl --out /data/submission.csv
```

## How it ranks (the short version)

The job description is the rubric. It says plainly that the right answer is not "whoever lists the most AI keywords," that career evidence beats buzzwords, and that behavioral signals decide who is actually hireable. Khoj encodes exactly that.

Every candidate gets a fit score in `[0, 1]` from four weighted components, then two multipliers:

| Part | What it captures | Weight |
|---|---|---|
| Career evidence | Retrieval, ranking, search, recsys, NLP, vector-DB, and production terms found in the **career-history descriptions and titles**, not the skills list | 0.40 |
| Skill trust | Relevant skills, each scaled by endorsements, months used, and Redrob assessment score, so unendorsed and untested skills earn almost nothing | 0.22 |
| Title | Direct-fit titles score high, off-role titles (Marketing Manager, Accountant, and so on) score near zero | 0.18 |
| Experience | Closeness to the JD's ideal 6 to 8 year band | 0.20 |
| Behavioral multiplier | Recency of activity, recruiter response rate, open-to-work, notice period | x0.5 to x1.0 |
| Location multiplier | India hubs (Pune and Noida preferred) at full weight, overseas candidates discounted unless flagged to relocate | x0.6 to x1.0 |

On top of that, named JD disqualifiers apply real penalties: keyword stuffers (AI skills under a non-technical title), entire careers at services firms with no product experience, job-hoppers, vision/speech/robotics profiles with no NLP or retrieval, and pure-research backgrounds with no production work.

### Honeypots

The pool seeds about eighty internally-impossible profiles, and ranking more than ten percent of them in the top 100 is an instant disqualification. Khoj detects them with conservative consistency checks (claimed mastery of a skill with zero months used, total tenure exceeding the stated career length, dates that do not add up) and forces them out of the shortlist. The trust-weighted scoring already starves them of points; this is the safety net. Current run: 0 honeypots in the top 100.

### Reasoning

Each of the 100 rows carries a one-line reasoning built from the candidate's own fields: title, years, the specific career evidence found, the trust-verified skills, and the behavioral signals, with honest concerns called out where they exist. Nothing is templated and nothing is invented.

## Repository layout

```
rank.py            reproduce entrypoint: candidates.jsonl -> submission.csv
khoj/
  lexicons.py      the JD encoded as machine-readable term sets
  scoring.py       the fit scorer (the heart of the system)
  honeypot.py      internal-consistency / impossibility detection
  reasoning.py     grounded, per-candidate reasoning
docs/
  METHODOLOGY.md   full design walkthrough and the rationale for every choice
submission_metadata.yaml   team and reproducibility metadata
requirements.txt   (standard library only; optional accelerators listed)
```

## Compute profile

Measured on the full 100,000-candidate pool: about 16 seconds wall-clock, well under 100 MB of working memory, CPU only, no network. The organizers' limits are 5 minutes, 16 GB, CPU only, no network, which this clears comfortably. A system that called a hosted model per candidate could not.

## Getting the data

The candidate pool ships with the hackathon bundle as `candidates.jsonl` (or `candidates.jsonl.gz`, which `rank.py` reads directly). It is not redistributed in this repository. Place it at the repo root or pass its path with `--candidates`.
