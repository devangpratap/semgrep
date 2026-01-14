# config.py
#
# Global settings for the Semantic Grep Engine.

from pathlib import Path

# ---- Model / AI backend ----

# Default local model name (for Ollama or similar).
MODEL_NAME = "llama3.2"

# ---- File system / indexing settings ----

# Default root directory to search.
# By default: the current working directory when you run the tool.
DEFAULT_ROOT_DIR = Path(".")

# File extensions we will scan.
ALLOWED_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".java",
    ".sql",
    ".json",
}

# Directories to ignore while walking the filesystem.
IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
}

# Maximum file size (in bytes) to read.
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

# How many lines to group into one chunk.
CHUNK_LINE_COUNT = 40

# How many top chunks to keep before sending anything to the LLM.
CANDIDATE_CHUNK_LIMIT = 20

# Where to store any cached index/embeddings (later if we want).
DATA_DIR = Path("data")