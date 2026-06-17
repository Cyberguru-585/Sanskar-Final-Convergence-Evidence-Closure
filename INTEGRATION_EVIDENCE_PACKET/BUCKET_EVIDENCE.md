# BUCKET_EVIDENCE.md — Integration Evidence (Execution → Bucket)

Scope: Evidence for BUCKET integration and immutable event recording semantics.

## 1) Endpoint used
**Current proven integration surface:** contract validation + immutable write semantics inside `runtime_adapters.py`.

- Adapter: `ExecutionToBucketAdapter.validate_and_write()`
- Contract validated: `EventRecordContract` (OWNER=`bucket`, immutable=True requirement)

**No external storage endpoint is proven** (no separate process / persistence backend shown in this evidence packet).

## 2) Request example (event record)
Example event input shape enforced by `EventRecordContract.REQUIRED_FIELDS`:

```json
{
  "trace_id": "trace-test001",
  "event_type": "execution_complete",
  "event_data": {
    "stage": "truth",
    "outcome": "SUCCESS",
    "execution_time_ms": 12
  },
  "ownership": {"owner": "bucket", "immutable": true}
}
```

## 3) Response example (bucket write result)
`validate_and_write()` returns an augmented record with:
- `bucket_write_timestamp` (UTC)
- `bucket_write_index`
- `bucket_sealed`: true

```json
{
  "trace_id": "trace-test001",
  "event_type": "execution_complete",
  "event_data": {
    "stage": "truth",
    "outcome": "SUCCESS",
    "execution_time_ms": 12
  },
  "ownership": {"owner": "bucket", "immutable": true},
  "bucket_write_timestamp": "2026-06-17T00:00:00.000000Z",
  "bucket_write_index": 0,
  "bucket_sealed": true
}
```

## 4) Ownership transfer proof
Ownership immutability is enforced by `EventRecordContract.validate()`:
- `ownership.owner` must equal `"bucket"`
- `ownership.immutable` must be exactly `true`

Evidence:
- `runtime_adapters.py` → `EventRecordContract`
- `runtime_adapters.py` → `ExecutionToBucketAdapter.validate_and_write()`

## 5) Trace propagation proof
- `ExecutionToBucketAdapter` preserves `trace_id` by reading `trace_id = event_record.get("trace_id", "UNKNOWN")` and storing it unchanged.

Evidence:
- `runtime_adapters.py` event augmentation uses `event_with_bucket_metadata = {**event_record, ...}`
- Review packets reference `trace_continuity_proof.json`.

## 6) Failure behavior
If the record fails `EventRecordContract.validate()`:
- Adapter returns `False, ContractViolation`
- `ContractViolation` includes:
  - `violation_type="contract_validation"`
  - `trace_id` (propagated)

Evidence:
- `runtime_adapters.py` → `ExecutionToBucketAdapter.validate_and_write()`.

## 7) Mocked vs real classification (mandatory)
**Classification:** **MOCKED/PARTIAL**
- Immutable write contract is proven inside in-process adapter state.
- **No external durable BUCKET endpoint** is proven here (no OS/network storage backend evidence).

Evidence of missing externalization:
- `GAP_INVENTORY.md`.

