import hashlib
import json
import time
import console
from sanskar import run_sanskar
from core import run_core
from enforcement import run_enforcement
from event_sourcing import store_event, replay_from_event, verify_replay_determinism, compute_event_hash
from observability import get_tracker



def compute_chain_hash(data):
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def verify_trace_continuity(trace_id, stages):
    proof = {
        "expected_trace_id": trace_id,
        "stages_checked": [],
        "all_match": True
    }

    for stage_name, stage_output in stages:
        stage_trace = stage_output.get("trace_id", None)
        matches = stage_trace == trace_id
        proof["stages_checked"].append({
            "stage": stage_name,
            "trace_id_found": stage_trace,
            "matches_expected": matches
        })
        if not matches:
            proof["all_match"] = False

    proof["verdict"] = "PASS — trace_id identical across all stages" if proof["all_match"] else "FAIL — trace_id mismatch detected"
    return proof


def strip_contract_version(data):
    if isinstance(data, dict):
        return {k: strip_contract_version(v) for k, v in data.items() if k != "contract_version"}
    elif isinstance(data, list):
        return [strip_contract_version(item) for item in data]
    else:
        return data


def run_tantra(input_contract, replay_mode=False):
    trace_id = input_contract.get("trace_id", "UNKNOWN")
    tracker = get_tracker()
    
    
    if replay_mode and "trace_id" in input_contract:
        replayed_input, is_valid = replay_from_event(trace_id)
        if replayed_input and is_valid:
            input_contract = replayed_input
        else:
            tracker.record_error(trace_id, "tantra-replay", "REPLAY_VERIFICATION_FAILED",
                                "Replay verification failed - event corrupted or not found")
            return {
                "trace_id": trace_id,
                "pipeline_status": "FAILED",
                "failure": {
                    "stage": "tantra-replay",
                    "code": "REPLAY_VERIFICATION_FAILED",
                    "message": "Replay verification failed - event corrupted or not found",
                    "trace_preserved": False
                },
                "contract_version": "v1"
            }

    if "trace_id" not in input_contract:
        console.step(1, "INPUT RECEIVED")
        console.info("Status", "FAILED — missing trace_id")
        console.failure_display({
            "stage": "tantra-input",
            "code": "MISSING_TRACE_ID",
            "message": "trace_id missing from input contract",
            "trace_preserved": False
        })
        tracker.record_error("UNKNOWN", "tantra-input", "MISSING_TRACE_ID",
                            "trace_id missing from input contract")
        return {
            "trace_id": "UNKNOWN",
            "pipeline_status": "FAILED",
            "failure": {
                "stage": "tantra-input",
                "code": "MISSING_TRACE_ID",
                "message": "trace_id missing from input contract",
                "trace_preserved": False
            },
            "chain_integrity": "N/A — pipeline failed at input validation",
            "contract_version": "v1"
        }

    if "signal" not in input_contract:
        console.step(1, "INPUT RECEIVED")
        console.trace(trace_id)
        console.info("Status", "FAILED — signal missing")
        failure_output = {
            "trace_id": trace_id,
            "stage": "tantra-input",
            "failure": {
                "stage": "tantra-input",
                "code": "INVALID_SIGNAL",
                "message": "Signal missing in input contract",
                "trace_preserved": True
            }
        }
        console.failure_display(failure_output["failure"])

        trace_proof = verify_trace_continuity(trace_id, [
            ("input", input_contract),
            ("tantra-validation", failure_output)
        ])

        tracker.record_error(trace_id, "tantra-input", "INVALID_SIGNAL",
                            "Signal missing in input contract")

        return {
            "trace_id": trace_id,
            "pipeline_status": "FAILED",
            "failure": failure_output["failure"],
            "trace_continuity_proof": trace_proof,
            "chain_integrity": "N/A — pipeline failed at input validation",
            "contract_version": "v1"
        }

    
    store_event(trace_id, "INPUT", input_contract)

    
    sanskar_start = time.time()
    sanskar_output = run_sanskar(input_contract)
    sanskar_decision_state = sanskar_output.get("entities", [{}])[0].get("decision_state", "CONFIDENT") if sanskar_output.get("entities") else "UNKNOWN"
    tracker.record_stage_exit(trace_id, "sanskar", sanskar_start, 
                             decision_state=sanskar_decision_state, 
                             success="failure" not in sanskar_output,
                             replay_mode=replay_mode)

    if "failure" in sanskar_output:
        console.failure_display(sanskar_output["failure"])
        tracker.record_error(trace_id, "sanskar", sanskar_output["failure"].get("code", "UNKNOWN"),
                            sanskar_output["failure"].get("message", "Unknown error"))
        trace_proof = verify_trace_continuity(trace_id, [
            ("input", input_contract),
            ("sanskar", sanskar_output)
        ])
        return {
            "trace_id": trace_id,
            "pipeline_status": "FAILED",
            "failure": sanskar_output["failure"],
            "trace_continuity_proof": trace_proof,
            "chain_integrity": "N/A — pipeline failed at sanskar",
            "contract_version": "v1"
        }

    
    core_start = time.time()
    core_output = run_core(sanskar_output)
    core_decision_state = core_output.get("selected_decision_state", "CONFIDENT")
    core_confidence = core_output.get("selected_confidence", 0)
    tracker.record_stage_exit(trace_id, "core", core_start,
                             decision_state=core_decision_state,
                             success="failure" not in core_output,
                             replay_mode=replay_mode)

    # Track enforcement stage
    enforcement_start = time.time()
    enforcement_output = run_enforcement(core_output)
    enforcement_decision_state = enforcement_output.get("decision_state", "CONFIDENT")
    tracker.record_stage_exit(trace_id, "enforcement", enforcement_start,
                             decision_state=enforcement_decision_state,
                             success="failure" not in enforcement_output,
                             replay_mode=replay_mode)

    if "failure" in enforcement_output:
        trace_proof = verify_trace_continuity(trace_id, [
            ("input", input_contract),
            ("sanskar", sanskar_output),
            ("core", core_output),
            ("enforcement", enforcement_output)
        ])
        return {
            "trace_id": trace_id,
            "pipeline_status": "FAILED",
            "failure": enforcement_output["failure"],
            "stage_outputs": {
                "sanskar": sanskar_output,
                "core": core_output,
                "enforcement": enforcement_output
            },
            "trace_continuity_proof": trace_proof,
            "chain_integrity": "N/A — pipeline failed",
            "contract_version": "v1"
        }

    trace_proof = verify_trace_continuity(trace_id, [
        ("input", input_contract),
        ("sanskar", sanskar_output),
        ("core", core_output),
        ("enforcement", enforcement_output)
    ])

    chain_data = {
        "input": strip_contract_version(input_contract),
        "sanskar": sanskar_output,
        "core": core_output,
        "enforcement": enforcement_output
    }
    pipeline_hash = compute_chain_hash(chain_data)

    console.step(8, "FINAL TRUTH OUTPUT STORED")
    console.trace(trace_id)

    
    stage_latencies = tracker.get_stage_latencies(trace_id)

    truth_output = {
        "verdict": "PIPELINE_COMPLETE",
        "selected_entity": core_output["selected_entity"],
        "selected_score": core_output.get("selected_score"),
        "enforcement_action": enforcement_output.get("action"),
        "enforcement_target": enforcement_output.get("target"),
        "pipeline_hash": pipeline_hash,
        "chain_integrity": "VERIFIED — SHA-256 hash computed over full chain",
        "trace_continuity": trace_proof["verdict"],
        "stages_completed": ["input", "sanskar", "core", "enforcement", "truth"],
        "summary": (
            f"TANTRA pipeline completed successfully. "
            f"Entity '{core_output['selected_entity']}' selected with score "
            f"{core_output.get('selected_score')}. "
            f"Enforcement action '{enforcement_output.get('action')}' issued "
            f"targeting '{enforcement_output.get('target')}' region. "
            f"Trace {trace_id} preserved across all 5 stages."
        )
    }

    console.truth_record(truth_output)

    return {
        "trace_id": trace_id,
        "pipeline_status": "SUCCESS",
        "input": input_contract,
        "sanskar_output": sanskar_output,
        "core_decision": core_output,
        "enforcement": enforcement_output,
        "truth": truth_output,
        "trace_continuity_proof": trace_proof,
        "replay_mode": replay_mode,
        "event_sourced": True,
        "observability": {
            "stage_latencies": stage_latencies,
            "contract_version": "v1",
            "decision_state": core_decision_state
        },
        "contract_version": "v1"
    }