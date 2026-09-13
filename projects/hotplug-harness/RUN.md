# RUN.md — demo 捕获输出

```text
plugin roots: .../projects/hotplug-harness/plugins
loaded: {'tools': ['echo', 'flaky'], 'models': ['forbidden_tool', 'infinite_same_tool', 'scripted_happy', 'unique_infinite'], 'policies': ['allowlist']}
=== a) happy path with plugins ===
succeeded steps 3 tools 2 final done run_id ...
OK happy_path
=== b) select/load tool from plugins dir (no core change) ===
discovered_tool_files: ['echo', 'flaky']
registry.tools: ['echo', 'flaky']
hotplugged_greet_result: hi:maxzq
OK hotplug_tool
=== c) circuit_open on duplicate tool signature ===
circuit_open steps 4 tool_calls 3
OK circuit_open
=== d) budget_exceeded ===
budget_exceeded steps 5
tool_spans 4
OK budget_exceeded
=== e) forbidden tool blocked by policy ===
policy_blocked blocked:tool_not_allowlisted:drop_db
OK policy_blocked
ALL_OK
```

pytest: `7 passed`
