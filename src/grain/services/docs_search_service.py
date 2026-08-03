# SPDX-FileCopyrightText: 2024-2026 Shaznay Sison
# SPDX-License-Identifier: MIT

"""Docs search — fast, stdlib-only text search across the registry corpus.

Searches title + headings + body across the repo corpus and any registered
external roots (``docs_registry.external_roots`` in the manifest, or explicit
``extra_roots``), so one query can span several repos' documentation. Ranking
is deliberately simple and dependency-free: weighted term frequency (title >
headings > body). No embeddings — the manifest's ``embedding_provider: none``
default path stays the default path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_TITLE_WEIGHT = 10
_HEADING_WEIGHT = 4
_BODY_WEIGHT = 1


@dataclass
class SearchHit:
    rel_path: str
    root_name: str      # "" for the primary repo
    abs_path: Path
    title: str
    score: int
    snippet: str


def _tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def _count_terms(terms: list[str], text_lower: str) -> int:
    return sum(text_lower.count(term) for term in terms)


def search_corpus(
    root: Path,
    query: str,
    extra_roots: list[tuple[str, Path]] | None = None,
    limit: int = 10,
) -> list[SearchHit]:
    """Rank corpus docs against ``query`` and return the top ``limit`` hits."""
    from grain.adapters.manifest import load_manifest
    from grain.services.docs_corpus import external_roots_from_manifest, load_corpus

    try:
        manifest = load_manifest(root)
    except Exception:
        manifest = {}

    roots = external_roots_from_manifest(root, manifest)
    for name, path in extra_roots or []:
        if (name, path) not in roots:
            roots.append((name, path))

    corpus = load_corpus(root, manifest=manifest, external_roots=roots, use_cache=True)
    terms = _tokens(query)
    if not terms:
        return []

    hits: list[SearchHit] = []
    for doc in corpus:
        title_score = _count_terms(terms, doc.title.lower()) * _TITLE_WEIGHT
        heading_score = (
            _count_terms(terms, " ".join(doc.headings).lower()) * _HEADING_WEIGHT
        )
        body = doc.body()
        body_lower = body.lower()
        body_score = _count_terms(terms, body_lower) * _BODY_WEIGHT
        score = title_score + heading_score + body_score
        if score <= 0:
            continue
        hits.append(SearchHit(
            rel_path=doc.rel_path,
            root_name=doc.root_name,
            abs_path=doc.abs_path,
            title=doc.title,
            score=score,
            snippet=_snippet(body, terms),
        ))

    hits.sort(key=lambda h: (-h.score, h.root_name, h.rel_path))
    return hits[: max(limit, 0)]


def _snippet(body: str, terms: list[str]) -> str:
    """First non-heading line containing a query term, trimmed."""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lower = stripped.lower()
        if any(term in lower for term in terms):
            return stripped[:160]
    return ""
