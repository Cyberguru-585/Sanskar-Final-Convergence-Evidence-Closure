# RAJYA_EVIDENCE.md — Integration Evidence (SANSKAR → RAJYA)

Scope: Evidence for the downstream RAJYA integration from the SANSKAR participant.

## 1) Endpoint used (what is actually called)
**Current proven integration surface:** contract-adapter validation/forwarding inside `runtime_adapters.py`.

- Adapter: `SanskariToRajyaAdapter.validate_and_forward()`
- Contract validated: `IntelligenceOutputContract` (OWNER=`sanskar`, version=`intelligence_output_v1`)
- Behavior: If the SANSKAR output is structurally valid, the adapter forwards the dict to the next stage.

**No external OS/network endpoint is proven** in this repository evidence packet.

## 2) Request example (SANSKAR output contract)
Example (shape enforced by `IntelligenceOutputContract.REQUIRED_FIELDS` and entity constraints):

```json
{
  "trace_id": "trace-test001",
  "stage": "sanskar",
  "entities": [
    {
      "entity_id": "region_a",
      "score": 0.85,
      "confidence": 0.92,
      "decision_state": "CONFIDENT"
    }
  ],
  "ranking": ["region_a"],
  "metadata": {
    "schema_version": "v1",
    "algorithm": "max_yield_selector",
    "execution_time_ms": 2.5,
    "owner": "sanskar"
  }
}
```

## 3) Response example (RAJYA-facing forwarding result)
**In this codebase**, the adapter returns either:
- `True, <validated_sanskar_output_with_contract_version>` or
- `False, ContractViolation`.

Forwarded result includes contract_version set to `intelligence_output_v1`.

```json
{
  "ok": true,
  "forwarded_contract_version": "intelligence_output_v1",
  "authority_fields_present": false
}
```

## 4) Ownership transfer proof
RAJYA contract authority is established by how RAJYA is expected to validate later:
- RAJYA’s decision contract owner is enforced by `GovernanceDecisionContract.OWNER = "rajya"`
- SANSKAR adapter forbids SANSKAR from emitting authority fields (authority ceiling):
  - Forbidden fields: `enforcement_directive`, `governance_decision`, `bucket_write_direct`

Evidence:
- `runtime_adapters.py`: `SanskariToRajyaAdapter.validate_and_forward()` forbidden-fields check.
- `runtime_adapters.py`: `GovernanceDecisionContract` owner semantics.

## 5) Trace propagation proof
- The only trace discipline in this integration evidence is **structural trace preservation**: the adapters pass `trace_id` through unchanged.
- Additional chain-level trace continuity is referenced in repository evidence packet docs.

Evidence pointers:
- `runtime_adapters.py`: `trace_id = sanskar_output.get("trace_id", "UNKNOWN")` and preservation.
- `review_packets/REVIEW_PACKET.md` references trace continuity proofs.
- `trace_continuity_proof.json` referenced by review docs.

## 6) Failure behavior
When SANSKAR output is invalid:
- Adapter returns `False, ContractViolation` with:
  - `violation_type="contract_validation"`
  - includes `trace_id`

When SANSKAR output attempts authority overreach (forbidden fields present):
- Adapter returns `False, ContractViolation` with:
  - `violation_type="authority_violation"`

Evidence:
- `runtime_adapters.py` exception/violation construction.

## 7) Mocked vs real classification (mandatory)
**Classification:** **MOCKED/PARTIAL**
- Why: RAJYA is not proven as an external network service; the integration demonstrated is contract-level validation and in-process forwarding.
- The explicit gap is documented in `GAP_INVENTORY.md` under missing evidence for separate participant lifecycles and real network surfaces.

Evidence: `GAP_INVENTORY.md`.

