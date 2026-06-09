# cn-graphrag-eval-opt

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![GraphRAG](https://img.shields.io/badge/GraphRAG-Chinese%20Enterprise-16A34A)
![LLM](https://img.shields.io/badge/LLM-MiMo%20%7C%20OpenAI--Compatible-7C3AED)
![Tests](https://img.shields.io/badge/Tests-unittest-0EA5E9)
![License](https://img.shields.io/badge/License-MIT-111827)

🌐 Language: [中文](#中文说明) | [English](#english)

---

## 中文说明

`cn-graphrag-eval-opt` 是一个面向中文企业文档的 GraphRAG 检索评测与优化工具包。它不是单次问答 demo，而是一个可复现实验系统：从文档加载、中文分块、实体图谱索引、GraphRAG 检索、RAG 指标评测，到多配置搜索、排行榜和报告产出，形成一条完整的 RAG 优化闭环。

本项目借鉴了多个高质量开源项目的工程思路，但代码为原创实现，不 vendoring 上游源码：

- 🧭 [Microsoft GraphRAG](https://github.com/microsoft/graphrag)：配置驱动的 indexing/query 工作流。
- ⚡ [HKUDS LightRAG](https://github.com/HKUDS/LightRAG)：轻量图增强检索和 local/global/hybrid/mix 查询模式。
- 🧪 [AutoRAG](https://github.com/Marker-Inc-Korea/AutoRAG)：基于 corpus + QA 的 pipeline 搜索和 leaderboard。
- 📏 [Ragas](https://github.com/vibrantlabsai/ragas)：context precision、answer relevance、faithfulness 等评测指标语义。
- ✅ [DeepEval](https://github.com/confident-ai/deepeval)：CI-friendly 质量门禁和回归测试思路。
- 🧰 [RAGFlow](https://github.com/infiniflow/ragflow)：面向操作者的 RAG 工作流与产品体验参考。
- 🚀 [R2R](https://github.com/SciPhi-AI/R2R)：面向服务化的 query trace 响应形态。

### ✨ 核心能力

| 模块 | 能力 |
| --- | --- |
| 📚 文档处理 | 加载 Markdown/TXT 企业文档，生成 corpus manifest |
| ✂️ 中文分块 | 支持 sentence / recursive / fixed 策略和 overlap |
| 🕸️ 图谱索引 | 抽取企业实体，构建 chunk-entity 和 entity-entity 共现图 |
| 🔎 GraphRAG 检索 | 支持 `naive`、`local`、`global`、`hybrid`、`mix`，并用 RRF 融合 lexical / dense / graph 信号 |
| 📊 评测指标 | deterministic Ragas-style proxy metrics，支持 DeepEval-style 质量门禁 |
| 🧭 配置搜索 | AutoRAG-style 多 pipeline config 搜索和 best config 输出 |
| 🧩 Provider Registry | 记录 LightRAG、AutoRAG、Ragas、DeepEval、Neo4j 等可选生态集成 |
| 🧱 持久化存储 | JSONL index store 支持 chunks、entities、edges round trip |
| 🔌 Query API | API-ready query response，包含 citations、contexts、scores、trace |
| 🧾 实验产物 | 输出 chunks、entities、case results、leaderboard、summary、report |
| 🤖 LLM 配置 | 支持 MiMo / OpenAI-compatible `.env` 配置和脱敏检查 |

### 🗂️ 项目结构

```text
cn-graphrag-eval-opt/
  configs/default.toml                 # 实验配置网格
  examples/corpus/                     # 中文企业文档样例
  examples/qa.jsonl                    # 种子 QA benchmark
  src/cn_graphrag_eval_opt/
    config.py                          # 项目配置模型
    connectors.py                      # corpus connector registry
    corpus.py                          # corpus / QA 加载
    datasets.py                        # bootstrap QA 构造
    chunking.py                        # 中文分块
    graph.py                           # 实体图谱索引
    fusion.py                          # reciprocal rank fusion
    retrieval.py                       # GraphRAG 检索器
    evaluation.py                      # RAG 指标与答案合成
    evaluator_adapters.py              # Ragas / DeepEval 数据适配与质量门禁
    providers.py                       # optional provider registry
    stores.py                          # JSONL index store
    api.py                             # query request / response dataclasses
    llm.py                             # LLM .env 配置加载
    optimization.py                    # pipeline 搜索
    pipeline.py                        # ingest -> index -> evaluate 编排
    reporting.py                       # 实验产物写入
    service.py                         # query service facade
    adapters.py                        # 可选上游集成描述
    cli.py                             # CLI 入口
  tests/                               # 单元与集成测试
```

### 🚀 快速开始

```bash
git clone https://github.com/cetshow/cn-graphrag-eval-opt.git
cd cn-graphrag-eval-opt
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

运行默认 GraphRAG 优化实验：

```bash
python -m cn_graphrag_eval_opt optimize --config configs/default.toml
```

运行带 trace 的查询：

```bash
python -m cn_graphrag_eval_opt query "哪个部门每月复核高危权限？" --corpus examples/corpus --query-mode mix
```

从自己的 corpus 构建 bootstrap QA：

```bash
python -m cn_graphrag_eval_opt dataset build --corpus path/to/corpus --out data/qa.bootstrap.jsonl
```

### 🤖 MiMo LLM 配置

默认 pipeline 是 deterministic 的，不需要 LLM key。若要接入 MiMo 或未来的 model-backed evaluator/generator，请复制 `.env.example` 为 `.env` 并填入专属 API Key。`.env` 已被 git 忽略，不会提交。

```env
LLM_PROVIDER=mimo
LLM_API_PROTOCOL=openai
LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
LLM_API_KEY=replace-with-your-dedicated-api-key
LLM_MODEL=mimo-v2.5-pro
LLM_TEMPERATURE=0.2
LLM_TOP_P=1.0
LLM_MAX_TOKENS=2048
LLM_TIMEOUT_SECONDS=60
LLM_RETRY_COUNT=2
ANTHROPIC_BASE_URL=https://token-plan-sgp.xiaomimimo.com/anthropic
```

脱敏检查配置：

```bash
python -m cn_graphrag_eval_opt llm-config --env .env
```

### 📈 实验产物

默认输出目录包含：

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

### 🧪 开发验证

```bash
python -m unittest discover -s tests
python -m cn_graphrag_eval_opt integrations
python -m cn_graphrag_eval_opt llm-config --env .env.example
python -m cn_graphrag_eval_opt optimize --config configs/default.toml
python -m cn_graphrag_eval_opt quality-gate --summary runs/demo/summary.json --threshold retrieval_recall=0.8 --threshold faithfulness=0.7
```

### 🎯 简历表述

> 构建了一个中文企业文档 GraphRAG 检索评测与优化工具包，参考 LightRAG、Microsoft GraphRAG、AutoRAG、Ragas、DeepEval 和 R2R 的工程模式，实现配置驱动索引、RRF 图增强检索、多 pipeline 搜索、RAG 指标评测、CI 质量门禁、query trace、MiMo/OpenAI-compatible LLM 配置和可复现实验报告。

更完整的项目讲述见 [`docs/resume-framing.md`](docs/resume-framing.md)。

---

## English

`cn-graphrag-eval-opt` is a GraphRAG retrieval evaluation and optimization toolkit for Chinese enterprise documents. Instead of being a one-off chatbot demo, it provides a reproducible RAG experiment workflow: corpus loading, Chinese-aware chunking, entity graph indexing, GraphRAG retrieval, RAG metric evaluation, pipeline search, leaderboards, and reports.

This repository is inspired by proven open-source RAG systems, while keeping the implementation original and dependency-light:

- 🧭 [Microsoft GraphRAG](https://github.com/microsoft/graphrag): config-driven indexing and query workflows.
- ⚡ [HKUDS LightRAG](https://github.com/HKUDS/LightRAG): lightweight graph-enhanced local/global/hybrid/mix retrieval.
- 🧪 [AutoRAG](https://github.com/Marker-Inc-Korea/AutoRAG): corpus + QA based pipeline optimization and leaderboard artifacts.
- 📏 [Ragas](https://github.com/vibrantlabsai/ragas): evaluation vocabulary such as context precision, answer relevance, and faithfulness.
- ✅ [DeepEval](https://github.com/confident-ai/deepeval): CI-friendly quality gates and regression testing patterns.
- 🧰 [RAGFlow](https://github.com/infiniflow/ragflow): operator-facing RAG workflows and product experience references.
- 🚀 [R2R](https://github.com/SciPhi-AI/R2R): production-facing query responses with context traces.

### ✨ Features

| Area | Capability |
| --- | --- |
| 📚 Corpus | Load Chinese enterprise Markdown/TXT documents and produce manifests |
| ✂️ Chunking | Chinese-aware sentence, recursive, and fixed-window splitting |
| 🕸️ Graph Index | Build entity co-occurrence graphs over traceable chunks |
| 🔎 Retrieval | Compare `naive`, `local`, `global`, `hybrid`, and `mix` modes with RRF over lexical / dense / graph signals |
| 📊 Evaluation | Deterministic Ragas-style proxy metrics plus DeepEval-style quality gates |
| 🧭 Optimization | AutoRAG-style config search and best-config selection |
| 🧩 Provider Registry | Track optional LightRAG, AutoRAG, Ragas, DeepEval, and Neo4j integration paths |
| 🧱 Persistent Store | JSONL index store for chunk, entity, and edge round trips |
| 🔌 Query API | API-ready responses with citations, contexts, scores, and traces |
| 🧾 Artifacts | Write chunks, entities, case results, leaderboard, summary, and reports |
| 🤖 LLM Config | MiMo / OpenAI-compatible `.env` config with secret-safe inspection |

### 🚀 Quickstart

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

Run a traced query:

```bash
python -m cn_graphrag_eval_opt query "哪个部门每月复核高危权限？" --corpus examples/corpus --query-mode mix
```

### 🤖 LLM Configuration

The baseline is deterministic and does not require model credentials. For model-backed generation or future Ragas/DeepEval runs, copy `.env.example` to `.env` and fill in your dedicated provider key. `.env` is ignored by git.

```env
LLM_PROVIDER=mimo
LLM_API_PROTOCOL=openai
LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
LLM_API_KEY=replace-with-your-dedicated-api-key
LLM_MODEL=mimo-v2.5-pro
LLM_TEMPERATURE=0.2
LLM_TOP_P=1.0
LLM_MAX_TOKENS=2048
LLM_TIMEOUT_SECONDS=60
LLM_RETRY_COUNT=2
ANTHROPIC_BASE_URL=https://token-plan-sgp.xiaomimimo.com/anthropic
```

Inspect the loaded config without leaking secrets:

```bash
python -m cn_graphrag_eval_opt llm-config --env .env
```

### 📊 Metrics

- `retrieval_recall`: required-term or gold-context coverage.
- `context_precision`: fraction of retrieved contexts containing expected evidence.
- `answer_relevance`: lexical overlap between expected and generated answers.
- `faithfulness`: generated answer terms supported by retrieved contexts.
- `estimated_token_cost`: rough context cost proxy for retrieval breadth.

### 🧪 Development

```bash
python -m unittest discover -s tests
python -m cn_graphrag_eval_opt integrations
python -m cn_graphrag_eval_opt llm-config --env .env.example
python -m cn_graphrag_eval_opt optimize --config configs/default.toml
python -m cn_graphrag_eval_opt quality-gate --summary runs/demo/summary.json --threshold retrieval_recall=0.8 --threshold faithfulness=0.7
```

### 🎯 Resume Framing

> Built a Chinese enterprise GraphRAG evaluation and optimization toolkit inspired by LightRAG, Microsoft GraphRAG, AutoRAG, Ragas, DeepEval, and R2R. Implemented config-driven indexing, RRF graph-enhanced retrieval, pipeline search, RAG metric evaluation, CI quality gates, query tracing, MiMo/OpenAI-compatible LLM configuration, and reproducible experiment artifacts.

See [`docs/resume-framing.md`](docs/resume-framing.md) for the longer project narrative.

## License

MIT. See [LICENSE](LICENSE).
