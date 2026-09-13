# B1 · Durable Runtime（Temporal 对照）

对照调研稿 `docs/b1-durable-runtime-research.md`。

## 硬规则

- Workflow **不是**业务事务；打款/工单写入走 **Activity → Java 领域 API（幂等）**。
- Signal 只注入批准意图；**禁止**在 Signal 回调里直接打款。
- 幂等键：`tenant:thread:effect`。
- Worker **禁止**持业务库超级账号绕过领域 API。

## 运行

```bash
cd curriculum/advanced/B1-durable-runtime
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python demo.py
```

使用 `WorkflowEnvironment.start_time_skipping()`（无需自建 Temporal 集群）。
