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

## 2026-06-17 Added Seven-Experiment Suite

This section adds the seven experiment categories that are useful for demonstrating product fit beyond
the first built-in dataset: scale-up, cross-document multi-hop QA, noisy retrieval, top-k cost/effect
curves, real MiMo LLM answering, chunking strategy comparison, and vertical-industry transfer.

Shared baseline unless stated otherwise:

- `query_mode=naive`
- `chunk_size=96`
- `overlap=12`
- `top_k=2`
- Retrieval signals: lexical + hashing dense
- Graph expansion: none

| # | Experiment | Dataset / setup | Best or observed result | Quantified analysis |
| ---: | --- | --- | --- | --- |
| 1 | Scale-up corpus | `scale_enterprise`, 12 docs, 1326 chars, 12 QA | `naive`, recall 0.9722, precision 0.7917, faithfulness 1.0000, token cost 39.7642 | Baseline remains best; versus `local`, it improves recall by 0.0555, precision by 0.2084, and cuts token cost by 49.6%. |
| 2 | Cross-document multi-hop QA | `multi_hop_enterprise`, 6 docs, 505 chars, 6 QA | `hybrid`, recall 0.9444, precision 0.6667, faithfulness 1.0000, token cost 76.1467 | `hybrid` improves recall over baseline from 0.8333 to 0.9444, but costs 44.3% more and lowers precision from 0.7500 to 0.6667. |
| 3 | Noisy retrieval robustness | `noisy_enterprise`, 3 relevant + 3 distractor docs, 507 chars, 4 QA | `naive`, recall 1.0000, precision 1.0000, faithfulness 1.0000, token cost 50.4700 | Baseline is robust when lexical anchors are clear; versus `local`, it improves precision by 0.1667 and cuts token cost by 20.1%. |
| 4 | Cost-effect top-k curve | `multi_hop_enterprise`, `hybrid`, chunk 160, overlap 24, top-k sweep | top-k 5 reaches recall 1.0000; top-k 3 is the default best-ranked tradeoff | top-k 3 improves recall over top-k 1 from 0.7778 to 0.9444 but raises token cost by 213.7%; top-k 5 reaches full recall but costs another 65.7% over top-k 3. |
| 5 | Real MiMo LLM answer audit | 3 online MiMo calls over built-in, multi-hop, and noisy datasets | 1/3 answers passed strict chunk-id grounding; average citation coverage 0.3333 | Single-hop answer used exact `chunk_id` and passed; two harder cases used numeric citations like `[1]`, so the audit correctly flagged `answer_missing_chunk_citation`. |
| 6 | Chunking strategy comparison | `scale_enterprise`, `naive`, top-k 2, chunk 96 / overlap 12 | `sentence` and `recursive` tie; `fixed` is worse | `fixed` keeps recall 0.9722 but drops precision from 0.7917 to 0.7083, drops answer relevance from 1.0000 to 0.9040, and costs 23.6% more. |
| 7 | Vertical-industry transfer | `vertical_industry`, finance/manufacturing/retail/healthcare, 4 docs, 343 chars, 4 QA | `global`, recall 1.0000, precision 0.5417, faithfulness 1.0000, token cost 57.6575 | `global` improves precision over baseline from 0.5000 to 0.5417 at 12.7% higher token cost, showing graph expansion can help when entity terms are domain-specific. |

### Scale-Up Corpus Leaderboard

Command:

```bash
python -m cn_graphrag_eval_opt optimize --corpus examples/benchmarks/scale_enterprise/corpus --qa examples/benchmarks/scale_enterprise/qa.jsonl --out <experiment-out-dir>
```

| Query mode | Chunk | Overlap | Top-K | Recall | Precision | Relevance | Faithfulness | Token cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| naive | 96 | 12 | 2 | 0.9722 | 0.7917 | 1.0000 | 1.0000 | 39.7642 |
| local | 128 | 16 | 3 | 0.9167 | 0.5833 | 0.9300 | 1.0000 | 78.8825 |
| global | 128 | 16 | 3 | 0.9167 | 0.5417 | 0.9300 | 1.0000 | 81.4083 |
| hybrid | 160 | 24 | 3 | 0.9722 | 0.3889 | 1.0000 | 1.0000 | 100.2083 |
| mix | 192 | 24 | 4 | 0.9722 | 0.2917 | 1.0000 | 1.0000 | 133.6992 |

### Cross-Document Multi-Hop Leaderboard

Command:

```bash
python -m cn_graphrag_eval_opt optimize --corpus examples/benchmarks/multi_hop_enterprise/corpus --qa examples/benchmarks/multi_hop_enterprise/qa.jsonl --out <experiment-out-dir>
```

| Query mode | Chunk | Overlap | Top-K | Recall | Precision | Relevance | Faithfulness | Token cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| naive | 96 | 12 | 2 | 0.8333 | 0.7500 | 0.5004 | 1.0000 | 52.7617 |
| local | 128 | 16 | 3 | 0.8889 | 0.6111 | 0.5004 | 1.0000 | 76.0950 |
| global | 128 | 16 | 3 | 0.8889 | 0.7222 | 0.4598 | 1.0000 | 58.0200 |
| hybrid | 160 | 24 | 3 | 0.9444 | 0.6667 | 0.5004 | 1.0000 | 76.1467 |
| mix | 192 | 24 | 4 | 0.9444 | 0.6250 | 0.5004 | 1.0000 | 100.0000 |

### Noisy Retrieval Leaderboard

Command:

```bash
python -m cn_graphrag_eval_opt optimize --corpus examples/benchmarks/noisy_enterprise/corpus --qa examples/benchmarks/noisy_enterprise/qa.jsonl --out <experiment-out-dir>
```

| Query mode | Chunk | Overlap | Top-K | Recall | Precision | Relevance | Faithfulness | Token cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| naive | 96 | 12 | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 50.4700 |
| local | 128 | 16 | 3 | 1.0000 | 0.8333 | 1.0000 | 1.0000 | 63.2050 |
| global | 128 | 16 | 3 | 1.0000 | 0.7500 | 1.0000 | 1.0000 | 69.2975 |
| hybrid | 160 | 24 | 3 | 1.0000 | 0.6667 | 1.0000 | 1.0000 | 75.3900 |
| mix | 192 | 24 | 4 | 1.0000 | 0.5000 | 1.0000 | 1.0000 | 101.3275 |

### Top-K Cost-Effect Curve

Setup: `multi_hop_enterprise`, `query_mode=hybrid`, `chunk_size=160`, `overlap=24`.

| Top-K | Recall | Precision | Faithfulness | Token cost |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0.7778 | 1.0000 | 1.0000 | 24.2700 |
| 2 | 0.8333 | 0.7500 | 1.0000 | 49.5300 |
| 3 | 0.9444 | 0.6667 | 1.0000 | 76.1467 |
| 4 | 0.9444 | 0.6250 | 1.0000 | 100.0000 |
| 5 | 1.0000 | 0.5333 | 1.0000 | 126.1450 |
| 8 | 1.0000 | 0.4722 | 1.0000 | 150.3100 |

### MiMo LLM Answer Audit

Setup: online `mimo-v2.5-pro` via `.env`, three representative questions.

| Scenario | Retrieval config | Grounded | Citation coverage | Audit finding |
| --- | --- | ---: | ---: | --- |
| built-in single-hop access question | `local`, top-k 3 | true | 1.0000 | MiMo cited `security_access:0000` exactly. |
| multi-hop supplier onboarding question | `hybrid`, top-k 3 | false | 0.0000 | Answer used numeric references like `[1]` instead of exact chunk ids. |
| noisy privacy question | `naive`, top-k 2 | false | 0.0000 | Answer was semantically correct but used numeric citation format, so strict audit flagged it. |

Strict grounded pass rate: 1/3 = 33.3%. This is a product-relevant result: retrieval can surface the
right evidence, while production LLM answering still needs strict citation-format prompting or a citation
normalization layer before the answer can be considered fully grounded.

### Chunking Strategy Comparison

Setup: `scale_enterprise`, `query_mode=naive`, `chunk_size=96`, `overlap=12`, `top_k=2`.

| Strategy | Chunks | Recall | Precision | Relevance | Faithfulness | Token cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sentence | 23 | 0.9722 | 0.7917 | 1.0000 | 1.0000 | 39.7642 |
| recursive | 23 | 0.9722 | 0.7917 | 1.0000 | 1.0000 | 39.7642 |
| fixed | 24 | 0.9722 | 0.7083 | 0.9040 | 1.0000 | 49.1683 |

### Vertical-Industry Transfer Leaderboard

Command:

```bash
python -m cn_graphrag_eval_opt optimize --corpus examples/benchmarks/vertical_industry/corpus --qa examples/benchmarks/vertical_industry/qa.jsonl --out <experiment-out-dir>
```

| Query mode | Chunk | Overlap | Top-K | Recall | Precision | Relevance | Faithfulness | Token cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| naive | 96 | 12 | 2 | 1.0000 | 0.5000 | 1.0000 | 1.0000 | 51.1725 |
| local | 128 | 16 | 3 | 1.0000 | 0.5417 | 1.0000 | 1.0000 | 57.6575 |
| global | 128 | 16 | 3 | 1.0000 | 0.5417 | 1.0000 | 1.0000 | 57.6575 |
| hybrid | 160 | 24 | 3 | 1.0000 | 0.3333 | 1.0000 | 1.0000 | 77.0325 |
| mix | 192 | 24 | 4 | 1.0000 | 0.2500 | 1.0000 | 1.0000 | 102.1900 |

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
