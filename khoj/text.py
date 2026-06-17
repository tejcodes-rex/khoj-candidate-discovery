"""
Text normalization, multilingual handling, and a dependency-free TF-IDF vector
space with cosine similarity.

Why pure standard library: the brief asks for a lightning-fast system, and a
judge must be able to clone the repo and run it on any laptop with no GPU and no
model download. This module is the always-available semantic backend. A stronger
sentence-transformer backend plugs in behind the same interface (see
khoj/backends.py) when accuracy headroom is wanted.
"""

import math
import re
from collections import Counter, defaultdict

# A compact Hinglish and transliteration map so multilingual fragments in
# profiles contribute real signal instead of being dropped as noise.
HINGLISH_MAP = {
    "kaam": "work", "experience": "experience", "haath": "hand",
    "seekh": "learn", "seekhne": "learning", "banaye": "built",
    "banaya": "built", "kiya": "did", "lead": "lead", "team": "team",
    "production": "production", "deploy": "deploy", "fresher": "fresher",
    "himmat": "courage", "accha": "good", "strong": "strong", "data": "data",
    "pipeline": "pipeline", "projects": "projects", "saare": "many",
    "bahut": "many", "raha": "", "hoon": "", "hai": "", "pe": "", "ka": "",
    "ki": "", "me": "", "ko": "", "par": "",
}

STOP = set("""a an the of and or to in on for with at by from as is are was were be
been being this that these those it its their his her your our we you they i me
my mine he she them us""".split())

_TOKEN = re.compile(r"[a-z0-9+.#]+")


def normalize_text(text):
    """Lowercase, strip junk, fold common Hinglish to English keywords."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    tokens = _TOKEN.findall(text)
    folded = []
    for t in tokens:
        if t in HINGLISH_MAP:
            mapped = HINGLISH_MAP[t]
            if mapped:
                folded.append(mapped)
        else:
            folded.append(t)
    return " ".join(folded)


def tokenize(text):
    return [t for t in _TOKEN.findall(normalize_text(text)) if t not in STOP and len(t) > 1]


class TfidfSpace:
    """A small TF-IDF model with cosine similarity. Fit once on the corpus."""

    def __init__(self):
        self.idf = {}
        self.doc_vectors = []
        self.doc_ids = []

    def fit(self, docs, doc_ids):
        n = len(docs)
        df = defaultdict(int)
        tokenized = []
        for d in docs:
            toks = tokenize(d)
            tokenized.append(toks)
            for t in set(toks):
                df[t] += 1
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1.0 for t, c in df.items()}
        self.doc_ids = list(doc_ids)
        self.doc_vectors = [self._vector(toks) for toks in tokenized]
        return self

    def _vector(self, tokens):
        tf = Counter(tokens)
        total = sum(tf.values()) or 1
        vec = {}
        for t, c in tf.items():
            if t in self.idf:
                vec[t] = (c / total) * self.idf[t]
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def vector(self, text):
        return self._vector(tokenize(text))

    @staticmethod
    def cosine(a, b):
        if len(a) > len(b):
            a, b = b, a
        return sum(v * b.get(t, 0.0) for t, v in a.items())

    def query(self, text, top_n=None):
        """Return (doc_id, score) sorted descending."""
        qv = self.vector(text)
        scored = [(self.doc_ids[i], self.cosine(qv, dv))
                  for i, dv in enumerate(self.doc_vectors)]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n] if top_n else scored
