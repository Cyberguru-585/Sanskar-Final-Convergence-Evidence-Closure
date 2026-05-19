import json
import hashlib
from datetime import datetime
from pathlib import Path


def compute_event_hash(event_data):
    
    serialized = json.dumps(event_data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_chained_hash(event_data, previous_hash):
    
    combined = {
        "data": event_data,
        "previous_hash": previous_hash
    }
    serialized = json.dumps(combined, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def store_event(trace_id, event_type, event_data, event_store_path="event_store.json"):
    
    event_store = []
    
    if Path(event_store_path).exists():
        with open(event_store_path, 'r') as f:
            event_store = json.load(f)
    
    timestamp = datetime.utcnow().isoformat() + "Z"
    event_hash = compute_event_hash(event_data)
    
    
    trace_events = [e for e in event_store if e["trace_id"] == trace_id]
    if trace_events:
        
        previous_event_hash = trace_events[-1].get("current_event_hash", trace_events[-1].get("event_hash", "0" * 64))
    else:
        previous_event_hash = "0" * 64  # Root hash (all zeros)
    
    
    current_event_hash = compute_chained_hash(event_data, previous_event_hash)
    
    event = {
        "event_id": f"EVT-{trace_id}-{len(trace_events) + 1}",
        "trace_id": trace_id,
        "event_type": event_type,
        "timestamp": timestamp,
        "data": event_data,
        "event_hash": event_hash,
        "previous_event_hash": previous_event_hash,
        "current_event_hash": current_event_hash,
        "immutable": True,
        "lineage_sequence": len(trace_events) + 1
    }
    
    event_store.append(event)
    
    
    with open(event_store_path, 'w') as f:
        json.dump(event_store, f, indent=2, default=str)
    
    return event


def get_event_by_trace_id(trace_id, event_store_path="event_store.json"):
    
    if not Path(event_store_path).exists():
        return None
    
    with open(event_store_path, 'r') as f:
        event_store = json.load(f)
    
    for event in event_store:
        if event["trace_id"] == trace_id and event["event_type"] == "INPUT":
            return event
    
    return None


def replay_from_event(trace_id, event_store_path="event_store.json"):
    
    event = get_event_by_trace_id(trace_id, event_store_path)
    
    if not event:
        return None, False
    
    stored_hash = event["event_hash"]
    computed_hash = compute_event_hash(event["data"])
    
    is_valid = stored_hash == computed_hash
    
    return event["data"], is_valid


def verify_replay_determinism(original_hash, replayed_hash):
    
    return {
        "original_hash": original_hash,
        "replayed_hash": replayed_hash,
        "is_deterministic": original_hash == replayed_hash,
        "verdict": "PASS — determinism verified" if original_hash == replayed_hash else "FAIL — determinism violation"
    }


def verify_lineage_integrity(trace_id, event_store_path="event_store.json"):
    
    if not Path(event_store_path).exists():
        return {
            "trace_id": trace_id,
            "status": "NO_EVENTS",
            "events_verified": 0,
            "chain_valid": False,
            "mutations_detected": [],
            "deletions_detected": [],
            "corruption_detected": False,
            "verdict": "FAIL — no event store found"
        }
    
    with open(event_store_path, 'r') as f:
        event_store = json.load(f)
    
    trace_events = [e for e in event_store if e["trace_id"] == trace_id]
    
    if not trace_events:
        return {
            "trace_id": trace_id,
            "status": "NO_EVENTS",
            "events_verified": 0,
            "chain_valid": False,
            "mutations_detected": [],
            "deletions_detected": [],
            "corruption_detected": False,
            "verdict": "FAIL — no events found for trace"
        }
    
    mutations_detected = []
    corruption_detected = False
    
    
    for i, event in enumerate(trace_events):
        # Check mutation: verify hash integrity
        recomputed_hash = compute_event_hash(event["data"])
        if recomputed_hash != event["event_hash"]:
            mutations_detected.append({
                "event_id": event["event_id"],
                "sequence": i + 1,
                "reason": "event_hash_mismatch",
                "stored_hash": event["event_hash"],
                "computed_hash": recomputed_hash
            })
            corruption_detected = True
        
        
        if i == 0:
            expected_previous = "0" * 64
        else:
            expected_previous = trace_events[i - 1]["current_event_hash"]
        
        if event["previous_event_hash"] != expected_previous:
            mutations_detected.append({
                "event_id": event["event_id"],
                "sequence": i + 1,
                "reason": "broken_lineage_chain",
                "expected_previous": expected_previous,
                "actual_previous": event["previous_event_hash"]
            })
            corruption_detected = True
        
        
        recomputed_current = compute_chained_hash(event["data"], event["previous_event_hash"])
        if recomputed_current != event["current_event_hash"]:
            mutations_detected.append({
                "event_id": event["event_id"],
                "sequence": i + 1,
                "reason": "chained_hash_mismatch",
                "stored_current": event["current_event_hash"],
                "computed_current": recomputed_current
            })
            corruption_detected = True
    
    
    expected_sequences = list(range(1, len(trace_events) + 1))
    actual_sequences = [e["lineage_sequence"] for e in trace_events]
    
    if actual_sequences != expected_sequences:
        deletions_detected = [s for s in expected_sequences if s not in actual_sequences]
    else:
        deletions_detected = []
    
    proof = {
        "trace_id": trace_id,
        "status": "VERIFIED",
        "events_verified": len(trace_events),
        "chain_valid": not corruption_detected and len(deletions_detected) == 0,
        "mutations_detected": mutations_detected,
        "deletions_detected": deletions_detected,
        "corruption_detected": corruption_detected,
        "lineage_chain": [
            {
                "sequence": e["lineage_sequence"],
                "event_id": e["event_id"],
                "event_hash": e["event_hash"],
                "previous_event_hash": e["previous_event_hash"],
                "current_event_hash": e["current_event_hash"],
                "timestamp": e["timestamp"]
            }
            for e in trace_events
        ],
        "verdict": "PASS — lineage chain integrity verified" if (not corruption_detected and len(deletions_detected) == 0) else "FAIL — corruption or deletion detected"
    }
    
    return proof
