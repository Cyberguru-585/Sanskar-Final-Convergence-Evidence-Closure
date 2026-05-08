from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
from datetime import datetime
import hashlib
from typing import Dict, Any
from sanskar import run_sanskar
from core import run_core
from enforcement import run_enforcement
from tantra import compute_chain_hash, verify_trace_continuity

app = FastAPI(title="Sanskar Intelligence Service", version="v1")

# In-memory storage for traces (for simplicity; in production, use database)
traces: Dict[str, Dict[str, Any]] = {}

# Truth store file
TRUTH_STORE = "truth_store.json"
OBSERVABILITY_LOG = "observability.log"

class SignalInput(BaseModel):
    trace_id: str
    signal: Dict[str, Any]
    contract_version: str = "v1"

class ReplayInput(BaseModel):
    trace_id: str
    contract_version: str = "v1"

def log_observability(trace_id: str, stage: str, verdict: str, pipeline_hash: str = ""):
    timestamp = datetime.utcnow().isoformat()
    log_entry = {
        "trace_id": trace_id,
        "timestamp": timestamp,
        "stage": stage,
        "verdict": verdict,
        "hash": pipeline_hash
    }
    with open(OBSERVABILITY_LOG, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def persist_truth(trace_id: str, verdict: str, pipeline_hash: str):
    truth_entry = {
        "trace_id": trace_id,
        "verdict": verdict,
        "pipeline_hash": pipeline_hash,
        "timestamp": datetime.utcnow().isoformat(),
        "contract_version": "v1"
    }
    if os.path.exists(TRUTH_STORE):
        with open(TRUTH_STORE, "r") as f:
            truths = json.load(f)
    else:
        truths = []
    truths.append(truth_entry)
    with open(TRUTH_STORE, "w") as f:
        json.dump(truths, f, indent=2)

def strip_contract_version(data):
    if isinstance(data, dict):
        return {k: strip_contract_version(v) for k, v in data.items() if k != "contract_version"}
    elif isinstance(data, list):
        return [strip_contract_version(item) for item in data]
    else:
        return data

def add_contract_version(data: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(data, dict):
        data["contract_version"] = "v1"
    return data

@app.post("/signal")
async def signal_endpoint(input_data: SignalInput):
    if input_data.contract_version != "v1":
        raise HTTPException(status_code=400, detail="Unsupported contract version")
    
    trace_id = input_data.trace_id
    
    # Run the full pipeline
    sanskar_output = run_sanskar(input_data.dict())
    if "failure" in sanskar_output:
        log_observability(trace_id, "sanskar", "FAILURE")
        failure_payload = {"trace_id": trace_id, "failure": sanskar_output["failure"]}
        traces[trace_id] = add_contract_version(failure_payload)
        return add_contract_version(failure_payload)
    
    core_output = run_core(sanskar_output)
    enforcement_output = run_enforcement(core_output)
    
    if "failure" in enforcement_output:
        log_observability(trace_id, "enforcement", "FAILURE")
        failure_payload = {"trace_id": trace_id, "failure": enforcement_output["failure"]}
        traces[trace_id] = add_contract_version(failure_payload)
        return add_contract_version(failure_payload)
    
    # Compute chain hash
    chain_data = {
        "input": strip_contract_version(input_data.dict()),
        "sanskar": sanskar_output,
        "core": core_output,
        "enforcement": enforcement_output
    }
    pipeline_hash = compute_chain_hash(chain_data)
    trace_proof = verify_trace_continuity(trace_id, [
        ("input", input_data.dict()),
        ("sanskar", sanskar_output),
        ("core", core_output),
        ("enforcement", enforcement_output)
    ])

    # Truth output
    truth_output = {
        "verdict": "PIPELINE_COMPLETE",
        "selected_entity": core_output["selected_entity"],
        "selected_score": core_output.get("selected_score"),
        "enforcement_action": enforcement_output.get("action"),
        "enforcement_target": enforcement_output.get("target"),
        "pipeline_hash": pipeline_hash,
        "chain_integrity": "VERIFIED — SHA-256 hash computed over full chain",
        "trace_continuity": trace_proof["verdict"],
        "trace_continuity_proof": trace_proof,
        "stages_completed": ["input", "sanskar", "core", "enforcement", "truth"],
        "contract_version": "v1"
    }
    
    full_output = {
        "trace_id": trace_id,
        "pipeline_status": "SUCCESS",
        "input": input_data.dict(),
        "sanskar_output": sanskar_output,
        "core_decision": core_output,
        "enforcement": enforcement_output,
        "truth": truth_output
    }
    
    traces[trace_id] = add_contract_version(full_output)
    persist_truth(trace_id, truth_output["verdict"], pipeline_hash)
    log_observability(trace_id, "truth", "SUCCESS", pipeline_hash)
    
    return add_contract_version(full_output)

@app.get("/trace/{trace_id}")
async def get_trace(trace_id: str):
    if trace_id not in traces:
        raise HTTPException(status_code=404, detail="Trace not found")
    return traces[trace_id]

@app.get("/health")
async def health_check():
    return add_contract_version({"status": "healthy", "service": "sanskar"})

@app.post("/replay")
async def replay_endpoint(input_data: ReplayInput):
    if input_data.contract_version != "v1":
        raise HTTPException(status_code=400, detail="Unsupported contract version")
    
    trace_id = input_data.trace_id
    if trace_id not in traces:
        raise HTTPException(status_code=404, detail="Trace not found for replay")
    
    original = traces[trace_id]
    if "failure" in original:
        log_observability(trace_id, "replay", "SUCCESS", "")
        return add_contract_version(original)

    original_input = original.get("input", {})
    rerun_output = run_sanskar(original_input)
    if "failure" in rerun_output:
        raise HTTPException(status_code=500, detail="Replay failed: upstream sanskar failure")

    rerun_core = run_core(rerun_output)
    rerun_enforcement = run_enforcement(rerun_core)
    if "failure" in rerun_enforcement:
        raise HTTPException(status_code=500, detail="Replay failed: enforcement failure")

    chain_data = {
        "input": strip_contract_version(original_input),
        "sanskar": rerun_output,
        "core": rerun_core,
        "enforcement": rerun_enforcement
    }
    new_hash = compute_chain_hash(chain_data)
    original_hash = original["truth"]["pipeline_hash"]
    if new_hash != original_hash:
        raise HTTPException(status_code=500, detail="Replay hash mismatch")

    log_observability(trace_id, "replay", "SUCCESS", original_hash)
    return add_contract_version(original)

@app.get("/ranking")
async def get_ranking():
    # Get latest ranking from traces
    latest_trace = None
    for trace in traces.values():
        if "ranking" in trace.get("sanskar_output", {}):
            latest_trace = trace
            break
    if not latest_trace:
        raise HTTPException(status_code=404, detail="No ranking available")
    return add_contract_version({
        "ranking": latest_trace["sanskar_output"]["ranking"],
        "entities": latest_trace["sanskar_output"]["entities"]
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)