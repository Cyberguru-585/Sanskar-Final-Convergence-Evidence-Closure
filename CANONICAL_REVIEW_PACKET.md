# CANONICAL_REVIEW_PACKET.md — 5-minute reviewer guide (SANSKAR Final)

## System Purpose
Integrate **SANSKAR** into the TANTRA ecosystem as a **bounded intelligence producer** that:
- produces ranking/entities + confidence
- never grants governance authority
- preserves `trace_id`
- is fail-closed at integration boundaries

## Entry Point
Run the canonical deterministic integration verification:

```bash
python tantra_integration_self_test.py
```

This is the fastest way to validate integration behaviors and failure handling.

## Runtime Flow
1) **Input**: input contract with immutable `trace_id`
2) **SANSKAR**: deterministic intelligence output (no governance fields)
3) **RAJYA**: governance decision validated via contract rules (approval/rejection)
4) **ENFORCEMENT**: fail-closed action directive generation
5) **Bucket**: immutable event record validation + stored lineage (in this repository: adapter-level)
6) **InsightBridge**: telemetry emission (in this repository: adapter-level)
7) **Replay safety**: deterministic replay verification from event store

## Top 3 Files
1. `runtime_adapters.py` — contract enforcement between SANSKAR → RAJYA → ENFORCEMENT and event → Bucket → InsightBridge
2. `tantra.py` — orchestration pipeline + replay_mode behavior
3. `GAP_INVENTORY.md` — explicit proven vs unproven mapping (used to resolve convergence contradiction)

## Example Request
(Trace-bound input contract; exact fields may vary by harness, but `trace_id` must exist.)

```json
{
  "trace_id": "trace-7af92126",
  "signal": {
    "dataset": "crop_yield.csv"
  }
}
```

## Example Response
Successful pipeline returns a structured verdict with trace continuity proof.

```json
{
  "trace_id": "trace-7af92126",
  "pipeline_status": "SUCCESS",
  "truth": {
    "verdict": "PIPELINE_COMPLETE",
    "chain_integrity": "VERIFIED — SHA-256 hash computed over full chain",
    "trace_continuity_proof": {"verdict": "PASS"}
  }
}
```

## Authority Boundaries
- SANSKAR cannot emit governance/authority fields.
- Contract adapters block forbidden fields at boundary crossings.
- RAJYA decision is validated before ENFORCEMENT.

Evidence location: `runtime_adapters.py` forbidden-fields and contract validation.

## Failure Modes
The integration supports structured failure returns including trace continuity proof; boundary/contract violations result in `ContractViolation` and failure outputs.

Common categories (evidence-backed):
- invalid/malformed input
- dependency unavailable behavior (bounded harness)
- authority violation attempt (blocked)
- replay verification failure

## Proof Locations (authoritative within repo)
Use these referenced proof files (declared by review packet docs):
- `tantra_integration_test_report.json`
- `trace_continuity_proof.json`
- `constitutional_convergence_proof.json`
- `governance_pressure_test.json`
- `distributed_failure_recovery.json`

## Current Status
**NOT CONVERGED** as an end-to-end real TANTRA ecosystem participant.

Reason: the integration is proven at the **contract-adapter** level, but the required **real external network endpoints and independent lifecycle evidence** for RAJYA/Bucket/InsightBridge/ENFORCEMENT is explicitly missing per `GAP_INVENTORY.md`.

This resolves the convergence contradiction conclusively.

