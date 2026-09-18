# Stage 03 跑通证据

日期：2026-09-13  
生成模型：`grok-4.6`  
检索：本地 TF-IDF（中转站无 Embedding；CJK 用单字/双字）  
命令：`python rag_answer.py`

关键结果摘要：

1. Agent 定义题：命中 `agent_basics-*`，回答带 `[agent_basics-2]`
2. 何时不该 RAG：命中 `rag_notes-*`，带引用
3. 跨城差旅：命中 `company_faq-2` →「需提前申请差旅单」
4. 火星年假：虽有弱相关命中，模型按约束回答「不知道 / 资料没有」

对照 JD：RAG 检索 + 引用生成 + 无依据时不硬编。
