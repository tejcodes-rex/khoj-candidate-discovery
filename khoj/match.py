"""
Word-boundary phrase matching.

Naive `term in text` matching is a trap on real profile text: "search" hides
inside "research", "rag" inside "storage", "live" inside "delivered". That
silently hands retrieval credit to the exact candidates the JD rejects and makes
the reasoning claim skills nobody listed. Every lexicon match in the scorer goes
through here instead.

Implementation: single-word terms are matched against the set of whole tokens in
the text (so "ml" never matches "html" and "search" never matches "research");
multi-word and hyphenated phrases are matched as substrings (they are specific
enough that embedding is not a risk). This is both correct and fast enough to
score 100,000 candidates in well under the compute budget.
"""

import re
from functools import lru_cache

_TOKEN = re.compile(r"[a-z0-9]+")
_SINGLE = re.compile(r"^[a-z0-9]+$")


@lru_cache(maxsize=256)
def _split(terms_tuple):
    singles = frozenset(t for t in terms_tuple if t and _SINGLE.match(t))
    phrases = tuple(t for t in terms_tuple if t and not _SINGLE.match(t))
    return singles, phrases


def hits(text, terms):
    """Return the set of terms (lowercased) that appear as whole tokens/phrases."""
    if not text or not terms:
        return set()
    norm = text.lower()
    singles, phrases = _split(tuple(sorted(terms)))
    tokens = set(_TOKEN.findall(norm))
    out = set(singles & tokens)
    for p in phrases:
        if p in norm:
            out.add(p)
    return out


def has_any(text, terms):
    return bool(hits(text, terms))
