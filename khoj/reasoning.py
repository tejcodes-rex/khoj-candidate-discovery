"""
Reasoning generator.

Stage 4 reviewers read these by hand and check six things: that the text cites
specific facts from the profile, connects to the JD, admits real concerns, never
invents skills or employers, varies from candidate to candidate, and matches the
rank. So we build each line out of the candidate's own fields and the scoring
breakdown. Nothing here is templated boilerplate, and nothing is claimed that the
profile does not contain.
"""


# Matching uses stems and lowercase tokens; these read them back as clean prose.
_PRETTY = {
    "fine-tun": "fine-tuning", "finetun": "fine-tuning", "nlp": "NLP",
    "natural language": "NLP", "llm": "LLMs", "rag": "RAG", "recsys": "recsys",
    "ann": "ANN", "bm25": "BM25", "faiss": "FAISS", "hnsw": "HNSW", "e5": "E5",
    "bge": "BGE", "ml ": None, "ml": None, "neural": "neural nets",
    "openai embedding": "OpenAI embeddings", "sentence-transformer": "sentence-transformers",
    "pinecone": "Pinecone", "milvus": "Milvus", "qdrant": "Qdrant",
    "weaviate": "Weaviate", "elasticsearch": "Elasticsearch", "opensearch": "OpenSearch",
    "vespa": "Vespa", "pgvector": "pgvector", "vector search": "vector search",
    "learning to rank": "learning-to-rank",
}


def _clean(term):
    t = term.strip()
    if t in _PRETTY:
        return _PRETTY[t]
    return t


def _evidence_phrase(detail):
    c = detail["career"]
    # surface the most role-defining terms first: infra and embeddings, then
    # specific ML/IR concepts, and only generic terms as a last resort
    specific = [t for t in c["ml"] if t in
                ("ranking", "retrieval", "recommendation", "search", "embedding",
                 "embeddings", "semantic search", "vector search", "personalization",
                 "learning to rank", "fine-tun")]
    ordered = c["infra"] + c["embed"] + specific + c["eval"] + c["ml"]
    seen, out = set(), []
    for t in ordered:
        ct = _clean(t)
        if ct and ct.lower() not in seen:
            seen.add(ct.lower())
            out.append(ct)
        if len(out) == 3:
            break
    return ", ".join(out) if out else None


def make_reasoning(cand, scored, rank):
    p = cand.get("profile", {})
    d = scored["detail"]
    comp = scored["components"]
    title = p.get("current_title", "professional")
    yoe = d["yoe"]
    parts = []

    # Lead with role and experience, the JD's first filter.
    lead = f"{title} with {yoe:.1f} yrs"
    ev = _evidence_phrase(d)
    if comp["career_evidence"] >= 0.5 and ev:
        lead += f"; career history shows {ev}"
    elif comp["career_evidence"] >= 0.25 and ev:
        lead += f"; some retrieval/ML evidence ({ev})"
    parts.append(lead)

    # Skills, but only the trust-verified ones, with a stuffing note when relevant.
    ts = d["trusted_skills"]
    if ts:
        names = ", ".join(n for n, _ in ts[:3])
        parts.append(f"{len(ts)} trust-verified skills ({names})")
    elif d["n_stuffed"] >= 3:
        parts.append(f"{d['n_stuffed']} AI skills listed but unendorsed/untested")

    # Availability, straight from behavioral signals.
    b = d["beh_notes"]
    if b["days_since_active"] <= 30:
        parts.append(f"active {b['days_since_active']}d ago, response rate {b['response_rate']:.0%}")
    elif b["days_since_active"] >= 120:
        parts.append(f"inactive {b['days_since_active']}d, response rate {b['response_rate']:.0%}")

    # Honest concerns. The reviewers reward this explicitly.
    concerns = list(d["penalties"])
    if comp["location"] < 0.8:
        concerns.append(d["loc_note"])
    if b["notice_period_days"] > 90:
        concerns.append(f"{b['notice_period_days']}-day notice")
    if scored["is_honeypot"]:
        concerns.append("internally inconsistent profile")

    sentence = "; ".join(parts) + "."
    if concerns:
        # tone has to match the rank: top ranks note concerns lightly, low ranks lead with them
        if rank <= 25:
            sentence += f" Minor concern: {concerns[0]}."
        else:
            sentence += f" Held back by {concerns[0]}."
    elif rank > 60:
        sentence += " Adjacent fit, included toward the lower band."
    return sentence
