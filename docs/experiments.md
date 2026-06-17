# Dataset Experiments

This page records reproducible dataset experiment results for the built-in Chinese enterprise
GraphRAG evaluation set. The numbers below come from an actual local run, not estimated README copy.

## Multi-Scale Benchmark Summary

All benchmarks use the same comparison baseline unless stated otherwise:

| Field | Baseline |
| --- | --- |
| Name | default `naive` retriever |
| Query mode | `naive` |
| Chunk size | `96` |
| Overlap | `12` |
| Top-K | `2` |
| Retrieval signals | lexical + hashing dense |
| Graph expansion | none |

| Dataset | Documents | Characters | QA cases | Best mode | Recall | Precision | Faithfulness | Token cost | Quantified outcome vs baseline |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |
| built-in enterprise corpus | 3 | 302 | 3 | `local` | 1.0000 | 1.0000 | 0.9792 | 30.5167 | `local` improves precision from 0.6667 to 1.0000 and cuts token cost by 22.3%. |
| small enterprise benchmark | 5 | 659 | 8 | `naive` | 1.0000 | 0.6875 | 0.9961 | 45.8575 | baseline remains best; it saves 39.8% token cost versus `local`. |
| medium enterprise benchmark | 10 | 1284 | 15 | `naive` | 1.0000 | 0.8333 | 0.9983 | 44.1240 | baseline remains best; it saves 48.4% token cost versus `local`. |

Interpretation:

- The 3-document built-in corpus benefits from local graph retrieval because entity-local context removes
  irrelevant chunks and lowers the estimated context cost.
- The small and medium benchmarks are keyword-heavy enterprise policy suites. Their questions share clear
  lexical anchors with the answer passages, so the `naive` lexical + hashing dense baseline is already
  strong and cheaper than graph-expanded modes.
- These results are useful product evidence: the optimizer can discover when graph retrieval helps and
  when a simpler baseline should be kept for cost and precision.

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

These are small and medium synthetic enterprise policy benchmarks for product verification and
resume/demo storytelling. They are intentionally deterministic and CI-friendly. Larger external Chinese
RAG benchmarks should be added before claiming broad benchmark superiority.

## 2026-06-17 Small Enterprise Benchmark

Command:

```bash
python -m cn_graphrag_eval_opt optimize --corpus examples/benchmarks/small_enterprise/corpus --qa examples/benchmarks/small_enterprise/qa.jsonl --out <experiment-out-dir>
```

Dataset:

| Item | Value |
| --- | ---: |
| Documents | 5 |
| Total corpus characters | 659 |
| QA cases | 8 |
| Pipeline configs compared | 5 |

Leaderboard:

| Query mode | Chunk | Overlap | Top-K | Recall | Precision | Relevance | Faithfulness | Token cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| naive | 96 | 12 | 2 | 1.0000 | 0.6875 | 0.9931 | 0.9961 | 45.8575 |
| local | 128 | 16 | 3 | 1.0000 | 0.6250 | 0.9931 | 0.9961 | 76.2100 |
| global | 128 | 16 | 3 | 0.8750 | 0.4375 | 0.8789 | 0.9961 | 80.2338 |
| hybrid | 160 | 24 | 3 | 1.0000 | 0.4167 | 0.9931 | 0.9961 | 121.4087 |
| mix | 192 | 24 | 4 | 1.0000 | 0.3438 | 0.9931 | 0.9961 | 160.9350 |

Quantified effect:

- The `naive` baseline is the best configuration on this benchmark.
- Compared with `local`, `naive` keeps recall equal at 1.0000, improves precision by 0.0625, and reduces
  estimated token cost from 76.2100 to 45.8575, a 39.8% reduction.
- Compared with `mix`, `naive` keeps recall equal at 1.0000 and reduces estimated token cost by 71.5%.

## 2026-06-17 Medium Enterprise Benchmark

Command:

```bash
python -m cn_graphrag_eval_opt optimize --corpus examples/benchmarks/medium_enterprise/corpus --qa examples/benchmarks/medium_enterprise/qa.jsonl --out <experiment-out-dir>
```

Dataset:

| Item | Value |
| --- | ---: |
| Documents | 10 |
| Total corpus characters | 1284 |
| QA cases | 15 |
| Pipeline configs compared | 5 |

Leaderboard:

| Query mode | Chunk | Overlap | Top-K | Recall | Precision | Relevance | Faithfulness | Token cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| naive | 96 | 12 | 2 | 1.0000 | 0.8333 | 0.9927 | 0.9983 | 44.1240 |
| local | 128 | 16 | 3 | 1.0000 | 0.5667 | 0.9927 | 0.9983 | 85.4373 |
| global | 128 | 16 | 3 | 1.0000 | 0.4778 | 0.9927 | 0.9983 | 89.7487 |
| hybrid | 160 | 24 | 3 | 1.0000 | 0.4222 | 0.9927 | 0.9983 | 118.1447 |
| mix | 192 | 24 | 4 | 1.0000 | 0.3333 | 0.9927 | 0.9983 | 156.8333 |

Quantified effect:

- The `naive` baseline is also the best configuration on this medium benchmark.
- Compared with `local`, `naive` keeps recall equal at 1.0000, improves precision by 0.2666, and reduces
  estimated token cost from 85.4373 to 44.1240, a 48.4% reduction.
- Compared with `mix`, `naive` keeps recall equal at 1.0000 and reduces estimated token cost by 71.9%.
