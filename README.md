# Semantic Grep

A local semantic search tool for your codebase. Instead of matching exact strings like regular grep, this uses a locally running LLM (Ollama with llama3.2) to understand what you mean and find relevant code/text.

## How it works

1. **Indexer** scans your project files and splits them into chunks
2. **Embedding** generates vector embeddings for each chunk using Ollama
3. **Search** compares your natural language query against all chunks using cosine similarity and returns the best matches

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed and running (`ollama serve`)
- llama3.2 model pulled (`ollama pull llama3.2`)
- `requests` library (`pip install requests`)

## Usage

Search with a query directly:

```
python main.py "find the database connection logic" -d /path/to/project
```

Or run in interactive mode (no query argument):

```
python main.py -d /path/to/project
```

### Options

- `query` — natural language search query (optional, starts interactive mode if omitted)
- `-d, --dir` — root directory to scan (default: current directory)
- `-n, --results` — number of results to show (default: 10)

## Project structure

- `config.py` — settings (model name, allowed file types, chunk size, etc.)
- `indexer.py` — file walking and chunking
- `embedding.py` — Ollama embedding generation
- `search.py` — cosine similarity search and result formatting
- `main.py` — CLI entry point
