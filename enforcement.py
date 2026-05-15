import console
from datetime import datetime
from async_orchestration import AsyncOrchestrator, ExecutionState


def run_enforcement(core_output, async_simulation=False, enable_uncertainty_propagation=True):
    
    trace_id = core_output["trace_id"]

    if "failure" in core_output:
        return {
            "trace_id": trace_id,
            "stage": "enforcement",
            "failure": {
                "stage": "enforcement",
                "code": "UPSTREAM_FAILURE",
                "message": f"Enforcement cannot proceed: upstream failure from {core_output['failure'].get('stage', 'unknown')}",
                "upstream_failure": core_output["failure"],
                "trace_preserved": True
            },
            "contract_version": "v1"
        }

    console.step(7, "ENFORCEMENT ACTION GENERATED")
    console.trace(trace_id)

    entity = core_output["selected_entity"]
    priority = core_output.get("priority", "medium")
    score = core_output.get("selected_score", 0)
    decision_state = core_output.get("selected_decision_state", "CONFIDENT")
    reasoning = core_output.get("reasoning", "")

    if priority == "critical":
        enforcement_type = "immediate_resource_reallocation"
        urgency = "immediate"
    elif priority == "high":
        enforcement_type = "resource_allocation"
        urgency = "current_cycle"
    elif priority == "medium":
        enforcement_type = "scheduled_allocation"
        urgency = "next_cycle"
    else:
        enforcement_type = "monitoring_only"
        urgency = "passive"

    
    governance_warning = None
    if enable_uncertainty_propagation:
        if decision_state == "AMBIGUOUS":
            governance_warning = "low_confidence_execution_risk"
        elif decision_state == "LOW_CONFIDENCE":
            governance_warning = "moderate_confidence_execution_risk"
    
    ack_timestamp = datetime.utcnow().isoformat() + "Z"

    directives = [
        {
            "directive_id": f"DIR-001-{entity}",
            "action": "prioritize_irrigation",
            "target": entity,
            "description": f"Allocate priority irrigation resources to {entity} region",
            "status": "pending",
            "acknowledged": False,
            "ack_timestamp": None,
            "execution_status": "PENDING"
        },
        {
            "directive_id": f"DIR-002-{entity}",
            "action": "allocate_fertilizer",
            "target": entity,
            "description": f"Increase fertilizer supply allocation to {entity} region",
            "status": "pending",
            "acknowledged": False,
            "ack_timestamp": None,
            "execution_status": "PENDING"
        },
        {
            "directive_id": f"DIR-003-{entity}",
            "action": "deploy_monitoring",
            "target": entity,
            "description": f"Deploy enhanced crop monitoring sensors in {entity} region",
            "status": "pending",
            "acknowledged": False,
            "ack_timestamp": None,
            "execution_status": "PENDING"
        }
    ]
    
    
    async_contexts = None
    if async_simulation:
        orchestrator = AsyncOrchestrator()
        async_contexts = []
        
        for directive in directives:
            
            exec_context = orchestrator.queue_async_directive(
                directive, 
                trace_id, 
                stage="enforcement",
                delay_ms=100
            )
            async_contexts.append(exec_context)
    
    
    execution_verification_context = {
        "executor_id": "EXECUTOR-001",
        "execution_completed": False,
        "completion_hash": None,
        "verified_by": None,
        "separation_of_concerns": {
            "issuance": {
                "issued_by": "enforcement",
                "issuance_timestamp": ack_timestamp,
                "directives_issued": len(directives)
            },
            "verification": {
                "verified_by": "external_executor",
                "verification_timestamp": None,
                "result_hash": None
            }
        }
    }

    enf_output = {
        "trace_id": trace_id,
        "stage": "enforcement",
        "action": "prioritize_irrigation",
        "target": entity,
        "enforcement_type": enforcement_type,
        "priority": priority,
        "decision_state": decision_state,
        "urgency": urgency,
        "enforcement_score": score,
        "directives": directives,
        "enforcement_rationale": (
            f"Based on core decision: {entity} selected with priority '{priority}' "
            f"(decision_state: {decision_state}). "
            f"Enforcement type: {enforcement_type}. "
            f"Three directives issued covering irrigation, fertilizer, and monitoring."
        ),
        "core_reasoning_reference": reasoning,
        "acknowledgment": {
            "acknowledged": False,
            "ack_timestamp": None,
            "execution_status": "PENDING",
            "status_updated_at": ack_timestamp
        },
        
        "async_execution": {
            "enabled": async_simulation,
            "execution_contexts": async_contexts
        } if async_simulation else None,
        
        "external_execution_verification": execution_verification_context,
        
        "governance": {
            "decision_state": decision_state,
            "governance_warning": governance_warning,
            "uncertainty_propagated": enable_uncertainty_propagation
        },
        "contract_version": "v1"
    }

    console.enforcement_display(enf_output)

    return enf_output
