# A5 过关题作答（O5）

## MCP 工具描述被偷偷改了怎么办？

Registry 保存已评审的 `description` + `schema_fingerprint` + 钉版本。调用时比对 MCP 广告：描述不一致 → `description_tamper`；schema hash 不一致 → `schema_fingerprint_mismatch`。未评审工具不能注册。

## 沙箱

写文件必须落在 sandbox root；路径穿越 = `sandbox_escape`。
