# Chinese GraphRAG Evaluation Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable Chinese enterprise document GraphRAG evaluation and optimization toolkit and push it to `cetshow/cn-graphrag-eval-opt`.

**Architecture:** A dependency-light Python package implements a deterministic baseline inspired by LightRAG query modes and AutoRAG/Ragas evaluation. Optional adapters document upgrade paths to upstream packages without making the demo depend on remote APIs.

**Tech Stack:** Python 3.10+, standard-library CLI via `argparse`, dataclasses, JSON/JSONL, unittest, optional `lightrag-hku`, `AutoRAG`, and `ragas`.

---

### Task 1: Project Skeleton and Tests

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `.gitignore`
- Create: `tests/test_chunking.py`
- Create: `tests/test_pipeline.py`

- [x] **Step 1: Add metadata, docs, and failing tests**

Create project metadata, a quickstart README, and behavior tests that import the intended package
API before it exists.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest discover -s tests`

Expected: FAIL with `ModuleNotFoundError: No module named 'cn_graphrag_eval_opt'`.

### Task 2: Core Data Model and Chunking

**Files:**
- Create: `src/cn_graphrag_eval_opt/models.py`
- Create: `src/cn_graphrag_eval_opt/chunking.py`
- Create: `src/cn_graphrag_eval_opt/__init__.py`

- [ ] **Step 1: Implement dataclasses and Chinese splitter**

Implement `Document`, `Chunk`, `QACase`, `PipelineConfig`, `TrialSummary`, and
`ChineseTextSplitter`.

- [ ] **Step 2: Run chunking tests**

Run: `python -m unittest tests.test_chunking`

Expected: PASS.

### Task 3: Corpus, Graph, Retrieval, and Evaluation

**Files:**
- Create: `src/cn_graphrag_eval_opt/corpus.py`
- Create: `src/cn_graphrag_eval_opt/graph.py`
- Create: `src/cn_graphrag_eval_opt/retrieval.py`
- Create: `src/cn_graphrag_eval_opt/evaluation.py`

- [ ] **Step 1: Implement loading, indexing, retrieval, and metrics**

Implement Markdown/TXT loading, JSONL QA loading, entity graph extraction, lexical retrieval,
LightRAG-style query modes, and deterministic Ragas-style proxy metrics.

- [ ] **Step 2: Run pipeline tests**

Run: `python -m unittest tests.test_pipeline`

Expected: PASS.

### Task 4: Optimization, Reporting, CLI, and Examples

**Files:**
- Create: `src/cn_graphrag_eval_opt/optimization.py`
- Create: `src/cn_graphrag_eval_opt/reporting.py`
- Create: `src/cn_graphrag_eval_opt/adapters.py`
- Create: `src/cn_graphrag_eval_opt/cli.py`
- Create: `src/cn_graphrag_eval_opt/__main__.py`
- Create: `examples/corpus/*.md`
- Create: `examples/qa.jsonl`

- [ ] **Step 1: Implement optimizer, report writer, adapters, CLI, and example data**

Implement `run_optimization`, report writing, optional integration descriptors, and a runnable demo.

- [ ] **Step 2: Run full tests and CLI demo**

Run: `python -m unittest discover -s tests`

Run: `python -m cn_graphrag_eval_opt optimize --corpus examples/corpus --qa examples/qa.jsonl --out runs/demo`

Expected: tests PASS and report files are written.

### Task 5: Git Initialization and Push

**Files:**
- Modify: repository git metadata

- [ ] **Step 1: Initialize repository**

Run: `git init -b main`

- [ ] **Step 2: Commit project**

Run: `git add .`

Run: `git commit -m "feat: build cn graphrag eval optimizer"`

- [ ] **Step 3: Push to GitHub**

Run: `git remote add origin https://github.com/cetshow/cn-graphrag-eval-opt.git`

Run: `git push -u origin main`
