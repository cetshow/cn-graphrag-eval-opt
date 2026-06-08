# Competitive GraphRAG Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `cn-graphrag-eval-opt` from a runnable baseline into a competitive GraphRAG evaluation project inspired by LightRAG, AutoRAG, Microsoft GraphRAG, Ragas, DeepEval, Neo4j GraphRAG, and Haystack.

**Architecture:** Keep the dependency-light local baseline, then introduce provider interfaces, retriever fusion, persistent stores, evaluator adapters, connector extension points, and API-ready query traces through small pull requests.

**Tech Stack:** Python 3.10+, standard library baseline, `unittest`, optional integration packages (`ragas`, `deepeval`, `neo4j`, `lightrag`, `autorag`), JSON/JSONL/TOML artifacts.

---

## File Structure

- `src/cn_graphrag_eval_opt/providers.py`: provider capability registry and optional package metadata.
- `src/cn_graphrag_eval_opt/fusion.py`: rank-fusion strategies for retrieval signals.
- `src/cn_graphrag_eval_opt/stores.py`: in-memory and file-backed store interfaces.
- `src/cn_graphrag_eval_opt/evaluator_adapters.py`: local case conversion for Ragas and DeepEval.
- `src/cn_graphrag_eval_opt/connectors.py`: corpus connector registry.
- `src/cn_graphrag_eval_opt/api.py`: API-ready request and response models.
- `tests/test_providers.py`: provider registry tests.
- `tests/test_fusion.py`: reciprocal-rank-fusion tests.
- `tests/test_stores.py`: index persistence tests.
- `tests/test_evaluator_adapters.py`: optional evaluator adapter tests.
- `tests/test_connectors.py`: connector registry tests.
- `tests/test_service_api.py`: traced query response tests.

### Task 1: Provider Registry PR

**Files:**

- Create: `src/cn_graphrag_eval_opt/providers.py`
- Modify: `src/cn_graphrag_eval_opt/adapters.py`
- Modify: `src/cn_graphrag_eval_opt/cli.py`
- Test: `tests/test_providers.py`

- [ ] **Step 1: Write provider registry tests**

```python
from cn_graphrag_eval_opt.providers import ProviderRegistry, default_provider_registry


def test_default_provider_registry_contains_local_and_optional_providers():
    registry = default_provider_registry()
    names = {provider.name for provider in registry.list()}
    assert {"local", "lightrag", "autorag", "ragas", "deepeval", "neo4j"} <= names


def test_provider_registry_filters_by_capability():
    registry = default_provider_registry()
    evaluators = registry.with_capability("evaluation")
    assert "ragas" in {provider.name for provider in evaluators}
    assert "deepeval" in {provider.name for provider in evaluators}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_providers`

Expected: FAIL because `cn_graphrag_eval_opt.providers` does not exist yet.

- [ ] **Step 3: Implement provider registry**

Create immutable provider specs with `name`, `package`, `role`, `capabilities`, `available`, and
`install_hint`. Register the local baseline plus LightRAG, AutoRAG, Ragas, DeepEval, and Neo4j.

- [ ] **Step 4: Route adapter status through the registry**

Update `optional_integrations()` so the CLI and adapter layer share the same provider metadata.

- [ ] **Step 5: Run verification and commit**

Run: `python -m unittest discover -s tests`

Expected: all tests pass.

Commit: `feat: add provider registry`

### Task 2: Rank Fusion PR

**Files:**

- Create: `src/cn_graphrag_eval_opt/fusion.py`
- Modify: `src/cn_graphrag_eval_opt/retrieval.py`
- Modify: `src/cn_graphrag_eval_opt/models.py`
- Test: `tests/test_fusion.py`

- [ ] **Step 1: Write fusion tests**

```python
from cn_graphrag_eval_opt.fusion import reciprocal_rank_fusion


def test_reciprocal_rank_fusion_combines_ranked_signals():
    fused = reciprocal_rank_fusion(
        {
            "lexical": ["c1", "c2", "c3"],
            "graph": ["c2", "c4"],
            "dense": ["c3", "c2"],
        },
        k=60,
    )
    assert fused[0].item_id == "c2"
    assert {score.signal for score in fused[0].signals} == {"lexical", "graph", "dense"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_fusion`

Expected: FAIL because `fusion.py` does not exist yet.

- [ ] **Step 3: Implement fusion dataclasses and algorithm**

Create `SignalContribution` and `FusedScore`. Implement Reciprocal Rank Fusion with deterministic
tie-breaking by item ID.

- [ ] **Step 4: Use fusion in `GraphRAGRetriever.retrieve()`**

Build ranked lists for lexical, dense, local graph, and global graph signals, then convert fused scores
into retrieval results with evidence showing signal names and ranks.

- [ ] **Step 5: Run verification and commit**

Run: `python -m unittest discover -s tests`

Expected: all tests pass.

Commit: `feat: add retriever rank fusion`

### Task 3: Persistent Store PR

**Files:**

- Create: `src/cn_graphrag_eval_opt/stores.py`
- Modify: `src/cn_graphrag_eval_opt/graph.py`
- Modify: `src/cn_graphrag_eval_opt/reporting.py`
- Test: `tests/test_stores.py`

- [ ] **Step 1: Write store round-trip tests**

```python
from cn_graphrag_eval_opt.chunking import ChineseTextSplitter
from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.models import Document
from cn_graphrag_eval_opt.stores import JsonlIndexStore


def test_jsonl_index_store_round_trips_graph_index(tmp_path):
    chunks = ChineseTextSplitter(chunk_size=80, overlap=0).split(
        Document(doc_id="doc", title="权限", text="安全部门每月复核高危权限。")
    )
    index = GraphIndex.from_chunks(chunks)
    store = JsonlIndexStore(tmp_path)
    store.save(index)
    loaded = store.load()
    assert sorted(loaded.chunks) == sorted(index.chunks)
    assert sorted(loaded.entities) == sorted(index.entities)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_stores`

Expected: FAIL because `stores.py` does not exist yet.

- [ ] **Step 3: Implement JSONL index store**

Persist chunks, entities, and graph edges into a portable artifact folder. Load them back into
`GraphIndex` without changing retrieval callers.

- [ ] **Step 4: Add store metadata to reports**

Record store type, chunk count, entity count, and edge count in trial summaries.

- [ ] **Step 5: Run verification and commit**

Run: `python -m unittest discover -s tests`

Expected: all tests pass.

Commit: `feat: add persistent index store`

### Task 4: Evaluator Adapter PR

**Files:**

- Create: `src/cn_graphrag_eval_opt/evaluator_adapters.py`
- Modify: `src/cn_graphrag_eval_opt/evaluation.py`
- Modify: `src/cn_graphrag_eval_opt/adapters.py`
- Test: `tests/test_evaluator_adapters.py`

- [ ] **Step 1: Write adapter conversion tests**

```python
from cn_graphrag_eval_opt.evaluator_adapters import to_ragas_rows
from cn_graphrag_eval_opt.models import CaseEvaluation


def test_case_results_convert_to_ragas_rows():
    case = CaseEvaluation(
        question="谁复核高危权限？",
        expected_answer="安全部门",
        generated_answer="安全部门每月复核高危权限。",
        retrieved_chunk_ids=["doc-0001"],
        metrics={"faithfulness": 1.0},
    )
    rows = to_ragas_rows([case], {"doc-0001": "安全部门每月复核高危权限。"})
    assert rows[0]["question"] == "谁复核高危权限？"
    assert rows[0]["answer"] == "安全部门每月复核高危权限。"
    assert rows[0]["contexts"] == ["安全部门每月复核高危权限。"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_evaluator_adapters`

Expected: FAIL because `evaluator_adapters.py` does not exist yet.

- [ ] **Step 3: Implement Ragas and DeepEval data conversion**

Expose pure-data conversion functions first. Keep runtime imports optional and return clear availability
errors when packages are missing.

- [ ] **Step 4: Add quality gate helper**

Create a threshold evaluator that fails when configured aggregate metrics fall below required values.

- [ ] **Step 5: Run verification and commit**

Run: `python -m unittest discover -s tests`

Expected: all tests pass.

Commit: `feat: add evaluator adapters`

### Task 5: API-Ready Query Surface PR

**Files:**

- Create: `src/cn_graphrag_eval_opt/api.py`
- Modify: `src/cn_graphrag_eval_opt/service.py`
- Modify: `src/cn_graphrag_eval_opt/cli.py`
- Test: `tests/test_service_api.py`

- [ ] **Step 1: Write traced response tests**

```python
from cn_graphrag_eval_opt.api import QueryRequest


def test_query_request_defaults_to_mix_mode():
    request = QueryRequest(question="采购合同怎么审批？")
    assert request.query_mode == "mix"
    assert request.top_k == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_service_api`

Expected: FAIL because `api.py` does not exist yet.

- [ ] **Step 3: Implement request and response dataclasses**

Add `QueryRequest`, `Citation`, and `QueryResponse`. Include answer, citations, config, retrieval
mode, and timing metadata fields.

- [ ] **Step 4: Route service output through response models**

Keep the existing CLI behavior while exposing structured response objects for future FastAPI support.

- [ ] **Step 5: Run verification and commit**

Run: `python -m unittest discover -s tests`

Expected: all tests pass.

Commit: `feat: add traced query response models`
