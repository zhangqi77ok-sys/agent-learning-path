# Stage 04 过关题作答

## 1. 状态机里「状态」存了什么、为什么要持久化检查点？
本图状态包括：`query / research / draft / approved / final / effects`。Checkpoint（`MemorySaver`）按 `thread_id` 存节点状态，HITL 暂停或进程抖动后可从断点恢复，不必重跑已完成的 researcher/writer。

## 2. 人机回环卡在哪一节点、恢复时如何避免重复副作用？
卡在 `approval_gate` 的 `interrupt()`。批准/拒绝通过 `Command(resume=...)` 注入。已执行节点不会在 resume 时自动再跑；本课用 `effects` 验证 researcher/writer 各只出现一次。外部写操作还应写状态或用幂等键。

## 3. 什么场景该拆 Multi-Agent，什么场景单 Agent 就够？
单 Agent：工具少、目标单一、上下文短。拆 Multi-Agent/多节点角色：职责冲突、不同提示/权限、要独立重试与评测。本课 researcher/writer/human 分离，解耦找证据、写草案、担责批准。
