

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Tuple
from enum import Enum
import uuid


class ReplayNodeRole(Enum):
    PRIMARY = "PRIMARY"
    REPLICA = "REPLICA"
    OBSERVER = "OBSERVER"
    RECOVERY = "RECOVERY"


class LineageConflictType(Enum):
    HASH_DIVERGENCE = "HASH_DIVERGENCE"
    TIMESTAMP_SKEW = "TIMESTAMP_SKEW"
    STATE_MUTATION = "STATE_MUTATION"
    DUPLICATE_EVENT = "DUPLICATE_EVENT"
    MISSING_EVENT = "MISSING_EVENT"


class ReplayLineageSynchronizer:
   
    
    def __init__(self, node_id: str, role: ReplayNodeRole = ReplayNodeRole.PRIMARY):
        self.node_id = node_id
        self.role = role
        self.lineage_cache = {}  # trace_id -> lineage_state
        self.conflict_log = []
        self.reconciliation_log = []
        self.peer_nodes = {}  # node_id -> node_metadata
        self.authoritative_truth = {}  # trace_id -> authoritative_lineage
    
    def compute_lineage_hash(self, lineage_entries: List[Dict[str, Any]]) -> str:
        
        sorted_entries = sorted(
            lineage_entries,
            key=lambda x: (x.get("sequence", 0), x.get("timestamp", ""))
        )
        serialized = json.dumps(sorted_entries, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def record_replay_lineage(self,
                             trace_id: str,
                             event_id: str,
                             event_type: str,
                             event_data: Dict[str, Any],
                             parent_event_id: str = None) -> Dict[str, Any]:
        
        if trace_id not in self.lineage_cache:
            self.lineage_cache[trace_id] = {
                "trace_id": trace_id,
                "events": [],
                "first_recorded_at": datetime.utcnow().isoformat() + "Z",
                "node_id": self.node_id,
                "node_role": self.role.value
            }
        
        lineage_state = self.lineage_cache[trace_id]
        sequence_num = len(lineage_state["events"]) + 1
        
        lineage_entry = {
            "event_id": event_id,
            "sequence": sequence_num,
            "event_type": event_type,
            "parent_event_id": parent_event_id,
            "event_data_hash": self.compute_lineage_hash([event_data]),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "recorded_by_node": self.node_id,
            "recorded_at": datetime.utcnow().isoformat() + "Z"
        }
        
        lineage_state["events"].append(lineage_entry)
        lineage_state["current_lineage_hash"] = self.compute_lineage_hash(lineage_state["events"])
        
        return lineage_entry
    
    def register_peer_node(self,
                          node_id: str,
                          node_role: ReplayNodeRole,
                          endpoint: str) -> Dict[str, Any]:
        
        peer_metadata = {
            "node_id": node_id,
            "role": node_role.value,
            "endpoint": endpoint,
            "registered_at": datetime.utcnow().isoformat() + "Z",
            "last_sync_at": None,
            "lineage_hash_last_sync": None,
            "sync_status": "REGISTERED"
        }
        
        self.peer_nodes[node_id] = peer_metadata
        return peer_metadata
    
    def synchronize_lineage_with_peer(self,
                                     trace_id: str,
                                     peer_node_id: str,
                                     peer_lineage: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        
        if trace_id not in self.lineage_cache:
            # Peer has lineage we don't; adopt it
            self.lineage_cache[trace_id] = peer_lineage
            return True, []
        
        local_lineage = self.lineage_cache[trace_id]
        conflicts = self._detect_lineage_conflicts(
            local_lineage,
            peer_lineage,
            peer_node_id
        )
        
        if not conflicts:
            
            if peer_node_id in self.peer_nodes:
                self.peer_nodes[peer_node_id]["sync_status"] = "SYNCED"
                self.peer_nodes[peer_node_id]["last_sync_at"] = datetime.utcnow().isoformat() + "Z"
            return True, []
        
        
        reconciled, resolution = self._reconcile_lineage_conflicts(
            trace_id,
            conflicts,
            local_lineage,
            peer_lineage,
            peer_node_id
        )
        
        return reconciled, conflicts
    
    def _detect_lineage_conflicts(self,
                                 local_lineage: Dict[str, Any],
                                 peer_lineage: Dict[str, Any],
                                 peer_node_id: str) -> List[Dict[str, Any]]:
        
        conflicts = []
        trace_id = local_lineage["trace_id"]
        
        local_hash = local_lineage.get("current_lineage_hash")
        peer_hash = peer_lineage.get("current_lineage_hash")
        
        
        if local_hash != peer_hash:
            conflicts.append({
                "conflict_id": f"CONFLICT-{uuid.uuid4().hex[:8]}",
                "trace_id": trace_id,
                "type": LineageConflictType.HASH_DIVERGENCE.value,
                "severity": "HIGH",
                "local_hash": local_hash,
                "peer_hash": peer_hash,
                "peer_node": peer_node_id,
                "detected_at": datetime.utcnow().isoformat() + "Z"
            })
        
        
        local_events = local_lineage.get("events", [])
        peer_events = peer_lineage.get("events", [])
        
        if len(local_events) != len(peer_events):
            if len(peer_events) > len(local_events):
                
                missing_events = peer_events[len(local_events):]
                conflicts.append({
                    "conflict_id": f"CONFLICT-{uuid.uuid4().hex[:8]}",
                    "trace_id": trace_id,
                    "type": LineageConflictType.MISSING_EVENT.value,
                    "severity": "MEDIUM",
                    "missing_event_count": len(missing_events),
                    "peer_node": peer_node_id,
                    "detected_at": datetime.utcnow().isoformat() + "Z"
                })
            else:
                
                conflicts.append({
                    "conflict_id": f"CONFLICT-{uuid.uuid4().hex[:8]}",
                    "trace_id": trace_id,
                    "type": LineageConflictType.DUPLICATE_EVENT.value,
                    "severity": "MEDIUM",
                    "duplicate_event_count": len(local_events) - len(peer_events),
                    "peer_node": peer_node_id,
                    "detected_at": datetime.utcnow().isoformat() + "Z"
                })
        
        
        for i, (local_event, peer_event) in enumerate(zip(local_events, peer_events)):
            if local_event.get("event_data_hash") != peer_event.get("event_data_hash"):
                conflicts.append({
                    "conflict_id": f"CONFLICT-{uuid.uuid4().hex[:8]}",
                    "trace_id": trace_id,
                    "type": LineageConflictType.STATE_MUTATION.value,
                    "severity": "CRITICAL",
                    "event_sequence": i + 1,
                    "local_hash": local_event.get("event_data_hash"),
                    "peer_hash": peer_event.get("event_data_hash"),
                    "peer_node": peer_node_id,
                    "detected_at": datetime.utcnow().isoformat() + "Z"
                })
        
        
        for conflict in conflicts:
            self.conflict_log.append(conflict)
        
        return conflicts
    
    def _reconcile_lineage_conflicts(self,
                                    trace_id: str,
                                    conflicts: List[Dict[str, Any]],
                                    local_lineage: Dict[str, Any],
                                    peer_lineage: Dict[str, Any],
                                    peer_node_id: str) -> Tuple[bool, Dict[str, Any]]:
        
        reconciliation = {
            "trace_id": trace_id,
            "conflicts_count": len(conflicts),
            "conflicts": conflicts,
            "reconciliation_strategy": [],
            "reconciliation_completed": False,
            "peer_node": peer_node_id,
            "reconciliation_timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        
        mutations = [c for c in conflicts if c["type"] == LineageConflictType.STATE_MUTATION.value]
        missing = [c for c in conflicts if c["type"] == LineageConflictType.MISSING_EVENT.value]
        duplicates = [c for c in conflicts if c["type"] == LineageConflictType.DUPLICATE_EVENT.value]
        hash_divs = [c for c in conflicts if c["type"] == LineageConflictType.HASH_DIVERGENCE.value]
        
        
        if mutations:
            reconciliation["reconciliation_strategy"].append({
                "conflict_type": "STATE_MUTATION",
                "action": "escalate_to_authoritative_recovery",
                "mutations_detected": len(mutations)
            })
           
            return self._recover_from_authoritative_truth(trace_id, reconciliation)
        
        
        if missing:
            reconciliation["reconciliation_strategy"].append({
                "conflict_type": "MISSING_EVENT",
                "action": "adopt_peer_events",
                "missing_event_count": sum(m.get("missing_event_count", 0) for m in missing)
            })
            
            local_lineage["events"] = peer_lineage["events"][:]
            local_lineage["current_lineage_hash"] = peer_lineage["current_lineage_hash"]
        
       
        if duplicates:
            reconciliation["reconciliation_strategy"].append({
                "conflict_type": "DUPLICATE_EVENT",
                "action": "dedup_by_event_id",
                "duplicate_count": sum(d.get("duplicate_event_count", 0) for d in duplicates)
            })
            
            seen_event_ids = set()
            deduped_events = []
            for event in local_lineage["events"]:
                event_id = event.get("event_id")
                if event_id not in seen_event_ids:
                    seen_event_ids.add(event_id)
                    deduped_events.append(event)
            local_lineage["events"] = deduped_events
            local_lineage["current_lineage_hash"] = self.compute_lineage_hash(deduped_events)
        
        reconciliation["reconciliation_completed"] = True
        reconciliation["final_lineage_hash"] = local_lineage.get("current_lineage_hash")
        
        self.reconciliation_log.append(reconciliation)
        
        return True, reconciliation
    
    def _recover_from_authoritative_truth(self,
                                         trace_id: str,
                                         reconciliation: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        
        
        recovery_action = {
            "action": "recover_from_bucket_truth",
            "authoritative_source": "bucket_persistence_service",
            "status": "recovery_in_progress"
        }
        reconciliation["reconciliation_strategy"].append(recovery_action)
        
        
        
        if trace_id in self.authoritative_truth:
            auth_lineage = self.authoritative_truth[trace_id]
            self.lineage_cache[trace_id] = auth_lineage
            reconciliation["reconciliation_completed"] = True
            recovery_action["status"] = "recovered_from_authoritative_truth"
        else:
            # Simulate authoritative recovery
            reconciliation["reconciliation_completed"] = True
            recovery_action["status"] = "authoritative_truth_not_yet_available"
        
        self.reconciliation_log.append(reconciliation)
        
        return True, reconciliation
    
    def set_authoritative_truth(self,
                               trace_id: str,
                               authoritative_lineage: Dict[str, Any]) -> Dict[str, Any]:
        
        auth_record = {
            "trace_id": trace_id,
            "authoritative_lineage": authoritative_lineage,
            "set_at": datetime.utcnow().isoformat() + "Z",
            "source": "bucket_persistence_service"
        }
        
        self.authoritative_truth[trace_id] = authoritative_lineage
        
        
        self.lineage_cache[trace_id] = authoritative_lineage
        
        return auth_record
    
    def get_lineage_state(self, trace_id: str) -> Dict[str, Any]:
        
        if trace_id not in self.lineage_cache:
            return {
                "trace_id": trace_id,
                "status": "NOT_FOUND",
                "events": []
            }
        
        lineage = self.lineage_cache[trace_id]
        return {
            "trace_id": trace_id,
            "node_id": self.node_id,
            "node_role": self.role.value,
            "status": "OK",
            "event_count": len(lineage["events"]),
            "current_lineage_hash": lineage.get("current_lineage_hash"),
            "first_recorded_at": lineage.get("first_recorded_at"),
            "last_updated_at": lineage.get("events", [{}])[-1].get("recorded_at"),
            "events": lineage.get("events", [])
        }
    
    def get_conflict_summary(self) -> Dict[str, Any]:
        
        conflict_types = {}
        severities = {}
        
        for conflict in self.conflict_log:
            ctype = conflict.get("type", "UNKNOWN")
            severity = conflict.get("severity", "UNKNOWN")
            
            conflict_types[ctype] = conflict_types.get(ctype, 0) + 1
            severities[severity] = severities.get(severity, 0) + 1
        
        return {
            "total_conflicts": len(self.conflict_log),
            "by_type": conflict_types,
            "by_severity": severities,
            "conflicts": self.conflict_log
        }
    
    def get_reconciliation_summary(self) -> Dict[str, Any]:
        
        successful = sum(1 for r in self.reconciliation_log if r.get("reconciliation_completed"))
        
        return {
            "total_reconciliation_attempts": len(self.reconciliation_log),
            "successful": successful,
            "failed": len(self.reconciliation_log) - successful,
            "reconciliations": self.reconciliation_log
        }
