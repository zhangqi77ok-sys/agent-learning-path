# A3 过关题作答

## 权限为什么不能写在 Prompt？

模型可被注入/误工具结果欺骗；边界必须是网关身份 + 检索/工具 ACL + 审计。本课跨租户文档在 retrieve() 入口就被滤掉。

## D9 / G7 身份链

登录(gateway) → 内部 HMAC token(aud=agent-runtime) → Agent verify → 工具/检索带 tenant/user。错签、错 aud、过期、缺 token 全拒。

## 审批过期

高风险 export 审批 TTL 到期后 `approval_expired`，禁止副作用。
