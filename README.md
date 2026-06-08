# cn-graphrag-eval-opt

面向中文企业文档的 GraphRAG 检索评测与优化系统。项目参考
[HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) 的轻量图检索思想，以及
[Marker-Inc-Korea/AutoRAG](https://github.com/Marker-Inc-Korea/AutoRAG) 的 pipeline
自动评测思想，包装成一个可本地运行、可量化实验、可写入简历的工程项目。

## 项目定位

- 中文企业文档：制度、合同、产品手册、运维 SOP、FAQ。
- GraphRAG：用轻量实体共现图补强传统 chunk 检索。
- RAG 评测：输出 retrieval recall、context precision、answer relevance、faithfulness。
- 自动优化：批量比较 chunk size、overlap、top-k、query mode，推荐最优配置。
- 可选集成：预留 LightRAG、AutoRAG、Ragas adapter，基础功能不依赖外部 API。

## 快速运行

```powershell
cd D:\Data\Projects\cn-graphrag-eval-opt
$env:PYTHONPATH="src"
python -m cn_graphrag_eval_opt optimize --corpus examples/corpus --qa examples/qa.jsonl --out runs/demo
```

运行后会生成：

- `runs/demo/summary.json`
- `runs/demo/report.md`
- `runs/demo/best_config.json`

## 简历叙事

可包装为：

> 基于 LightRAG 与 AutoRAG 思路，开发面向中文企业文档的 GraphRAG 检索评测与优化系统，实现中文切分、图增强检索、RAG 指标评测、批量策略搜索和可复现实验报告，支持在无外部 LLM API 的环境下稳定运行 baseline，并预留 LightRAG/Ragas/AutoRAG 集成接口。

## 开发验证

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```
