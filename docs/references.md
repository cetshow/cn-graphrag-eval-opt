# Reference Projects

This project uses public RAG projects as architectural references, not as vendored source. The goal is
to borrow proven product and engineering patterns, then implement a compact original Chinese
enterprise GraphRAG evaluation toolkit.

| Project | Repository | Adopted Ideas |
| --- | --- | --- |
| Microsoft GraphRAG | https://github.com/microsoft/graphrag | Config-first `init/index/query` workflow, persistent indexing artifacts, experiment project roots, and cost-aware GraphRAG operations. |
| HKUDS LightRAG | https://github.com/HKUDS/LightRAG | Lightweight graph-enhanced retrieval, local/global/hybrid/mix query modes, incremental indexing orientation, and context traces for evaluation. |
| AutoRAG | https://github.com/Marker-Inc-Korea/AutoRAG | Corpus + QA dataset workflow, pipeline/module optimization, trial folders, summary files, and leaderboard-style comparison. |
| Ragas | https://github.com/vibrantlabsai/ragas | Metric vocabulary for context precision, context recall, answer relevancy, and faithfulness. The local baseline keeps deterministic proxy metrics for CI. |
| DeepEval | https://github.com/confident-ai/deepeval | Test-like evaluation workflow, threshold gates, and CI-friendly quality checks for RAG systems. |
| RAGFlow | https://github.com/infiniflow/ragflow | Product-oriented RAG workflow, document ingestion UX, and operator-facing evaluation experience for future UI/API work. |
| Neo4j GraphRAG Python | https://github.com/neo4j/neo4j-graphrag-python | Graph database retriever abstractions, vector/graph retrieval patterns, and production graph store integration boundaries. |
| Haystack | https://github.com/deepset-ai/haystack | Component pipeline conventions, retriever/generator separation, and production RAG application structure. |
| Pathway | https://github.com/pathwaycom/pathway | Incremental and streaming data processing mindset for future live document indexing. |
| R2R | https://github.com/SciPhi-AI/R2R | Production-facing query response shape with retrieved contexts, trace metadata, and application integration. |

## License Boundary

The repository does not copy source files from reference projects. MIT and Apache-2.0 projects can be
compatible with this repository, but resume-quality work should demonstrate original implementation,
clear attribution, and optional adapters rather than pasted upstream internals.
