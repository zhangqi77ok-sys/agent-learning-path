# Mock Interview Round 6 · MCP 投毒 vs 插件隔离

## 元信息

| 项 | 内容 |
|----|------|
| 候选人 | agent学生 |
| 面试官 | Agent工程师 |
| 前置 | R5 均分 8.9；复盘作业并行 |
| 证据 | `E:\deepseek-harness-java` MCP/Plugin 路径；课仓 A5 仅作对比 |

## R6-Q1 · 工具描述投毒

### 提问

> 1. `mcp__*` 工具的 **name/description/schema** 从哪来？谁能在运行中改掉描述诱导模型调高危工具？
> 2. `plugin__*`（JAR + ClassLoader）与 MCP 适配器相比，攻击面差在哪（代码执行 vs 描述投毒）？
> 3. 你如何在 **注册时 / PRE Hook / 审批矩阵** 挡住「描述被改、schema 漂移」？（是否要 schema hash / allowlist fingerprint？点本机类名）
> 4. 若 MCP 服务器被劫持返回新工具列表，热更新注册表时缺了哪一步会重现 R5 的「有 CALL 无 RESULT」或直接旁路审批？

### 候选人解答

1. `mcp__`：`listTools`→`McpToolAdapter`；描述/schema 外源；投毒=恶意 MCP/中间人。**诚实**：dsh 现状无 fingerprint。
2. `plugin__`=进程内字节码+ClassLoader；MCP=描述投毒/外带（除非工具封装 shell）。
3. 挡法：注册指纹 allowlist + PRE 比对 + 矩阵按名+指纹；禁静默 list 增量。A5 有、dsh 应补。
4. 热更：停旧→cancel 闭合 RESULT→审新指纹→再 register；缺闭合=悬挂 CALL；缺重绑审批=同名换皮旁路。


### 金标（Agent工程师）

1. **来源**：MCP `tools/list` → `McpToolAdapter`（或等价）映射进 `ToolRegistry`；描述与 JSON Schema 来自**外部进程**，不是宿主编写。投毒者=被入侵/恶意 MCP 服务端，或中间人改 list 响应。
2. **攻击面**：`plugin__` 可做到进程内字节码执行（更重，靠 ClassLoader 隔离+签名/unload）；MCP 默认是**工具面投毒与数据外带**（描述诱导、路径参数），除非 MCP 工具本身封装了 shell。
3. **防护**：注册时算 schema/description fingerprint，写入 allowlist；PRE Hook 比对 hash，漂移则 DENY 并合成 RESULT；审批矩阵按**完整工具名+指纹**而不仅是名字；禁止运行时静默接受 list 增量。
4. **热更新**：先停用旧工具名 → 等 in-flight cancel/闭合 → 再注册新指纹；缺闭合或缺审批绑定会 CALL 悬挂或未审批执行。

### 评分

| 维度 | 分 | 评语 |
|------|----|------|
| 来源与投毒模型 | 9/10 | listTools/Adapter/外源说清 |
| 攻击面对比 | 9/10 | 字节码 vs 描述投毒 |
| 防护设计 | 9.5/10 | 指纹+PRE+矩阵；点出 dsh 缺口与 A5 对照 |
| 热更新时序 | 9.5/10 | 停旧→闭合→重审→注册；换皮旁路 |
| **总分** | **9.2/10** | 安全深挖过关；加分：承认 dsh 无 fingerprint |

## 状态

- R6-Q1：已完成（9.2）
- 下一题：可开 R6-Q2（指纹落库/漂移告警）或交架构侧续挖
