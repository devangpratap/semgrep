# embedding.py
#
# Generate embeddings for text chunks using a local LLM (Ollama).
# These embeddings enable semantic similarity search.

import json
import requests
from typing import List, Optional
from dataclasses import dataclass

from config import MODEL_NAME
from indexer import Chunk


# Ollama API endpoint for embeddings
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"


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
    Generate embeddings for a list of chunks.

    Args:
        chunks: List of Chunk objects to embed.
        model: The model name to use for embeddings.

    Returns:
        List of EmbeddedChunk objects (chunks that failed are skipped).
    """
    embedded: List[EmbeddedChunk] = []
    total = len(chunks)

    for i, chunk in enumerate(chunks):
        # Progress indicator
        if (i + 1) % 10 == 0 or i == 0:
            print(f"[embedding] Processing chunk {i + 1}/{total}...")

        embedding = get_embedding(chunk.text, model)

        if embedding is not None:
            embedded.append(EmbeddedChunk(chunk=chunk, embedding=embedding))

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
