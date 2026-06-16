# Dataset Experiments

This page records reproducible dataset experiment results for the built-in Chinese enterprise
GraphRAG evaluation set. The numbers below come from an actual local run, not estimated README copy.

## 2026-06-17 Built-In Enterprise Corpus

Command:

```bash
python -m cn_graphrag_eval_opt optimize --config configs/default.toml --out <experiment-out-dir>
```

Dataset:

| Item | Value |
| --- | ---: |
| Documents | 3 |
| Total corpus characters | 302 |
| QA cases | 3 |
| Pipeline configs compared | 5 |
| Metric mode | deterministic offline proxy metrics |

Best configuration:

| Field | Value |
| --- | --- |
| Query mode | `local` |
| Chunk size | `128` |
| Overlap | `16` |
| Top-K | `3` |
| Chunk strategy | `recursive` |

Comparison baseline:

| Field | Value |
| --- | --- |
| Name | default `naive` retriever |
| Query mode | `naive` |
| Chunk size | `96` |
| Overlap | `12` |
| Top-K | `2` |
| Retrieval signals | lexical + hashing dense |
| Graph expansion | none |

Best metrics:

| Metric | Value |
| --- | ---: |
| retrieval_recall | 1.0000 |
| context_precision | 1.0000 |
| answer_relevance | 1.0000 |
| faithfulness | 0.9792 |
| estimated_context_chars | 97.6667 |
| estimated_token_cost | 30.5167 |

Leaderboard:

| Query mode | Chunk | Overlap | Top-K | Recall | Precision | Relevance | Faithfulness | Token cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| naive | 96 | 12 | 2 | 1.0000 | 0.6667 | 1.0000 | 0.9792 | 39.2733 |
| local | 128 | 16 | 3 | 1.0000 | 1.0000 | 1.0000 | 0.9792 | 30.5167 |
| global | 128 | 16 | 3 | 1.0000 | 0.8333 | 1.0000 | 0.9792 | 51.6667 |
| hybrid | 160 | 24 | 3 | 1.0000 | 0.4444 | 1.0000 | 0.9792 | 91.5600 |
| mix | 192 | 24 | 4 | 1.0000 | 0.4444 | 1.0000 | 0.9792 | 91.5600 |

Quantified effect:

- Compared with the default `naive` baseline (`query_mode=naive`, `chunk_size=96`, `overlap=12`,
  `top_k=2`; lexical + hashing dense signals without entity-graph expansion), the best `local` config
  improves context precision from 0.6667 to 1.0000 and reduces estimated token cost from 39.2733 to
  30.5167, a 22.3% reduction.
- Compared with the global config, the best config keeps the same recall and faithfulness while
  reducing estimated token cost by 40.9%.
- Compared with hybrid/mix, the best config keeps the same recall and faithfulness while reducing
  estimated token cost by 66.7%.
- The result passes the default product quality gate thresholds used in CI:
  `retrieval_recall >= 0.8` and `faithfulness >= 0.7`.

Case-level results for the best config:

| Question | Retrieved chunks | Recall | Precision | Faithfulness |
| --- | --- | ---: | ---: | ---: |
| 谁负责发放电脑？ | `hr_onboarding:0000` | 1.0000 | 1.0000 | 0.9375 |
| 哪个部门每月复核高危权限？ | `security_access:0000` | 1.0000 | 1.0000 | 1.0000 |
| 员工提交发票后多久完成审核？ | `expense_policy:0000` | 1.0000 | 1.0000 | 1.0000 |

Scope note:

This is a small built-in regression dataset for product verification and resume/demo storytelling. It
is intentionally deterministic and CI-friendly. Larger external Chinese RAG benchmarks should be added
before claiming broad benchmark superiority.
