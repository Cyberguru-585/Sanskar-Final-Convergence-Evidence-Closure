import console


def run_core(sanskar_output):
    trace_id = sanskar_output["trace_id"]

    if "failure" in sanskar_output:
        return {
            "trace_id": trace_id,
            "stage": "core",
            "failure": {
                "stage": "core",
                "code": "UPSTREAM_FAILURE",
                "message": f"Core cannot proceed: upstream failure from {sanskar_output['failure'].get('stage', 'unknown')}",
                "upstream_failure": sanskar_output["failure"],
                "trace_preserved": True
            },
            "contract_version": "v1"
        }

    console.step(6, "CORE DECISION GENERATED")
    console.trace(trace_id)

    entities = sanskar_output["entities"]
    ranking = sanskar_output["ranking"]
    downstream = sanskar_output.get("downstream_decision", {})

    all_candidates = [
        {
            "entity_id": e["entity_id"],
            "score": e["score"],
            "confidence": e["confidence"]
        }
        for e in entities
    ]

    selected_entity = ranking[0]
    selected_score = next(e["score"] for e in entities if e["entity_id"] == selected_entity)
    selected_confidence = next(e["confidence"] for e in entities if e["entity_id"] == selected_entity)

    if selected_score >= 0.8:
        priority = "critical"
        priority_reason = "Score >= 0.8: critical priority — immediate action required"
    elif selected_score >= 0.6:
        priority = "high"
        priority_reason = "Score >= 0.6: high priority — action recommended within current cycle"
    elif selected_score >= 0.4:
        priority = "medium"
        priority_reason = "Score >= 0.4: medium priority — schedule for next cycle"
    else:
        priority = "low"
        priority_reason = "Score < 0.4: low priority — monitor only"

    runner_up = ranking[1] if len(ranking) > 1 else None
    runner_up_score = next((e["score"] for e in entities if e["entity_id"] == runner_up), None)
    margin = round(selected_score - runner_up_score, 4) if runner_up_score else None

    reasoning = (
        f"Selection rule: 'highest_ranked_region_selected'. "
        f"{selected_entity} is the top-ranked entity with score {selected_score}. "
    )
    if runner_up and margin is not None:
        reasoning += (
            f"Runner-up is {runner_up} with score {runner_up_score} "
            f"(margin: {margin}). "
        )
    reasoning += f"Assigned priority: {priority}."

    core_output = {
        "trace_id": trace_id,
        "stage": "core",
        "decision": f"prioritize region {selected_entity}",
        "selected_entity": selected_entity,
        "selected_score": selected_score,
        "selected_confidence": selected_confidence,
        "priority": priority,
        "priority_reason": priority_reason,
        "selection_criteria": "highest_ranked_region_selected",
        "logic": "highest_ranked_region_selected",
        "all_candidates": all_candidates,
        "margin_over_runner_up": margin,
        "runner_up": runner_up,
        "reasoning": reasoning,
        "downstream_recommendation": downstream,
        "contract_version": "v1"
    }

    console.decision_display(core_output)

    return core_output