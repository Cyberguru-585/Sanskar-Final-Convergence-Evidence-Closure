import console


def run_enforcement(core_output):
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

    directives = [
        {
            "directive_id": f"DIR-001-{entity}",
            "action": "prioritize_irrigation",
            "target": entity,
            "description": f"Allocate priority irrigation resources to {entity} region",
            "status": "pending"
        },
        {
            "directive_id": f"DIR-002-{entity}",
            "action": "allocate_fertilizer",
            "target": entity,
            "description": f"Increase fertilizer supply allocation to {entity} region",
            "status": "pending"
        },
        {
            "directive_id": f"DIR-003-{entity}",
            "action": "deploy_monitoring",
            "target": entity,
            "description": f"Deploy enhanced crop monitoring sensors in {entity} region",
            "status": "pending"
        }
    ]

    enf_output = {
        "trace_id": trace_id,
        "stage": "enforcement",
        "action": "prioritize_irrigation",
        "target": entity,
        "enforcement_type": enforcement_type,
        "priority": priority,
        "urgency": urgency,
        "enforcement_score": score,
        "directives": directives,
        "enforcement_rationale": (
            f"Based on core decision: {entity} selected with priority '{priority}'. "
            f"Enforcement type: {enforcement_type}. "
            f"Three directives issued covering irrigation, fertilizer, and monitoring."
        ),
        "core_reasoning_reference": reasoning,
        "contract_version": "v1"
    }

    console.enforcement_display(enf_output)

    return enf_output