# search.py
#
# Semantic search over embedded chunks.
# Uses cosine similarity to find the most relevant code/text for a query.

import math
from typing import List, Tuple
from dataclasses import dataclass

from config import CANDIDATE_CHUNK_LIMIT
from indexer import Chunk
from embedding import EmbeddedChunk, embed_query


@dataclass
class SearchResult:
    """A search result with relevance score."""
    chunk: Chunk
    score: float  # cosine similarity (0 to 1, higher is better)


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        vec_a: First vector.
        vec_b: Second vector.

    Returns:
        Cosine similarity score between -1 and 1.
    """
    if len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def search(
    query: str,
    embedded_chunks: List[EmbeddedChunk],
    top_k: int = CANDIDATE_CHUNK_LIMIT,
) -> List[SearchResult]:
    """
    Search for chunks most semantically similar to the query.

    Args:
        query: Natural language search query.
        embedded_chunks: List of chunks with their embeddings.
        top_k: Number of top results to return.

    Returns:
        List of SearchResult objects sorted by relevance (highest first).
    """
    # Get embedding for the query
    query_embedding = embed_query(query)

    if query_embedding is None:
        print("[search] Failed to embed query.")
        return []

    # Score all chunks
    scored: List[Tuple[float, EmbeddedChunk]] = []

    for ec in embedded_chunks:
        score = cosine_similarity(query_embedding, ec.embedding)
        scored.append((score, ec))

    # Sort by score (descending) and take top_k
    scored.sort(key=lambda x: x[0], reverse=True)
    top_results = scored[:top_k]

    # Convert to SearchResult objects
    results = [
        SearchResult(chunk=ec.chunk, score=score)
        for score, ec in top_results
    ]

    return results


def format_results(results: List[SearchResult]) -> str:
    """
    Format search results for display.

    Args:
        results: List of SearchResult objects.

    Returns:
        Formatted string showing the results.
    """
    if not results:
        return "No results found."

    lines = []
    lines.append(f"Found {len(results)} relevant chunks:\n")
    lines.append("-" * 60)

    for i, result in enumerate(results, 1):
        chunk = result.chunk
        lines.append(
            f"\n[{i}] {chunk.file_path} "
            f"(lines {chunk.start_line}-{chunk.end_line}) "
            f"[score: {result.score:.4f}]"
        )
        lines.append("-" * 60)

        # Show a preview of the chunk (first 5 lines)
        preview_lines = chunk.text.split("\n")[:5]
        preview = "\n".join(preview_lines)
        if len(chunk.text.split("\n")) > 5:
            preview += "\n..."

        lines.append(preview)
        lines.append("-" * 60)

    return "\n".join(lines)
