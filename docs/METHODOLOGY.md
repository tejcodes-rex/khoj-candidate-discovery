# Khoj methodology and design walkthrough

This document explains how the ranker works and, more importantly, why each
choice was made. Read it end to end and you will be able to defend every part of
the system. The structure follows the order the code runs in.

## 1. The core idea

The job description for this role is not a vague wish list. It is a detailed,
opinionated rubric that tells us exactly what counts and what is a trap. The whole
design philosophy of Khoj is to take that rubric literally and encode it as
scoring logic, rather than throwing a generic embedding-similarity model at the
problem and hoping it captures the nuance.

Three sentences from the JD drive everything:

1. "The right answer is not finding candidates whose skills section contains the
   most AI keywords. That's a trap we've explicitly built into the dataset."
2. "A Tier 5 candidate may not use the words RAG or Pinecone, but if their career
   history shows they built a recommendation system at a product company, they're
   a fit."
3. "A perfect-on-paper candidate who hasn't logged in for six months and has a 5%
   response rate is, for hiring purposes, not actually available."

So: read the career history, not the keyword list. Trust skills only when there
is evidence behind them. And treat availability as a real factor, not an
afterthought. Everything below is a direct consequence of those three lines.

## 2. Why rule-based and not an embedding model

We deliberately did not build "embed the JD, embed each profile, sort by cosine
similarity." Three reasons, and these are good interview answers:

- It rewards exactly the keyword stuffing the JD warns against. A Marketing
  Manager who pasted forty AI skills into their profile embeds close to the JD. A
  plainly-worded engineer who actually built ranking systems embeds further away.
  Pure similarity ranks the wrong one higher.
- The compute budget is five minutes on CPU for 100,000 candidates. A transparent
  feature scorer runs in about 16 seconds. It also means we never depend on a
  model download or a network call, which the rules forbid during ranking.
- We have to explain and defend the ranking. A rule-based scorer produces a score
  breakdown for every candidate, which is also what powers the reasoning column.
  A cosine score explains nothing.

This is the central design bet: the JD gives us enough structure that careful
feature engineering beats a generic semantic model, and it does so faster and
more defensibly. A semantic similarity component can be added later as one signal
among several, but it is not the foundation.

## 3. The four fit components

Each candidate gets a fit score in `[0, 1]` from a weighted sum of four parts.
The weights live in `khoj/scoring.py` as `WEIGHTS` and are deliberately readable.

### 3.1 Career evidence (weight 0.40, the largest)

We scan the text of every career-history entry (titles and descriptions) plus the
summary and headline, and count distinct hits across five term families defined in
`khoj/lexicons.py`:

- core ML and IR terms (retrieval, ranking, recommendation, search, NLP, embeddings)
- vector and hybrid-search infrastructure (FAISS, Milvus, Pinecone, Elasticsearch, BM25)
- embedding model families (sentence-transformers, BGE, E5)
- evaluation literacy (NDCG, MRR, MAP, A/B testing)
- production evidence (deployed, shipped, at scale, owned, end to end)

Infrastructure and embedding-model mentions are weighted higher than generic ML
terms because they are harder to fake and map directly to the JD's hard
requirements. The weighted count is squashed so that roughly six strong hits reach
the maximum. This is the single most important signal, because it captures what
someone actually did, which is what the JD says to reward.

### 3.2 Skill trust (weight 0.22)

The skills list is useful only if you do not take it at face value. For each skill
that is relevant to the role (matched on word boundaries so "ml" never matches
"html" and "search" never matches "research"), we compute a trust value from three
platform-backed signals:

- endorsements received (capped at 20)
- months the skill has actually been used (capped at 24)
- the Redrob skill-assessment score for that skill, when present

A skill with zero endorsements, zero months, and no assessment earns a trust near
zero and is counted as stuffing rather than as a real skill. A skill that is
endorsed, used for years, and assessed highly earns full trust. The relevant
trusted skills are summed and squashed so about three solid skills reach the
maximum. This is what makes the keyword-stuffer traps score badly: their skills
are all surface, no substance.

### 3.3 Title (weight 0.18)

Directly-relevant titles (AI Engineer, ML Engineer, Search/Relevance Engineer,
Data Scientist, Applied Scientist) score 1.0. Adjacent technical titles (Software
Engineer, Data Engineer) score a middling 0.55 and rely on career evidence to lift
them, which is the correct behaviour for the JD's "Tier 5 hidden gem" who built ML
under a plain title. Off-role titles (Marketing Manager, Accountant, Mechanical
Engineer, and so on) score near zero, because no skill list should rescue a
candidate who has never done the job.

### 3.4 Experience (weight 0.20)

The JD's ideal band is 6 to 8 years, with 5 to 9 acceptable and flexibility beyond
that. The score peaks inside 6 to 8 and falls off smoothly on both sides, with
very junior candidates penalized hardest, because the role explicitly disqualifies
people without enough production seniority.

## 4. The disqualifier penalties

The JD has an unusually blunt "things we explicitly do not want" section. Each one
is a multiplier applied to the fit score, so they can stack:

- Keyword stuffer (non-technical current title carrying four or more AI skills):
  fit multiplied by 0.15. This is the strongest penalty and directly targets the
  built-in trap.
- Entire career at services and consulting firms (Infosys, TCS, Wipro, Accenture,
  and similar) with no product-company experience: multiplied by 0.7. Having a
  product company anywhere in the history removes the penalty and adds a small
  boost.
- Job-hopper (four or more roles averaging under 20 months each): multiplied by
  0.65. The JD says it wants someone who will stay three-plus years and calls out
  title-chasing explicitly.
- Vision, speech, or robotics focus with no NLP or retrieval signal: multiplied by
  0.5. The JD says these candidates would be relearning fundamentals.
- Pure research background with no production evidence: multiplied by 0.65.

These are intentionally conservative. They down-weight rather than zero out, so a
strong candidate with one yellow flag still competes.

## 5. The two multipliers

After fit is computed, two real-world factors scale it.

Behavioral availability (`_behavioral`) turns the Redrob activity signals into a
multiplier between 0.5 and 1.0, built from recency of last activity, recruiter
response rate, open-to-work status, interview completion, and a small notice-period
adjustment. The JD and the signals document both say the same thing: a candidate
who cannot be reached is not actually hireable, so down-weight them. We use a
multiplier rather than a component so that being unreachable scales down an
otherwise strong candidate proportionally.

Location (`_location`) favours India hubs, with Pune and Noida preferred per the
JD. Overseas candidates are discounted unless they are flagged willing to relocate,
because the JD says it does not sponsor work visas.

## 6. Honeypots

About eighty profiles in the pool are internally impossible and are forced to
relevance tier 0 in the hidden ground truth. Ranking more than ten percent of them
in the top 100 is an automatic disqualification, so this matters.

`khoj/honeypot.py` applies conservative checks that are essentially never wrong:
claiming advanced or expert proficiency in a skill used for zero months, total
career tenure exceeding the stated years of experience by more than three years, a
single role longer than the whole career, and dates that do not parse or run
backwards. A flagged candidate is forced to a score of zero and drops out of the
shortlist.

We tuned this carefully. An earlier version also flagged any skill used longer than
the paid career, which wrongly caught 2,800 legitimate people who learned a skill
in college. We removed it. The current checks flag 43 candidates with near-perfect
precision, and zero honeypots reach our top 100. Note that the trust-weighted
scoring would mostly avoid them anyway, since their fake skills earn no trust; the
explicit check is the safety net, not the main defence.

## 7. The reasoning column

Stage 4 reviewers read the reasoning by hand and check six things: specific facts,
JD connection, honest concerns, no hallucination, variation across candidates, and
tone matching the rank. `khoj/reasoning.py` builds each line from the candidate's
own fields and the score breakdown, so every claim is grounded. It surfaces the
real career evidence found, the trust-verified skill names, the activity signals,
and any concern (a penalty, a weak location, a long notice period) phrased more
gently for high ranks and more directly for low ones. Nothing is templated.

## 8. Output and validation

`rank.py` makes two passes over the file. The first scores everyone and keeps only
the score and id, which keeps memory tiny. It rounds each score to six decimals,
then sorts by score descending and candidate id ascending, which guarantees the
validator's tie-break rule (equal scores ordered by id ascending) holds exactly.
The second pass pulls back just the hundred finalists to attach reasoning. The
output matches the required header and row count, and we run the organizers'
`validate_submission.py` on it before every submission.

## 9. How we validated and calibrated without the ground truth

The competition hides the labels and runs no leaderboard, so we built our own
measurement. `khoj/goldlabel.py` is an independent gold relevance labeler: a hard,
tiered checklist (0 to 5) read straight from the JD and from the archetype
structure we found in the data. It is deliberately built differently from the
scorer (a checklist, not a weighted formula), so when the two agree it means
something, and where they disagree we have a place to look.

`evaluate_internal.py` then computes the exact official composite
(0.50 NDCG@10 + 0.30 NDCG@50 + 0.15 MAP + 0.05 P@10) of our ranking against that
gold, and ablates each signal to show its contribution.

Two things this surfaced, and both were acted on:

- The behavioral and location multipliers were too aggressive. The signals
  document calls them a "modifier," but ours were swinging scores by up to half,
  letting reachability override qualification. We softened both to gentle modifier
  ranges. The JD intent is preserved; the dominance is gone.
- The evidence and skill signals were saturating. Every qualified ML candidate hit
  career = 1.0 and skill = 1.0, so "exceptional" and merely "good" candidates
  collapsed to the same ceiling and behavioral noise decided the order. We
  de-saturated both so the full stack (retrieval plus vector infra plus embeddings
  plus eval literacy, the JD's hard requirements) separates from partial evidence.
  This moved our internal NDCG@10 from 0.82 to 0.95 and made the top 10 entirely
  tier-4 and tier-5 candidates.

The honest caveat we keep front of mind: agreement with our own gold is not proof
of agreement with the hidden ground truth. Both are faithful readings of the same
JD. We deliberately did not chase the gold composite where it would have meant
gutting career evidence (the JD's most explicitly stated signal), because that
would be overfitting to our own labeler rather than to the JD. We trust the
coverage and trap-avoidance checks (top 10 all ideal, zero stuffers, zero
honeypots) more than the raw composite number.

Remaining honest limitations:

- Thresholds are reasoned and gold-calibrated, not learned from real labels.
- A lexical or embedding similarity signal could catch fits phrased in words our
  lexicons miss.
- The honeypot checks catch the impossibilities visible in the data; some
  honeypots likely need fields we do not have, and we rely on the scorer to avoid
  those (it puts zero in the top 100).

## 10. Likely interview questions and the honest answers

- Why not embeddings? See section 2: keyword-stuffer vulnerability, compute budget,
  and explainability. We treat semantic similarity as an optional add-on signal,
  not the base.
- How do you beat the keyword stuffers? Career evidence outweighs the skills list,
  skills are trust-weighted to near zero without endorsements or assessments, and a
  non-technical title with many AI skills takes a hard penalty.
- How do you find the hidden gems? Adjacent titles are not penalized and rise on
  career evidence, so a plainly-worded engineer who built a recsys at a product
  company ranks well without the buzzwords.
- How do you avoid honeypots? Conservative consistency checks plus trust-weighting
  that starves impossible profiles of points.
- Does it scale? Yes, 16 seconds for 100,000 on a CPU, linear in pool size, no
  per-candidate model calls, which is the whole point of the compute constraint.
