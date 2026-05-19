

import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DivergenceType(Enum):
    HASH_MISMATCH = "hash_mismatch"
    CONFLICTING_LINEAGE = "conflicting_lineage"
    DUPLICATE_EVENT = "duplicate_event"
    OUT_OF_ORDER_EVENT = "out_of_order_event"
    STALE_REPLAY_EVENT = "stale_replay_event"
    CORRUPTED_METADATA = "corrupted_metadata"
    MISSING_EVENT = "missing_event"


@dataclass
class ReplayEvent:
    
    event_id: str
    trace_id: str
    service: str
    sequence_number: int
    payload: Dict[str, Any]
    timestamp: str
    content_hash: str
    replay_mode: str
    lineage_path: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DivergenceReport:
    
    divergence_id: str
    divergence_type: str
    trace_id: str
    timestamp: str
    affected_services: List[str]
    conflicting_events: List[Dict[str, Any]]
    expected_state: Dict[str, Any]
    actual_state: Dict[str, Any]
    severity: str
    reconciliation_action: str
    reconciliation_required: bool


class ReplayDivergenceDetector:
    
    
    def __init__(self):
        self.event_log: List[ReplayEvent] = []
        self.divergence_reports: List[DivergenceReport] = []
        self.canonical_traces: Dict[str, List[ReplayEvent]] = {}
        self.replay_cache: Dict[str, Dict[str, Any]] = {}
        self.hash_registry: Dict[str, str] = {}  # event_id -> content_hash
        
    def record_replay_event(self, event: ReplayEvent) -> bool:
        
        self.event_log.append(event)
        
        
        if event.trace_id not in self.canonical_traces:
            self.canonical_traces[event.trace_id] = []
        self.canonical_traces[event.trace_id].append(event)
        
        
        self.hash_registry[event.event_id] = event.content_hash
        
        logger.info(f"Recorded replay event {event.event_id} for trace {event.trace_id}")
        return True
    
    def detect_duplicate_events(self, trace_id: str) -> List[Tuple[ReplayEvent, ReplayEvent]]:
        """Detect duplicate events in replay."""
        if trace_id not in self.canonical_traces:
            return []
        
        events = self.canonical_traces[trace_id]
        duplicates = []
        
        for i, event1 in enumerate(events):
            for event2 in events[i+1:]:
                
                if (event1.service == event2.service and
                    event1.sequence_number == event2.sequence_number and
                    event1.content_hash == event2.content_hash):
                    duplicates.append((event1, event2))
        
        return duplicates
    
    def detect_out_of_order_events(self, trace_id: str) -> List[Tuple[ReplayEvent, ReplayEvent]]:
        
        if trace_id not in self.canonical_traces:
            return []
        
        events = self.canonical_traces[trace_id]
        out_of_order = []
        
        
        last_sequence = {}
        
        for event in events:
            service = event.service
            if service in last_sequence:
                if event.sequence_number <= last_sequence[service]:
                    
                    prev_event = next(e for e in events if e.service == service and e.sequence_number == last_sequence[service])
                    out_of_order.append((prev_event, event))
            last_sequence[service] = event.sequence_number
        
        return out_of_order
    
    def detect_hash_mismatch(self, trace_id: str) -> List[Dict[str, Any]]:
        
        if trace_id not in self.canonical_traces:
            return []
        
        events = self.canonical_traces[trace_id]
        mismatches = []
        
        for event in events:
            
            serialized = json.dumps(event.payload, sort_keys=True, default=str)
            computed_hash = hashlib.sha256(serialized.encode()).hexdigest()
            
            if computed_hash != event.content_hash:
                mismatches.append({
                    "event_id": event.event_id,
                    "service": event.service,
                    "expected_hash": event.content_hash,
                    "computed_hash": computed_hash,
                    "corruption_detected": True
                })
        
        return mismatches
    
    def detect_conflicting_lineage(self, trace_id: str) -> List[Dict[str, Any]]:
        
        if trace_id not in self.canonical_traces:
            return []
        
        events = self.canonical_traces[trace_id]
        lineage_paths = set()
        conflicts = []
        
        for event in events:
            lineage_key = tuple(event.lineage_path)
            
            
            for existing_path in lineage_paths:
                
                if len(lineage_key) == len(existing_path):
                    differences = sum(1 for a, b in zip(lineage_key, existing_path) if a != b)
                    if differences > 1:  # More than 1 service differs = conflict
                        conflicts.append({
                            "trace_id": trace_id,
                            "conflicting_lineages": [lineage_key, existing_path],
                            "conflict_type": "incompatible_service_paths"
                        })
            
            lineage_paths.add(lineage_key)
        
        return conflicts
    
    def detect_stale_replay_events(self, trace_id: str, stale_threshold_seconds: int = 300) -> List[ReplayEvent]:
        
        if trace_id not in self.canonical_traces:
            return []
        
        events = self.canonical_traces[trace_id]
        now = datetime.utcnow()
        stale = []
        
        for event in events:
            event_time = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
            age_seconds = (now - event_time.replace(tzinfo=None)).total_seconds()
            
            if age_seconds > stale_threshold_seconds:
                stale.append(event)
        
        return stale
    
    def comprehensive_divergence_check(self, trace_id: str) -> List[DivergenceReport]:
        
        reports = []
        
        
        duplicates = self.detect_duplicate_events(trace_id)
        if duplicates:
            for dup1, dup2 in duplicates:
                report = DivergenceReport(
                    divergence_id=f"DIV-DUP-{len(reports)}",
                    divergence_type=DivergenceType.DUPLICATE_EVENT.value,
                    trace_id=trace_id,
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    affected_services=[dup1.service],
                    conflicting_events=[dup1.to_dict(), dup2.to_dict()],
                    expected_state={"event_count": 1},
                    actual_state={"event_count": 2},
                    severity="HIGH",
                    reconciliation_action="REJECT_DUPLICATE",
                    reconciliation_required=True
                )
                reports.append(report)
        
        
        out_of_order = self.detect_out_of_order_events(trace_id)
        if out_of_order:
            for event1, event2 in out_of_order:
                report = DivergenceReport(
                    divergence_id=f"DIV-OOO-{len(reports)}",
                    divergence_type=DivergenceType.OUT_OF_ORDER_EVENT.value,
                    trace_id=trace_id,
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    affected_services=[event1.service],
                    conflicting_events=[event1.to_dict(), event2.to_dict()],
                    expected_state={"sequence_order": "ascending"},
                    actual_state={"sequence_order": "non_ascending"},
                    severity="CRITICAL",
                    reconciliation_action="REPLAY_RECONSTRUCTION",
                    reconciliation_required=True
                )
                reports.append(report)
        
        
        mismatches = self.detect_hash_mismatch(trace_id)
        if mismatches:
            for mismatch in mismatches:
                report = DivergenceReport(
                    divergence_id=f"DIV-HASH-{len(reports)}",
                    divergence_type=DivergenceType.HASH_MISMATCH.value,
                    trace_id=trace_id,
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    affected_services=[mismatch["service"]],
                    conflicting_events=[mismatch],
                    expected_state={"hash": mismatch["expected_hash"]},
                    actual_state={"hash": mismatch["computed_hash"]},
                    severity="CRITICAL",
                    reconciliation_action="REJECT_CORRUPTED_EVENT",
                    reconciliation_required=True
                )
                reports.append(report)
        
     
        conflicts = self.detect_conflicting_lineage(trace_id)
        if conflicts:
            for conflict in conflicts:
                report = DivergenceReport(
                    divergence_id=f"DIV-LINEAGE-{len(reports)}",
                    divergence_type=DivergenceType.CONFLICTING_LINEAGE.value,
                    trace_id=trace_id,
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    affected_services=list(set(sum(conflict["conflicting_lineages"], ()))),
                    conflicting_events=[conflict],
                    expected_state={"lineage_consistency": "strict"},
                    actual_state={"lineage_consistency": "violated"},
                    severity="CRITICAL",
                    reconciliation_action="ABORT_REPLAY",
                    reconciliation_required=True
                )
                reports.append(report)
        
        
        stale = self.detect_stale_replay_events(trace_id)
        if stale:
            for event in stale:
                report = DivergenceReport(
                    divergence_id=f"DIV-STALE-{len(reports)}",
                    divergence_type=DivergenceType.STALE_REPLAY_EVENT.value,
                    trace_id=trace_id,
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    affected_services=[event.service],
                    conflicting_events=[event.to_dict()],
                    expected_state={"event_age": "recent"},
                    actual_state={"event_timestamp": event.timestamp},
                    severity="MEDIUM",
                    reconciliation_action="SKIP_STALE_EVENT",
                    reconciliation_required=True
                )
                reports.append(report)
        
        self.divergence_reports.extend(reports)
        return reports
    
    def is_replay_safe(self, trace_id: str) -> bool:
        
        reports = self.comprehensive_divergence_check(trace_id)
        
        
        critical_reports = [r for r in reports if r.severity in ["CRITICAL"]]
        return len(critical_reports) == 0
    
    def get_divergence_reports(self, trace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        
        reports = [asdict(r) for r in self.divergence_reports]
        if trace_id:
            reports = [r for r in reports if r["trace_id"] == trace_id]
        return reports
    
    def export_state(self) -> Dict[str, Any]:
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_events": len(self.event_log),
            "total_traces": len(self.canonical_traces),
            "divergence_reports": len(self.divergence_reports),
            "critical_divergences": sum(1 for r in self.divergence_reports if r.severity == "CRITICAL"),
            "reports": self.get_divergence_reports()
        }
