

import json
import hashlib
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TraceNode:
    
    node_id: str
    trace_id: str
    service_name: str
    timestamp: str
    input_hash: str
    output_hash: str
    duration_ms: float
    causality_vector: Dict[str, int]  # Lamport clock
    parent_node_id: Optional[str] = None
    children_node_ids: List[str] = None
    
    def __post_init__(self):
        if self.children_node_ids is None:
            self.children_node_ids = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TraceGraph:
    
    trace_id: str
    created_at: str
    root_node_id: Optional[str]
    nodes: Dict[str, TraceNode]
    edges: List[Tuple[str, str]]  # (from_node, to_node)
    causality_respected: bool
    graph_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "created_at": self.created_at,
            "root_node_id": self.root_node_id,
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": self.edges,
            "causality_respected": self.causality_respected,
            "graph_hash": self.graph_hash
        }


class CausalityVector:
    
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.clock: Dict[str, int] = {service_name: 0}
    
    def increment(self):
        """Increment local clock."""
        self.clock[self.service_name] = self.clock.get(self.service_name, 0) + 1
    
    def observe(self, received_vector: Dict[str, int]):
        
        for service, value in received_vector.items():
            if service not in self.clock:
                self.clock[service] = 0
            self.clock[service] = max(self.clock[service], value)
        self.increment()
    
    def to_dict(self) -> Dict[str, int]:
        return self.clock.copy()


class DistributedTraceReconstructor:
    
    
    def __init__(self):
        self.trace_graphs: Dict[str, TraceGraph] = {}
        self.service_trace_nodes: Dict[str, List[TraceNode]] = {}
        self.lineage_recovery_records: List[Dict[str, Any]] = []
        self.causality_violations: List[Dict[str, Any]] = []
        self.execution_graph_cache: Dict[str, Dict[str, Any]] = {}
        
    def create_trace_node(self,
                         trace_id: str,
                         service_name: str,
                         input_hash: str,
                         output_hash: str,
                         duration_ms: float,
                         causality_vector: Dict[str, int],
                         parent_node_id: Optional[str] = None) -> TraceNode:
        
        node_id = f"NODE-{trace_id}-{service_name}-{len(self.service_trace_nodes.get(service_name, []))}"
        
        node = TraceNode(
            node_id=node_id,
            trace_id=trace_id,
            service_name=service_name,
            timestamp=datetime.utcnow().isoformat() + "Z",
            input_hash=input_hash,
            output_hash=output_hash,
            duration_ms=duration_ms,
            causality_vector=causality_vector,
            parent_node_id=parent_node_id
        )
        
        if service_name not in self.service_trace_nodes:
            self.service_trace_nodes[service_name] = []
        self.service_trace_nodes[service_name].append(node)
        
        logger.info(f"Created trace node {node_id} for service {service_name}")
        return node
    
    def build_trace_graph(self, trace_id: str, nodes: List[TraceNode]) -> TraceGraph:
        
        if not nodes:
            logger.warning(f"No nodes to build graph for trace {trace_id}")
            return None
        
        nodes_dict = {node.node_id: node for node in nodes}
        edges = []
        root_node = None
        causality_respected = True
        
        
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                
                
                if self._causally_precedes(node1.causality_vector, node2.causality_vector):
                    edges.append((node1.node_id, node2.node_id))
                    node1.children_node_ids.append(node2.node_id)
                    node2.parent_node_id = node1.node_id
                elif not self._causally_precedes(node2.causality_vector, node1.causality_vector):
                    
                    
                    causality_respected = False
                    self.causality_violations.append({
                        "trace_id": trace_id,
                        "node1": node1.node_id,
                        "node2": node2.node_id,
                        "reason": "incomparable_causality_vectors"
                    })
        
        
        root_nodes = [n for n in nodes if n.parent_node_id is None]
        if root_nodes:
            root_node = root_nodes[0]
        
        
        graph_content = json.dumps({
            "nodes": [n.node_id for n in nodes],
            "edges": sorted(edges)
        }, sort_keys=True)
        graph_hash = hashlib.sha256(graph_content.encode()).hexdigest()
        
        graph = TraceGraph(
            trace_id=trace_id,
            created_at=datetime.utcnow().isoformat() + "Z",
            root_node_id=root_node.node_id if root_node else None,
            nodes=nodes_dict,
            edges=edges,
            causality_respected=causality_respected,
            graph_hash=graph_hash
        )
        
        self.trace_graphs[trace_id] = graph
        logger.info(f"Built trace graph for {trace_id} with {len(nodes)} nodes, causality_respected={causality_respected}")
        return graph
    
    def _causally_precedes(self, vc1: Dict[str, int], vc2: Dict[str, int]) -> bool:
        
        all_keys = set(vc1.keys()) | set(vc2.keys())
        
        less_equal = True
        strictly_less = False
        
        for key in all_keys:
            v1 = vc1.get(key, 0)
            v2 = vc2.get(key, 0)
            
            if v1 > v2:
                less_equal = False
                break
            if v1 < v2:
                strictly_less = True
        
        return less_equal and strictly_less
    
    def reconstruct_lineage_after_restart(self,
                                         trace_id: str,
                                         available_services: List[str]) -> Dict[str, Any]:
        
        if trace_id not in self.trace_graphs:
            logger.warning(f"No trace graph found for {trace_id}")
            return None
        
        graph = self.trace_graphs[trace_id]
        unavailable_services = []
        available_nodes = []
        missing_nodes = []
        
        
        for node in graph.nodes.values():
            if node.service_name in available_services:
                available_nodes.append(node)
            else:
                unavailable_services.append(node.service_name)
                missing_nodes.append(node)
        
        
        recoverable_edges = []
        for edge_from, edge_to in graph.edges:
            from_node = graph.nodes[edge_from]
            to_node = graph.nodes[edge_to]
            
            if from_node.service_name in available_services and to_node.service_name in available_services:
                recoverable_edges.append((edge_from, edge_to))
        
        recovery_record = {
            "trace_id": trace_id,
            "recovery_timestamp": datetime.utcnow().isoformat() + "Z",
            "total_nodes": len(graph.nodes),
            "available_nodes": len(available_nodes),
            "unavailable_nodes": len(missing_nodes),
            "unavailable_services": list(set(unavailable_services)),
            "recoverable_edges": len(recoverable_edges),
            "total_edges": len(graph.edges),
            "lineage_recoverable": len(recoverable_edges) > 0,
            "recovery_percentage": round(len(available_nodes) / len(graph.nodes) * 100, 2) if graph.nodes else 0,
            "original_graph_hash": graph.graph_hash
        }
        
        self.lineage_recovery_records.append(recovery_record)
        logger.info(f"Reconstructed lineage for {trace_id}: {recovery_record['recovery_percentage']}% recoverable")
        return recovery_record
    
    def verify_trace_continuity(self, trace_id: str) -> bool:
        
        
        if trace_id not in self.trace_graphs:
            return False
        
        graph = self.trace_graphs[trace_id]
        
        
        
        
        visited = set()
        
        def has_cycle_dfs(node_id: str, path: Set[str]) -> bool:
            if node_id in path:
                return True
            path.add(node_id)
            
            node = graph.nodes[node_id]
            for child_id in node.children_node_ids:
                if has_cycle_dfs(child_id, path.copy()):
                    return True
            return False
        
        
        
        if graph.root_node_id:
            if has_cycle_dfs(graph.root_node_id, set()):
                logger.error(f"Cycle detected in trace {trace_id}")
                return False
        
        return graph.causality_respected
    
    def extract_service_lineage(self, trace_id: str, service_name: str) -> List[TraceNode]:
        
        
        if trace_id not in self.trace_graphs:
            return []
        
        graph = self.trace_graphs[trace_id]
        nodes = [n for n in graph.nodes.values() if n.service_name == service_name]
        
        
        
        nodes = sorted(nodes, key=lambda n: (n.causality_vector.get(service_name, 0), n.timestamp))
        return nodes
    
    def get_execution_order(self, trace_id: str) -> List[str]:
        """Get the execution order of services for a trace."""
        if trace_id not in self.trace_graphs:
            return []
        
        graph = self.trace_graphs[trace_id]
        if not graph.root_node_id:
            return []
        
        order = []
        visited = set()
        
        def dfs(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            node = graph.nodes[node_id]
            if node.service_name not in order:
                order.append(node.service_name)
            for child_id in node.children_node_ids:
                dfs(child_id)
        
        dfs(graph.root_node_id)
        return order
    
    def export_trace_graph(self, trace_id: str) -> Dict[str, Any]:
        
        
        if trace_id not in self.trace_graphs:
            return {}
        
        graph = self.trace_graphs[trace_id]
        return graph.to_dict()
    
    def export_state(self) -> Dict[str, Any]:
        
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_traces": len(self.trace_graphs),
            "total_lineage_recoveries": len(self.lineage_recovery_records),
            "causality_violations": len(self.causality_violations),
            "lineage_recovery_records": self.lineage_recovery_records,
            "causality_violations": self.causality_violations
        }
