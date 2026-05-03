# indexer.py
#
# Walk the filesystem, filter useful files, and split them into text chunks.
# Uses AST-based parsing for supported languages, falls back to line-based chunking.

import os
from pathlib import Path
from dataclasses import dataclass
from typing import List

from config import (
    DEFAULT_ROOT_DIR,
    ALLOWED_EXTENSIONS,
    IGNORE_DIRS,
    MAX_FILE_SIZE_BYTES,
    CHUNK_LINE_COUNT,
    AST_ENABLED,
    AST_EXTENSIONS,
)


# A chunk of text from a file (with line numbers)
@dataclass
class Chunk:
    file_path: Path
    start_line: int
    end_line: int
    text: str


def iter_files(root: Path | None = None):
    """
    Yield all file paths under `root` that:
    - have allowed extensions
    - are not inside ignored directories
    """
    if root is None:
        root = DEFAULT_ROOT_DIR

    root = Path(root).resolve()

    for dirpath, dirnames, filenames in os.walk(root):
        # prevent scanning useless dirs
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        for fname in filenames:
            path = Path(dirpath) / fname

            if path.suffix in ALLOWED_EXTENSIONS:
                yield path


def read_file_chunks(path: Path) -> List[Chunk]:
    """
    Read a file and split into chunks.
    Uses AST-based parsing for supported languages if enabled,
    falls back to line-based chunking otherwise.
    """
    chunks: List[Chunk] = []

    try:
        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return chunks

        with path.open("r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception:
        return chunks

    if not source.strip():
        return chunks

    # Try AST-based chunking for supported file types
    if AST_ENABLED and path.suffix in AST_EXTENSIONS:
        ast_chunks = _try_ast_chunking(path, source)
        if ast_chunks:
            return ast_chunks

    # Fallback: line-based chunking
    return _line_based_chunking(path, source)


def _try_ast_chunking(path: Path, source: str) -> List[Chunk]:
    """Attempt AST-based chunking. Returns empty list on failure."""
    if path.suffix == ".py":
        from ast_parser import parse_python_file, extract_top_level_code

        chunks = []

        # Get function/class chunks
        ast_chunks = parse_python_file(path, source)
        if ast_chunks:
            chunks.extend(ast_chunks)

        # Get module-level code (imports, constants, etc.)
        top_level = extract_top_level_code(path, source)
        if top_level:
            chunks.append(top_level)

        return chunks

    return []


def _line_based_chunking(path: Path, source: str) -> List[Chunk]:
    """Original line-based chunking as fallback."""
    chunks: List[Chunk] = []
    lines = source.splitlines(keepends=True)
    total = len(lines)
    i = 0

    while i < total:
        start = i + 1
        end_index = min(i + CHUNK_LINE_COUNT, total)
        end = end_index

        chunk_text = "".join(lines[i:end_index])

        chunks.append(
            Chunk(
                file_path=path,
                start_line=start,
                end_line=end,
                text=chunk_text,
            )
        )

        i = end_index

    return chunks


def build_index(root: Path | None = None) -> List[Chunk]:
    """
    Build the full chunk index for all allowed files.
    Returns a list of Chunk objects.
    """
    index: List[Chunk] = []

    for file_path in iter_files(root):
        index.extend(read_file_chunks(file_path))

    return index