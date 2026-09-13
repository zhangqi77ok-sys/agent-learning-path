# 10 个死亡坑：课堂缺什么 → Capstone 补了什么

| # | 坑 | Capstone 补丁 | 证明 |
|---|----|---------------|------|
| 1 | Checkpoint≠业务一致性 | effect ledger + outbox | (b) mock create_calls=1 |
| 2 | 无 Worker 租约 | A8 队列租约（本控制面委托平台层） | A8 demo1 |
| 3 | HITL 无身份/过期 | ApprovalStore 审批人+过期+快照哈希 | test_b_expired |
| 4 | 租户只在 State | 网关 HMAC 令牌注入四键 | (a) + forged token |
| 5 | MCP 投毒 | A5 registry 指纹（工具白名单 FORBIDDEN） | (d) export_all |
| 6 | RAG 无 ACL | retrieve 前 tenant/role 过滤 | (c) |
| 7 | 无 Eval 门禁 | trace_to_fixture + regression | (e) |
| 8 | 无成本/P99 | A7 预算路由 + README P95 声明 | A7 + README |
| 9 | 无 Spring 集成 | issue_internal_token 模拟 Java 网关 | identity.py |
| 10 | 无事故闭环 | Bad Case 入库 + 负例 pytest | tests/ |
