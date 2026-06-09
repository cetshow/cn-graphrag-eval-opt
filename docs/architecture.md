# Architecture

`cn-graphrag-eval-opt` is organized as a small but complete RAG experiment system.

## Workflow

```mermaid
flowchart LR
    A["Chinese enterprise documents"] --> B["Corpus loader"]
    B --> C["Chinese chunker"]
    C --> D["Entity graph index"]
    D --> E["GraphRAG retriever"]
    E --> K["MiMo grounded answerer"]
    E --> F["RAG evaluator"]
    F --> G["Pipeline optimizer"]
    G --> H["Trial artifacts"]
    H --> J["Quality gate"]
    K --> I["Query service"]
```

## Design References

- GraphRAG: explicit project initialization, indexing, querying, and responsible artifact production.
- LightRAG: lightweight graph retrieval modes for local/global/hybrid reasoning.
- AutoRAG: trial-oriented configuration search and leaderboard output.
- Ragas: metric vocabulary for judging context and answer quality.
- DeepEval: CI-friendly quality gates for retrieval and answer regressions.
- MiMo: OpenAI-compatible chat completions for grounded Chinese enterprise answers.
- R2R: query responses include context traces rather than only generated text.

## Extension Points

- Replace lexical retrieval with dense embeddings or BM25 in `retrieval.py`.
- Persist indexes to SQLite, NetworkX, Neo4j, Qdrant, or another store behind `GraphIndex`.
- Extend the MiMo answerer with streaming output and structured response parsing.
- Swap proxy metrics for Ragas model-backed metrics when credentials are available.
- Tune `quality-gate` thresholds as the corpus and QA benchmark grow.
- Expose `QueryService` through FastAPI for a production-style HTTP surface.
