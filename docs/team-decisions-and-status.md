# 团队结论与进度（写进仓库，不靠群聊独白）

> 维护约定：架构/深挖口径、过关标准、PR 状态、follow-up **以本文 + 各模块 PASS/RUN 为准**；群聊只做短同步。
> 最后更新：2026-09-13

## 主线已合入（A 线）

| 模块 | 路径 | PR | 过关要点 |
|------|------|-----|----------|
| 高级课纲 / JD / 面试题 | `docs/curriculum-advanced-3to5y.md` 等 | #6 | 3–5 年口径 |
| A1 Runtime/Harness | `curriculum/advanced/A1-runtime/` | #7 | 预算/熔断 |
| A2 长任务一致性 | `curriculum/advanced/A2-long-task/` | #8 | ledger/outbox/lease |
| A3 租户/RBAC/审批 | `curriculum/advanced/A3-tenant-auth/` | #9 | 四键/网关令牌 |
| A4 进阶 RAG | `curriculum/advanced/A4-advanced-rag/` | #10 | ACL/版本/过期 |
| A5 MCP Registry | `curriculum/advanced/A5-mcp-registry/` | #11 | 指纹/沙箱 |
| A6 Eval/OTEL/门禁 | `curriculum/advanced/A6-eval-otel/` | #12 | 硬门禁/holdout |
| A7 模型网关 | `curriculum/advanced/A7-model-gateway/` | #13 | 路由/429/缓存键 |
| A8 HA 平台 | `curriculum/advanced/A8-ha-platform/` | #14 | 双 Worker/隔离池 |
| A9 Capstone | `curriculum/advanced/A9-capstone/` | #15 | 五段演示 |

作品集主项目 = **A9**。细节看各目录 `README.md` / `PASS.md` / `RUN.md` / `HOLES.md`。

## B 线（最新框架对照）

| 项 | 状态 | 链接 / 路径 |
|----|------|-------------|
| B1 调研稿 | **已合 main** | `docs/b1-durable-runtime-research.md` · [PR #16](https://github.com/zhangqi77ok-sys/agent-learning-path/pull/16) |
| B1-code Temporal | **已合 main** | `curriculum/advanced/B1-durable-runtime/` · [PR #17](https://github.com/zhangqi77ok-sys/agent-learning-path/pull/17) |
| B2 A2A | **已合 main** | `curriculum/advanced/B2-a2a/` · [PR #19](https://github.com/zhangqi77ok-sys/agent-learning-path/pull/19) |
| B3 上下文工程 | 未开 | compaction 保留字段进 Harness |

### 深挖四条（答「用了 Temporal」会被打回）

1. checkpoint **数据** ≠ Durable **续跑**；Workflow / Activity / Signal 分工 + Activity 幂等。
2. MCP = 工具；A2A = Agent 委托；委托必须带下行身份、幂等键、取消。
3. 上下文工程进 Harness（预算/compaction 硬字段），不单靠堆 Prompt。
4. Langfuse/OTEL 对齐 A6 四层硬门禁；坏例回放进 CI。

### Java 归属（§2 已签字）

见 `docs/b1-durable-runtime-research.md` 与 `curriculum/advanced/B1-durable-runtime/OWNERSHIP.md`。

三项挂科：① Workflow 当业务事务 ② Signal 直接打款 ③ Worker 持业务库超管账号。

## 口述优先（投递前）

| 来源 | 题号 |
|------|------|
| 架构 | G1, G7, O9 |
| 深挖 | O1, O4, O5, O8, O10 |
| 证据 | Capstone 五段 + 各模块故障注入，不背框架名 |

讲法模板：**失败现场 → 修法 → Trace/Eval 防回归**。

## 非阻塞 follow-up（不挡投递 / 不挡合入）

- [ ] A5 symlink 逃逸
- [ ] A6 incomplete fixture 默认禁写 holdout（A9 已部分做）
- [ ] A8 demo2 空断言清理
- [ ] B1 demo3 真 kill Worker 续跑证明
- [ ] G7/D9 HITL 令牌续签细节
- [ ] PASS O10 七段口述（#15 合入时已补）

## 协作约定（按 maxzq 要求）

1. **关键结论、过关标准、归属表、挂科现场写进 GitHub**（本文或模块 PASS），群里只短同步。
2. 代码 PR 必须含：跑通证据（RUN）、JD/面试对照一句、故障注入。
3. GitHub API/Merge 抽风时：分支已推则贴 compare 链接；网页 Merge 后回写本文状态。

## 模拟面试

| 场次 | 文档 | 状态 |
|------|------|------|
| R1 | `docs/mock-interviews/round-01-deep-dive-and-java.md` | **通过**（深挖+架构已评分） |
| 索引 | `docs/mock-interviews/README.md` | 已建 |
| R2 | `docs/mock-interviews/round-02-q-and-capstone.md` | **通过**（深挖+架构已评分） |
| R3 | `docs/mock-interviews/round-03-g1-o10.md` | **通过**（深挖+架构已评分） |

约定：提问与解答全文进 GitHub；群聊短同步。

## 下一步

1. ~~maxzq / 架构师网页 Merge **#17**。~~ **已合**（2026-09-13）。
2. ~~Merge 后 @agent学生 开 **B2**~~ **已交付**（`curriculum/advanced/B2-a2a/`，DESIGN.md + 负例 demo）。
3. ~~**Mock Interview R1** 待评分~~ **已通过并合入**（见 `docs/mock-interviews/`）。
4. ~~**Mock Interview R2** 待评分~~ **已通过**（见 `docs/mock-interviews/round-02-q-and-capstone.md`）。
5. ~~**Mock Interview R3** 待评分~~ **已通过**。下一步：计时口述 / 简历包装。

## 简历包装

- 文档：`docs/resume-differentials.md`（三条差异化：Java 归属链 / 坏例进 CI / MCP≠A2A）
- 状态：架构①已审通过；待深挖审②③
- 下一步：O10 脱稿计时（个人练习，纪要可选入库）
