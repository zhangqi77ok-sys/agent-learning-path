# A4 · 进阶 RAG（混合检索 / 版本过期 / 检索前 ACL）

对照课纲 A4、口试 O4/O7。

## 硬规则

- 检索 API **不接受**客户端 `tenant_id`，只信 Identity。
- ACL + 租户 + 生效窗在打分前过滤。
- 文档版本不可变；任务可 pin `kb_alias`；别名原子切换不影响历史 pin。

## 运行

```bash
cd 03-modules/A4-advanced-rag
python demo.py
```
