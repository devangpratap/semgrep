# main.py
#
# Minimal CLI to test the indexer.

import argparse
from pathlib import Path

from indexer import build_index


def main():
    parser = argparse.ArgumentParser(description="Semantic Grep (local) - MVP")
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Root folder to scan (default: current directory)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    chunks = build_index(root)

    # quick summary output
    file_count = len({c.file_path for c in chunks})
    print(f"Root: {root}")
    print(f"Files scanned: {file_count}")
    print(f"Chunks built: {len(chunks)}")

    # show a small preview to know it's real
    if chunks:
        c = chunks[0]
        print("\n--- Preview (first chunk) ---")
        print(f"{c.file_path}  (lines {c.start_line}-{c.end_line})")
        print(c.text[:500])


if __name__ == "__main__":
    main()