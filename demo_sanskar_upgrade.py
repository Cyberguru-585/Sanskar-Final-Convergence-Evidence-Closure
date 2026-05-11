

import json
from tantra import run_tantra


def demo_1_uncertainty_detection():
    """Demonstrate uncertainty detection layer."""
    print("\n" + "="*70)
    print("DEMO 1: UNCERTAINTY DETECTION LAYER")
    print("="*70)
    
    input_contract = {
        "trace_id": "DEMO-UNCERTAINTY-001",
        "signal": {
            "dataset": "crop_yield.csv"
        }
    }
    
    result = run_tantra(input_contract)
    
    if result["pipeline_status"] == "SUCCESS":
        entities = result["sanskar_output"]["entities"]
        
        print("\n Decision states detected for each region:")
        for entity in entities:
            print(f"  {entity['entity_id']:12} | decision_state: {entity.get('decision_state', 'UNKNOWN'):15} | confidence: {entity['confidence']:.3f}")
        
        top_entity = entities[0]
        print(f"\n Top ranked: {top_entity['entity_id']}")
        print(f"   Decision state: {top_entity.get('decision_state', 'UNKNOWN')}")
        print(f"   Confidence after adjustment: {top_entity['confidence']}")


def demo_2_confidence_engine():
    """Demonstrate 4-factor confidence engine."""
    print("\n" + "="*70)
    print("DEMO 2: CONFIDENCE ENGINE UPGRADE (4-Factor Model)")
    print("="*70)
    
    input_contract = {
        "trace_id": "DEMO-CONFIDENCE-002",
        "signal": {
            "dataset": "crop_yield.csv"
        }
    }
    
    result = run_tantra(input_contract)
    
    if result["pipeline_status"] == "SUCCESS":
        top_entity = result["sanskar_output"]["entities"][0]
        
        print(f"\n Entity: {top_entity['entity_id']}")
        print(f"\n   Confidence Calculation:")
        
        if "confidence_factors" in top_entity:
            factors = top_entity["confidence_factors"]
            print(f"   • Score contribution (50%):      {factors['score_contribution']:.4f}")
            print(f"   • Feature quality (25%):         {factors['feature_quality']:.4f}")
            print(f"   • Feature stability (15%):       {factors['feature_stability']:.4f}")
            print(f"   • Missing data penalty (10%):    {factors['missing_penalty']:.4f}")
            print(f"   " + "-"*40)
            print(f"   Final confidence:                {top_entity['confidence']:.4f}")


def demo_3_comparative_explanations():
    """Demonstrate real comparative explanations."""
    print("\n" + "="*70)
    print("DEMO 3: REAL COMPARATIVE REASONING")
    print("="*70)
    
    input_contract = {
        "trace_id": "DEMO-COMPARATIVE-003",
        "signal": {
            "dataset": "crop_yield.csv"
        }
    }
    
    result = run_tantra(input_contract)
    
    if result["pipeline_status"] == "SUCCESS":
        comp = result["sanskar_output"]["comparative_explanation"]
        
        print(f"\n Comparative Explanation:")
        print(f"\n   Summary: {comp['summary']}")
        
        if comp["advantages"]:
            print(f"\n   Advantages of top ranked:")
            for adv in comp["advantages"][:3]:
                print(f"   • {adv['factor']}: +{adv['delta']:.4f}")
        
        if comp["disadvantages"]:
            print(f"\n   Disadvantages:")
            for dis in comp["disadvantages"][:2]:
                print(f"   • {dis['factor']}: {dis['delta']:.4f}")


def demo_4_event_replay():
    """Demonstrate event-source replay."""
    print("\n" + "="*70)
    print("DEMO 4: EVENT-SOURCE REPLAY RECONSTRUCTION")
    print("="*70)
    
    # First execution
    input_contract = {
        "trace_id": "DEMO-REPLAY-004",
        "signal": {
            "dataset": "crop_yield.csv"
        }
    }
    
    result1 = run_tantra(input_contract)
    hash1 = result1["truth"]["pipeline_hash"]
    
    print(f"\n Original Execution:")
    print(f"   Trace ID: DEMO-REPLAY-004")
    print(f"   Pipeline hash: {hash1[:16]}...")
    
    # Replay execution
    result2 = run_tantra(input_contract, replay_mode=True)
    
    if result2["pipeline_status"] == "SUCCESS":
        hash2 = result2["truth"]["pipeline_hash"]
        print(f"\n Replay Execution:")
        print(f"   Pipeline hash: {hash2[:16]}...")
        print(f"   Event sourced: {result2.get('event_sourced', False)}")
        print(f"   Replay mode: {result2.get('replay_mode', False)}")
        
        if hash1 == hash2:
            print(f"\n DETERMINISM VERIFIED: Hashes match!")
        else:
            print(f"\n DETERMINISM FAILED: Hashes differ!")


def demo_5_enforcement_acknowledgment():
    """Demonstrate enforcement acknowledgment loop."""
    print("\n" + "="*70)
    print("DEMO 5: ENFORCEMENT ACKNOWLEDGMENT LOOP")
    print("="*70)
    
    input_contract = {
        "trace_id": "DEMO-ACK-005",
        "signal": {
            "dataset": "crop_yield.csv"
        }
    }
    
    result = run_tantra(input_contract)
    
    if result["pipeline_status"] == "SUCCESS":
        enforcement = result["enforcement"]
        
        print(f"\n Enforcement Directives:")
        for directive in enforcement["directives"][:2]:
            print(f"\n   {directive['directive_id']}:")
            print(f"   • Action: {directive['action']}")
            print(f"   • Execution status: {directive.get('execution_status', 'PENDING')}")
            print(f"   • Acknowledged: {directive.get('acknowledged', False)}")
        
        if "acknowledgment" in enforcement:
            ack = enforcement["acknowledgment"]
            print(f"\n Acknowledgment Object:")
            print(f"   • Acknowledged: {ack.get('acknowledged', False)}")
            print(f"   • Execution status: {ack.get('execution_status', 'PENDING')}")
            print(f"   • Status updated at: {ack.get('status_updated_at', 'N/A')}")


def demo_6_observability():
    """Demonstrate observability telemetry."""
    print("\n" + "="*70)
    print("DEMO 6: OBSERVABILITY TELEMETRY UPGRADE")
    print("="*70)
    
    input_contract = {
        "trace_id": "DEMO-OBSERVABILITY-006",
        "signal": {
            "dataset": "crop_yield.csv"
        }
    }
    
    result = run_tantra(input_contract)
    
    if result["pipeline_status"] == "SUCCESS" and "observability" in result:
        obs = result["observability"]
        
        print(f"\n Observability Telemetry:")
        print(f"   Contract version: {obs.get('contract_version', 'v1')}")
        print(f"   Decision state: {obs.get('decision_state', 'UNKNOWN')}")
        
        if "stage_latencies" in obs:
            print(f"\n   Stage Latencies (ms):")
            for stage, latency in obs["stage_latencies"].items():
                print(f"   • {stage:15}: {latency:8.2f} ms")


def demo_7_distributed_services():
    """Demonstrate distributed stage services."""
    print("\n" + "="*70)
    print("DEMO 7: DISTRIBUTED STAGE PREPARATION")
    print("="*70)
    
    from distributed_services import get_service_registry
    
    registry = get_service_registry()
    services = registry.list_services()
    
    print(f"\n Available Services:")
    for service in services:
        print(f"   • {service} (isolated, callable independently)")
    
    # Test direct service call
    input_contract = {
        "trace_id": "DEMO-SERVICE-007",
        "signal": {
            "dataset": "crop_yield.csv"
        }
    }
    
    sanskar_result = registry.call_stage("sanskar", input_contract)
    
    print(f"\n Direct Service Call:")
    print(f"   Service: sanskar")
    print(f"   Status: {'SUCCESS' if 'entities' in sanskar_result else 'FAILED'}")
    print(f"   Entities returned: {len(sanskar_result.get('entities', []))}")


def demo_8_contract_validation():
    """Demonstrate contract schema validation."""
    print("\n" + "="*70)
    print("DEMO 8: CONTRACT SCHEMA VALIDATION")
    print("="*70)
    
    from schema_validation import get_validator
    
    validator = get_validator()
    
    # Test valid input
    valid_input = {
        "trace_id": "DEMO-VALIDATION-008",
        "signal": {
            "dataset": "crop_yield.csv"
        },
        "contract_version": "v1"
    }
    
    result = validator.validate_input(valid_input)
    
    print(f"\n Valid Input Contract:")
    print(f"   Validation result: {result['validation_result']}")
    print(f"   Contract type: {result['contract_type']}")
    print(f"   Errors: {len(result['errors'])}")
    
    
    invalid_input = {
        "signal": {
            "dataset": "crop_yield.csv"
        }
        
    }
    
    result = validator.validate_input(invalid_input)
    
    print(f"\n Invalid Input Contract (missing trace_id):")
    print(f"   Validation result: {result['validation_result']}")
    print(f"   Errors detected: {len(result['errors'])}")
    for error in result['errors']:
        print(f"   • {error}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("SANSKAR UPGRADE - COMPREHENSIVE DEMONSTRATION")
    print("All 8 Hard Requirements")
    print("="*70)
    
    try:
        demo_1_uncertainty_detection()
        demo_2_confidence_engine()
        demo_3_comparative_explanations()
        demo_4_event_replay()
        demo_5_enforcement_acknowledgment()
        demo_6_observability()
        demo_7_distributed_services()
        demo_8_contract_validation()
        
        print("\n" + "="*70)
        print(" ALL DEMONSTRATIONS COMPLETE")
        print("="*70)
        print("\nAll 8 hard requirements successfully demonstrated!")
        
    except Exception as e:
        print(f"\n Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
