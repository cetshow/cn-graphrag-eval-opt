# cn-graphrag-eval-opt Design

## Goal

Build a resume-ready Chinese enterprise document GraphRAG evaluation and optimization toolkit,
initialize it as a git repository, and push it to the private GitHub repository
`cetshow/cn-graphrag-eval-opt`.

## Upstream References

LightRAG contributes the retrieval architecture inspiration: local, global, hybrid, naive, and mix
query modes; a dual text-chunk plus graph retrieval shape; incremental and lightweight graph indexing
principles; and RAGAS-facing evaluation hooks. AutoRAG contributes the optimization shape: corpus plus
QA datasets, pipeline configuration search, retrieval metrics, generation metrics, result summaries,
and a deployable best pipeline artifact.

This project does not vendor upstream code. It implements a compact, dependency-light baseline and
provides adapter seams for optional `lightrag-hku`, `AutoRAG`, and `ragas` installation.

## Architecture

The first version is CLI-first. It reads Chinese Markdown/TXT enterprise documents, chunks them using
Chinese-aware strategies, builds a lightweight entity co-occurrence graph, retrieves contexts through
naive/local/global/hybrid/mix modes, evaluates against JSONL QA cases, searches a small configuration
grid, and writes Markdown/JSON reports.

The baseline avoids remote LLM calls so tests and demos are deterministic. Faithfulness and relevance
use transparent lexical proxies, while the adapter layer documents where real Ragas/LightRAG/AutoRAG
calls plug in.

## LLM Configuration

The deterministic baseline stays usable without credentials, but the product now exposes a standard
LLM configuration surface for model-backed generation and evaluator integrations. `.env.example`
documents the required variables, while `.env` is local-only and ignored by git.

The first configured provider is MiMo through its OpenAI-compatible Token Plan endpoint:

- `LLM_PROVIDER=mimo`
- `LLM_API_PROTOCOL=openai`
- `LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1`
- `LLM_MODEL=mimo-v2.5-pro`
- `ANTHROPIC_BASE_URL` is optional for the Anthropic-compatible endpoint from the same plan.

Runtime parameters include `LLM_TEMPERATURE`, `LLM_TOP_P`, `LLM_MAX_TOKENS`,
`LLM_TIMEOUT_SECONDS`, and `LLM_RETRY_COUNT`. The CLI exposes `llm-config` to print a redacted view of
the loaded configuration so developers can verify provider setup without leaking API keys.

## Components

- `models.py`: dataclasses for documents, chunks, QA cases, retrieval results, metric summaries, and
  pipeline configs.
- `chunking.py`: Chinese sentence and recursive chunk splitters with overlap.
- `corpus.py`: Markdown/TXT corpus loader and JSONL QA loader.
- `graph.py`: lightweight entity extraction and co-occurrence graph index.
- `retrieval.py`: lexical and graph-enhanced retrievers with LightRAG-style query modes.
- `evaluation.py`: Ragas-style deterministic retrieval/generation proxy metrics.
- `llm.py`: `.env` loader and OpenAI-compatible LLM runtime configuration.
- `optimization.py`: AutoRAG-style pipeline grid runner and best-config selector.
- `reporting.py`: JSON and Markdown report writer.
- `adapters.py`: optional integration descriptors for LightRAG, AutoRAG, and Ragas.
- `cli.py`: `ingest`, `evaluate`, `optimize`, `query`, `integrations`, and `llm-config` commands.

## Data Flow

Documents are loaded from a folder, split into chunks, indexed into a graph, and queried for each QA
case. Each trial produces contexts and a simple extractive answer. Metrics are computed per case and
aggregated per pipeline config. The optimizer ranks trials by retrieval recall, faithfulness, answer
relevance, context precision, and lower estimated token cost.

## Error Handling

The CLI validates missing corpus paths, empty corpora, malformed QA JSONL rows, invalid query modes,
and impossible chunk settings. Reports still include failed trial metadata when a pipeline config is
invalid.

## Testing

Unit tests cover Chinese chunking, corpus/QA loading, graph retrieval mode differences, Ragas-style
metrics, AutoRAG-style optimization ranking, report generation, and the CLI demo path. Tests use only
the standard library so the repository remains runnable before optional integrations are installed.
