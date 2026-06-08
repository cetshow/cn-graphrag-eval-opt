# Reference Projects

This project uses public RAG projects as architectural references, not as vendored source.

## Microsoft GraphRAG

- Repository: https://github.com/microsoft/graphrag
- License: MIT
- Adopted ideas: explicit `init/index/query` workflow, config-driven project roots, persistent
  indexing artifacts, and responsible warning that graph indexing can be expensive on real corpora.

## HKUDS LightRAG

- Repository: https://github.com/HKUDS/LightRAG
- License: MIT
- Adopted ideas: lightweight graph-enhanced retrieval, local/global/hybrid/mix query modes, and
  retrieval contexts that can be evaluated by downstream metrics.

## AutoRAG

- Repository: https://github.com/Marker-Inc-Korea/AutoRAG
- License: Apache-2.0
- Adopted ideas: corpus + QA dataset workflow, optimization over multiple RAG module combinations,
  trial folders, summary files, and leaderboard-style comparison.

## Ragas

- Repository: https://github.com/vibrantlabsai/ragas
- License: Apache-2.0
- Adopted ideas: metric vocabulary for context precision, context recall, answer relevancy, and
  faithfulness. This repository keeps deterministic proxy metrics by default so CI does not need LLM
  credentials.

## R2R

- Repository: https://github.com/SciPhi-AI/R2R
- Adopted ideas: production-facing query response shape with retrieved contexts and trace metadata.
