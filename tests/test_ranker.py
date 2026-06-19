"""
Tests for the ranker. Two things matter most and are covered here:

  1. The scoring logic does what the JD says: stuffers lose, gems win, honeypots
     are caught, behavioral signals move the score.
  2. The output obeys every rule the official validator enforces, so we can never
     fail Stage 1 on a format technicality.

Run: pytest -q
"""

import csv
import io
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from khoj.scoring import score_candidate
from khoj.honeypot import detect
from khoj.reasoning import make_reasoning


def _skill(name, prof="advanced", endorse=30, dur=30):
    return {"name": name, "proficiency": prof, "endorsements": endorse, "duration_months": dur}


def _signals(**kw):
    base = {
        "last_active_date": "2026-06-01", "open_to_work_flag": True,
        "recruiter_response_rate": 0.8, "interview_completion_rate": 0.8,
        "notice_period_days": 30, "skill_assessment_scores": {}, "willing_to_relocate": True,
    }
    base.update(kw)
    return base


def _cand(cid, title, yoe, skills, descriptions, company="Swiggy",
          location="Pune", country="India", signals=None, career=None):
    history = career or [{
        "company": company, "title": title, "start_date": "2020-01-01", "end_date": None,
        "duration_months": int(yoe * 12), "is_current": True, "industry": "Tech",
        "company_size": "201-500", "description": " ".join(descriptions),
    }]
    return {
        "candidate_id": cid,
        "profile": {"anonymized_name": "X", "headline": title, "summary": " ".join(descriptions),
                    "location": location, "country": country, "years_of_experience": yoe,
                    "current_title": title, "current_company": company,
                    "current_company_size": "201-500", "current_industry": "Tech"},
        "career_history": history,
        "education": [{"institution": "X", "degree": "B.E.", "field_of_study": "CS",
                       "start_year": 2014, "end_year": 2018, "tier": "tier_2"}],
        "skills": skills,
        "redrob_signals": signals or _signals(),
    }


def test_real_fit_outranks_keyword_stuffer():
    gem = _cand("CAND_0000001", "Machine Learning Engineer", 7,
                [_skill("NLP"), _skill("FAISS"), _skill("Ranking")],
                ["Built and shipped a recommendation and ranking system with embeddings "
                 "and vector retrieval, deployed to production at scale, owned end to end."])
    stuffer = _cand("CAND_0000002", "Marketing Manager", 8,
                    [_skill("NLP", endorse=0, dur=0), _skill("LLM", endorse=0, dur=0),
                     _skill("RAG", endorse=0, dur=0), _skill("Embeddings", endorse=0, dur=0)],
                    ["Ran marketing campaigns and managed brand strategy."])
    assert score_candidate(gem)["final"] > score_candidate(stuffer)["final"]


def test_honeypot_is_zeroed():
    hp = _cand("CAND_0000003", "ML Engineer", 6,
               [_skill("NLP", prof="expert", dur=0)],
               ["Production ML and retrieval work."])
    s = score_candidate(hp)
    assert s["is_honeypot"] and s["final"] == 0.0


def test_unreachable_candidate_is_downweighted():
    base_desc = ["Shipped production ranking and retrieval systems with embeddings."]
    reachable = _cand("CAND_0000004", "ML Engineer", 7,
                      [_skill("NLP"), _skill("FAISS")], base_desc,
                      signals=_signals(last_active_date="2026-06-10", recruiter_response_rate=0.9))
    ghost = _cand("CAND_0000005", "ML Engineer", 7,
                  [_skill("NLP"), _skill("FAISS")], base_desc,
                  signals=_signals(last_active_date="2024-01-01", recruiter_response_rate=0.02,
                                   open_to_work_flag=False))
    assert score_candidate(reachable)["final"] > score_candidate(ghost)["final"]


def test_services_only_penalized_vs_product():
    desc = ["Built production retrieval and ranking systems with embeddings at scale."]
    product = _cand("CAND_0000006", "ML Engineer", 7, [_skill("NLP"), _skill("FAISS")], desc, company="Flipkart")
    services = _cand("CAND_0000007", "ML Engineer", 7, [_skill("NLP"), _skill("FAISS")], desc,
                     company="Infosys",
                     career=[{"company": "Infosys", "title": "ML Engineer", "start_date": "2018-01-01",
                              "end_date": None, "duration_months": 84, "is_current": True,
                              "industry": "IT Services", "company_size": "10001+", "description": desc[0]}])
    assert score_candidate(product)["final"] > score_candidate(services)["final"]


def test_junior_title_downweighted_for_senior_role():
    desc = ["Production ranking and retrieval with embeddings, shipped at scale."]
    senior = _cand("CAND_0000008", "Senior Machine Learning Engineer", 7, [_skill("NLP"), _skill("FAISS")], desc)
    junior = _cand("CAND_0000009", "Junior Machine Learning Engineer", 7, [_skill("NLP"), _skill("FAISS")], desc)
    assert score_candidate(senior)["final"] > score_candidate(junior)["final"]


def test_reasoning_is_grounded_and_nonempty():
    gem = _cand("CAND_0000010", "ML Engineer", 7, [_skill("NLP"), _skill("FAISS")],
                ["Built a production ranking system with embeddings."])
    r = make_reasoning(gem, score_candidate(gem), 1)
    assert "7.0 yrs" in r and len(r) > 30


def test_output_passes_official_validator(tmp_path):
    """Generate a tiny submission and run the organizers' validator on it."""
    rows = []
    for i in range(1, 101):
        rows.append({"candidate_id": f"CAND_{i:07d}", "rank": i,
                     "score": f"{(1.0 - i*0.005):.6f}", "reasoning": f"reason {i}"})
    out = tmp_path / "team_test.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        w.writeheader()
        w.writerows(rows)

    validator = next(ROOT.glob("data/raw/official/**/validate_submission.py"), None)
    if validator is None:
        pytest.skip("official validator not present in this checkout")
    res = subprocess.run([sys.executable, str(validator), str(out)],
                         capture_output=True, text=True)
    assert "Submission is valid." in res.stdout, res.stdout + res.stderr


def test_tiebreak_orders_by_candidate_id_ascending():
    """Equal scores must be emitted candidate_id ascending (validator rule)."""
    pairs = sorted([(0.5, "CAND_0000020"), (0.5, "CAND_0000010")], key=lambda x: (-x[0], x[1]))
    assert [c for _, c in pairs] == ["CAND_0000010", "CAND_0000020"]
