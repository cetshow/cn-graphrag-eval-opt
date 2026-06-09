# Resume Framing

## Problem

Chinese enterprise RAG projects often stop at a single demo query. That makes it hard to prove whether
retrieval quality improved after changing chunking, graph expansion, top-k, or query mode. This project
turns Chinese enterprise documents into a repeatable GraphRAG evaluation and optimization workflow.

## Architecture

The toolkit loads Markdown/TXT policy documents, splits them with Chinese-aware chunking, builds an
entity co-occurrence graph, retrieves with LightRAG-style `naive`, `local`, `global`, `hybrid`, and
`mix` modes, evaluates each QA case, and ranks pipeline configurations. It writes reproducible
AutoRAG-style artifacts: corpus manifests, chunks, entity graphs, case-level metrics, leaderboards,
best configs, and Markdown reports.

## Metrics

The baseline is deterministic so it can run in CI without model credentials. It tracks retrieval
recall, context precision, answer relevance, faithfulness, estimated context characters, and estimated
token cost. Optional adapter points map the local metric vocabulary to Ragas-style evaluation concepts.

## Impact

The project demonstrates more than prompt engineering. It shows experiment design, retrieval
architecture, graph reasoning, quality measurement, pipeline optimization, reproducible artifacts, and
production-facing query traces. These are the parts interviewers can ask about deeply.

## Interview Pitch

Built a Chinese enterprise GraphRAG evaluation and optimization toolkit inspired by Microsoft GraphRAG,
LightRAG, AutoRAG, Ragas, and R2R. Implemented config-driven indexing, graph-enhanced retrieval modes,
deterministic RAG metrics, pipeline search, query tracing, and reproducible reports so changes to a RAG
pipeline can be measured rather than guessed.

## Resume Bullet

- Built a Chinese enterprise GraphRAG evaluation toolkit with config-driven indexing, graph-enhanced
  retrieval, deterministic RAG metrics, pipeline optimization, traced query responses, and reproducible
  experiment artifacts including corpus manifests, entity graphs, case-level results, leaderboards, and
  reports.
