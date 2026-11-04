"""Semantic search and ranking over the HackerTube corpus.

Retrieval: embed the query (and any alternative phrasings) with the same model HackerTube used
(bge-small-en-v1.5, no prefix), take the top candidates by cosine similarity, optionally mix in a
cross-encoder score, then let HackerTube's quality score (distinct months HN recommended the video)
scale relevance. Quality only reorders relevant hits; it can't lift an off-topic classic to the top.

The cross-encoder is off by default: on situation-style queries ("I'm becoming a manager") it
scores everything near zero, while plain embeddings hold up and answer in a few ms.
"""

from __future__ import annotations

import math
import os
import re
from typing import Iterable

import numpy as np

from .data import Corpus

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
RERANK_MODEL = "jinaai/jina-reranker-v1-turbo-en"
STANCE_ORDER = {"strong_rec": 0, "rec": 1, "reference": 2, "critical": 3, "joke": 4}


def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _doc_text(v: dict) -> str:
    tags = ", ".join([v.get("primary_topic") or ""] + (v.get("tags") or []))
    return f"{v['title']} ({v['channel']}). {v.get('summary', '')} {v.get('why_hn', '')} Topics: {tags}"


class Index:
    def __init__(self, corpus: Corpus, rerank: bool | None = None):
        self.c = corpus
        if rerank is None:
            rerank = os.environ.get("HACKERTUBE_RERANK", "0") == "1"
        self.use_rerank = rerank
        self._embedder = None
        self._reranker = None
        self._max_q = math.log1p(max(v["score"] for v in corpus.videos))
        self._titles = [_norm_title(v["title"]) for v in corpus.videos]

    # Models load lazily so the MCP handshake is instant; first query pays a one-off download.
    def _embed(self, texts: list[str]) -> np.ndarray:
        if self._embedder is None:
            from fastembed import TextEmbedding

            self._embedder = TextEmbedding(EMBED_MODEL)
        q = np.stack(list(self._embedder.embed(texts))).astype(np.float32)
        return q / (np.linalg.norm(q, axis=1, keepdims=True) + 1e-12)

    def _rerank(self, query: str, docs: list[str]) -> list[float]:
        if self._reranker is None:
            from fastembed.rerank.cross_encoder import TextCrossEncoder

            self._reranker = TextCrossEncoder(RERANK_MODEL)
        return [float(s) for s in self._reranker.rerank(query, docs)]

    def quality(self, v: dict) -> float:
        """HackerTube score squashed to [0, 1]."""
        return math.log1p(v["score"]) / self._max_q

    def mask(
        self,
        *,
        levels: Iterable[str] | None = None,
        content_types: Iterable[str] | None = None,
        topic: str | None = None,
        include_news: bool = False,
        recommended_only: bool = True,
    ) -> np.ndarray:
        levels = set(levels or [])
        content_types = set(content_types or [])
        out = np.ones(len(self.c.videos), dtype=bool)
        for i, v in enumerate(self.c.videos):
            if levels and v["level"] not in levels:
                out[i] = False
            elif content_types and v["content_type"] not in content_types:
                out[i] = False
            elif not include_news and v["shelf_life"] == "news":
                out[i] = False
            elif recommended_only and v["hn"]["recommenders"] == 0:
                out[i] = False
            elif topic and not any(topic in (c["id"], c["area"]) for c in v["categories"]):
                out[i] = False
        return out

    def _dedupe(self, rows: list[int], k: int, skip: set[str] = frozenset()) -> list[int]:
        seen, out = set(skip), []
        for i in rows:
            t = self._titles[i]
            if t in seen:
                continue
            seen.add(t)
            out.append(i)
            if len(out) == k:
                break
        return out

    def search(
        self,
        query: str | list[str],
        k: int = 5,
        quality_weight: float = 0.3,
        candidates: int = 40,
        **filters,
    ) -> list[tuple[dict, float, float]]:
        """Return [(video, final_score, relevance)] best first. Relevance is in [0, 1].

        `query` may be several phrasings of the same need. A video scores the average of its best
        and its mean similarity across them: pure max let one stray phrasing ("...B-trees and LSM
        trees") pull in off-topic hits (tree-sitter, APL trees) that fit nothing else asked.
        """
        queries = [query] if isinstance(query, str) else [q for q in query if q.strip()]
        allowed = self.mask(**filters)
        if not queries or not allowed.any():
            return []
        per_query = self.c.embeddings @ self._embed(queries).T
        sims = 0.5 * per_query.max(axis=1) + 0.5 * per_query.mean(axis=1)
        sims[~allowed] = -np.inf
        n = min(candidates, int(allowed.sum()))
        cand = np.argpartition(-sims, n - 1)[:n]

        # bge-small cosines: off-topic ~0.5, on-topic roughly 0.6-0.9
        rel = [float(np.clip((sims[i] - 0.5) / 0.4, 0, 1)) for i in cand]
        if self.use_rerank:
            raw = self._rerank(queries[0], [_doc_text(self.c.videos[i]) for i in cand])
            rel = [(r + _sigmoid(s)) / 2 for r, s in zip(rel, raw)]

        scored = sorted(
            (
                (r * (1 - quality_weight + quality_weight * self.quality(self.c.videos[i])), r, i)
                for r, i in zip(rel, cand)
            ),
            reverse=True,
        )
        by_row = {i: (f, r) for f, r, i in scored}
        keep = self._dedupe([i for _, _, i in scored], k)
        return [(self.c.videos[i], by_row[i][0], by_row[i][1]) for i in keep]

    def similar(self, vid: str, k: int = 5) -> list[tuple[dict, float]]:
        """Nearest neighbours by content embedding, excluding the video itself and re-uploads."""
        i = self.c.row[vid]
        sims = self.c.embeddings @ self.c.embeddings[i]
        order = [int(j) for j in np.argsort(-sims) if j != i]
        keep = self._dedupe(order, k, skip={self._titles[i]})
        return [(self.c.videos[j], float(sims[j])) for j in keep]

    def top_in_topic(self, topic: str, k: int = 10, **filters) -> list[dict]:
        allowed = self.mask(topic=topic, **filters)
        rows = [i for i in range(len(self.c.videos)) if allowed[i]]  # videos are best-scored first
        return [self.c.videos[i] for i in self._dedupe(rows, k)]

    def hn_comments(self, vid: str) -> list[dict]:
        return sorted(
            self.c.mentions.get(vid, []),
            key=lambda m: (STANCE_ORDER.get(m["stance"], 9), m["month"]),
        )
