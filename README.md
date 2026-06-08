# cn-graphrag-eval-opt

Chinese enterprise document GraphRAG retrieval evaluation and optimization toolkit.

This repository is a practical second-stage RAG project inspired by the architecture patterns of:

- [Microsoft GraphRAG](https://github.com/microsoft/graphrag): config-driven indexing and query workflows.
- [HKUDS LightRAG](https://github.com/HKUDS/LightRAG): lightweight graph-enhanced local/global/hybrid query modes.
- [AutoRAG](https://github.com/Marker-Inc-Korea/AutoRAG): corpus + QA driven pipeline search and leaderboard artifacts.
- [Ragas](https://github.com/vibrantlabsai/ragas): retrieval and generation quality metrics such as context precision, answer relevance, and faithfulness.
- [R2R](https://github.com/SciPhi-AI/R2R): production-facing query service shape with context traces.

The code in this repository is original and dependency-light. It does not vendor upstream project code.
Optional adapters show where `lightrag-hku`, `AutoRAG`, and `ragas` can be connected when those packages
and model credentials are available.

## What It Builds

`cn-graphrag-eval-opt` turns a folder of Chinese enterprise Markdown/TXT documents into a reproducible
GraphRAG experiment:

1. Load and manifest enterprise documents.
2. Split Chinese text into traceable chunks.
3. Build a lightweight entity co-occurrence graph.
4. Retrieve with LightRAG-style `naive`, `local`, `global`, `hybrid`, and `mix` modes.
5. Evaluate with deterministic Ragas-style proxy metrics.
6. Search multiple pipeline configurations.
7. Write an AutoRAG-style trial folder with indexes, case results, leaderboard, best config, and reports.
8. Serve traced query responses through a small Python service facade.

## Repository Layout

```text
cn-graphrag-eval-opt/
  configs/default.toml                 # Config-driven experiment grid
  examples/corpus/                     # Small Chinese enterprise corpus
  examples/qa.jsonl                    # Seed QA benchmark
  src/cn_graphrag_eval_opt/
    config.py                          # Project config model
    corpus.py                          # Corpus and QA loaders
    datasets.py                        # Bootstrap QA builder
    chunking.py                        # Chinese-aware chunking
    graph.py                           # Entity graph index
    retrieval.py                       # GraphRAG retriever
    evaluation.py                      # RAG metrics and answer synthesis
    optimization.py                    # Pipeline search
    pipeline.py                        # Ingest -> index -> evaluate orchestration
    reporting.py                       # Trial artifact writers
    service.py                         # Query service facade
    adapters.py                        # Optional upstream integration descriptors
    cli.py                             # Developer CLI
  tests/                               # Unit and integration tests
```

## Quickstart

```bash
git clone https://github.com/cetshow/cn-graphrag-eval-opt.git
cd cn-graphrag-eval-opt
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

Run the default GraphRAG optimization:

```bash
python -m cn_graphrag_eval_opt optimize --config configs/default.toml
```

The trial folder contains:

```text
runs/demo/
  inputs/corpus_manifest.json
  index/chunks.jsonl
  index/entities.json
  evaluations/case_results.jsonl
  leaderboard.csv
  summary.json
  best_config.json
  reports/report.md
```

Run a traced query:

```bash
python -m cn_graphrag_eval_opt query "哪个部门每月复核高危权限？" --corpus examples/corpus --query-mode mix
```

Build a bootstrap QA set from your own corpus:

```bash
python -m cn_graphrag_eval_opt dataset build --corpus path/to/corpus --out data/qa.bootstrap.jsonl
```

Create a starter config:

```bash
python -m cn_graphrag_eval_opt init --out graphrag.toml
```

## Configuration

The default experiment grid lives in `configs/default.toml`:

```toml
[corpus]
corpus_path = "examples/corpus"
qa_path = "examples/qa.jsonl"
out_dir = "runs/demo"

[[optimization.configs]]
query_mode = "mix"
chunk_size = 192
overlap = 24
top_k = 4
```

Use this to compare chunk sizes, overlaps, top-k values, and query modes against the same QA set.

## Evaluation Metrics

The baseline metrics are deterministic so CI and local demos do not need external LLM credentials:

- `retrieval_recall`: required-term or gold-context coverage.
- `context_precision`: fraction of retrieved contexts containing expected evidence.
- `answer_relevance`: lexical overlap between expected and generated answer.
- `faithfulness`: generated answer terms supported by retrieved contexts.
- `estimated_token_cost`: rough context cost proxy for comparing retrieval breadth.

When `ragas` is installed, the adapter layer maps these names to Ragas concepts:
`context_recall`, `context_precision`, `answer_relevancy`, and `faithfulness`.

## Development

```bash
python -m unittest discover -s tests
python -m cn_graphrag_eval_opt integrations
python -m cn_graphrag_eval_opt optimize --config configs/default.toml
```

Optional integrations:

```bash
python -m pip install -e ".[integrations]"
```

The project is intentionally usable without optional integrations. That makes the evaluation pipeline
reproducible in CI and on machines without GPU/model credentials.

## Resume Framing

> Built a Chinese enterprise document GraphRAG evaluation and optimization toolkit inspired by LightRAG,
> Microsoft GraphRAG, AutoRAG, and Ragas. Implemented config-driven indexing, graph-enhanced retrieval,
> pipeline search, RAG metric evaluation, traceable query service, and reproducible experiment artifacts
> including corpus manifests, chunk indexes, entity graphs, case-level metrics, leaderboards, and reports.

## License

MIT. See [LICENSE](LICENSE).
