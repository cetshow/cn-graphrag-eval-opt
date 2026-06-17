# cn-graphrag-eval-opt

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![GraphRAG](https://img.shields.io/badge/GraphRAG-Chinese%20Enterprise-16A34A)
![MiMo](https://img.shields.io/badge/MiMo-OpenAI--Compatible-7C3AED)
![Tests](https://img.shields.io/badge/Tests-unittest-0EA5E9)
![License](https://img.shields.io/badge/License-MIT-111827)

Language: [中文](#中文说明) | [English](#english)

---

## 中文说明

`cn-graphrag-eval-opt` 是一个面向中文企业文档的 GraphRAG 检索、评测、优化与 MiMo LLM 问答工具。它提供可复现的本地 baseline，也提供 OpenAI-compatible MiMo 运行时入口，适合用来验证 chunking、图谱扩展、RRF 融合、top-k、质量门禁和 LLM 回答效果。

项目借鉴 Microsoft GraphRAG、LightRAG、AutoRAG、Ragas、DeepEval、RAGFlow 和 R2R 的工程思路，但实现保持轻量、可测试、可扩展，不 vendoring 上游源码。

### 核心能力

| 模块 | 能力 |
| --- | --- |
| 文档处理 | 加载 Markdown/TXT 企业文档，生成 corpus manifest |
| 中文分块 | 支持 sentence / recursive / fixed 策略和 overlap |
| 图谱索引 | 抽取企业实体，构建 chunk-entity 与 entity-entity 共现图 |
| GraphRAG 检索 | 支持 `naive`、`local`、`global`、`hybrid`、`mix` |
| RRF 融合 | 融合 lexical、dense、local graph、global graph 信号 |
| MiMo LLM | 通过 OpenAI-compatible `/chat/completions` 调用 MiMo |
| Query API | 输出 answer、contexts、citations、scores、trace、LLM metadata |
| 回答审计 | 校验 LLM 回答中的 `chunk_id` 引用，输出 grounded、citation coverage 和 warnings |
| 增量索引 | 保存 `doc_status.json`，按文档 hash 跳过未变文档并支持逻辑删除 |
| 评测优化 | 运行多 pipeline config，输出 leaderboard、best config 和 report |
| 实验结果 | 内置数据集真实跑出 recall/precision/relevance/faithfulness/token cost 等量化指标 |
| 质量门禁 | 用 `quality-gate` 在 CI 中阻断低质量检索结果 |
| 可选生态 | 通过 provider registry 和 `provenance` 描述上游参考、许可证和复用边界 |

### 环境要求

- Python 3.10、3.11 或 3.12
- 支持 Windows、macOS、Linux
- 本地 baseline 不需要 GPU、不需要外部服务、不需要 LLM API Key
- MiMo LLM 问答需要 MiMo Token Plan 或 pay-as-you-go API Key
- 网络访问只在执行 `ask` 的在线模式或 `llm-smoke` 非 dry-run 时发生

### 安装

```bash
git clone https://github.com/cetshow/cn-graphrag-eval-opt.git
cd cn-graphrag-eval-opt
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

### MiMo 配置

复制 `.env.example` 为 `.env`，填入你的专属凭证。`.env` 已被 `.gitignore` 忽略。

```env
LLM_PROVIDER=mimo
LLM_API_PROTOCOL=openai
LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
LLM_API_KEY=replace-with-your-dedicated-api-key
LLM_MODEL=mimo-v2.5-pro
LLM_TEMPERATURE=0.2
LLM_TOP_P=1.0
LLM_MAX_TOKENS=2048
LLM_CONTEXT_MAX_CHARS=12000
LLM_TIMEOUT_SECONDS=60
LLM_RETRY_COUNT=2
LLM_AUTH_HEADER=api-key
ANTHROPIC_BASE_URL=https://token-plan-sgp.xiaomimimo.com/anthropic
```

MiMo Token Plan 官方示例使用 `api-key` header；本项目默认按该方式发送请求。先做脱敏检查：

`LLM_MAX_TOKENS` 控制 MiMo 输出预算，`LLM_CONTEXT_MAX_CHARS` 控制送入 LLM 的检索上下文字符预算，避免长文档直接撑爆请求。

```bash
python -m cn_graphrag_eval_opt llm-config --env .env
python -m cn_graphrag_eval_opt llm-smoke --env .env --dry-run
```

确认 key 可用后再执行真实联网 smoke：

```bash
python -m cn_graphrag_eval_opt llm-smoke --env .env --prompt "请用一句话介绍 MiMo。"
```

在真实联网前，可以先运行非联网产品诊断：

```bash
python -m cn_graphrag_eval_opt doctor --corpus examples/corpus --env .env.example --question "哪个部门每月复核高危权限？"
```

`doctor` 会检查 corpus 加载、分块数量、检索结果、离线回答审计和 MiMo 脱敏请求计划，并用 `offline_ready` / `online_ready` 标记当前可用状态。

### 使用方式

运行默认 GraphRAG 优化实验：

```bash
python -m cn_graphrag_eval_opt optimize --config configs/default.toml
```

运行离线检索查询：

```bash
python -m cn_graphrag_eval_opt query "哪个部门每月复核高危权限？" --corpus examples/corpus --query-mode mix
```

运行离线问答模式，使用 deterministic extractive answer：

```bash
python -m cn_graphrag_eval_opt ask "哪个部门每月复核高危权限？" --corpus examples/corpus --offline
```

运行 MiMo LLM grounded answer：

```bash
python -m cn_graphrag_eval_opt ask "哪个部门每月复核高危权限？" --corpus examples/corpus --env .env
```

`ask` 的 JSON trace 会包含 `grounded`、`citation_coverage`、`cited_chunk_ids`、`missing_citation_ids` 和 `warnings`，用于检查回答是否引用了本次检索上下文。

持久化索引并启用增量账本：

```bash
python -m cn_graphrag_eval_opt ingest --corpus examples/corpus --out runs/index --incremental
```

索引目录会写入 `chunks.jsonl`、`graph.json`、`metadata.json` 和 `doc_status.json`。再次执行时，未变文档会按内容 hash 跳过；需要逻辑移除文档时可添加 `--delete-doc-id <doc_id>`。

运行 CI 质量门禁：

```bash
python -m cn_graphrag_eval_opt quality-gate --summary runs/demo/summary.json --threshold retrieval_recall=0.8 --threshold faithfulness=0.7
```

### 输出产物

默认实验会写入：

```text
runs/demo/
  inputs/corpus_manifest.json
  index/chunks.jsonl
  index/entities.json
  index/store/
  evaluations/case_results.jsonl
  leaderboard.csv
  summary.json
  best_config.json
  reports/report.md
```

### 数据集实验结果

在内置中文企业文档数据集和新增 benchmark 上实际运行：

```bash
python -m cn_graphrag_eval_opt optimize --config configs/default.toml --out <experiment-out-dir>
python -m cn_graphrag_eval_opt optimize --corpus examples/benchmarks/small_enterprise/corpus --qa examples/benchmarks/small_enterprise/qa.jsonl --out <experiment-out-dir>
python -m cn_graphrag_eval_opt optimize --corpus examples/benchmarks/medium_enterprise/corpus --qa examples/benchmarks/medium_enterprise/qa.jsonl --out <experiment-out-dir>
```

三组实验覆盖 3/5/10 篇企业制度文档、302/659/1284 个中文字符、3/8/15 条 QA，并统一比较 5 组 pipeline 配置。对比 baseline 是默认实验配置中的 `naive` 检索：`query_mode=naive`、`chunk_size=96`、`overlap=12`、`top_k=2`，检索信号为 lexical + hashing dense，不使用实体图局部/全局扩展。

| 数据集 | 最佳模式 | Recall | Precision | Faithfulness | Token cost | 相对 baseline 结论 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| built-in enterprise corpus | `local` | 1.0000 | 1.0000 | 0.9792 | 30.5167 | precision 从 0.6667 提升到 1.0000，token cost 降低 22.3%。 |
| small enterprise benchmark | `naive` | 1.0000 | 0.6875 | 0.9961 | 45.8575 | baseline 最优，相比 `local` 降低 39.8% token cost。 |
| medium enterprise benchmark | `naive` | 1.0000 | 0.8333 | 0.9983 | 44.1240 | baseline 最优，相比 `local` 降低 48.4% token cost。 |

结论不是“图谱永远更好”：短小且实体关系明确的 3 文档集上 `local` 图谱检索更精确、更省上下文；词面锚点更强的小/中型制度集上 `naive` baseline 更稳、更省 token。完整 leaderboard、baseline 定义和 case-level 结果见 [docs/experiments.md](docs/experiments.md)。

### 开发与测试

```bash
python -m unittest discover -s tests
python -m cn_graphrag_eval_opt integrations
python -m cn_graphrag_eval_opt provenance
python -m cn_graphrag_eval_opt doctor --corpus examples/corpus --env .env.example --question "哪个部门每月复核高危权限？"
python -m cn_graphrag_eval_opt llm-config --env .env.example
python -m cn_graphrag_eval_opt llm-smoke --env .env.example --dry-run
python -m cn_graphrag_eval_opt optimize --config configs/default.toml
python -m cn_graphrag_eval_opt quality-gate --summary runs/demo/summary.json --threshold retrieval_recall=0.8 --threshold faithfulness=0.7
```

### 上游参考与许可证边界

本项目使用 MIT License 发布。项目会参考 Microsoft GraphRAG、LightRAG、AutoRAG、RAGFlow、Ragas、R2R 等公开 RAG 系统的架构、评测和产品设计，但除非文件中明确说明，否则当前仓库不 vendoring、不复制、不修改这些上游项目源码。

参考项目仍遵循各自许可证：LightRAG 与 R2R 使用 MIT License，AutoRAG 与 RAGFlow 使用 Apache License 2.0。可选集成作为第三方包使用，仍受其自身许可证约束。若未来复制、修改或派生上游源码，相关文件或模块必须保留上游版权声明、许可证文本、NOTICE 义务和本地修改说明。

## English

`cn-graphrag-eval-opt` is a GraphRAG retrieval, evaluation, optimization, and MiMo LLM answering toolkit for Chinese enterprise documents. It provides a reproducible local baseline and an OpenAI-compatible MiMo runtime for grounded RAG answers.

The project follows engineering ideas from Microsoft GraphRAG, LightRAG, AutoRAG, Ragas, DeepEval, RAGFlow, and R2R while keeping the implementation original, lightweight, testable, and dependency-conscious.

### Features

| Area | Capability |
| --- | --- |
| Corpus | Load Chinese enterprise Markdown/TXT documents and write manifests |
| Chunking | Sentence, recursive, and fixed-window splitting |
| Graph Index | Entity extraction plus chunk-entity and entity-entity co-occurrence graph |
| Retrieval | `naive`, `local`, `global`, `hybrid`, and `mix` query modes |
| Fusion | Reciprocal Rank Fusion over lexical, dense, local graph, and global graph signals |
| MiMo LLM | OpenAI-compatible `/chat/completions` client with retry support |
| Query API | Answers with contexts, citations, scores, traces, and LLM metadata |
| Answer Audit | Validates `chunk_id` citations in LLM answers and reports grounded, citation coverage, and warnings |
| Incremental Index | Persists `doc_status.json`, skips unchanged document hashes, and supports logical document deletion |
| Evaluation | Deterministic Ragas-style proxy metrics for CI-safe runs |
| Optimization | AutoRAG-style config search, leaderboard, best config, and reports |
| Experiment Results | Reports measured recall, precision, relevance, faithfulness, and token-cost metrics on the built-in dataset |
| Quality Gate | Threshold-based CI gate over retrieval/evaluation metrics |

### Environment Requirements

- Python 3.10, 3.11, or 3.12
- Windows, macOS, or Linux
- No GPU, external service, or LLM key required for the deterministic baseline
- MiMo Token Plan or pay-as-you-go API key required for online LLM answering
- Network access is used only by online `ask` and non-dry-run `llm-smoke`

### Installation

```bash
git clone https://github.com/cetshow/cn-graphrag-eval-opt.git
cd cn-graphrag-eval-opt
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

### MiMo Configuration

Copy `.env.example` to `.env` and fill in your dedicated credentials. `.env` is ignored by git.

```env
LLM_PROVIDER=mimo
LLM_API_PROTOCOL=openai
LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
LLM_API_KEY=replace-with-your-dedicated-api-key
LLM_MODEL=mimo-v2.5-pro
LLM_TEMPERATURE=0.2
LLM_TOP_P=1.0
LLM_MAX_TOKENS=2048
LLM_CONTEXT_MAX_CHARS=12000
LLM_TIMEOUT_SECONDS=60
LLM_RETRY_COUNT=2
LLM_AUTH_HEADER=api-key
ANTHROPIC_BASE_URL=https://token-plan-sgp.xiaomimimo.com/anthropic
```

MiMo Token Plan examples use the `api-key` header, so this project uses it by default.

`LLM_MAX_TOKENS` controls the MiMo completion budget. `LLM_CONTEXT_MAX_CHARS` controls the retrieved-context character budget sent to the model, which keeps long corpora from overwhelming a request.

```bash
python -m cn_graphrag_eval_opt llm-config --env .env
python -m cn_graphrag_eval_opt llm-smoke --env .env --dry-run
python -m cn_graphrag_eval_opt llm-smoke --env .env --prompt "Introduce MiMo in one sentence."
```

Before making a live network call, run the non-network product diagnostics:

```bash
python -m cn_graphrag_eval_opt doctor --corpus examples/corpus --env .env.example --question "哪个部门每月复核高危权限？"
```

`doctor` checks corpus loading, chunk counts, retrieval, offline answer audit, and the redacted MiMo request plan, then reports `offline_ready` and `online_ready`.

### Usage

```bash
python -m cn_graphrag_eval_opt optimize --config configs/default.toml
python -m cn_graphrag_eval_opt query "哪个部门每月复核高危权限？" --corpus examples/corpus --query-mode mix
python -m cn_graphrag_eval_opt ask "哪个部门每月复核高危权限？" --corpus examples/corpus --offline
python -m cn_graphrag_eval_opt ask "哪个部门每月复核高危权限？" --corpus examples/corpus --env .env
python -m cn_graphrag_eval_opt ingest --corpus examples/corpus --out runs/index --incremental
python -m cn_graphrag_eval_opt quality-gate --summary runs/demo/summary.json --threshold retrieval_recall=0.8 --threshold faithfulness=0.7
```

The `ask` response trace includes `grounded`, `citation_coverage`, `cited_chunk_ids`, `missing_citation_ids`, and `warnings` so callers can inspect whether an LLM answer cites the retrieved context.

`ingest --out --incremental` writes `chunks.jsonl`, `graph.json`, `metadata.json`, and `doc_status.json`. Re-running the command skips unchanged documents by content hash; use `--delete-doc-id <doc_id>` for logical document removal from the persisted index.

### Dataset Experiment Results

Run the built-in corpus plus the added small and medium enterprise benchmarks:

```bash
python -m cn_graphrag_eval_opt optimize --config configs/default.toml --out <experiment-out-dir>
python -m cn_graphrag_eval_opt optimize --corpus examples/benchmarks/small_enterprise/corpus --qa examples/benchmarks/small_enterprise/qa.jsonl --out <experiment-out-dir>
python -m cn_graphrag_eval_opt optimize --corpus examples/benchmarks/medium_enterprise/corpus --qa examples/benchmarks/medium_enterprise/qa.jsonl --out <experiment-out-dir>
```

The three suites cover 3/5/10 policy documents, 302/659/1284 Chinese characters, 3/8/15 QA cases, and the same 5 pipeline configs. The comparison baseline is the default `naive` retriever: `query_mode=naive`, `chunk_size=96`, `overlap=12`, and `top_k=2`. It uses lexical + hashing dense retrieval signals without local/global entity-graph expansion.

| Dataset | Best mode | Recall | Precision | Faithfulness | Token cost | Result vs baseline |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| built-in enterprise corpus | `local` | 1.0000 | 1.0000 | 0.9792 | 30.5167 | precision improves from 0.6667 to 1.0000 and token cost drops by 22.3%. |
| small enterprise benchmark | `naive` | 1.0000 | 0.6875 | 0.9961 | 45.8575 | baseline wins and costs 39.8% less than `local`. |
| medium enterprise benchmark | `naive` | 1.0000 | 0.8333 | 0.9983 | 44.1240 | baseline wins and costs 48.4% less than `local`. |

The measured conclusion is deliberately practical: graph retrieval helps on the compact entity-local corpus, while the simple `naive` baseline remains stronger on keyword-heavy small/medium policy suites. See [docs/experiments.md](docs/experiments.md) for full leaderboards, baseline definitions, and case-level results.

### Development

```bash
python -m unittest discover -s tests
python -m cn_graphrag_eval_opt integrations
python -m cn_graphrag_eval_opt provenance
python -m cn_graphrag_eval_opt doctor --corpus examples/corpus --env .env.example --question "哪个部门每月复核高危权限？"
python -m cn_graphrag_eval_opt llm-config --env .env.example
python -m cn_graphrag_eval_opt llm-smoke --env .env.example --dry-run
python -m cn_graphrag_eval_opt optimize --config configs/default.toml
```

### Upstream References and License Boundary

This project is released under the MIT License. It studies public RAG systems such as Microsoft GraphRAG, LightRAG, AutoRAG, RAGFlow, Ragas, and R2R as architectural, evaluation, and product references, but the repository does not vendor, copy, or modify their source code unless explicitly stated.

Reference projects remain under their own licenses: LightRAG and R2R use the MIT License; AutoRAG and RAGFlow use the Apache License 2.0. Optional integrations are consumed as third-party packages under their own licenses. If future changes copy, modify, or derive upstream source code, the copied files or derived modules must preserve the upstream copyright, license text, NOTICE obligations, and local modification notes.

## License

MIT. See [LICENSE](LICENSE).
