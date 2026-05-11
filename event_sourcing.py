import json
import hashlib
from datetime import datetime
from pathlib import Path


def compute_event_hash(event_data):
    """Compute SHA-256 hash of event data for immutability verification."""
    serialized = json.dumps(event_data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def store_event(trace_id, event_type, event_data, event_store_path="event_store.json"):
    """
    Store an immutable event in the event store.
    
    Event structure:
    {
        "event_id": "EVT-{trace_id}-{timestamp}",
        "trace_id": trace_id,
        "event_type": event_type,
        "timestamp": ISO-8601 timestamp,
        "data": event_data,
        "event_hash": SHA-256 hash of data for verification
    }
    """
    event_store = []
    
    
    if Path(event_store_path).exists():
        with open(event_store_path, 'r') as f:
            event_store = json.load(f)
    
    timestamp = datetime.utcnow().isoformat() + "Z"
    event_hash = compute_event_hash(event_data)
    
    event = {
        "event_id": f"EVT-{trace_id}-{len(event_store) + 1}",
        "trace_id": trace_id,
        "event_type": event_type,
        "timestamp": timestamp,
        "data": event_data,
        "event_hash": event_hash,
        "immutable": True
    }
    
    event_store.append(event)
    
    
    with open(event_store_path, 'w') as f:
        json.dump(event_store, f, indent=2, default=str)
    
    return event


def get_event_by_trace_id(trace_id, event_store_path="event_store.json"):
    """Retrieve input event for a given trace_id."""
    if not Path(event_store_path).exists():
        return None
    
    with open(event_store_path, 'r') as f:
        event_store = json.load(f)
    
    
    for event in event_store:
        if event["trace_id"] == trace_id and event["event_type"] == "INPUT":
            return event
    
    return None


def replay_from_event(trace_id, event_store_path="event_store.json"):
    """
    Replay execution from stored input event.
    Returns the immutable input event and flags replay mode.
    """
    event = get_event_by_trace_id(trace_id, event_store_path)
    
    if not event:
        return None, False
    
    
    stored_hash = event["event_hash"]
    computed_hash = compute_event_hash(event["data"])
    
    is_valid = stored_hash == computed_hash
    
    return event["data"], is_valid


def verify_replay_determinism(original_hash, replayed_hash):
    """Verify that replay produces identical hash."""
    return {
        "original_hash": original_hash,
        "replayed_hash": replayed_hash,
        "is_deterministic": original_hash == replayed_hash,
        "verdict": "PASS — determinism verified" if original_hash == replayed_hash else "FAIL — determinism violation"
    }
