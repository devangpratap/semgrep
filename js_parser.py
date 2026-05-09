# js_parser.py
#
# Regex-based chunking for JavaScript/TypeScript files.
# Extracts functions, classes, and arrow functions as semantic chunks.
# Not a full AST parser — uses pattern matching for speed and zero dependencies.

import re
from pathlib import Path
from typing import List, Optional

from indexer import Chunk

# Patterns for JS/TS constructs
PATTERNS = [
    # class declarations
    re.compile(r"^(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+(\w+)", re.MULTILINE),
    # named function declarations
    re.compile(r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)", re.MULTILINE),
    # arrow / const functions: const foo = (...) => or const foo = function
    re.compile(r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[a-zA-Z_]\w*)\s*=>", re.MULTILINE),
    re.compile(r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function", re.MULTILINE),
]


def parse_js_file(path: Path, source: str) -> Optional[List[Chunk]]:
    """
    Parse a JS/TS file into chunks based on top-level declarations.
    Each function or class becomes its own chunk.

    Returns None if no declarations are found.
    """
    lines = source.splitlines(keepends=True)
    total_lines = len(lines)

    # Find all declaration start positions
    declarations = []
    for pattern in PATTERNS:
        for match in pattern.finditer(source):
            line_no = source[:match.start()].count("\n") + 1
            name = match.group(1)
            declarations.append((line_no, name))

    if not declarations:
        return None

    # Sort by line number
    declarations.sort(key=lambda x: x[0])

    # Deduplicate overlapping matches at the same line
    seen_lines = set()
    unique = []
    for line_no, name in declarations:
        if line_no not in seen_lines:
            seen_lines.add(line_no)
            unique.append((line_no, name))
    declarations = unique

    chunks: List[Chunk] = []

    for i, (start_line, name) in enumerate(declarations):
        # End line is either the line before the next declaration or EOF
        if i + 1 < len(declarations):
            end_line = declarations[i + 1][0] - 1
            # Trim trailing blank lines between declarations
            while end_line > start_line and not lines[end_line - 1].strip():
                end_line -= 1
        else:
            end_line = total_lines

        chunk_text = "".join(lines[start_line - 1 : end_line])

        # Determine node type
        first_line = lines[start_line - 1].strip()
        if "class " in first_line:
            node_type = "class"
        else:
            node_type = "function"

        context_prefix = f"# [{node_type}] {name}\n"

        chunks.append(
            Chunk(
                file_path=path,
                start_line=start_line,
                end_line=end_line,
                text=context_prefix + chunk_text,
            )
        )

    return chunks if chunks else None


def extract_js_top_level(path: Path, source: str) -> Optional[Chunk]:
    """
    Extract top-level code (imports, constants) that isn't inside
    any detected function or class declaration.
    """
    lines = source.splitlines(keepends=True)
    total_lines = len(lines)

    # Find occupied line ranges
    occupied = set()
    for pattern in PATTERNS:
        for match in pattern.finditer(source):
            start = source[:match.start()].count("\n") + 1
            occupied.add(start)

    # Build declaration ranges (same logic as parse_js_file)
    declarations = []
    for pattern in PATTERNS:
        for match in pattern.finditer(source):
            line_no = source[:match.start()].count("\n") + 1
            declarations.append(line_no)

    declarations = sorted(set(declarations))

    occupied_lines = set()
    for i, start in enumerate(declarations):
        if i + 1 < len(declarations):
            end = declarations[i + 1] - 1
        else:
            end = total_lines
        for ln in range(start, end + 1):
            occupied_lines.add(ln)

    # Collect non-occupied lines
    top_level = []
    for i in range(1, total_lines + 1):
        if i not in occupied_lines:
            top_level.append(lines[i - 1])

    text = "".join(top_level).strip()
    if not text:
        return None

    return Chunk(
        file_path=path,
        start_line=1,
        end_line=total_lines,
        text=f"# [module-level] {path.name}\n{text}",
    )
