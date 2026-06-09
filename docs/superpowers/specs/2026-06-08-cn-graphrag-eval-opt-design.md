# cn-graphrag-eval-opt Competitive Design

## Goal

Build `cn-graphrag-eval-opt` into a resume-ready Chinese enterprise GraphRAG evaluation and
optimization project. The repository should look and behave like a real developer tool: config-driven,
testable, extensible, reproducible, and easy to discuss in interviews.

The project is inspired by high-quality public RAG repositories, but it must not become a copy-paste
fork. The upgrade strategy is to reuse proven architecture patterns, create original implementation
code, keep optional adapters for upstream ecosystems, and document license-sensitive boundaries.

## Source Audit Status

CodeGraph has been initialized and used for the source audit. The indexed baseline contains 23 files,
265 nodes, and 530 edges across the Python package, tests, and CI workflow. CodeGraph was used to read
the project structure and the main CLI -> pipeline -> chunk/index/retrieve/evaluate/report flow, plus
the supporting config, chunking, dataset, embedding, text, adapter, reporting, storage, and test code.

CodeGraph findings:

- `GraphRAGPipeline.run_optimization()` loads corpus and QA data, runs the optimizer, reevaluates the
  best config, and writes trial artifacts.
- `evaluate_cases()` is a central dependency used by CLI evaluation, optimization, pipeline execution,
  and tests.
- `write_trial_artifacts()` is the artifact boundary for reproducibility and should stay heavily
  covered by integration tests.
- `load_project_config()`, `build_synthetic_qa()`, and `optional_integrations()` are important CLI
  entry dependencies; provider and connector PRs should add direct coverage around them.

Current implemented surface:

- CLI commands for `init`, `dataset build`, `ingest`, `evaluate`, `optimize`, `query`, and
  `integrations`.
- Config-driven experiment grid in `configs/default.toml`.
- Chinese-aware chunking, connector-backed corpus loading, bootstrap QA generation, hashing
  embeddings, entity graph indexing, RRF retrieval fusion, deterministic metric evaluation,
  optimization ranking, report writing, persistent JSONL index storage, evaluator data adapters,
  API-ready query response models, and a query service facade.
- Provider registry metadata for local baseline, LightRAG, AutoRAG, Ragas, DeepEval, and Neo4j
  integration paths.
- Tests for chunking, pipeline behavior, provider metadata, retriever fusion, stores, evaluator
  adapters, corpus connectors, service responses, documentation quality, and LLM config loading.
- Documentation for architecture, references, README quickstart, CI, and resume framing.

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

Main remaining gaps:

- Model-backed generation and real Ragas/DeepEval scoring are not enabled by default because the
  baseline must stay CI-safe without credentials.
- Dataset and connector support is still intentionally small; HTML/PDF/web connectors remain future
  extension points.
- Query service is an API-ready Python facade, not a FastAPI/HTTP service.
- Incremental indexing and external graph/vector stores are designed as extension points, not yet
  production services.

## Competitive Reference Projects

| Project | What It Does Well | Ideas To Adapt |
| --- | --- | --- |
| [Microsoft GraphRAG](https://github.com/microsoft/graphrag) | End-to-end indexing/query workflow, config-first project setup, persistent artifacts, prompt and graph indexing discipline. | Keep `init/index/query` mental model, artifact tree, explicit config validation, and cost-aware warnings. |
| [HKUDS LightRAG](https://github.com/HKUDS/LightRAG) | Lightweight graph + vector retrieval, local/global/hybrid/mix query modes, incremental update orientation. | Formalize local/global/mix retrieval, add clearer trace evidence, and support incremental index updates. |
| [AutoRAG](https://github.com/Marker-Inc-Korea/AutoRAG) | Corpus + QA driven optimization, configurable module search, trial folders, leaderboards, deployable best pipeline. | Expand optimizer into repeatable experiment runs with comparable trials, best-config export, and module registry. |
| [Ragas](https://github.com/vibrantlabsai/ragas) | RAG metric vocabulary and LLM-judged evaluation concepts. | Keep deterministic CI metrics while adding an optional adapter that maps local case data into Ragas datasets. |
| [DeepEval](https://github.com/confident-ai/deepeval) | Test-style evaluation for LLM/RAG systems and CI-friendly quality gates. | Add threshold gates so retrieval/evaluation regressions can fail CI intentionally. |
| [Neo4j GraphRAG Python](https://github.com/neo4j/neo4j-graphrag-python) | Production graph database integration, retrievers, vector search, and graph-backed retrieval patterns. | Design graph store interfaces so the current in-memory graph can later swap to Neo4j without changing callers. |
| [Haystack](https://github.com/deepset-ai/haystack) | Component pipeline model, retrievers/readers/generators, production RAG framework conventions. | Add provider interfaces and small component contracts before adding large optional dependencies. |
| [Pathway](https://github.com/pathwaycom/pathway) | Streaming/incremental data processing and live document indexing patterns. | Leave connector and incremental ingest seams for future document update workflows. |
| [R2R](https://github.com/SciPhi-AI/R2R) | Production-facing RAG service shape, context traces, and application integration mindset. | Turn the query facade into a traced API-ready response model with citations and metadata. |

## Design Principles

- Dependency-light baseline first. The repository must run tests and demos without API keys, GPUs, or
  heavyweight services.
- Optional integrations second. Ragas, DeepEval, Neo4j, LightRAG, and AutoRAG are treated as optional
  providers behind explicit adapters.
- Reproducibility over demos. Every experiment writes inputs, indexes, case-level results, aggregate
  metrics, leaderboard rows, best config, and reports.
- Chinese enterprise documents as the first-class scenario. Chunking, examples, QA cases, and README
  language should reflect audit, security, HR, procurement, and operations style documents.
- Traceability everywhere. Query results should include chunk IDs, entities, retrieval evidence,
  scores, and config metadata.
- PR-sized evolution. Each upgrade should be reviewable, testable, and mergeable on its own.

## Target Architecture

```text
cn_graphrag_eval_opt/
  connectors/       # corpus sources and dataset loaders
  indexing/         # chunking, entity extraction, graph/vector index builders
  retrievers/       # lexical, dense, graph, fusion, and query-mode retrievers
  stores/           # in-memory, JSONL, SQLite, and optional external store adapters
  evaluators/       # deterministic metrics plus optional Ragas/DeepEval adapters
  generators/       # extractive baseline and optional LLM answer providers
  experiments/      # optimization search, trial tracking, quality gates
  service/          # traced query response model and optional HTTP API
  cli.py            # command surface
```

The current flat module layout can evolve gradually. The first upgrade PRs should introduce small
interfaces and tests without moving every file at once.

## Roadmap By Pull Request

### PR-001: Competitive Design Roadmap

Purpose: document the benchmark projects, current gaps, upgrade architecture, and stepwise PR plan.

Files:

- `docs/superpowers/specs/2026-06-08-cn-graphrag-eval-opt-design.md`
- `docs/superpowers/plans/2026-06-08-cn-graphrag-eval-opt-competitive-upgrade.md`
- `docs/references.md`

Acceptance:

- No local absolute filesystem paths in developer-facing docs.
- Reference projects are linked and mapped to concrete project upgrades.
- Existing tests still pass.

### PR-002: Provider Interfaces And Registry

Purpose: convert the current optional integration descriptors into typed provider interfaces.

Planned files:

- Create `src/cn_graphrag_eval_opt/providers.py`.
- Modify `src/cn_graphrag_eval_opt/adapters.py`.
- Modify `src/cn_graphrag_eval_opt/cli.py`.
- Add `tests/test_providers.py`.

Expected outcome:

- `ProviderSpec`, `ProviderRegistry`, and provider capability flags.
- Built-in descriptors for local baseline, LightRAG, AutoRAG, Ragas, DeepEval, and Neo4j.
- CLI output showing install status, role, capabilities, and import names.

### PR-003: Retriever Fusion And Trace Quality

Purpose: make retrieval ranking more credible and explainable.

Planned files:

- Create `src/cn_graphrag_eval_opt/fusion.py`.
- Modify `src/cn_graphrag_eval_opt/retrieval.py`.
- Modify `src/cn_graphrag_eval_opt/models.py`.
- Add `tests/test_fusion.py`.

Expected outcome:

- Reciprocal Rank Fusion for lexical, dense, local graph, and global graph signals.
- Retrieval traces that expose signal contributions, normalized ranks, and entity matches.
- Regression tests proving `mix` improves or preserves recall over individual modes on the seed QA set.

### PR-004: Persistent Store Abstractions

Purpose: make the project feel like an indexable system rather than a one-shot script.

Planned files:

- Create `src/cn_graphrag_eval_opt/stores.py`.
- Modify `src/cn_graphrag_eval_opt/graph.py`.
- Modify `src/cn_graphrag_eval_opt/reporting.py`.
- Add `tests/test_stores.py`.

Expected outcome:

- In-memory and JSONL-backed store interfaces for chunks, vectors, entities, and edges.
- Export/import round trip for indexes.
- Store metadata in trial artifacts.

### PR-005: Real Evaluation Adapter Layer

Purpose: bridge deterministic CI metrics with optional LLM/RAG evaluators.

Planned files:

- Create `src/cn_graphrag_eval_opt/evaluator_adapters.py`.
- Modify `src/cn_graphrag_eval_opt/evaluation.py`.
- Modify `src/cn_graphrag_eval_opt/adapters.py`.
- Add `tests/test_evaluator_adapters.py`.

Expected outcome:

- Local case-result schema can be converted to Ragas-style and DeepEval-style inputs.
- Missing optional packages produce clear messages rather than crashes.
- Threshold quality gates can be configured for CI.

### PR-006: Corpus Connectors And Dataset Scaling

Purpose: move beyond a tiny demo corpus.

Planned files:

- Create `src/cn_graphrag_eval_opt/connectors.py`.
- Modify `src/cn_graphrag_eval_opt/corpus.py`.
- Add `examples/corpus_large/`.
- Add `examples/qa_extended.jsonl`.
- Add `tests/test_connectors.py`.

Expected outcome:

- Local file connector with extension registry.
- Markdown/TXT baseline remains deterministic.
- Future hooks for HTML/PDF readers are explicit and tested through capability metadata.

### PR-007: Query API Surface

Purpose: make the project easier to demo and integrate.

Planned files:

- Create `src/cn_graphrag_eval_opt/api.py`.
- Modify `src/cn_graphrag_eval_opt/service.py`.
- Modify `src/cn_graphrag_eval_opt/cli.py`.
- Add `tests/test_service_api.py`.

Expected outcome:

- API-ready request/response dataclasses.
- Citations, chunk IDs, scores, evidence, and config metadata in responses.
- Optional FastAPI adapter can be added without becoming a required dependency.

### PR-008: Reports, CI Gates, And Resume Polish

Purpose: make the repository interview-ready.

Planned files:

- Modify `README.md`.
- Modify `docs/architecture.md`.
- Modify `.github/workflows/ci.yml`.
- Add `docs/resume-framing.md`.
- Add `tests/test_quality_gate.py`.

Expected outcome:

- README remains generic and avoids local paths.
- CI runs tests plus deterministic evaluation gate.
- Resume framing explains problem, architecture, metrics, and business value.

## Interview Narrative

The concise narrative should be:

> I built a Chinese enterprise GraphRAG evaluation and optimization toolkit. I studied Microsoft
> GraphRAG, LightRAG, AutoRAG, Ragas, DeepEval, Neo4j GraphRAG, and Haystack, then implemented an
> original dependency-light baseline with optional provider adapters. The project supports
> config-driven indexing, graph-enhanced retrieval modes, rank-fusion roadmap, QA-driven evaluation,
> pipeline optimization, reproducible trial artifacts, and traced query responses.

## Non-Goals

- Do not vendor source code from upstream RAG repositories.
- Do not require paid model APIs for baseline tests.
- Do not add heavyweight services before the local interfaces are stable.
- Do not hide deterministic proxy metrics behind inflated LLM claims.
