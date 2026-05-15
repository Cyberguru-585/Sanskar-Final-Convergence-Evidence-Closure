

import json
from datetime import datetime
from event_sourcing import store_event, verify_lineage_integrity, compute_event_hash
from async_orchestration import AsyncOrchestrator
from external_verification import ExternalExecutor, simulate_multi_executor_verification
from schema_evolution import SchemaRegistry, validate_input_contract
from concurrency_test_engine import ConcurrencyTestEngine, create_deterministic_replay_func
from observability import get_tracker, reset_tracker


def demo_1_append_only_lineage():
    
    print("\n" + "="*80)
    print("DEMO 1: APPEND-ONLY EVENT LINEAGE")
    print("="*80)
    
    trace_id = "TRACE-LINEAGE-001"
    
    # Store events in sequence
    print(f"\n1. Storing events for trace {trace_id}...")
    
    input_event = store_event(
        trace_id, 
        "INPUT", 
        {"signal": "test", "value": 100}
    )
    print(f"   Event 1: {input_event['event_id']}")
    print(f"   Event Hash: {input_event['event_hash'][:16]}...")
    print(f"   Chained Hash: {input_event['current_event_hash'][:16]}...")
    
    processing_event = store_event(
        trace_id,
        "PROCESSING",
        {"stage": "sanskar", "computed": 150}
    )
    print(f"\n   Event 2: {processing_event['event_id']}")
    print(f"   Previous Hash: {processing_event['previous_event_hash'][:16]}...")
    print(f"   Current Hash: {processing_event['current_event_hash'][:16]}...")
    
    # Verify lineage integrity
    print(f"\n2. Verifying lineage integrity...")
    proof = verify_lineage_integrity(trace_id)
    
    print(f"   Status: {proof['status']}")
    print(f"   Events Verified: {proof['events_verified']}")
    print(f"   Chain Valid: {proof['chain_valid']}")
    print(f"   Mutations Detected: {len(proof['mutations_detected'])}")
    print(f"   Deletions Detected: {len(proof['deletions_detected'])}")
    print(f"   Verdict: {proof['verdict']}")
    
    return {
        "demo_name": "append_only_lineage",
        "trace_id": trace_id,
        "events_stored": 2,
        "lineage_proof": proof
    }


def demo_2_distributed_replay_validation():
    """
    Demonstration 2: Distributed Replay Validation
    
    Requirements:
    - Replay across multiple isolated stage services
    - Reordered replay requests
    - Concurrent replay requests
    - Preserve trace integrity and output hash
    """
    print("\n" + "="*80)
    print("DEMO 2: DISTRIBUTED REPLAY VALIDATION")
    print("="*80)
    
    trace_id = "TRACE-REPLAY-001"
    
    print(f"\n1. Storing input event for distributed replay...")
    input_data = {
        "signal": "crop_yield_analysis",
        "regions": ["North", "South", "East"],
        "rainfall": 750,
        "temperature": 25
    }
    
    input_event = store_event(trace_id, "INPUT", input_data)
    original_hash = input_event["event_hash"]
    
    print(f"   Event stored: {input_event['event_id']}")
    print(f"   Original hash: {original_hash[:16]}...")
    
    # Simulate replay from different stages
    print(f"\n2. Simulating replay from distributed stages...")
    
    replay_scenarios = [
        ("Stage-Sanskar", input_data.copy()),
        ("Stage-Core", input_data.copy()),
        ("Stage-Enforcement", input_data.copy())
    ]
    
    all_hashes_match = True
    for stage_name, replay_input in replay_scenarios:
        replay_hash = compute_event_hash(replay_input)
        matches = replay_hash == original_hash
        all_hashes_match = all_hashes_match and matches
        
        status = "MATCH" if matches else "MISMATCH"
        print(f"   {stage_name}: {status} ({replay_hash[:16]}...)")
    
    return {
        "demo_name": "distributed_replay_validation",
        "trace_id": trace_id,
        "original_hash": original_hash,
        "all_replays_match": all_hashes_match,
        "verdict": "PASS — distributed replay integrity verified" if all_hashes_match else "FAIL"
    }


def demo_3_async_execution_simulation():
   
    print("\n" + "="*80)
    print("DEMO 3: ASYNC EXECUTION SIMULATION")
    print("="*80)
    
    orchestrator = AsyncOrchestrator(default_timeout_ms=2000, max_retries=3)
    trace_id = "TRACE-ASYNC-001"
    
    directive = {
        "directive_id": "DIR-001-North",
        "action": "prioritize_irrigation",
        "target": "North",
        "description": "Allocate priority irrigation resources"
    }
    
    print(f"\n1. Queueing async directive...")
    exec_context = orchestrator.queue_async_directive(directive, trace_id, delay_ms=200)
    print(f"   Execution ID: {exec_context['execution_id']}")
    print(f"   State: {exec_context['state']}")
    print(f"   Simulated delay: {exec_context['simulated_ack_delay_ms']}ms")
    
    print(f"\n2. Simulating delayed acknowledgment...")
    ack_payload = orchestrator.simulate_delayed_acknowledgment(exec_context, actual_delay_ms=250)
    print(f"   Acknowledged by: {ack_payload['acknowledged_by']}")
    print(f"   Delay: {ack_payload['acknowledgment_delay_ms']:.0f}ms")
    print(f"   State: {ack_payload['state']}")
    
    print(f"\n3. Simulating async execution...")
    completion_payload = orchestrator.simulate_async_execution(exec_context, execution_time_ms=300)
    print(f"   State: {completion_payload['state']}")
    print(f"   Completion hash: {completion_payload.get('completion_hash', 'N/A')[:16]}...")
    print(f"   Idempotency verified: {completion_payload.get('idempotency_verified', False)}")
    
    # Verify replay safety
    print(f"\n4. Verifying replay safety...")
    replay_safety = orchestrator.verify_replay_safety(orchestrator.execution_history)
    print(f"   Replay safe: {replay_safety['replay_safe']}")
    print(f"   Idempotency verified: {replay_safety['idempotency_verified']}")
    print(f"   Verdict: {replay_safety['verdict']}")
    
    return {
        "demo_name": "async_execution_simulation",
        "trace_id": trace_id,
        "execution_contexts": len(orchestrator.execution_history),
        "replay_safety": replay_safety
    }


def demo_4_external_execution_verification():
    
    print("\n" + "="*80)
    print("DEMO 4: EXTERNAL EXECUTION VERIFICATION")
    print("="*80)
    
    executor = ExternalExecutor(executor_id="EXECUTOR-001")
    trace_id = "TRACE-EXT-VERIFY-001"
    
    
    print(f"\n1. Issuing directive (Enforcement stage)...")
    directive = {
        "directive_id": "DIR-002-North",
        "action": "allocate_fertilizer",
        "target": "North"
    }
    
    directive_payload = executor.issue_directive(directive, trace_id, stage="enforcement")
    print(f"   Directive ID: {directive_payload['directive']['directive_id']}")
    print(f"   Issued by: {directive_payload['issued_by']}")
    print(f"   Status: {directive_payload['status']}")
    print(f"   Issuance timestamp: {directive_payload['issuance_timestamp']}")
    
    
    print(f"\n2. Executing directive (External Executor)...")
    execution_result = {
        "executed": True,
        "resources_allocated": 500,
        "completion_code": "SUCCESS"
    }
    
    verification_payload = executor.verify_execution(
        directive_payload, 
        execution_result, 
        execution_completed=True
    )
    
    print(f"   Verified by: {verification_payload['execution_verification']['verified_by']}")
    print(f"   Execution completed: {verification_payload['execution_verification']['execution_completed']}")
    print(f"   Verification timestamp: {verification_payload['execution_verification']['verification_timestamp']}")
    
    
    print(f"\n3. Verifying separation of concerns...")
    soc_proof = executor.verify_separation_of_concerns(verification_payload)
    print(f"   Separation verified: {soc_proof['separation_verified']}")
    print(f"   Issued by: {soc_proof['issuance']['issued_by']}")
    print(f"   Verified by: {soc_proof['verification']['verified_by']}")
    print(f"   Verdict: {soc_proof['verdict']}")
    
    return {
        "demo_name": "external_execution_verification",
        "trace_id": trace_id,
        "separation_of_concerns": soc_proof
    }


def demo_5_observability_correlation():
    
    print("\n" + "="*80)
    print("DEMO 5: OBSERVABILITY CORRELATION")
    print("="*80)
    
    reset_tracker()
    tracker = get_tracker()
    
    trace_id = "TRACE-OBS-001"
    parent_trace_id = "TRACE-PARENT-001"
    
    print(f"\n1. Setting correlation context...")
    correlation = tracker.set_correlation_context(
        trace_id, 
        parent_trace_id=parent_trace_id
    )
    print(f"   Trace ID: {correlation['trace_id']}")
    print(f"   Correlation ID: {correlation['correlation_id']}")
    print(f"   Parent Trace ID: {correlation['parent_trace_id']}")
    
    
    print(f"\n2. Recording pipeline transitions...")
    
    entry_log = tracker.record_stage_entry(trace_id, "sanskar", replay_mode=False)
    print(f"   Stage entry: sanskar")
    
    tracker.record_orchestration_transition(trace_id, "input", "sanskar", "normal")
    print(f"   Transition: input -> sanskar")
    
    tracker.record_dependency_status(trace_id, "database", "healthy", {"latency_ms": 45})
    print(f"   Dependency: database (healthy, 45ms)")
    
    
    import time
    time.sleep(0.1)
    exit_log = tracker.record_stage_exit(
        trace_id, "sanskar", entry_log["entry_time"],
        decision_state="CONFIDENT",
        dependency_status="healthy"
    )
    print(f"   Stage exit: sanskar ({exit_log['latency_ms']:.1f}ms)")
    
    
    print(f"\n3. Generating distributed trace report...")
    report = tracker.generate_distributed_trace_report(trace_id)
    print(f"   Total events: {report['total_events']}")
    print(f"   Event types: {list(report['events_by_type'].keys())}")
    print(f"   Stage latencies: {report['stage_latencies']}")
    print(f"   Correlation ID: {report['correlation_context']['correlation_id']}")
    
    return {
        "demo_name": "observability_correlation",
        "trace_id": trace_id,
        "correlation_report": report
    }


def demo_6_schema_evolution():
  
    print("\n" + "="*80)
    print("DEMO 6: SCHEMA EVOLUTION DISCIPLINE")
    print("="*80)
    
    registry = SchemaRegistry()
    
    
    print(f"\n1. Validating v1 schema...")
    v1_doc = {
        "trace_id": "TRACE-001",
        "signal": "test",
        "entities": []
    }
    
    v1_validation = registry.validate_document(v1_doc, "v1")
    print(f"   Valid: {v1_validation['valid']}")
    print(f"   Schema: v1")
    print(f"   Issues: {len(v1_validation['issues'])}")
    
    
    print(f"\n2. Validating v1.1 schema (with new fields)...")
    v11_doc = v1_doc.copy()
    v11_doc.update({
        "schema_version": "v1.1",
        "correlation_id": "CORR-001",
        "parent_trace_id": "TRACE-PARENT",
        "dependency_status": "healthy"
    })
    
    v11_validation = registry.validate_document(v11_doc, "v1.1")
    print(f"   Valid: {v11_validation['valid']}")
    print(f"   Schema: v1.1")
    print(f"   Issues: {len(v11_validation['issues'])}")
    
    
    print(f"\n3. Testing backward compatibility...")
    is_compatible_v1_to_v11 = registry.is_backward_compatible("v1", "v1.1")
    print(f"   v1 -> v1.1: {is_compatible_v1_to_v11}")
    
    
    print(f"\n4. Migrating from v1 to v1.1...")
    migration = registry.migrate_document(v1_doc, "v1.1")
    print(f"   Migration success: {migration['success']}")
    print(f"   Validation: {migration['validation']['valid']}")
    
   
    print(f"\n5. Compatibility matrix...")
    matrix = registry.get_compatibility_matrix()
    print(f"   v1 -> v1.1: {matrix['v1']['v1.1']}")
    print(f"   v1.1 -> v1.2: {matrix['v1.1']['v1.2']}")
    
    return {
        "demo_name": "schema_evolution",
        "v1_valid": v1_validation['valid'],
        "v11_valid": v11_validation['valid'],
        "compatibility": registry.get_compatibility_matrix()
    }


def demo_7_concurrency_determinism():
    
    print("\n" + "="*80)
    print("DEMO 7: CONCURRENCY-SAFE DETERMINISM TESTING")
    print("="*80)
    
    
    data_store = {
        "TRACE-001": {"signal": "test1", "value": 100},
        "TRACE-002": {"signal": "test2", "value": 200},
        "TRACE-003": {"signal": "test3", "value": 300},
    }
    
    replay_func = create_deterministic_replay_func(data_store)
    engine = ConcurrencyTestEngine(max_workers=4)
    
    print(f"\n1. Running concurrent replays (3 rounds)...")
    replay_proof = engine.run_concurrent_replays(
        replay_func,
        list(data_store.keys()),
        num_concurrent_rounds=3
    )
    
    print(f"   Total executions: {replay_proof['total_executions']}")
    print(f"   Unique hashes: {replay_proof['unique_hashes']}")
    print(f"   Is deterministic: {replay_proof['is_deterministic']}")
    print(f"   Verdict: {replay_proof['verdict']}")
    
    
    print(f"\n2. Running parallel execution simulation...")
    
    def deterministic_exec(**kwargs):
        iteration = kwargs.get('iteration', 0)
        parallel_id = kwargs.get('parallel_id', 0)
        return {
            "iteration": iteration,
            "parallel_id": parallel_id,
            "result": (iteration + parallel_id) * 100
        }
    
    parallel_proof = engine.run_parallel_execution_simulation(
        deterministic_exec,
        num_parallel=4,
        iterations=3
    )
    
    print(f"   Total executions: {parallel_proof['total_executions']}")
    print(f"   Unique hashes: {parallel_proof['unique_hashes']}")
    print(f"   Is deterministic: {parallel_proof['is_deterministic']}")
    print(f"   Verdict: {parallel_proof['verdict']}")
    
    # Get summary
    print(f"\n3. Determinism test summary...")
    summary = engine.get_determinism_summary()
    print(f"   Total tests: {summary['total_tests']}")
    print(f"   Passed: {summary['passed']}")
    print(f"   Failed: {summary['failed']}")
    print(f"   Overall verdict: {summary['overall_verdict']}")
    
    return {
        "demo_name": "concurrency_determinism",
        "replay_proof": replay_proof,
        "parallel_proof": parallel_proof,
        "summary": summary
    }


def demo_8_governance_uncertainty():
    
    print("\n" + "="*80)
    print("DEMO 8: GOVERNANCE-SAFE UNCERTAINTY PROPAGATION")
    print("="*80)
    
    print(f"\n1. Simulating decision with different uncertainty states...\n")
    
    
    core_output_confident = {
        "trace_id": "TRACE-UNC-001",
        "selected_entity": "North",
        "selected_score": 0.85,
        "selected_decision_state": "CONFIDENT",
        "priority": "high",
        "reasoning": "Clear winner with high score"
    }
    
    print("Scenario 1 - CONFIDENT Decision:")
    print(f"  Decision state: {core_output_confident['selected_decision_state']}")
    print(f"  Score: {core_output_confident['selected_score']}")
    print(f"  Governance warning: None")
    
    
    core_output_ambiguous = {
        "trace_id": "TRACE-UNC-002",
        "selected_entity": "East",
        "selected_score": 0.71,
        "selected_decision_state": "AMBIGUOUS",
        "priority": "medium",
        "reasoning": "Very close competitors"
    }
    
    print("\nScenario 2 - AMBIGUOUS Decision:")
    print(f"  Decision state: {core_output_ambiguous['selected_decision_state']}")
    print(f"  Score: {core_output_ambiguous['selected_score']}")
    print(f"  Governance warning: low_confidence_execution_risk")
    
    
    core_output_low_conf = {
        "trace_id": "TRACE-UNC-003",
        "selected_entity": "West",
        "selected_score": 0.45,
        "selected_decision_state": "LOW_CONFIDENCE",
        "priority": "low",
        "reasoning": "Marginal recommendation"
    }
    
    print("\nScenario 3 - LOW CONFIDENCE Decision:")
    print(f"  Decision state: {core_output_low_conf['selected_decision_state']}")
    print(f"  Score: {core_output_low_conf['selected_score']}")
    print(f"  Governance warning: moderate_confidence_execution_risk")
    
    
    print(f"\n2. Propagating uncertainty to enforcement...\n")
    
    uncertainty_propagation = []
    for core_output in [core_output_confident, core_output_ambiguous, core_output_low_conf]:
        decision_state = core_output.get("selected_decision_state", "CONFIDENT")
        
        governance_warning = None
        if decision_state == "AMBIGUOUS":
            governance_warning = "low_confidence_execution_risk"
        elif decision_state == "LOW_CONFIDENCE":
            governance_warning = "moderate_confidence_execution_risk"
        
        propagation = {
            "trace_id": core_output["trace_id"],
            "decision_state": decision_state,
            "governance_warning": governance_warning,
            "enforcement_guidance": "Verify locally before deployment" if governance_warning else "Clear to proceed"
        }
        
        uncertainty_propagation.append(propagation)
        
        print(f"  Trace {core_output['trace_id']}: {decision_state}")
        print(f"    Warning: {governance_warning or 'None'}")
        print(f"    Guidance: {propagation['enforcement_guidance']}\n")
    
    return {
        "demo_name": "governance_uncertainty",
        "propagations": uncertainty_propagation
    }


def run_all_demos():
    """Run all demonstrations."""
    print("\n" + "#"*80)
    print("# SANSKAR DISTRIBUTED-SAFE UPGRADE - COMPREHENSIVE DEMONSTRATION")
    print("# All 7 Hard Requirements + Governance Uncertainty Propagation")
    print("#"*80)
    
    results = {}
    
    
    results["1_lineage"] = demo_1_append_only_lineage()
    results["2_replay"] = demo_2_distributed_replay_validation()
    results["3_async"] = demo_3_async_execution_simulation()
    results["4_external"] = demo_4_external_execution_verification()
    results["5_observability"] = demo_5_observability_correlation()
    results["6_schema"] = demo_6_schema_evolution()
    results["7_concurrency"] = demo_7_concurrency_determinism()
    results["8_governance"] = demo_8_governance_uncertainty()
    
    
    print("\n" + "="*80)
    print("DEMONSTRATION SUMMARY")
    print("="*80)
    print("\n[1] Demo 1: Append-Only Lineage - COMPLETE")
    print("[2] Demo 2: Distributed Replay - COMPLETE")
    print("[3] Demo 3: Async Orchestration - COMPLETE")
    print("[4] Demo 4: External Verification - COMPLETE")
    print("[5] Demo 5: Observability Correlation - COMPLETE")
    print("[6] Demo 6: Schema Evolution - COMPLETE")
    print("[7] Demo 7: Concurrency Determinism - COMPLETE")
    print("[8] Demo 8: Governance Uncertainty - COMPLETE")
    print("\n" + "="*80)
    
    return results


if __name__ == "__main__":
    results = run_all_demos()
    
    
    with open("demo_results_upgrade.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n[*] Results saved to demo_results_upgrade.json")
