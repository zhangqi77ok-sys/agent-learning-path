# A9 过关（O10 / Q15）

能对着 10 个死亡坑逐条指出：课堂缺什么、Capstone 补了什么、哪条故障注入证明。五段演示缺一不可；跨租户越权=0；已批准副作用恰好 1；危险工具误调用=0。

## O10 七段口述（对着本 Capstone 故障注入）

1. **场景与影响**：企业知识助手误把 `export_all` 当普通工具；或跨租户读到 checkpoint / 文档。影响面：数据泄漏与重复开票。
2. **Ownership**：你负责控制面边界（身份、ACL、Outbox、预算熔断、Trace→Eval），不甩锅「模型抽风」。
3. **Trace 卡点**：(e) fixture 可见 `tools` 含 `export_all`、缺/有 `retrieve.filter`；跨租户读在 store 层直接 0 行。
4. **根因**：权限写在 Prompt；副作用只靠 checkpoint；危险工具无硬禁；incomplete fixture 仍进金标。
5. **修复**：网关 HMAC 四键；(b) ledger+Outbox+Idempotency-Key；(d) circuit/budget + FORBIDDEN；(e) incomplete 禁入库。
6. **回归**：`tests/test_negatives.py` 8 条负例 + 五段 demo；A6 硬门禁拦危险工具。
7. **指标**：跨租户越权=0；已批准副作用恰好 1；危险工具误调用=0；只读问答 P95 目标见 README（课程约定）。
