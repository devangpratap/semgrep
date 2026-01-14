# indexer.py
#
# Walk the filesystem, filter useful files, and split them into text chunks.
# No AI here — this is just smart file parsing.

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
    Read a file, split into CHUNK_LINE_COUNT-line chunks,
    attach line numbers for better search results.
    """
    chunks: List[Chunk] = []

    try:
        # skip massive files (logs, binaries, etc.)
        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return chunks

        with path.open("r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return chunks

    if not lines:
        return chunks

    total = len(lines)
    i = 0

    while i < total:
        start = i + 1          # 1-based line numbering
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