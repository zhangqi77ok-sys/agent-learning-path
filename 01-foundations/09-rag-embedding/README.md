# Lesson 08 — Embedding 向量检索（对比 Lesson 07）

## 学什么

1. 用 Embedding 把 chunk / 问题变成向量  
2. 用余弦相似度取 TopK  
3. 同一问题对比：**关键词重叠 vs 向量检索**  
4. 理解同义改写时，向量检索通常更稳  

## 怎么跑

```bash
cd agent-learning-path
source .venv/bin/activate
export AGENTROUTER_API_KEY=...
export AGENTROUTER_BASE_URL=https://agentrouter.org/v1
export AGENTROUTER_MODEL=deepseek-v4-flash
# 按你在 AgentRouter 控制台看到的嵌入模型名修改：
export AGENTROUTER_EMBED_MODEL=text-embedding-3-small

python 01-foundations/09-rag-embedding/rag_embed.py
```

知识库复用 `01-foundations/08-rag-keyword/kb/`。

## 观察点

- 「一年能休几天假」这种改写，关键词分是否变差、向量是否仍命中 FAQ  
- score 含义不同：关键词是重叠分，向量是余弦相似度（通常 0~1）  
- 库外问题是否仍拒答  

## 验收

1. 贴一段关键词 Top3 与向量 Top3 的对比  
2. 一句话：什么时候关键词可能反而更好？  
3. 若 embedding 报错，你改成了哪个 `AGENTROUTER_EMBED_MODEL`？
