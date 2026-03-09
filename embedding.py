# embedding.py
#
# Generate embeddings for text chunks using a local LLM (Ollama).
# These embeddings enable semantic similarity search.
# Embeddings are cached to disk so re-runs skip already-embedded chunks.

import hashlib
import json
import requests
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from config import MODEL_NAME, DATA_DIR
from indexer import Chunk


# Ollama API endpoint for embeddings
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"

# Cache file path
CACHE_FILE = DATA_DIR / "embedding_cache.json"


def _chunk_key(text: str, model: str) -> str:
    """Stable cache key: SHA256 of text + model name."""
    return hashlib.sha256(f"{model}:{text}".encode()).hexdigest()


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")


@dataclass
class EmbeddedChunk:
    """A chunk with its embedding vector attached."""
    chunk: Chunk
    embedding: List[float]


def get_embedding(text: str, model: str = MODEL_NAME) -> Optional[List[float]]:
    """
    Get embedding vector for a piece of text using Ollama.

    Args:
        text: The text to embed.
        model: The model name to use for embeddings.

    Returns:
        A list of floats representing the embedding, or None on failure.
    """
    try:
        response = requests.post(
            OLLAMA_EMBED_URL,
            json={"model": model, "prompt": text},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("embedding")
    except requests.RequestException as e:
        print(f"[embedding] Error getting embedding: {e}")
        return None


def embed_chunks(chunks: List[Chunk], model: str = MODEL_NAME) -> List[EmbeddedChunk]:
    """
    Generate embeddings for a list of chunks, using disk cache where possible.

    Args:
        chunks: List of Chunk objects to embed.
        model: The model name to use for embeddings.

    Returns:
        List of EmbeddedChunk objects (chunks that failed are skipped).
    """
    cache = _load_cache()
    embedded: List[EmbeddedChunk] = []
    total = len(chunks)
    new_embeddings = 0

    for i, chunk in enumerate(chunks):
        key = _chunk_key(chunk.text, model)

        if key in cache:
            embedding = cache[key]
        else:
            if new_embeddings % 10 == 0:
                print(f"[embedding] Embedding chunk {i + 1}/{total}...")
            embedding = get_embedding(chunk.text, model)
            if embedding is None:
                continue
            cache[key] = embedding
            new_embeddings += 1

        embedded.append(EmbeddedChunk(chunk=chunk, embedding=embedding))

    if new_embeddings > 0:
        _save_cache(cache)
        print(f"[embedding] {new_embeddings} new embeddings saved to cache.")
    else:
        print(f"[embedding] All {total} chunks loaded from cache.")

    print(f"[embedding] Successfully embedded {len(embedded)}/{total} chunks.")
    return embedded


def embed_query(query: str, model: str = MODEL_NAME) -> Optional[List[float]]:
    """
    Generate embedding for a search query.

    Args:
        query: The search query text.
        model: The model name to use for embeddings.

    Returns:
        Embedding vector for the query, or None on failure.
    """
    return get_embedding(query, model)
