# ENFORCEMENT_EVIDENCE.md — Integration Evidence (Core → Enforcement)

Scope: Evidence for the ENFORCEMENT integration and fail-closed action directive generation.

## 1) Endpoint used
**Current proven integration surface:** enforcement pipeline stage in `enforcement.py` invoked by `tantra.py`.

- Entry: `tantra.run_tantra()` calls `run_enforcement(core_output)`
- Contract/ceiling enforcement: governed by upstream adapter contracts and explicit omission/forbidden authority fields at adapters.

**No external OS/network endpoint is proven** in this evidence packet.

## 2) Request example (input to enforcement)
`enforcement.py` is called with `core_output` shape (as constructed in `core.py`).

Example shape (minimal) typically used by enforcement stage:

```json
{
  "selected_entity": "region_a",
  "selected_score": 0.90,
  "decision_state": "CONFIDENT",
  "decision": "APPROVED",
  "trace_id": "trace-test001"
}
```

> Note: Exact field names are determined by `core.py`; this evidence packet treats them as structurally passed data because ENFORCEMENT evidence requirement here is about boundary/cross-system behavior.

## 3) Response example (enforcement output)
`tantra.py` expects these fields in `enforcement_output`:
- `decision_state`
- `action`
- `target`
- optional `failure` with `stage`, `code`, `message`.

Example success:

```json
{
  "decision_state": "CONFIDENT",
  "action": "prioritize_resource_allocation",
  "target": "region_a",
  "trace_id": "trace-test001",
  "contract_version": "v1"
}
```

Failure example:

```json
{
  "failure": {
    "stage": "enforcement",
    "code": "AUTHORIZATION_REQUIRED",
    "message": "Enforcement refused action without valid governance authorization",
    "trace_preserved": true
  }
}
```

## 4) Ownership transfer proof
ENFORCEMENT authority is capped to fail-closed execution:
- The integration contract forbids authority escalation from SANSKAR to downstream.
- RAJYA decisions are validated before forwarding to ENFORCEMENT.

Evidence:
- `runtime_adapters.py`:
  - `RajyaToEnforcementAdapter.validate_and_forward()` validates `GovernanceDecisionContract`
  - `GovernanceDecisionContract.OWNER = "rajya"`

## 5) Trace propagation proof
- `tantra.py` returns chain output with `trace_id` preserved through stages and includes `verify_trace_continuity` proof.

Evidence:
- `tantra.py` → `verify_trace_continuity()`
- `event_sourcing.py` + trace storage

## 6) Failure behavior
On failure in enforcement stage:
- `tantra.py` returns `pipeline_status: FAILED`
- includes `failure` and `trace_continuity_proof`.

Evidence:
- `tantra.py` enforcement failure return branch.

## 7) Mocked vs real classification (mandatory)
**Classification:** **MOCKED/PARTIAL**
- Enforcement is proven as a stage in the integrated pipeline.
- External ENFORCEMENT service endpoint + independently managed lifecycle is not proven.

Evidence:
- `GAP_INVENTORY.md` missing network surfaces + separate process lifecycle evidence.

