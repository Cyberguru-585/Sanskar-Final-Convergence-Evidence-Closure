
import json
from datetime import datetime
from typing import Dict, Any, List, Set, Tuple
import uuid


class ExecutionGraphNode:
    
    
    def __init__(self, node_id: str, node_type: str, trace_id: str, metadata: Dict[str, Any] = None):
        self.node_id = node_id
        self.node_type = node_type  # STAGE, DECISION, FAILURE, RECOVERY, TELEMETRY
        self.trace_id = trace_id
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.incoming_edges = []
        self.outgoing_edges = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class ExecutionGraphEdge:
    
    
    def __init__(self, 
                 source_node_id: str,
                 target_node_id: str,
                 edge_type: str,
                 metadata: Dict[str, Any] = None):
        self.edge_id = f"EDGE-{uuid.uuid4().hex[:8]}"
        self.source_node_id = source_node_id
        self.target_node_id = target_node_id
        self.edge_type = edge_type  # DIRECT, DEPENDENCY, REPLAY, RECOVERY, TELEMETRY
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "edge_type": self.edge_type,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class ExecutionGraphReconstructor:
        
    def __init__(self):
        self.nodes = {}  # node_id -> ExecutionGraphNode
        self.edges = {}  # edge_id -> ExecutionGraphEdge
        self.traces = {}  # trace_id -> trace_metadata
        self.dependency_graph = {}  # node_id -> list of dependent node_ids
    
    def add_stage_node(self,
                      trace_id: str,
                      stage_name: str,
                      stage_output: Dict[str, Any]) -> ExecutionGraphNode:
        
        node_id = f"STAGE-{stage_name.upper()}-{uuid.uuid4().hex[:8]}"
        
        node = ExecutionGraphNode(
            node_id=node_id,
            node_type="STAGE",
            trace_id=trace_id,
            metadata={
                "stage_name": stage_name,
                "status": "success" if "failure" not in stage_output else "failed",
                "output_hash": self._compute_hash(stage_output),
                "output_keys": list(stage_output.keys())
            }
        )
        
        self.nodes[node_id] = node
        return node
    
    def add_decision_node(self,
                         trace_id: str,
                         decision_type: str,
                         decision_data: Dict[str, Any]) -> ExecutionGraphNode:
        
        node_id = f"DECISION-{decision_type.upper()}-{uuid.uuid4().hex[:8]}"
        
        node = ExecutionGraphNode(
            node_id=node_id,
            node_type="DECISION",
            trace_id=trace_id,
            metadata={
                "decision_type": decision_type,
                "decision": decision_data.get("decision", ""),
                "confidence": decision_data.get("confidence", 0),
                "reasoning": decision_data.get("reasoning", "")
            }
        )
        
        self.nodes[node_id] = node
        return node
    
    def add_failure_node(self,
                        trace_id: str,
                        failure_info: Dict[str, Any]) -> ExecutionGraphNode:
        
        node_id = f"FAILURE-{failure_info.get('stage', 'UNKNOWN').upper()}-{uuid.uuid4().hex[:8]}"
        
        node = ExecutionGraphNode(
            node_id=node_id,
            node_type="FAILURE",
            trace_id=trace_id,
            metadata={
                "failure_stage": failure_info.get("stage"),
                "failure_code": failure_info.get("code"),
                "failure_message": failure_info.get("message"),
                "trace_preserved": failure_info.get("trace_preserved", False)
            }
        )
        
        self.nodes[node_id] = node
        return node
    
    def add_recovery_node(self,
                         trace_id: str,
                         recovery_info: Dict[str, Any]) -> ExecutionGraphNode:
        
        node_id = f"RECOVERY-{uuid.uuid4().hex[:8]}"
        
        node = ExecutionGraphNode(
            node_id=node_id,
            node_type="RECOVERY",
            trace_id=trace_id,
            metadata={
                "recovery_type": recovery_info.get("recovery_type"),
                "affected_service": recovery_info.get("affected_service"),
                "status": recovery_info.get("status"),
                "lineage_reconstructed": recovery_info.get("lineage_reconstructed", False),
                "replay_continuity_preserved": recovery_info.get("replay_continuity_preserved", False)
            }
        )
        
        self.nodes[node_id] = node
        return node
    
    def add_telemetry_node(self,
                          trace_id: str,
                          telemetry_data: Dict[str, Any]) -> ExecutionGraphNode:
        
        node_id = f"TELEMETRY-{uuid.uuid4().hex[:8]}"
        
        node = ExecutionGraphNode(
            node_id=node_id,
            node_type="TELEMETRY",
            trace_id=trace_id,
            metadata={
                "telemetry_type": telemetry_data.get("telemetry_type"),
                "metrics": telemetry_data.get("metrics", []),
                "service_state": telemetry_data.get("service_state")
            }
        )
        
        self.nodes[node_id] = node
        return node
    
    def add_edge(self,
                source_node_id: str,
                target_node_id: str,
                edge_type: str,
                metadata: Dict[str, Any] = None) -> ExecutionGraphEdge:
        """Add an edge between two nodes."""
        if source_node_id not in self.nodes or target_node_id not in self.nodes:
            raise ValueError(f"Source or target node not found")
        
        edge = ExecutionGraphEdge(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            edge_type=edge_type,
            metadata=metadata
        )
        
        self.edges[edge.edge_id] = edge
        
        
        self.nodes[source_node_id].outgoing_edges.append(edge.edge_id)
        self.nodes[target_node_id].incoming_edges.append(edge.edge_id)
        
        
        if source_node_id not in self.dependency_graph:
            self.dependency_graph[source_node_id] = []
        self.dependency_graph[source_node_id].append(target_node_id)
        
        return edge
    
    def reconstruct_from_execution_chain(self,
                                        chain_result: Dict[str, Any]) -> Dict[str, Any]:
       
        trace_id = chain_result.get("trace_id")
        
        
        self.traces[trace_id] = {
            "trace_id": trace_id,
            "chain_executed_at": chain_result.get("chain_executed_at"),
            "stages_executed": []
        }
        
        
        stage_nodes = {}
        stages = chain_result.get("stages", {})
        
        for i, (stage_name, stage_output) in enumerate(stages.items()):
            node = self.add_stage_node(trace_id, stage_name, stage_output)
            stage_nodes[stage_name] = node
            self.traces[trace_id]["stages_executed"].append(stage_name)
            
            
            if "decision" in stage_output:
                decision_node = self.add_decision_node(
                    trace_id,
                    stage_name,
                    stage_output
                )
                self.add_edge(
                    node.node_id,
                    decision_node.node_id,
                    edge_type="DECISION",
                    metadata={"stage": stage_name}
                )
        
        
        stage_names = list(stages.keys())
        for i in range(len(stage_names) - 1):
            current_stage = stage_names[i]
            next_stage = stage_names[i + 1]
            
            if current_stage in stage_nodes and next_stage in stage_nodes:
                self.add_edge(
                    stage_nodes[current_stage].node_id,
                    stage_nodes[next_stage].node_id,
                    edge_type="DIRECT",
                    metadata={"sequence": i + 1}
                )
        
        
        failures = chain_result.get("failures", [])
        failure_nodes = []
        for failure_info in failures:
            failure_node = self.add_failure_node(trace_id, failure_info)
            failure_nodes.append(failure_node)
            
            
            failing_stage = failure_info.get("stage")
            if failing_stage in stage_nodes:
                self.add_edge(
                    stage_nodes[failing_stage].node_id,
                    failure_node.node_id,
                    edge_type="FAILURE"
                )
        
        
        recovery_attempts = chain_result.get("recovery_attempts", [])
        for recovery_info in recovery_attempts:
            recovery_node = self.add_recovery_node(trace_id, recovery_info)
            
            
            if failure_nodes:
                self.add_edge(
                    failure_nodes[-1].node_id,
                    recovery_node.node_id,
                    edge_type="RECOVERY"
                )
            
            
            affected_service = recovery_info.get("affected_service")
            if affected_service and affected_service in stage_nodes:
                self.add_edge(
                    recovery_node.node_id,
                    stage_nodes[affected_service].node_id,
                    edge_type="RECOVERY",
                    metadata={"post_recovery": True}
                )
        
        
        telemetry_stage = stages.get("telemetry", {})
        if telemetry_stage:
            telemetry_node = self.add_telemetry_node(
                trace_id,
                {
                    "telemetry_type": "chain_execution",
                    "metrics": ["execution_latency", "service_health", "replay_lineage"],
                    "service_state": chain_result.get("service_states_at_execution", {})
                }
            )
            
            if "bucket" in stage_nodes:
                self.add_edge(
                    stage_nodes["bucket"].node_id,
                    telemetry_node.node_id,
                    edge_type="TELEMETRY"
                )
        
        return self.export_as_json(trace_id)
    
    def export_as_json(self, trace_id: str = None) -> Dict[str, Any]:
        
        graph_export = {
            "trace_id": trace_id,
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "nodes": [],
            "edges": [],
            "statistics": {}
        }
        
        
        filtered_nodes = {nid: n for nid, n in self.nodes.items() 
                         if trace_id is None or n.trace_id == trace_id}
        filtered_edges = {eid: e for eid, e in self.edges.items() 
                         if trace_id is None or 
                         (self.nodes.get(e.source_node_id, ExecutionGraphNode("", "", "")).trace_id == trace_id)}
        
        
        node_types = {}
        for node in filtered_nodes.values():
            graph_export["nodes"].append(node.to_dict())
            node_types[node.node_type] = node_types.get(node.node_type, 0) + 1
        
        
        edge_types = {}
        for edge in filtered_edges.values():
            graph_export["edges"].append(edge.to_dict())
            edge_types[edge.edge_type] = edge_types.get(edge.edge_type, 0) + 1
        
        
        graph_export["statistics"] = {
            "total_nodes": len(filtered_nodes),
            "total_edges": len(filtered_edges),
            "nodes_by_type": node_types,
            "edges_by_type": edge_types,
            "has_failures": any(n.node_type == "FAILURE" for n in filtered_nodes.values()),
            "has_recovery": any(n.node_type == "RECOVERY" for n in filtered_nodes.values()),
            "has_telemetry": any(n.node_type == "TELEMETRY" for n in filtered_nodes.values())
        }
        
        return graph_export
    
    def analyze_execution_paths(self, trace_id: str) -> List[List[str]]:
        
        paths = []
        
        
        trace_nodes = [nid for nid, n in self.nodes.items() if n.trace_id == trace_id]
        
        
        root_nodes = [nid for nid in trace_nodes 
                      if nid not in self.dependency_graph]
        
        
        for root in root_nodes:
            paths.extend(self._find_paths_dfs(root, trace_id))
        
        return paths
    
    def _find_paths_dfs(self, node_id: str, trace_id: str, path: List[str] = None) -> List[List[str]]:
        
        if path is None:
            path = []
        
        path = path + [node_id]
        
        if node_id not in self.dependency_graph:
            return [path]
        
        paths = []
        for neighbor in self.dependency_graph[node_id]:
            if neighbor not in path:  # Avoid cycles
                paths.extend(self._find_paths_dfs(neighbor, trace_id, path))
        
        return paths if paths else [path]
    
    def detect_critical_paths(self, trace_id: str) -> List[Dict[str, Any]]:
        
        critical_paths = []
        all_paths = self.analyze_execution_paths(trace_id)
        
        for path in all_paths:
            path_nodes = [self.nodes.get(nid) for nid in path]
            
            has_failure = any(n and n.node_type == "FAILURE" for n in path_nodes)
            has_recovery = any(n and n.node_type == "RECOVERY" for n in path_nodes)
            has_decision = any(n and n.node_type == "DECISION" for n in path_nodes)
            
            if has_failure or has_recovery or has_decision:
                critical_paths.append({
                    "path": path,
                    "path_length": len(path),
                    "has_failure": has_failure,
                    "has_recovery": has_recovery,
                    "has_governance_decision": has_decision,
                    "nodes": [self.nodes.get(nid).to_dict() if nid in self.nodes else {} 
                             for nid in path]
                })
        
        return critical_paths
    
    def _compute_hash(self, data: Dict[str, Any]) -> str:
        
        import hashlib
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]
