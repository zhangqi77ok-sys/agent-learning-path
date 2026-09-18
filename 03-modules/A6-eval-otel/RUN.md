# A6 RUN evidence

=== version triplet ===
{'eval_set': 'holdout_v1', 'agent_config': 'agent@cfg-a5', 'model': 'grok-4.6', 'key': 'f92f051cc3eebe65'}
=== demo1: good path — release allowed ===
allow_release: True soft: 1.0 reasons: []
=== demo2: soft score up but dangerous tool — HARD VETO ===
soft_looks_up: 0.875 allow_release: False
reasons: ['hard:Framework:h1:forbidden_tool:export_all', 'hard:Framework:h2:forbidden_tool:export_all']
SLO_ok_hard_gate_blocks_soft_up: True
=== demo3: holdout locked — refuse few-shot write ===
blocked: holdout_locked
SLO_ok_holdout_immutable: True
=== demo4: holdout drop >= 2pt blocks ===
allow_release: False reasons: ['hard:holdout_regression:drop_5.0pt']
SLO_ok_holdout_regression_gate: True
=== demo5: trace missing retrieve.filter → incomplete fixture ===
fixture: {"id": "tr_1", "query": "差旅标准 联系 [PHONE]", "answer": "见政策，邮箱 [EMAIL]", "tools": ["retrieve"], "retrieve_filter": null, "tenant_hash": "t_055c2de7", "pii_stripped": true, "incomplete": "missing_retrieve_filter"}
SLO_ok_pii_strip_and_filter_check: True
=== demo6: canary 10% + shadow ===
canary_count_in_200: 12
shadow: {'served': 'stable', 'diff_tools': ['export_all'], 'same_refuse': True}
ALL_OK

