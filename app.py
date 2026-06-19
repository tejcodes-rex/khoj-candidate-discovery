"""
Khoj sandbox app.

A hosted, runnable demo of the ranker, satisfying the submission's sandbox
requirement. Deploy it to Streamlit Cloud or HuggingFace Spaces straight from
this repo (entry point: app.py). It ranks a small candidate sample end to end on
CPU and lets you download the resulting CSV, which is exactly what the organizers
check at Stage 3's lower-stakes sanity pass.

Run locally:
    pip install streamlit
    streamlit run app.py

The ranking core (khoj/) stays dependency-free; only this front end uses
Streamlit.
"""

import io
import json

import streamlit as st

from khoj.scoring import score_candidate
from khoj.reasoning import make_reasoning

st.set_page_config(page_title="Khoj — Candidate Discovery", layout="wide")

st.title("Khoj")
st.caption("Intelligent candidate discovery for the Senior AI Engineer role. "
           "Career evidence over keywords, trust-weighted skills, behavioral availability, honeypot-aware.")


@st.cache_data
def load_default():
    out = []
    try:
        with open("sample_candidates.jsonl", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def read_upload(buf):
    text = io.TextIOWrapper(buf, encoding="utf-8") if hasattr(buf, "read") else buf
    out = []
    for line in text:
        line = line.strip() if isinstance(line, str) else line.decode("utf-8").strip()
        if line:
            out.append(json.loads(line))
    return out


with st.sidebar:
    st.header("Candidate sample")
    up = st.file_uploader("Upload a candidates .jsonl (optional)", type=["jsonl", "json"])
    top_k = st.slider("Shortlist size", 5, 100, 25)
    st.markdown("No upload? A bundled 80-candidate sample is used.")

candidates = read_upload(up) if up else load_default()

if not candidates:
    st.warning("No candidates loaded. Upload a .jsonl file to begin.")
    st.stop()

scored = []
for c in candidates:
    s = score_candidate(c)
    scored.append((s["final"], c["candidate_id"], c, s))
scored.sort(key=lambda x: (-x[0], x[1]))
ranked = scored[:top_k]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Candidates scored", len(candidates))
c2.metric("Shortlisted", len(ranked))
c3.metric("Honeypots excluded", sum(1 for _, _, _, s in scored if s["is_honeypot"]))
c4.metric("Top score", f"{ranked[0][0]:.3f}")

st.subheader("Ranked shortlist")
for rank, (score, cid, cand, s) in enumerate(ranked, 1):
    p = cand["profile"]
    gem = "  ·  hidden gem" if (s["components"]["title"] < 0.6 and s["components"]["career_evidence"] >= 0.7) else ""
    with st.expander(f"#{rank}  {p.get('current_title','')}  ·  {p.get('location','')}  ·  "
                     f"{p.get('years_of_experience','?')} yrs  ·  score {score:.3f}{gem}"):
        st.write(make_reasoning(cand, s, rank))
        comp = s["components"]
        cols = st.columns(6)
        for col, key in zip(cols, ["career_evidence", "skill_trust", "title", "experience", "behavioral", "location"]):
            col.metric(key.replace("_", " "), f"{comp[key]:.2f}")
        if s["detail"]["penalties"]:
            st.caption("Concerns: " + "; ".join(s["detail"]["penalties"]))

# Downloadable CSV in the exact submission format.
lines = ["candidate_id,rank,score,reasoning"]
for rank, (score, cid, cand, s) in enumerate(ranked, 1):
    reason = make_reasoning(cand, s, rank).replace('"', "'")
    lines.append(f'{cid},{rank},{score:.6f},"{reason}"')
st.download_button("Download ranked CSV", "\n".join(lines), file_name="submission.csv", mime="text/csv")
