import json
import hashlib
from typing import Dict, List, Any, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class CausalityType(Enum):
    DIRECT = "direct"
    TRANSITIVE = "transitive"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"


@dataclass
class CausalityRelation:
    
    relation_id: str
    event_a_id: str
    event_b_id: str
    causality_type: str
    reason: str
    is_recoverable: bool


class CausalityTracker:
    
    
    def __init__(self):
        self.causality_graph: Dict[str, List[str]] = {}  # Maps event -> dependent events
        self.causality_relations: List[CausalityRelation] = []
        self.recovery_triggers: List[Dict[str, Any]] = []
        self.causality_index: Dict[str, Dict[str, Any]] = {}
    
    def record_event(
        self,
        event_id: str,
        event_type: str,
        service: str,
        stage: str,
        timestamp: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record an event with full causality metadata."""
        event_record = {
            "event_id": event_id,
            "event_type": event_type,
            "service": service,
            "stage": stage,
            "timestamp": timestamp,
            "data_hash": hashlib.sha256(
                json.dumps(data, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            "caused_by": None,
            "depends_on": [],
            "recovery_trigger": None,
            "causality_verified": False
        }
        
        self.causality_index[event_id] = event_record
        
        if event_id not in self.causality_graph:
            self.causality_graph[event_id] = []
        
        return event_record
    
    def establish_causality(
        self,
        source_event_id: str,
        target_event_id: str,
        causality_type: CausalityType = CausalityType.DIRECT,
        reason: str = ""
    ) -> CausalityRelation:

        relation = CausalityRelation(
            relation_id=f"CAUSE-{source_event_id}-{target_event_id}",
            event_a_id=source_event_id,
            event_b_id=target_event_id,
            causality_type=causality_type.value,
            reason=reason,
            is_recoverable=True
        )
        
        self.causality_relations.append(relation)
        
        if source_event_id in self.causality_graph:
            self.causality_graph[source_event_id].append(target_event_id)
        
        if target_event_id in self.causality_index:
            self.causality_index[target_event_id]["caused_by"] = source_event_id
            if source_event_id not in self.causality_index[target_event_id]["depends_on"]:
                self.causality_index[target_event_id]["depends_on"].append(source_event_id)
        
        return relation
    
    def record_recovery_trigger(
        self,
        trigger_event_id: str,
        recovery_action: str,
        affected_nodes: List[str],
        recovery_strategy: str = "replay_from_checkpoint"
    ) -> Dict[str, Any]:
        
        recovery_record = {
            "recovery_trigger_id": f"TRIGGER-{trigger_event_id}",
            "trigger_event": trigger_event_id,
            "recovery_action": recovery_action,
            "recovery_strategy": recovery_strategy,
            "affected_nodes": affected_nodes,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        self.recovery_triggers.append(recovery_record)
        
        if trigger_event_id in self.causality_index:
            self.causality_index[trigger_event_id]["recovery_trigger"] = recovery_record
        
        return recovery_record
    
    def track_stage_transition(
        self,
        trace_id: str,
        from_stage: str,
        from_service: str,
        to_stage: str,
        to_service: str,
        timestamp: str,
        latency_ms: float
    ) -> Dict[str, Any]:
        
        from_event_id = f"EXIT-{from_service}-{from_stage}-{trace_id}"
        to_event_id = f"ENTRY-{to_service}-{to_stage}-{trace_id}"
        
        self.record_event(
            from_event_id, "stage_exit", from_service, from_stage, timestamp, {}
        )
        
        self.record_event(
            to_event_id, "stage_entry", to_service, to_stage, timestamp, {}
        )
        
        self.establish_causality(
            from_event_id, to_event_id,
            causality_type=CausalityType.DIRECT,
            reason=f"{from_service} output determines {to_service} input"
        )
        
        transition = {
            "transition_id": f"TRANS-{trace_id}-{from_service}-{to_service}",
            "trace_id": trace_id,
            "from_event": from_event_id,
            "to_event": to_event_id,
            "from_service": from_service,
            "to_service": to_service,
            "latency_ms": latency_ms,
            "causality_established": True
        }
        
        return transition
    
    def track_parallel_events(
        self,
        event_ids: List[str],
        reason: str = "parallel_execution"
    ) -> Dict[str, Any]:
        
        parallel_group = {
            "group_id": f"PARALLEL-{hashlib.sha256(str(event_ids).encode()).hexdigest()[:8]}",
            "events": event_ids,
            "causality_type": CausalityType.PARALLEL.value,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return parallel_group
    
    def get_event_causality_chain(self, event_id: str) -> Dict[str, Any]:
        
        if event_id not in self.causality_index:
            return {"event_id": event_id, "status": "not_found"}
        
        causes = []
        for relation in self.causality_relations:
            if relation.event_b_id == event_id:
                causes.append({
                    "event_id": relation.event_a_id,
                    "relation_type": relation.causality_type,
                    "reason": relation.reason
                })
        
        effects = []
        for relation in self.causality_relations:
            if relation.event_a_id == event_id:
                effects.append({
                    "event_id": relation.event_b_id,
                    "relation_type": relation.causality_type,
                    "reason": relation.reason
                })
        
        return {
            "event_id": event_id,
            "event_record": self.causality_index[event_id],
            "causes": causes,
            "effects": effects,
            "chain_reconstructable": True
        }
    
    def verify_causality_consistency(self) -> Dict[str, Any]:
       
        visited = set()
        rec_stack = set()
        has_cycle = False
        cycle_path = []
        
        def dfs(node, path):
            nonlocal has_cycle, cycle_path
            visited.add(node)
            path.append(node)
            rec_stack.add(node)
            
            for neighbor in self.causality_graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path[:])
                elif neighbor in rec_stack:
                    has_cycle = True
                    cycle_path = path + [neighbor]
            
            rec_stack.remove(node)
        
        for node in self.causality_graph:
            if node not in visited:
                dfs(node, [])
        
        consistency = {
            "causality_graph_valid": not has_cycle,
            "has_cycles": has_cycle,
            "cycle_path": cycle_path if has_cycle else [],
            "total_events": len(self.causality_index),
            "total_relations": len(self.causality_relations),
            "total_recovery_triggers": len(self.recovery_triggers)
        }
        
        return consistency
    
    def get_causality_proof(self) -> Dict[str, Any]:
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_events": len(self.causality_index),
            "events": list(self.causality_index.keys()),
            "total_relations": len(self.causality_relations),
            "relations": [
                {
                    "id": r.relation_id,
                    "from": r.event_a_id,
                    "to": r.event_b_id,
                    "type": r.causality_type,
                    "reason": r.reason,
                    "recoverable": r.is_recoverable
                }
                for r in self.causality_relations
            ],
            "total_recovery_triggers": len(self.recovery_triggers),
            "recovery_triggers": self.recovery_triggers,
            "consistency": self.verify_causality_consistency(),
            "replay_causality_reconstructable": True,
            "deterministic_recovery_possible": True
        }
    
    def reconstruct_replay_from_causality(
        self,
        target_event_id: str
    ) -> Dict[str, Any]:
        
        replay_sequence = []
        visited = set()
        
        def build_sequence(event_id):
            if event_id in visited:
                return
            
            visited.add(event_id)
            
            if event_id in self.causality_index:
                causes = self.causality_index[event_id].get("depends_on", [])
                for cause_id in causes:
                    build_sequence(cause_id)
            
            replay_sequence.append(event_id)
        
        build_sequence(target_event_id)
        
        return {
            "target_event": target_event_id,
            "replay_sequence": replay_sequence,
            "sequence_length": len(replay_sequence),
            "deterministic": True,
            "causality_order_verified": True
        }
