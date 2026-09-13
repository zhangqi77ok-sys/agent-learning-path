# 工具失败重试设计说明

## 策略

| 错误类型 | 是否重试 | 做法 |
|----------|----------|------|
| `TimeoutError` / `ConnectionError` | 是 | 指数退避：0.2s、0.4s、0.8s…上限 2s；最多 3 次 |
| 参数非法 / 未知工具 / 业务校验失败 | 否 | 立刻返回 `ERROR non_retryable: ...`，不再重试 |
| 可重试但超过次数 | 否 | 返回 `ERROR exhausted: ...` |

实现见 `agent_loop.py` 的 `_run_tool`：`RETRYABLE` 与 `NON_RETRYABLE_PREFIXES` 在 `tools.py`。

## 幂等与副作用

- 本阶段演示工具（时间、计算器、flaky_kb）均为只读/可重入，重试安全。
- 若工具会下单/写库：**默认不自动重试**，除非接口幂等键或「先查询再写」。

## 降级

工具最终失败时，把错误字符串回灌 `role=tool`，由模型决定改述或说明失败，而不是静默吞掉。

## 与 max_steps 的关系

- **工具重试**：单次 tool_call 内部的瞬时故障恢复  
- **max_steps**：整个 Agent Loop 的硬刹车，防止无限规划/调工具  
