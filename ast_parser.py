# ast_parser.py
#
# AST-based chunking for Python files.
# Extracts functions, classes, and methods as semantically meaningful chunks
# instead of splitting code into arbitrary line blocks.

import ast
from pathlib import Path
from typing import List, Optional

from indexer import Chunk


def parse_python_file(path: Path, source: str) -> Optional[List[Chunk]]:
    """
    Parse a Python file into AST-based chunks.
    Each function, method, and class becomes its own chunk.

    Returns None if parsing fails (syntax error, etc.)
    """
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return None

    chunks: List[Chunk] = []
    lines = source.splitlines(keepends=True)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start_line = node.lineno
            end_line = _get_end_line(node, lines)

            # Build chunk text from the source lines
            chunk_text = "".join(lines[start_line - 1 : end_line])

            # Add context: prepend the symbol name and type for better embeddings
            node_type = "class" if isinstance(node, ast.ClassDef) else "function"
            context_prefix = f"# [{node_type}] {node.name}\n"

            chunks.append(
                Chunk(
                    file_path=path,
                    start_line=start_line,
                    end_line=end_line,
                    text=context_prefix + chunk_text,
                )
            )

    return chunks if chunks else None


def _get_end_line(node: ast.AST, lines: List[str]) -> int:
    """
    Get the last line of an AST node.
    Uses end_lineno if available (Python 3.8+), otherwise walks children.
    """
    if hasattr(node, "end_lineno") and node.end_lineno is not None:
        return node.end_lineno

    # Fallback: find the max line number among all child nodes
    max_line = node.lineno
    for child in ast.walk(node):
        if hasattr(child, "lineno") and child.lineno:
            max_line = max(max_line, child.lineno)

    return max_line


def extract_top_level_code(path: Path, source: str) -> Optional[Chunk]:
    """
    Extract module-level code that isn't inside any function or class.
    This includes imports, constants, and top-level statements.
    """
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return None

    lines = source.splitlines(keepends=True)
    total_lines = len(lines)

    # Find all line ranges occupied by functions/classes
    occupied = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno
            end = _get_end_line(node, lines)
            for ln in range(start, end + 1):
                occupied.add(ln)

    # Collect non-occupied lines
    top_level_lines = []
    for i in range(1, total_lines + 1):
        if i not in occupied:
            top_level_lines.append(lines[i - 1])

    text = "".join(top_level_lines).strip()

    if not text:
        return None

    return Chunk(
        file_path=path,
        start_line=1,
        end_line=total_lines,
        text=f"# [module-level] {path.name}\n{text}",
    )
