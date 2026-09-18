# A5 · MCP / Registry / 沙箱

对照课纲 A5、口试 O5。

## 硬规则

- MCP 广告（description/schema）**不是**安全边界。
- Registry 钉版本 + schema 指纹；描述被改 / schema 被改 → fail-closed。
- 沙箱只允许白名单根目录写入；拒绝 `..` 与绝对路径。

## 运行

```bash
cd 03-modules/A5-mcp-registry
python demo.py
```
