# Stage 03 · 生产向 RAG

对照 JD：RAG / 向量库 / 知识库。

## 说明

当前中转站 **无可用 Embedding 模型**，本阶段用本地 TF-IDF 余弦检索作为检索层，生成仍走 Chat 模型。  
换成真实向量库时，只需替换 `LexicalIndex.search`，生成与引用约束不变。

## 运行

```bash
cd 02-applications/03-rag-service
python rag_answer.py
```

## 文档

- [PASS.md](./PASS.md)
- [RUN.md](./RUN.md)

## 交付清单

- [x] kb + chunk + retrieve + 带引用生成
- [x] 弱检索降级
- [x] PASS.md
- [x] RUN.md
