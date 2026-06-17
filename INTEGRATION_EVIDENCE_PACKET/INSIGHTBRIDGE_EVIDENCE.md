# INSIGHTBRIDGE_EVIDENCE.md — Integration Evidence (Bucket → InsightBridge)

## Purpose
This evidence file documents what is **proven** vs **not proven** in this repository for the INSIGHTBRIDGE integration that receives telemetry derived from BUCKET event records.

---

## 1) Endpoint used (what is actually invoked)
**Proven integration surface in this repo:** in-process telemetry emission via
`BucketToInsightBridgeAdapter.emit_telemetry()`.

- Adapter function: `BucketToInsightBridgeAdapter.emit_telemetry(event_record)`
- Side-effect: converts the incoming BUCKET event record into a telemetry dict and appends it to `telemetry_records`.

**Not proven here:** a real OS/network-bound InsightBridge service endpoint.

Evidence: `runtime_adapters.py` → `BucketToInsightBridgeAdapter.emit_telemetry()`.

---

## 2) Request example (BUCKET event record → telemetry input)
The adapter reads `trace_id` and fields inside `event_data`.

```json
{
  "trace_id": "trace-test001",
  "event_type": "execution_complete",
  "event_data": {
    "stage": "truth",
    "outcome": "SUCCESS",
    "execution_time_ms": 12
  }
}
```

---

## 3) Response example (telemetry emitted)
Adapter output is a telemetry dict like:

```json
{
  "trace_id": "trace-test001",
  "metric_type": "execution_event",
  "timestamp": "2026-06-17T00:00:00.000000Z",
  "event_stage": "truth",
  "event_outcome": "SUCCESS",
  "execution_time_ms": 12,
  "source": "bucket"
}
```

---

## 4) Ownership transfer proof
Ownership in this evidence is interpreted as **telemetry origin labeling** (not governance authority).

Proof in adapter logic:
- `BucketToInsightBridgeAdapter` sets `source: "bucket"`.
- The telemetry emission does not introduce governance/authority fields.

Evidence: `runtime_adapters.py` (`BucketToInsightBridgeAdapter.emit_telemetry`).

---

## 5) Trace propagation proof
Proof obligation: telemetry must carry the same `trace_id` as the triggering BUCKET record.

Evidence in adapter logic:
- reads `trace_id = event_record.get("trace_id", "UNKNOWN")`
- emits the same `trace_id` unchanged in the telemetry dict

---

## 6) Failure behavior
InsightBridge evidence in this repo is **best-effort emission**.

- If `event_data.stage` or `event_data.outcome` are missing: adapter uses defaults (`"unknown"`).
- If `event_data.execution_time_ms` is missing: adapter defaults `execution_time_ms` to `0`.

Evidence: `runtime_adapters.py` telemetry construction defaults.

---

## 7) Mocked vs real classification (mandatory)
**Classification:** **MOCKED/PARTIAL**

- Proven: telemetry emission is structurally correct and trace-linked *inside this repository’s in-process adapter chain*.
- Not proven: a real external InsightBridge service endpoint, persistence layer, or degraded-mode reconciliation.

Primary gap evidence: `GAP_INVENTORY.md`.

