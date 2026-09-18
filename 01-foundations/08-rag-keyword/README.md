# Lesson 07 — RAG 入门（作品 #1 起点）

## 学什么

1. 把知识库文档切成 chunk  
2. 用简单关键词重叠检索 TopK（先不引入向量库）  
3. 把证据塞进 Prompt，要求模型基于证据回答并引用  
4. 对「库里没有的问题」应回答不知道  

## 怎么跑

```bash
# 在仓库根目录
source .venv/bin/activate   # 按需
export AGENTROUTER_API_KEY=...
python 01-foundations/08-rag-keyword/rag_basic.py
```

## 你要观察的点

- 检索分高的 chunk 是否真相关  
- 有证据时回答是否带来源编号  
- 「火星年假」是否拒答 / 说不知道  

## 下一课预告

Embedding + 向量检索（或本地简易向量），对比本课关键词检索的差异。
