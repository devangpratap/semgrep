# main.py
#
# CLI entry point for Codeseek.
# Index files, embed chunks, and search with natural language queries.

import argparse
from pathlib import Path

from indexer import build_index
from embedding import embed_chunks
from search import search, format_results


def main():
    parser = argparse.ArgumentParser(description="Codeseek - local semantic code search")
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Natural language search query",
    )
    parser.add_argument(
        "-d", "--dir",
        default=".",
        help="Root folder to scan (default: current directory)",
    )
    parser.add_argument(
        "-n", "--results",
        type=int,
        default=10,
        help="Number of results to show (default: 10)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show indexing statistics (chunk counts by file type and method)",
    )
    args = parser.parse_args()

    root = Path(args.dir).resolve()

    # Build chunk index
    print(f"Scanning: {root}")
    chunks = build_index(root)

    file_count = len({c.file_path for c in chunks})
    print(f"Files scanned: {file_count}")
    print(f"Chunks built: {len(chunks)}")

    if not chunks:
        print("No files found to index.")
        return

    if args.stats:
        print_stats(chunks)
        return

    # If no query given, enter interactive mode
    if args.query is None:
        print("\nNo query provided. Enter a query (or 'quit' to exit):\n")
        while True:
            try:
                query = input("codeseek> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye.")
                break

            if not query or query.lower() in ("quit", "exit", "q"):
                print("Bye.")
                break

            run_search(query, chunks, args.results)
    else:
        run_search(args.query, chunks, args.results)


def print_stats(chunks):
    """Show chunk breakdown by file extension and parsing method."""
    from collections import Counter

    ext_counts = Counter()
    ast_counts = Counter()
    line_counts = Counter()

    for c in chunks:
        ext = c.file_path.suffix
        ext_counts[ext] += 1
        if c.text.startswith("# ["):
            ast_counts[ext] += 1
        else:
            line_counts[ext] += 1

    print(f"\n{'Extension':<12} {'Total':<8} {'AST':<8} {'Line-based':<10}")
    print("-" * 40)
    for ext in sorted(ext_counts):
        print(f"{ext:<12} {ext_counts[ext]:<8} {ast_counts.get(ext, 0):<8} {line_counts.get(ext, 0):<10}")
    print("-" * 40)
    print(f"{'Total':<12} {sum(ext_counts.values()):<8} {sum(ast_counts.values()):<8} {sum(line_counts.values()):<10}")


def run_search(query: str, chunks, top_k: int):
    """Embed chunks, run semantic search, and display results."""
    print(f"\nEmbedding {len(chunks)} chunks...")
    embedded = embed_chunks(chunks)

    if not embedded:
        print("Failed to generate embeddings. Is Ollama running?")
        return

    print(f"Searching for: \"{query}\"\n")
    results = search(query, embedded, top_k=top_k)
    print(format_results(results))


if __name__ == "__main__":
    main()
