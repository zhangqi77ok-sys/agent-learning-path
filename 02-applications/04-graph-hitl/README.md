# Stage 04 · LangGraph / Multi-Agent + HITL

对照 JD：LangGraph / 工作流 / Multi-Agent。

## 图结构
`researcher` → `writer` → `approval_gate`(interrupt) → `finalize` | `rejected`

- Checkpointer：`MemorySaver`
- 人机：`interrupt` + `Command(resume={'approved': True/False})`
- 用 `effects` 证明 resume 不重复跑调研/撰稿

## 运行
```bash
pip install 'langgraph>=0.2' 'langchain-core>=0.3'
cd 02-applications/04-graph-hitl
python graph_app.py
```

- [PASS.md](./PASS.md)
- [RUN.md](./RUN.md)

## 交付清单
- [x] LangGraph 状态图 + HITL
- [x] PASS 深挖题
- [x] RUN.md
