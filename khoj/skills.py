"""
Skill ontology and canonicalization.

Real profiles write the same skill a dozen ways: "JS", "Javascript", "java
script", "node", "nodejs". A keyword filter treats these as different tokens and
misses good people. We collapse surface forms to a canonical skill and group
canonical skills into families so that semantic neighbours ("Kafka" implies
"distributed systems") reinforce each other during scoring.

This is intentionally a hand-curated seed ontology. It is easy to extend, and a
larger version can be learned from the real dataset once we have it.
"""

import re

# canonical skill -> list of surface aliases (lowercased, punctuation-stripped)
ALIASES = {
    "javascript": ["js", "java script", "ecmascript"],
    "typescript": ["ts"],
    "node.js": ["node", "nodejs", "node js"],
    "python": ["py", "python3"],
    "postgresql": ["postgres", "psql", "postgre sql"],
    "kubernetes": ["k8s", "kube"],
    "machine learning": ["ml", "machinelearning"],
    "natural language processing": ["nlp"],
    "large language models": ["llm", "llms", "gen ai", "genai"],
    "recommendation systems": ["recsys", "recommender", "recommendation system"],
    "rest apis": ["rest", "restful", "rest api", "api", "apis"],
    "distributed systems": ["distributed system", "distributed computing"],
    "amazon web services": ["aws"],
    "vector search": ["semantic search", "ann", "nearest neighbour search"],
}

# canonical skill -> family. Family overlap gives partial credit during scoring.
FAMILY = {
    "javascript": "web", "typescript": "web", "node.js": "backend",
    "react": "web", "next.js": "web", "css": "web", "redux": "web",
    "python": "backend", "go": "backend", "java": "backend",
    "postgresql": "data", "redis": "data", "kafka": "data",
    "docker": "infra", "kubernetes": "infra", "amazon web services": "infra",
    "microservices": "backend", "system design": "backend",
    "rest apis": "backend", "grpc": "backend", "distributed systems": "backend",
    "machine learning": "ml", "pytorch": "ml", "tensorflow": "ml",
    "scikit-learn": "ml", "natural language processing": "ml",
    "transformers": "ml", "vector search": "ml", "recommendation systems": "ml",
    "large language models": "ml", "embeddings": "ml", "mlops": "ml",
    "pandas": "data", "feature engineering": "ml", "rag": "ml",
}

_ALIAS_LOOKUP = {}
for canon, al in ALIASES.items():
    _ALIAS_LOOKUP[canon] = canon
    for a in al:
        _ALIAS_LOOKUP[a] = canon


def _clean(token):
    return re.sub(r"[^a-z0-9+.# ]", "", token.strip().lower())


def canonical(skill):
    """Map a raw skill string to its canonical form."""
    c = _clean(skill)
    c = re.sub(r"\s+", " ", c).strip()
    return _ALIAS_LOOKUP.get(c, c)


def canonical_set(skills):
    """Canonicalize a list of raw skills into a deduplicated set."""
    out = set()
    for s in skills or []:
        c = canonical(s)
        if c:
            out.add(c)
    return out


def families(skills):
    """Return the set of skill families covered by a set of canonical skills."""
    return {FAMILY.get(s) for s in skills if FAMILY.get(s)}
