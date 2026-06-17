# INSIGHTBRIDGE_EVIDENCE.md — Integration Evidence (Bucket → InsightBridge)\n
\nScope: Evidence for the INSIGHTBRIDGE integration from Bucket telemetry emission.\n
\n## 1) Endpoint used\n**Current proven integration surface:** in-process telemetry emission via `BucketToInsightBridgeAdapter.emit_telemetry()`.\n
\n- Adapter: `BucketToInsightBridgeAdapter.emit_telemetry(event_record)`\n- Behavior: Converts a Bucket event record into a telemetry dict and appends it to `telemetry_records`.\n
\n**No external OS/network endpoint** is proven in this repository evidence packet.\n
\n## 2) Request example (bucket event record → telemetry input)\nExample event record shape accepted by the telemetry adapter:\n
```json\n{\n  \"trace_id\": \"trace-test001\",\n  \"event_type\": \"execution_complete\",\n  \"event_data\": {\n    \"stage\": \"truth\",\n    \"outcome\": \"SUCCESS\",\n    \"execution_time_ms\": 12\n  }\n}\n```\n
\n## 3) Response example (telemetry emitted)\nAdapter returns telemetry dict with:\n- `trace_id`\n- `metric_type=\"execution_event\"`\n- `event_stage` derived from `event_record.event_data.stage`\n- `event_outcome` derived from `event_record.event_data.outcome`\n- `execution_time_ms` derived from `event_record.event_data.execution_time_ms`\n\n```json\n{\n  \"trace_id\": \"trace-test001\",\n  \"metric_type\": \"execution_event\",\n  \"timestamp\": \"2026-06-17T00:00:00.000000Z\",\n  \"event_stage\": \"truth\",\n  \"event_outcome\": \"SUCCESS\",\n  \"execution_time_ms\": 12,\n  \"source\": \"bucket\"\n}\n```\n
\n## 4) Ownership transfer proof\nOwnership here is **telemetry origin**, not governance authority.\n\nEvidence:\n- `BucketToInsightBridgeAdapter` sets `source: \"bucket\"`.\n- Telemetry is derived from `event_record` and does not introduce governance fields.\n
\n## 5) Trace propagation proof\n- Adapter reads `trace_id = event_record.get(\"trace_id\", \"UNKNOWN\")`\n- Telemetry includes the same `trace_id` unchanged.\n
\nEvidence:\n- `runtime_adapters.py` → `BucketToInsightBridgeAdapter.emit_telemetry()`.\n- Review packet(s) reference trace continuity proofs (e.g., `trace_continuity_proof.json`).\n
\n## 6) Failure behavior\nThis adapter does not define explicit failure/exception contracts; it emits telemetry based on best-effort field reads.\n\n**Fallback behavior:**\n- If `event_data.stage` / `event_data.outcome` missing, defaults are used (`\"unknown\"`).\n- If `execution_time_ms` missing, default is `0`.\n
\nEvidence:\n- `runtime_adapters.py` telemetry construction defaults.\n
\n## 7) Mocked vs real classification (mandatory)\n**Classification:** **MOCKED/PARTIAL**\n- Telemetry emission is proven structurally and trace-linked inside memory.\n- No external InsightBridge service endpoint, persistence, or degradation behavior is proven.\n
\nEvidence:\n- `GAP_INVENTORY.md` documents missing evidence for real network surfaces and independent participant lifecycles.\n
