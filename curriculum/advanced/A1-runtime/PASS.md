# A1 过关题作答（对 Q1 / Q11）

## Q1. Runtime 和 while 调 LLM 差在哪？硬约束谁管？

while 循环只有「再问一次模型」。Harness 控制面要管：

1. **隔离键**：tenant / user / thread / run（本课 `RunState`）
2. **Loop 边界**：max_steps / 墙钟 / tool 次数预算
3. **Policy**：工具白名单；拒绝不在 schema/allowlist 的调用
4. **熔断**：重复 tool signature → `circuit_open`，防止烧钱死循环
5. **Cancel / Replay**：协作式取消；事件账可回放进评测

框架给图与检查点；**预算、ACL、租户键、熔断、Replay 语义**必须自建。

## Q11. 死循环怎么在烧钱前停？

本课演示：相同 tool signature 连续 ≥3 次 → `circuit_open`；另有 max_steps / max_wall_ms / max_tool_calls。  
SLO：≤8 step 或 ≤30s 进入熔断；预算耗尽后不再产生新 tool span。
