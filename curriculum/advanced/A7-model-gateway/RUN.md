# A7 RUN evidence

=== demo1: happy route premium ===
premium 10 ['route', 'success']
=== demo2: 429 on premium → fallback economy, terminal <15s ===
model: economy events: [{'event': 'route', 'primary': 'premium', 'fallback': 'economy', 'reason': 'default', 'budget_left': 4990}, {'event': 'upstream_error', 'model': 'premium', 'code': '429'}, {'event': 'success', 'model': 'economy', 'tokens': 12, 'elapsed_ms': 0.0}] elapsed_ms: 0.0
SLO_ok_429_terminal_lt_15s: True
=== demo3: cross-tenant same query must NOT share cache ===
SLO_ok_cross_tenant_cache_0: True
=== demo4: budget exhausted — no premium call ===
blocked: budget_exhausted:tenantPoor
degraded model: economy [{'event': 'route', 'primary': 'economy', 'fallback': 'economy', 'reason': 'low_budget', 'budget_left': 10}, {'event': 'success', 'model': 'economy', 'tokens': 10, 'elapsed_ms': 0}]
SLO_ok_over_budget_premium_0: True
=== demo5: high sensitivity → safe-small ===
safe-small [{'event': 'route', 'primary': 'safe-small', 'fallback': 'economy', 'reason': 'high_sensitivity', 'budget_left': 4958}]
ALL_OK

