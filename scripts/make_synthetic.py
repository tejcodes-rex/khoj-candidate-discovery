"""
Synthetic Indian professional dataset generator.

Builds a realistic, deliberately messy candidate pool that mirrors the Track 1
brief: unstandardized profiles, Hinglish fragments, missing fields, duplicates,
career metadata, and activity/behavioral signals. It also plants two kinds of
candidates we care about for evaluation:

  - "obvious" strong fits: clean pedigree, exact keyword overlap.
  - "hidden gems": strong demonstrated trajectory and impact but weak surface
    pedigree (tier-3 college, no brand-name employer, non-standard wording),
    the people a keyword filter buries.

Outputs:
  data/raw/profiles.jsonl   one JSON profile per line
  data/raw/jobs.json        a set of nuanced job descriptions
  data/raw/qrels.json       graded relevance labels per job for evaluation

Standard library only, fixed seed, fully reproducible.
"""

import json
import os
import random
from pathlib import Path

SEED = 20260617
random.seed(SEED)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Vocabulary pools (small but representative; expand freely)
# ---------------------------------------------------------------------------

FIRST = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh",
         "Ayaan", "Krishna", "Ishaan", "Ananya", "Diya", "Aadhya", "Saanvi",
         "Pari", "Anika", "Navya", "Myra", "Kiara", "Riya", "Fatima", "Zoya",
         "Rahul", "Priya", "Sneha", "Karthik", "Meera", "Rohan", "Neha",
         "Farhan", "Tejas", "Ishita", "Harshit", "Lakshya", "Devika"]

LAST = ["Sharma", "Verma", "Patel", "Reddy", "Nair", "Iyer", "Gupta", "Singh",
        "Khan", "Das", "Bose", "Mukherjee", "Naidu", "Rao", "Kulkarni",
        "Joshi", "Mehta", "Chauhan", "Pillai", "Mishra", "Ghosh", "Sheikh"]

TIER1_COLLEGE = ["IIT Bombay", "IIT Delhi", "IIT Madras", "BITS Pilani",
                 "IIIT Hyderabad", "NIT Trichy"]
TIER2_COLLEGE = ["VIT Vellore", "SRM Chennai", "Manipal Institute of Technology",
                 "PES University", "Thapar University", "COEP Pune"]
TIER3_COLLEGE = ["Govt Engineering College Indore", "Dr APJ Abdul Kalam University",
                 "Saveetha Engineering College", "Lovely Professional University",
                 "Kakatiya Institute of Tech", "RGPV affiliated college, Bhopal",
                 "Self-taught, no formal CS degree", "B.Com graduate, switched to tech"]

TIER1_EMPLOYER = ["Google", "Microsoft", "Amazon", "Flipkart", "Razorpay",
                  "Swiggy", "Zomato", "Atlassian"]
SMALL_EMPLOYER = ["a 12-person fintech startup", "a local SaaS company in Indore",
                  "freelance clients", "an early-stage healthtech startup",
                  "a Tier-2 city web agency", "own bootstrapped product",
                  "a Series-A logistics startup"]

CITY_TIER = {
    "Bengaluru": 1, "Mumbai": 1, "Delhi": 1, "Hyderabad": 1, "Pune": 1,
    "Chennai": 1, "Gurugram": 1,
    "Jaipur": 2, "Indore": 2, "Coimbatore": 2, "Nagpur": 2, "Bhopal": 2,
    "Kochi": 2, "Chandigarh": 2,
    "Hubli": 3, "Raipur": 3, "Guwahati": 3, "Siliguri": 3, "Warangal": 3,
}

BACKEND_SKILLS = ["Python", "Go", "Java", "Node.js", "PostgreSQL", "Redis",
                  "Kafka", "Docker", "Kubernetes", "AWS", "microservices",
                  "system design", "REST APIs", "gRPC"]
ML_SKILLS = ["PyTorch", "TensorFlow", "scikit-learn", "NLP", "transformers",
             "vector search", "recommendation systems", "LLMs", "RAG",
             "embeddings", "MLOps", "pandas", "feature engineering"]
FRONTEND_SKILLS = ["React", "TypeScript", "Next.js", "CSS", "Redux",
                   "accessibility", "performance optimization"]

# Alias / surface forms of real skills. A keyword filter scanning for the exact
# job-description terms misses these; our ontology canonicalizes them. Hidden
# gems are written this way on purpose.
BACKEND_ALIASES = ["JS", "node", "k8s", "postgres", "REST", "distributed system",
                   "microservices", "system design", "Go", "aws"]
ML_ALIASES = ["ml", "nlp", "recsys", "ann", "semantic search", "embeddings",
              "pandas", "py", "feature engineering"]

# Sparse, messy, mostly-Hinglish summaries with almost no job-description
# vocabulary. Semantic similarity to a polished JD stays low even though the
# person is genuinely qualified.
GEM_SUMMARY = [
    "kaam karne ka strong experience hai, sab khud banaya",
    "bahut saare projects banaye hain apne dum pe",
    "apne aap seekha aur real cheezein ship ki",
    "college se zyada kaam se seekha",
]

# Keyword-stuffed summaries that echo the JD almost word for word. Semantic
# search ranks these at the top, but their careers are flat and they are not
# really looking. The classic false positive.
STUFFED_BE = ("Backend engineer experienced in distributed systems, payments, "
              "high-throughput low-latency APIs, databases under load, reliable "
              "scalable system design, microservices, and clean REST API design.")
STUFFED_ML = ("Machine learning engineer specializing in semantic search, ranking, "
              "embeddings, retrieval, recommendation systems, RAG, evaluation "
              "metrics, and putting models into production at scale.")

# Hinglish / regional fragments to make profiles multilingual and messy
HINGLISH = [
    "kaam karne ka strong experience hai",
    "team ko lead kiya backend pe",
    "production me deploy kiya",
    "bahut saare projects banaye hain",
    "fresher hoon par seekhne ki himmat hai",
    "data pipeline pe accha haath hai",
]

NOISE_TITLES = ["SDE", "Software Engr.", "sr. backend dev", "ML engg",
                "Backend Developer ", "  Data Scientist", "full-stack dev",
                "Software Developer (Backend)", "AI/ML Engineer"]


def messy(text):
    """Randomly corrupt a string the way real scraped profiles are corrupted."""
    r = random.random()
    if r < 0.15:
        return text.upper()
    if r < 0.30:
        return text.lower()
    if r < 0.40:
        return "  " + text + "   "
    if r < 0.48:
        return text.replace(" ", "  ")
    return text


def career_history(n_roles, start_year, ascending, employers, base_title):
    """Build a list of roles. ascending=True means clear upward progression."""
    levels = ["Intern", "Junior", "Associate", "Senior", "Lead", "Staff"]
    roles = []
    year = start_year
    li = 0 if ascending else random.randint(1, 3)
    for i in range(n_roles):
        level = levels[min(li, len(levels) - 1)]
        dur = random.randint(1, 3)
        roles.append({
            "title": f"{level} {base_title}".strip(),
            "employer": random.choice(employers),
            "from": year,
            "to": year + dur,
            "blurb": messy(random.choice(HINGLISH)) if random.random() < 0.25 else "",
        })
        year += dur
        if ascending:
            li += 1
        else:
            li += random.choice([0, 0, 1])
    return roles


def behavioral_signals(intent):
    """Activity and intent signals. intent in {hot, warm, cold}."""
    if intent == "hot":
        return {
            "last_active_days": random.randint(0, 4),
            "open_to_work": True,
            "profile_completeness": round(random.uniform(0.85, 1.0), 2),
            "recent_applications": random.randint(3, 12),
            "response_rate": round(random.uniform(0.6, 0.95), 2),
        }
    if intent == "warm":
        return {
            "last_active_days": random.randint(5, 30),
            "open_to_work": random.choice([True, False]),
            "profile_completeness": round(random.uniform(0.6, 0.9), 2),
            "recent_applications": random.randint(0, 4),
            "response_rate": round(random.uniform(0.3, 0.7), 2),
        }
    return {
        "last_active_days": random.randint(60, 400),
        "open_to_work": False,
        "profile_completeness": round(random.uniform(0.2, 0.6), 2),
        "recent_applications": 0,
        "response_rate": round(random.uniform(0.0, 0.3), 2),
    }


def make_profile(idx, archetype):
    """
    archetype drives the planted ground truth used for evaluation.
      obvious_be : strong backend, clean pedigree, hot intent
      gem_be     : strong backend trajectory, weak pedigree (hidden gem)
      obvious_ml : strong ML, clean pedigree
      gem_ml     : strong ML trajectory, weak pedigree
      noise      : unrelated or weak, filler
    """
    name = f"{random.choice(FIRST)} {random.choice(LAST)}"
    city = random.choice(list(CITY_TIER))

    if archetype == "obvious_be":
        college = random.choice(TIER1_COLLEGE)
        employers = random.sample(TIER1_EMPLOYER, k=2)
        skills = random.sample(BACKEND_SKILLS, k=8)
        roles = career_history(3, 2018, True, employers, "Backend Engineer")
        intent = random.choice(["warm", "cold"])
        summary = "Backend engineer with distributed systems and high-scale API experience."
    elif archetype == "gem_be":
        college = random.choice(TIER3_COLLEGE)
        employers = random.sample(SMALL_EMPLOYER, k=2)
        skills = random.sample(BACKEND_ALIASES, k=7)
        roles = career_history(3, 2020, True, employers, "Backend Developer")
        roles[-1]["blurb"] = "5x traffic handle kiya, sab khud banaya aur ship kiya"
        intent = "hot"
        summary = messy(random.choice(GEM_SUMMARY))
    elif archetype == "obvious_ml":
        college = random.choice(TIER1_COLLEGE)
        employers = random.sample(TIER1_EMPLOYER, k=2)
        skills = random.sample(ML_SKILLS, k=8)
        roles = career_history(3, 2018, True, employers, "ML Engineer")
        intent = random.choice(["warm", "cold"])
        summary = "Machine learning engineer focused on NLP and recommendation systems."
    elif archetype == "gem_ml":
        college = random.choice(TIER3_COLLEGE)
        employers = random.sample(SMALL_EMPLOYER, k=2)
        skills = random.sample(ML_ALIASES, k=7)
        roles = career_history(2, 2021, True, employers, "Data Scientist")
        roles[-1]["blurb"] = "2M data pe khud ka system banaya aur prod me daala"
        intent = "hot"
        summary = messy(random.choice(GEM_SUMMARY))
    elif archetype == "stuffed_be":
        college = random.choice(TIER1_COLLEGE + TIER2_COLLEGE)
        employers = random.sample(TIER1_EMPLOYER, k=2)
        skills = random.sample(BACKEND_SKILLS, k=9)
        roles = career_history(2, 2019, False, employers, "Backend Engineer")
        intent = random.choice(["cold", "cold", "warm"])
        summary = STUFFED_BE
    elif archetype == "stuffed_ml":
        college = random.choice(TIER1_COLLEGE + TIER2_COLLEGE)
        employers = random.sample(TIER1_EMPLOYER, k=2)
        skills = random.sample(ML_SKILLS, k=9)
        roles = career_history(2, 2019, False, employers, "ML Engineer")
        intent = random.choice(["cold", "cold", "warm"])
        summary = STUFFED_ML
    else:  # noise
        college = random.choice(TIER2_COLLEGE + TIER3_COLLEGE)
        employers = random.sample(SMALL_EMPLOYER + TIER1_EMPLOYER, k=2)
        skills = random.sample(FRONTEND_SKILLS + BACKEND_SKILLS, k=random.randint(2, 5))
        roles = career_history(random.randint(1, 2), 2021, random.choice([True, False]),
                               employers, random.choice(["Frontend Developer", "QA Engineer", "Support"]))
        intent = random.choice(["warm", "cold", "hot"])
        summary = random.choice([
            "Frontend developer who enjoys building clean interfaces.",
            "QA engineer with manual and automation testing experience.",
            messy("fresher hoon, web development seekh raha hoon"),
            "",  # missing summary on purpose
        ])

    profile = {
        "candidate_id": f"CAND{idx:05d}",
        "name": name,
        "headline": messy(random.choice(NOISE_TITLES)),
        "summary": summary,
        "location": city,
        "city_tier": CITY_TIER[city],
        "education": college,
        "skills": [messy(s) for s in skills],
        "experience": roles,
        "signals": behavioral_signals(intent),
        "_archetype": archetype,  # ground-truth tag, stripped before real use
    }

    # Inject realistic messiness: drop fields, duplicate, add junk
    if random.random() < 0.12:
        profile.pop("location", None)
        profile.pop("city_tier", None)
    if random.random() < 0.08:
        profile["skills"] = []  # empty skills, must survive
    if random.random() < 0.05:
        profile["experience"] = []
    return profile


def build():
    profiles = []
    idx = 0

    # Distribution: lots of noise, some clean fits, keyword-stuffed-but-stagnant
    # false positives, and a precious few hidden gems.
    plan = (["obvious_be"] * 10 + ["gem_be"] * 8 + ["stuffed_be"] * 10 +
            ["obvious_ml"] * 10 + ["gem_ml"] * 8 + ["stuffed_ml"] * 10 +
            ["noise"] * 154)
    random.shuffle(plan)
    for arch in plan:
        profiles.append(make_profile(idx, arch))
        idx += 1

    # Plant a few near-duplicate profiles to test dedup
    for _ in range(6):
        dup = dict(random.choice(profiles))
        dup["candidate_id"] = f"CAND{idx:05d}"
        dup["name"] = dup["name"] + " "  # trivial variation
        profiles.append(dup)
        idx += 1

    random.shuffle(profiles)

    # Two nuanced job descriptions (the kind keyword filters choke on)
    jobs = [
        {
            "job_id": "JOB001",
            "title": "Backend Engineer, Payments",
            "description": (
                "We are looking for a backend engineer to own our payments platform. "
                "You will design high-throughput, low-latency services that move money "
                "reliably. We care far more about people who have actually shipped and "
                "scaled real systems than about where they studied. Comfort with "
                "distributed systems, databases under load, and clean API design is "
                "essential. Bonus if you have driven a system end to end and improved "
                "its latency or reliability. This is a hands-on role, not a manager role."
            ),
            "must_have": ["backend", "APIs", "databases", "distributed systems"],
            "nice_to_have": ["latency optimization", "payments", "Go", "Kafka"],
            "min_experience_years": 3,
            "seniority": "mid-to-senior",
        },
        {
            "job_id": "JOB002",
            "title": "Machine Learning Engineer, Search and Ranking",
            "description": (
                "Join us to build the retrieval and ranking brain of our product. You "
                "will work on semantic search, embeddings, and rerankers over very large, "
                "messy datasets. We want builders who have put ranking or recommendation "
                "systems into production, not only people who have read papers. Strong "
                "Python and a real feel for evaluation metrics matter. Background and "
                "pedigree matter less than what you have actually built and measured."
            ),
            "must_have": ["machine learning", "ranking", "embeddings", "Python"],
            "nice_to_have": ["semantic search", "RAG", "recommendation systems", "MLOps"],
            "min_experience_years": 2,
            "seniority": "mid",
        },
    ]

    # Graded relevance (qrels) derived from planted archetypes.
    # 3 = strong fit, 2 = good fit, 1 = marginal, 0 = irrelevant.
    # Gems are graded as strong fits even though their pedigree is weak; that is
    # exactly what the Hidden-Gem Recovery metric will measure.
    qrels = {"JOB001": {}, "JOB002": {}}
    for p in profiles:
        a = p["_archetype"]
        cid = p["candidate_id"]
        # 3 = strong hire (qualified, rising, reachable). 2 = qualified on paper
        # but stagnant and not really looking, a weaker hire for a recruiter who
        # needs someone who will actually move.
        if a in ("obvious_be", "gem_be"):
            qrels["JOB001"][cid] = 3
        elif a == "stuffed_be":
            qrels["JOB001"][cid] = 2
        elif a in ("obvious_ml", "gem_ml"):
            qrels["JOB002"][cid] = 3
        elif a == "stuffed_ml":
            qrels["JOB002"][cid] = 2
        # noise stays unjudged (treated as 0)

    with open(RAW / "profiles.jsonl", "w", encoding="utf-8") as f:
        for p in profiles:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(RAW / "jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    with open(RAW / "qrels.json", "w", encoding="utf-8") as f:
        json.dump(qrels, f, ensure_ascii=False, indent=2)

    n_gem = sum(1 for p in profiles if p["_archetype"] in ("gem_be", "gem_ml"))
    print(f"Wrote {len(profiles)} profiles to {RAW/'profiles.jsonl'}")
    print(f"  hidden gems planted: {n_gem}")
    print(f"  jobs: {len(jobs)}  ->  {RAW/'jobs.json'}")
    print(f"  qrels written to {RAW/'qrels.json'}")


if __name__ == "__main__":
    build()
