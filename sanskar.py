import pandas as pd
import console


def load_data(dataset):
    return pd.read_csv(dataset)


def normalize_data(df):
    df = df.copy()
    df.ffill(inplace=True)
    return df


def create_features(df):
    df = df.copy()
    df["rainfall_score"] = df["Rainfall_mm"].apply(lambda x: min(x / 800, 1))
    df["temp_score"] = df["Temperature_Celsius"].apply(lambda x: 1 - abs(x - 25)/25)
    df["irrigation_score"] = df["Irrigation_Used"].apply(lambda x: 1 if x else 0.5)
    df["fertilizer_score"] = df["Fertilizer_Used"].apply(lambda x: 1 if x else 0.6)
    df["yield_efficiency"] = df["Yield_tons_per_hectare"] / df["Days_to_Harvest"]
    return df


def compute_scores(df):
    df = df.copy()
    df["score"] = (
        0.25 * df["rainfall_score"] +
        0.20 * df["temp_score"] +
        0.20 * df["irrigation_score"] +
        0.15 * df["fertilizer_score"] +
        0.20 * df["yield_efficiency"]
    )
    return df


def aggregate_entities(df):
    return df.groupby("Region").mean(numeric_only=True).reset_index()


def build_entity_output(row):
    score = round(row["score"], 3)
    return {
        "entity_id": row["Region"],
        "score": score,
        "factors": [
            {
                "name": "rainfall",
                "weight": 0.25,
                "raw_value": round(row["rainfall_score"], 4),
                "contribution": round(0.25 * row["rainfall_score"], 3)
            },
            {
                "name": "temperature",
                "weight": 0.20,
                "raw_value": round(row["temp_score"], 4),
                "contribution": round(0.20 * row["temp_score"], 3)
            },
            {
                "name": "irrigation",
                "weight": 0.20,
                "raw_value": round(row["irrigation_score"], 4),
                "contribution": round(0.20 * row["irrigation_score"], 3)
            },
            {
                "name": "fertilizer",
                "weight": 0.15,
                "raw_value": round(row["fertilizer_score"], 4),
                "contribution": round(0.15 * row["fertilizer_score"], 3)
            },
            {
                "name": "yield_efficiency",
                "weight": 0.20,
                "raw_value": round(row["yield_efficiency"], 4),
                "contribution": round(0.20 * row["yield_efficiency"], 3)
            }
        ],
        "confidence": round(min(1.0, score + 0.1), 3),
        "explanation": (
            f"{row['Region']} achieved score {score} due to balanced rainfall, "
            f"temperature, irrigation and yield efficiency"
        )
    }


def rank_entities(entities):
    ranked = sorted(entities, key=lambda x: x["score"], reverse=True)
    ranking = [e["entity_id"] for e in ranked]
    return ranked, ranking


def comparative_explanation(entities):
    top = entities[0]
    second = entities[1]

    top_factors = {f["name"]: f["contribution"] for f in top["factors"]}
    second_factors = {f["name"]: f["contribution"] for f in second["factors"]}

    advantages = []
    for name in top_factors:
        diff = top_factors[name] - second_factors[name]
        if diff > 0:
            advantages.append(f"{name} (+{round(diff, 4)})")

    if not advantages:
        advantages = ["marginal overall advantage"]

    return (
        f"{top['entity_id']} (score={top['score']}) ranks higher than "
        f"{second['entity_id']} (score={second['score']}) due to advantages in: "
        f"{', '.join(advantages)}. "
        f"Score difference: {round(top['score'] - second['score'], 4)}"
    )


def simulate_scenarios(df, original_ranking):
    scenarios = []

    console.section("SCENARIO SIMULATION")

    df1 = df.copy()
    df1["Rainfall_mm"] *= 1.1
    df1 = create_features(df1)
    df1 = compute_scores(df1)
    df1 = aggregate_entities(df1)
    entities1 = [build_entity_output(r) for _, r in df1.iterrows()]
    ranked1, ranking1 = rank_entities(entities1)
    scenarios.append({
        "scenario": "increase_rainfall_10%",
        "description": "Simulate 10% increase in rainfall across all regions",
        "original_ranking": original_ranking,
        "updated_ranking": ranking1,
        "impact": "Tests sensitivity of rankings to rainfall changes"
    })
    console.scenario_display(
        "Scenario A: +10% Rainfall",
        "Simulate 10% increase in rainfall across all regions",
        original_ranking, ranking1
    )

    df2 = df.copy()
    df2["Temperature_Celsius"] -= 2
    df2 = create_features(df2)
    df2 = compute_scores(df2)
    df2 = aggregate_entities(df2)
    entities2 = [build_entity_output(r) for _, r in df2.iterrows()]
    ranked2, ranking2 = rank_entities(entities2)
    scenarios.append({
        "scenario": "decrease_temperature_2C",
        "description": "Simulate 2C decrease in temperature across all regions",
        "original_ranking": original_ranking,
        "updated_ranking": ranking2,
        "impact": "Tests sensitivity of rankings to temperature changes"
    })
    console.scenario_display(
        "Scenario B: -2°C Temperature",
        "Simulate 2C decrease in temperature across all regions",
        original_ranking, ranking2
    )

    return scenarios


def build_downstream_decision(ranked_entities, ranking):
    top = ranked_entities[0]
    bottom = ranked_entities[-1]
    return {
        "recommended_action": "prioritize_resource_allocation",
        "primary_target": top["entity_id"],
        "primary_target_score": top["score"],
        "deprioritized_target": bottom["entity_id"],
        "deprioritized_target_score": bottom["score"],
        "score_spread": round(top["score"] - bottom["score"], 4),
        "rationale": (
            f"Region {top['entity_id']} has the highest composite score ({top['score']}) "
            f"and should receive priority resource allocation. "
            f"Region {bottom['entity_id']} has the lowest score ({bottom['score']}) "
            f"and may need intervention to improve yield efficiency."
        ),
        "confidence_level": top["confidence"]
    }


def run_sanskar(input_contract):
    trace_id = input_contract["trace_id"]

    if "signal" not in input_contract:
        return {
            "trace_id": trace_id,
            "stage": "sanskar",
            "failure": {
                "stage": "sanskar",
                "code": "INVALID_SIGNAL",
                "message": "Signal missing in input contract",
                "trace_preserved": True
            },
            "contract_version": "v1"
        }

    if "dataset" not in input_contract["signal"]:
        return {
            "trace_id": trace_id,
            "stage": "sanskar",
            "failure": {
                "stage": "sanskar",
                "code": "MISSING_DATASET",
                "message": "Signal present but dataset path missing",
                "trace_preserved": True
            },
            "contract_version": "v1"
        }

    dataset = input_contract["signal"]["dataset"]

    console.step(1, "INPUT RECEIVED")
    console.trace(trace_id)
    console.info("Dataset", dataset)

    df = load_data(dataset)
    console.step(2, "DATA NORMALIZED")
    console.trace(trace_id)
    df = normalize_data(df)
    console.info("Rows", len(df))
    console.info("Columns", list(df.columns.tolist()))

    console.step(3, "FEATURES GENERATED")
    console.trace(trace_id)
    df = create_features(df)
    console.info("Features", "rainfall_score, temp_score, irrigation_score, fertilizer_score, yield_efficiency")

    console.step(4, "SCORES COMPUTED")
    console.trace(trace_id)
    df = compute_scores(df)
    df = aggregate_entities(df)

    entities = [build_entity_output(r) for _, r in df.iterrows()]
    ranked, ranking = rank_entities(entities)

    console.section("ALL ENTITY OUTPUTS")
    print()
    for i, e in enumerate(ranked):
        console.entity_card(e, i + 1)

    console.step(5, "RANKING GENERATED")
    console.trace(trace_id)
    console.ranking_board(ranked)
    console.comparison_panel(ranked[0], ranked[-1])

    scenarios = simulate_scenarios(df, ranking)

    downstream = build_downstream_decision(ranked, ranking)

    return {
        "trace_id": trace_id,
        "stage": "sanskar",
        "entities": ranked,
        "ranking": ranking,
        "comparative_explanation": comparative_explanation(ranked),
        "scenario_analysis": scenarios,
        "downstream_decision": downstream,
        "contract_version": "v1"
    }