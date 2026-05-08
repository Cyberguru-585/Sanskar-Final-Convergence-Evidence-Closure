# TANTRA Integration Engine

## Overview

Deterministic end-to-end TANTRA pipeline with full proof chain:

```
Input -> Sanskar -> Core Decision -> Enforcement -> Truth Output
```

## Components

### Console Display (console.py)
Universal display and formatting layer:
- Unified console output functions used by all pipeline stages
- Formatting utilities: `banner()`, `step()`, `trace()`, `section()`, `info()`
- Entity display: `entity_card()`, `ranking_board()`, `comparison_panel()`
- Stage outputs: `decision_display()`, `enforcement_display()`, `truth_record()`, `failure_display()`
- Scenario visualization: `scenario_display()`
- Ensures consistent, readable output across entire pipeline

### Sanskar (sanskar.py)
Deterministic intelligence engine:
- Loads and normalizes crop yield dataset
- Computes weighted feature scores (rainfall, temperature, irrigation, fertilizer, yield efficiency)
- Ranks entities (regions) by composite score
- Generates comparative explanations between top entities
- Performs scenario analysis (rainfall +10%, temperature -2C)
- Produces downstream decision recommendation

### Core Decision (core.py)
Deterministic decision layer with visible logic:
- Selection rule: highest_ranked_region_selected
- Evaluates all candidates with scores
- Assigns priority based on score thresholds (critical/high/medium/low)
- Documents full reasoning chain with margin over runner-up

### Enforcement (enforcement.py)
Actionable enforcement layer:
- Maps priority to enforcement type and urgency
- Generates structured directives (irrigation, fertilizer, monitoring)
- Each directive has ID, action, target, and status

### Pipeline (tantra.py)
Main orchestrator:
- Chains all stages with trace_id propagation
- Computes SHA-256 pipeline hash for integrity verification
- Verifies trace continuity across all stages
- Produces final truth output with verification data
- Handles failures gracefully at every stage

## Trace Continuity

Single trace_id (TRACE_123) propagates across:
- input
- sanskar
- core
- enforcement
- truth

Verified programmatically in trace_continuity_proof.json.

## Run

```bash
python test.py
```

## API Service

Start the service:

```bash
python api.py
```

Available endpoints:

- `POST /signal` — submit a trace signal and execute the full pipeline
- `GET /trace/{trace_id}` — retrieve full trace state
- `GET /health` — service health check
- `POST /replay` — replay a previous trace and verify deterministic output
- `GET /ranking` — retrieve the latest ranking state

All API responses are JSON-only and include `contract_version: "v1"`.

## Output Files

| File | Description |
|------|-------------|
| full_chain_output.json | Complete pipeline output with all stages |
| stage_sanskar.json | Sanskar stage output |
| stage_core.json | Core decision output with visible logic |
| stage_enforcement.json | Enforcement action with directives |
| stage_truth.json | Truth output with hash and verification |
| trace_continuity_proof.json | Proof that TRACE_123 is identical at every stage |
| failure_proof.json | Broken input tests with trace preservation |
| determinism_proof.json | 5 identical runs proving determinism |

## Proofs

- Trace Continuity: PASS
- Failure Handling: PASS (3 broken input tests)
- Determinism: PASS (5 runs, identical SHA-256 hashes)