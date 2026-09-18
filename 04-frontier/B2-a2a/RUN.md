# B2 RUN evidence

=== demo1: happy path delegate ===
done {'echo': {'q': '差旅'}, 'tenant': 'tenantA'} side_effects: 1
=== demo2: duplicate idempotency → same task, no double side effect ===
same_id: 5277d367 side_effects: 1
SLO_ok_idempotent_delegate: True
=== demo3: missing identity / idem / deadline ===
blocked: missing_identity
blocked: missing_idempotency_key
blocked: missing_deadline
=== demo4: past deadline → cancelled, side_effect=0 ===
cancelled side_effects: 0
SLO_ok_deadline_cancel: True
=== demo5: explicit cancel before run ===
SLO_ok_explicit_cancel: True
=== demo6: cross-tenant cancel blocked ===
blocked: cross_tenant_cancel
=== demo7: idem key tenant mismatch ===
blocked: idempotency_tenant_mismatch
ALL_OK

