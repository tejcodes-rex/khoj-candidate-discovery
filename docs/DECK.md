# Deck content for the Redrob submission template

Paste this slide by slide into a copy of "Idea Submission Template _ Redrob.pptx",
then export to PDF (under 5 MB). Keep the visual style of the template. Plain,
specific language beats buzzwords here, the reviewers say so directly.

Suggested length: 10 to 12 slides.

---

## Slide 1 — Title

**Khoj**
Intelligent Candidate Discovery for the Senior AI Engineer role

Team: [team name] · India Runs, Data and AI Challenge
One line: the ranker that reads what candidates built, not what they listed.

---

## Slide 2 — The problem

Redrob has to find a handful of genuine senior AI engineers inside a pool of
100,000 profiles. Keyword filters fail at this in a specific, costly way:

- They reward whoever lists the most AI keywords, including people who pasted
  them in and cannot do the work.
- They miss strong engineers who describe themselves plainly and never write the
  fashionable terms.
- They ignore whether a great-looking candidate is even reachable.

The job description says this outright: the right answer is not the keyword count,
and the dataset has traps built in to punish systems that think it is.

---

## Slide 3 — Our approach in one sentence

Treat the job description as the rubric. Score each candidate on what their career
history proves they built, trust their skills only when the platform backs them
up, apply the disqualifiers the JD names, and discount anyone who is not actually
available.

---

## Slide 4 — How it works

Each candidate gets a fit score from four weighted parts:

- Career evidence (0.40): retrieval, ranking, search, recsys, NLP and vector-DB
  work found in the career-history text, weighted above the skills list.
- Skill trust (0.22): relevant skills scaled by endorsements, months used, and
  Redrob assessment score, so unbacked skills earn almost nothing.
- Title (0.18): direct-fit titles high, off-role titles near zero.
- Experience (0.20): closeness to the JD's 6 to 8 year ideal.

Then two multipliers: behavioral availability (activity, response rate, open to
work) and location (India hubs preferred). Named disqualifiers (keyword stuffers,
services-only careers, job hoppers, vision/speech-only, pure research) apply real
penalties.

[Visual: the pipeline diagram from the README.]

---

## Slide 5 — The design bet: rules over a black box

We did not build "embed everything and sort by similarity." Three reasons:

- Similarity rewards the exact keyword stuffing the JD warns about.
- The compute limit is five minutes on CPU for 100,000 candidates. We run in about
  40 seconds with no model and no network.
- We have to explain and defend every ranking. A transparent scorer produces a
  breakdown for each candidate, which also powers the reasoning column.

---

## Slide 6 — Defeating the traps (the headline)

We compared our top 100 against a naive keyword-count ranking, the trap the JD
built the dataset around:

| In the top 100 | Naive keyword ranking | Khoj |
|---|---|---|
| Keyword stuffers | 85 | 0 |
| Unreachable candidates | 70 | 10 |
| Honeypots | varies | 0 |
| India-based | 78 | 100 |
| Mean recruiter response rate | 0.41 | 0.74 |

The naive ranking fills 85 percent of its shortlist with people who cannot do the
job. Ours has none.

---

## Slide 7 — Honeypots and disqualification safety

The pool seeds about 80 internally-impossible profiles. Ranking more than 10
percent of them in the top 100 is an automatic disqualification.

- We detect them with conservative consistency checks (mastery of a skill used
  zero months, total tenure exceeding stated experience, dates that do not add up).
- Trust-weighted scoring already starves them of points.
- Result: 0 honeypots in our top 100.

---

## Slide 8 — Results and reproducibility

- Passes the organizers' validator: "Submission is valid."
- Ranks all 100,000 candidates in about 40 seconds on a laptop CPU, no GPU, no
  network. Comfortably inside the 5-minute limit.
- One command reproduces the submission: `python rank.py --candidates ./candidates.jsonl --out ./submission.csv`
- Top picks are textbook fits: a search engineer at Sarvam AI doing ranking and
  retrieval, an AI research engineer at Razorpay in Pune, an ex-LinkedIn ML
  engineer working on BM25 and FAISS.

---

## Slide 9 — Reasoning you can trust

Every one of the 100 rows carries a grounded, one-line justification built from
the candidate's own fields, with honest concerns surfaced. Example:

"AI Research Engineer with 6.5 yrs; career history shows fine-tuning, ranking,
recommendation; 5 trust-verified skills (BM25, PEFT, MLflow); active 22 days ago,
response rate 89%."

Nothing templated, nothing invented, tone matched to the rank.

---

## Slide 10 — Why this is the right system for Redrob

This is not a benchmark hack. It is the shape of a real recruiting ranker:
explainable to recruiters, fast enough to run over the whole pool on commodity
hardware, honest about who is reachable, and resistant to the gaming that keyword
search invites. It is the v2 ranker the JD itself asks the hire to build.

---

## Slide 11 — Roadmap

- Calibrate the trust and disqualifier thresholds against a small labeled set.
- Add a lexical or learned similarity signal as one more component.
- A recruiter feedback loop so the ranking improves from real selections.
- Extend honeypot detection as more profile fields become available.

---

## Slide 12 — Close

Khoj finds the engineers a keyword filter buries and refuses the ones it would be
fooled by, in 40 seconds, with a reason for every pick.

Repo: [github url] · Live demo: [sandbox url]
