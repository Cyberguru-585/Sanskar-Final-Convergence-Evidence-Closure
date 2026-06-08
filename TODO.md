# TODO - BHIV runtime realism + proof hardening

## Step 1 — Clarify production claims
- [ ] Audit docs/proof files for `READY_FOR_PRODUCTION` / production-ready wording.
- [ ] Replace with “Operational Prototype — Deployment Candidate” (or equivalent) where lifecycle is simulated.

## Step 2 — Upgrade deployment_validator to real lifecycle

- [ ] Modify `deployment_validator.py` to start real runtime participants (reuse `runtime_service_bootstrap.py` orchestrator logic).
- [ ] Replace `time.sleep`-based “cold boot / warm restart / health validation” with real checks (process liveness + real endpoints if present).
- [ ] Implement genuine warm restart: terminate/restart processes; verify new PIDs and any persisted state restore.

## Step 3 — Ensure health/readiness/metrics endpoints exist
- [ ] Inspect participant service code inside `runtime_service_bootstrap.py` for HTTP endpoints.
- [ ] Add minimal `/health` and `/readiness` to participants if missing.
- [ ] Add minimal `/metrics` (Prometheus-compatible) only if metrics claims remain.

## Step 4 — Make hostile crash/recovery truth real
- [ ] Update `runtime_hostile_suite.py` “partial crash” to actually kill the real participant PID.
- [ ] Verify recovery by restarting supervisor/orchestrator and confirming continuity (new PID + recovered ability to serve health).

## Step 5 — Observability external proof
- [ ] Add real telemetry/metrics emission or remove unproven collector claims.
- [ ] Add a verification step that proves exporter endpoints are reachable and data is emitted.

## Step 6 — Regenerate proof JSON artifacts and update review packets
- [ ] Run demo scripts to generate updated proof artifacts.
- [ ] Update `PRODUCTION_READY_REVIEW_PACKET*`, `FINAL_DELIVERY_INDEX.md`, and other marketing docs to match new evidence.

## Step 7 — Testing
- [ ] Run: `python runtime_service_bootstrap.py`
- [ ] Run: `python deployment_validator.py`
- [ ] Run: `python runtime_hostile_suite.py`

