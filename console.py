import json


WIDTH = 70


def banner(title):
    print("\n" + "=" * WIDTH)
    print(f"  {title}")
    print("=" * WIDTH)


def step(n, title):
    print(f"\n{'-' * WIDTH}")
    print(f"  STEP {n} -- {title}")
    print(f"{'-' * WIDTH}")


def trace(trace_id):
    print(f"  TRACE_ID: {trace_id}")


def divider():
    print(f"{'-' * WIDTH}")


def section(title):
    print(f"\n  +{'-' * (WIDTH - 4)}+")
    print(f"  |  {title:<{WIDTH - 6}}|")
    print(f"  +{'-' * (WIDTH - 4)}+")


def info(label, value):
    print(f"  {label}: {value}")


def entity_card(entity, index=None):
    prefix = f"  [{index}] " if index is not None else "  "
    print(f"{prefix}{entity['entity_id']}")
    print(f"      Score: {entity['score']}")
    print(f"      Confidence: {entity['confidence']}")
    print(f"      Top Factors:")
    for f in entity["factors"]:
        bar_len = int(f["contribution"] * 100)
        bar = "#" * bar_len + "." * (20 - bar_len)
        print(f"        {f['name']:<20} weight={f['weight']}  raw={f['raw_value']}  contribution={f['contribution']}  [{bar}]")
    print(f"      Explanation: {entity['explanation']}")
    print()


def ranking_board(ranked_entities):
    section("RANKING BOARD")
    print()
    for i, e in enumerate(ranked_entities):
        medal = ""
        if i == 0:
            medal = " <-- HIGHEST"
        elif i == len(ranked_entities) - 1:
            medal = " <-- LOWEST"
        print(f"    {i+1}. {e['entity_id']:<12} -- {e['score']}{medal}")
    print()


def comparison_panel(top, bottom):
    section("COMPARATIVE EXPLANATION")
    print()
    print(f"    BEST:  {top['entity_id']} (score={top['score']})")

    top_factors = {f["name"]: f["contribution"] for f in top["factors"]}
    bottom_factors = {f["name"]: f["contribution"] for f in bottom["factors"]}

    strengths = []
    for name in top_factors:
        diff = top_factors[name] - bottom_factors.get(name, 0)
        if diff > 0:
            strengths.append(f"{name} (+{round(diff, 4)})")

    if strengths:
        print(f"    Strengths: {', '.join(strengths)}")
    else:
        print(f"    Strengths: marginal overall advantage across all factors")

    print()
    print(f"    WORST: {bottom['entity_id']} (score={bottom['score']})")

    weaknesses = []
    for name in bottom_factors:
        diff = top_factors.get(name, 0) - bottom_factors[name]
        if diff > 0:
            weaknesses.append(f"{name} (-{round(diff, 4)})")

    if weaknesses:
        print(f"    Weaknesses: {', '.join(weaknesses)}")

    print()
    print(f"    WHY: {top['entity_id']} ranks highest due to", end=" ")
    if strengths:
        factor_names = [s.split(" ")[0] for s in strengths]
        print(f"{' and '.join(factor_names)} strength.")
    else:
        print("marginal overall advantage.")

    print(f"    WHY: {bottom['entity_id']} ranks lowest due to", end=" ")
    if weaknesses:
        factor_names = [s.split(" ")[0] for s in weaknesses]
        print(f"weaker {' and '.join(factor_names)} performance.")
    else:
        print("marginally lower scores across all factors.")
    print()


def scenario_display(scenario_name, description, before_ranking, after_ranking):
    print(f"\n    Scenario: {scenario_name}")
    print(f"    Description: {description}")
    print()
    print(f"    {'BEFORE':<30} {'AFTER':<30}")
    print(f"    {'-' * 28}   {'-' * 28}")
    max_len = max(len(before_ranking), len(after_ranking))
    for i in range(max_len):
        before = f"{i+1}. {before_ranking[i]}" if i < len(before_ranking) else ""
        after = f"{i+1}. {after_ranking[i]}" if i < len(after_ranking) else ""

        changed = ""
        if i < len(before_ranking) and i < len(after_ranking) and before_ranking[i] != after_ranking[i]:
            changed = " <-- CHANGED"

        print(f"    {before:<30} {after:<30}{changed}")
    print()


def truth_record(data):
    section("FINAL TRUTH RECORD")
    print()
    formatted = json.dumps(data, indent=2, default=str)
    for line in formatted.split("\n"):
        print(f"    {line}")
    print()


def failure_display(error_data):
    section("FAILURE -- STRUCTURED ERROR")
    print()
    print(f"    Stage:           {error_data.get('stage', 'unknown')}")
    print(f"    Code:            {error_data.get('code', 'unknown')}")
    print(f"    Message:         {error_data.get('message', 'unknown')}")
    print(f"    Trace Preserved: {error_data.get('trace_preserved', False)}")
    print()


def decision_display(core_output):
    section("CORE DECISION LOGIC")
    print()
    print(f"    Selection Rule:      {core_output['selection_criteria']}")
    print(f"    Selected Entity:     {core_output['selected_entity']}")
    print(f"    Selected Score:      {core_output['selected_score']}")
    print(f"    Selected Confidence: {core_output['selected_confidence']}")
    print(f"    Priority:            {core_output['priority']}")
    print(f"    Priority Reason:     {core_output['priority_reason']}")
    if core_output.get('runner_up'):
        print(f"    Runner-up:           {core_output['runner_up']}")
        print(f"    Margin:              {core_output['margin_over_runner_up']}")
    print()
    print(f"    All Candidates:")
    for c in core_output.get("all_candidates", []):
        marker = " <-- SELECTED" if c["entity_id"] == core_output["selected_entity"] else ""
        print(f"      {c['entity_id']:<12} score={c['score']}  confidence={c['confidence']}{marker}")
    print()
    print(f"    Reasoning: {core_output['reasoning']}")
    print()


def enforcement_display(enf_output):
    section("ENFORCEMENT ACTION")
    print()
    print(f"    Action:           {enf_output['action']}")
    print(f"    Target:           {enf_output['target']}")
    print(f"    Enforcement Type: {enf_output['enforcement_type']}")
    print(f"    Priority:         {enf_output['priority']}")
    print(f"    Urgency:          {enf_output['urgency']}")
    print()
    print(f"    Directives:")
    for d in enf_output.get("directives", []):
        print(f"      [{d['directive_id']}] {d['action']} -> {d['target']} (status: {d['status']})")
    print()
    print(f"    Rationale: {enf_output['enforcement_rationale']}")
    print()
