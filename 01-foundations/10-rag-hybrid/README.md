# Lesson 09 — 混合检索（关键词 + 向量 + RRF）

## 学什么

生产 RAG 很少只靠一路召回。本课把两路结果用 **RRF（Reciprocal Rank Fusion）** 融合：

```text
score(d) = Σ 1 / (k + rank_i(d))
```

- 关键词：稳抓专有名词、制度原文  
- 向量：稳住同义改写  
- RRF：不要求两路分数同量纲，只看排名  

## 怎么跑

```bash
cd agent-learning-path
git pull
source .venv/bin/activate
export AGENTROUTER_API_KEY=...
export AGENTROUTER_BASE_URL=https://agentrouter.org/v1
export AGENTROUTER_MODEL=deepseek-v4-flash
export AGENTROUTER_EMBED_MODEL=text-embedding-3-small

python 01-foundations/10-rag-hybrid/rag_hybrid.py
```

若 embedding 失败，脚本会自动退化为仅关键词，课仍能学完融合思想。

## 观察点

- 同一问题下关键词 Top5、向量 Top5、融合 Top3 是否不同  
- 专有数字（如 2000 元、10 天）关键词是否更强  
- 同义改写时融合是否比单路更稳  

## 下一课

把 `KB_SEARCH` 做成 Agent 工具，检索进入 Agent Loop。
