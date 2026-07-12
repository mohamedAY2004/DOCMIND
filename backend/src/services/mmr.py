"""Maximal Marginal Relevance selection over retrieved chunks (pure numpy).

Runs between the vector over-fetch and the cross-encoder rerank stage: at that
point both the relevance term (candidate-to-query) and the diversity term
(candidate-to-candidate) are cosine similarities in the same embedding space,
so no score calibration is needed. ``lambda_mult=1.0`` is pure relevance
(vector order); ~0.7 keeps the ordering relevance-heavy while pruning
near-duplicate chunks.

Deliberately a plain function rather than a ``stores/`` provider: MMR is one
algorithm, not a swappable backend.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np


def mmr_select(
    query_vector: Sequence[float],
    candidates: Sequence,
    *,
    k: int,
    lambda_mult: float = 0.7,
) -> list:
    """Greedily select ``k`` candidates balancing relevance and diversity.

    ``candidates`` are ``RetrievedChunk``-like objects sorted by vector score;
    their ``embedding`` attribute must be populated (search with
    ``with_vectors=True``). If any candidate lacks an embedding the whole
    selection soft-degrades to ``candidates[:k]`` — a partial skip would
    silently drop possibly-relevant chunks and produce a confusing hybrid
    ordering, so it is all-or-nothing.
    """
    if k <= 0 or not candidates:
        return []
    if len(candidates) <= k:
        return list(candidates)  # nothing to prune; keep vector order

    embeddings = [getattr(c, "embedding", None) for c in candidates]
    if any(e is None or len(e) == 0 for e in embeddings):
        return list(candidates)[:k]  # vectors unavailable

    V = np.asarray(embeddings, dtype=np.float32)  # (n, d)
    q = np.asarray(query_vector, dtype=np.float32)  # (d,)
    # Row-normalise; zero-norm vectors get norm 1 so their cosine sims are 0.
    norms = np.linalg.norm(V, axis=1)
    norms[norms == 0.0] = 1.0
    Vn = V / norms[:, None]
    qn = q / (np.linalg.norm(q) or 1.0)

    relevance = Vn @ qn  # (n,) cosine similarity to the query
    # Ties resolve to the lower index (better vector rank) via argmax.
    selected = [int(np.argmax(relevance))]
    remaining = [i for i in range(len(candidates)) if i != selected[0]]
    while remaining and len(selected) < k:
        # Max cosine of each remaining candidate to anything already selected.
        max_sim = (Vn[remaining] @ Vn[selected].T).max(axis=1)
        mmr = lambda_mult * relevance[remaining] - (1.0 - lambda_mult) * max_sim
        best = int(np.argmax(mmr))
        selected.append(remaining.pop(best))
    return [candidates[i] for i in selected]
