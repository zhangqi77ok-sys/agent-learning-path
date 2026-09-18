# A3 · 企业租户 / RBAC / 审批 / 审计

对照 `docs/curriculum.md` A3、D9、G7。

## 硬规则

- 身份只由网关抬权签发短时内部令牌；Agent **只信**内部令牌。
- 检索 ACL 在服务端、检索前过滤；Prompt 不是边界。
- 高风险动作要审批人 + 过期 + 版本化快照；过期后副作用 = 0。

本课用 Python stub 模拟 Spring 网关；生产换成 Java 签发同一 claims 形状即可。

## 运行

```bash
cd 03-modules/A3-tenant-auth
python demo.py
```
