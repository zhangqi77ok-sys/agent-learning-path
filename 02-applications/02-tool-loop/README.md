# Stage 02 · 单 Agent（工具 + 记忆 + 重试）

对照 JD：Tool Calling / 记忆 / Agent Loop。

## 目标

- 手写 Agent Loop（`tool_calls` → 执行 → 回灌 → 再调模型）
- 工具失败可重试（超时类）与不可重试（参数/业务）分离
- 短期记忆：本 run 内的 `messages`（会话级）

## 运行

```bash
# 仓库根目录已配置 .env（OPENAI_* 或 AGENTROUTER_*）
cd 02-applications/02-tool-loop
python agent_loop.py
```

期望日志中出现 `[retry] flaky_kb`（前两次超时），随后工具成功并给出最终中文总结。

## 文档

- [RETRY.md](./RETRY.md) 重试设计
- [PASS.md](./PASS.md) 过关题作答
- [RUN.md](./RUN.md) 跑通证据

## 交付清单

- [x] `agent_loop.py` + 3 个工具（含 flaky）
- [x] 失败重试说明
- [x] 过关题书面作答
- [x] 跑通证据
