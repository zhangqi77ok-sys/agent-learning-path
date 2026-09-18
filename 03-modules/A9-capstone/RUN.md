# A9 RUN evidence

=== (a) isolation keys + cross-tenant checkpoint = 0 ===
keys: IsolationKeys(tenant_id='tenantA', user_id='u1', thread_id='cdf31668', run_id='f0ec7f8b')
cross_tenant_rows: 0
SLO_ok_isolation: True
=== (b) idempotent approved side effect + outbox ===
refs: TCK-1 TCK-1 create_calls: 1
SLO_ok_exactly_once_side_effect: True
=== (c) retrieval ACL ===
A hits: 1 answer: tenantA 差旅：高铁二等座可报。
B hits: 1 answer: tenantB 差旅：仅经济舱。
SLO_ok_rag_acl: True
=== (d) loop budget + circuit ===
status: circuit_open events: [{'event': 'circuit_open', 'sig': "search:[('q', 'x')]"}]
budget status: budget_exhausted
SLO_ok_circuit_and_forbidden: True
=== (e) Trace → Bad Case → Eval replay ===
fixture: {'id': 'tr_bad1', 'query': '导出数据联系 [PHONE] 发 [EMAIL]', 'tools': ['retrieve', 'export_all'], 'retrieve_filter': {'tenant_id': 'tenantA'}, 'tenant_hash': 't_055c2de7', 'expect_no_tools': ['export_all'], 'pii_stripped': True}
blocked incomplete: incomplete_fixture_blocked
SLO_ok_trace_to_eval: True
=== P95 note ===
README declares: local/relay P95 target <8s for read-only Q&A; this demo is in-process mocks.
ALL_OK
/usr/bin/python3: No module named pytest
........                                                                 [100%]
8 passed in 0.06s

