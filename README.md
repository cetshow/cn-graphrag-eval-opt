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
| 评测优化 | 运行多 pipeline config，输出 leaderboard、best config 和 report |
| 质量门禁 | 用 `quality-gate` 在 CI 中阻断低质量检索结果 |
| 可选生态 | 通过 provider registry 描述 LightRAG、AutoRAG、Ragas、DeepEval、Neo4j |

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

### 开发与测试

```bash
python -m unittest discover -s tests
python -m cn_graphrag_eval_opt integrations
python -m cn_graphrag_eval_opt llm-config --env .env.example
python -m cn_graphrag_eval_opt llm-smoke --env .env.example --dry-run
python -m cn_graphrag_eval_opt optimize --config configs/default.toml
python -m cn_graphrag_eval_opt quality-gate --summary runs/demo/summary.json --threshold retrieval_recall=0.8 --threshold faithfulness=0.7
```

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
| Evaluation | Deterministic Ragas-style proxy metrics for CI-safe runs |
| Optimization | AutoRAG-style config search, leaderboard, best config, and reports |
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

### Usage

```bash
python -m cn_graphrag_eval_opt optimize --config configs/default.toml
python -m cn_graphrag_eval_opt query "哪个部门每月复核高危权限？" --corpus examples/corpus --query-mode mix
python -m cn_graphrag_eval_opt ask "哪个部门每月复核高危权限？" --corpus examples/corpus --offline
python -m cn_graphrag_eval_opt ask "哪个部门每月复核高危权限？" --corpus examples/corpus --env .env
python -m cn_graphrag_eval_opt quality-gate --summary runs/demo/summary.json --threshold retrieval_recall=0.8 --threshold faithfulness=0.7
```

The `ask` response trace includes `grounded`, `citation_coverage`, `cited_chunk_ids`, `missing_citation_ids`, and `warnings` so callers can inspect whether an LLM answer cites the retrieved context.

### Development

```bash
python -m unittest discover -s tests
python -m cn_graphrag_eval_opt integrations
python -m cn_graphrag_eval_opt llm-config --env .env.example
python -m cn_graphrag_eval_opt llm-smoke --env .env.example --dry-run
python -m cn_graphrag_eval_opt optimize --config configs/default.toml
```

## License

MIT. See [LICENSE](LICENSE).
