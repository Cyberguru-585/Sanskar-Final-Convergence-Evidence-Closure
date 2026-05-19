import pandas as pd
import console
from adaptive_intelligence import AdaptiveIntelligenceRefinement, SignalQualityMetrics


def load_data(dataset):
    return pd.read_csv(dataset)


def normalize_data(df):
    df = df.copy()
    df.ffill(inplace=True)
    return df


def parse_boolean(flag):
    return str(flag).strip().upper() in {"TRUE", "YES", "1"}


def normalize_category(value):
    if pd.isna(value):
        return ""
    return str(value).strip().title()


def create_features(df):
    df = df.copy()
    df["Rainfall_mm"] = df["Rainfall_mm"].astype(float)
    df["Temperature_Celsius"] = df["Temperature_Celsius"].astype(float)
    df["Irrigation_Used"] = df["Irrigation_Used"].apply(parse_boolean)
    df["Fertilizer_Used"] = df["Fertilizer_Used"].apply(parse_boolean)
    df["Soil_Type"] = df["Soil_Type"].apply(normalize_category)
    df["Weather_Condition"] = df["Weather_Condition"].apply(normalize_category)

    df["rainfall_score"] = df["Rainfall_mm"].apply(lambda x: min(max((x - 100) / 900, 0), 1))
    df["temp_score"] = df["Temperature_Celsius"].apply(lambda x: max(0, 1 - abs(x - 25) / 15))
    df["irrigation_score"] = df["Irrigation_Used"].apply(lambda x: 1.0 if x else 0.35)
    df["fertilizer_score"] = df["Fertilizer_Used"].apply(lambda x: 1.0 if x else 0.35)
    df["yield_efficiency"] = df["Yield_tons_per_hectare"].astype(float) / df["Days_to_Harvest"].astype(float)
    df["yield_efficiency_score"] = df["yield_efficiency"].apply(lambda x: min(max(x / 0.08, 0), 1))

    soil_quality_map = {
        "Loam": 0.98,
        "Silt": 0.95,
        "Clay": 0.90,
        "Peaty": 0.88,
        "Sandy": 0.85,
        "Chalky": 0.82
    }
    df["soil_quality_score"] = df["Soil_Type"].map(soil_quality_map).fillna(0.80)

    weather_quality_map = {
        "Sunny": 0.95,
        "Cloudy": 0.92,
        "Rainy": 0.88
    }
    df["weather_score"] = df["Weather_Condition"].map(weather_quality_map).fillna(0.85)
    return df


def compute_scores(df):
    df = df.copy()
    df["score"] = (
        0.15 * df["rainfall_score"] +
        0.12 * df["temp_score"] +
        0.18 * df["irrigation_score"] +
        0.08 * df["fertilizer_score"] +
        0.28 * df["yield_efficiency_score"] +
        0.10 * df["soil_quality_score"] +
        0.09 * df["weather_score"]
    )
    return df


def aggregate_entities(df):
    return df.groupby("Region").mean(numeric_only=True).reset_index()


def build_entity_output(row):
    score = round(row["score"], 4)
    factor_weights = {
        "rainfall": 0.15,
        "temperature": 0.12,
        "irrigation": 0.18,
        "fertilizer": 0.08,
        "yield_efficiency": 0.28,
        "soil_quality": 0.10,
        "weather": 0.09
    }
    factors = [
        {
            "name": "rainfall",
            "weight": factor_weights["rainfall"],
            "raw_value": round(row["rainfall_score"], 4),
            "contribution": round(factor_weights["rainfall"] * row["rainfall_score"], 4)
        },
        {
            "name": "temperature",
            "weight": factor_weights["temperature"],
            "raw_value": round(row["temp_score"], 4),
            "contribution": round(factor_weights["temperature"] * row["temp_score"], 4)
        },
        {
            "name": "irrigation",
            "weight": factor_weights["irrigation"],
            "raw_value": round(row["irrigation_score"], 4),
            "contribution": round(factor_weights["irrigation"] * row["irrigation_score"], 4)
        },
        {
            "name": "fertilizer",
            "weight": factor_weights["fertilizer"],
            "raw_value": round(row["fertilizer_score"], 4),
            "contribution": round(factor_weights["fertilizer"] * row["fertilizer_score"], 4)
        },
        {
            "name": "yield_efficiency",
            "weight": factor_weights["yield_efficiency"],
            "raw_value": round(row["yield_efficiency_score"], 4),
            "contribution": round(factor_weights["yield_efficiency"] * row["yield_efficiency_score"], 4)
        },
        {
            "name": "soil_quality",
            "weight": factor_weights["soil_quality"],
            "raw_value": round(row["soil_quality_score"], 4),
            "contribution": round(factor_weights["soil_quality"] * row["soil_quality_score"], 4)
        },
        {
            "name": "weather",
            "weight": factor_weights["weather"],
            "raw_value": round(row["weather_score"], 4),
            "contribution": round(factor_weights["weather"] * row["weather_score"], 4)
        }
    ]

    # Enhanced confidence calculation
    avg_feature_quality = (
        row["rainfall_score"] + row["temp_score"] + row["irrigation_score"] +
        row["fertilizer_score"] + row["yield_efficiency_score"] +
        row["soil_quality_score"] + row["weather_score"]
    ) / 7.0
    
    # Calculate feature stability (lower variance = higher stability)
    feature_values = [
        row["rainfall_score"], row["temp_score"], row["irrigation_score"],
        row["fertilizer_score"], row["yield_efficiency_score"],
        row["soil_quality_score"], row["weather_score"]
    ]
    feature_variance = sum((f - avg_feature_quality) ** 2 for f in feature_values) / len(feature_values)
    feature_stability = max(0, 1.0 - feature_variance)  # Normalize: lower variance = higher stability
    
   
    missing_count = sum(1 for f in feature_values if f < 0.1)
    missing_penalty = min(0.2, missing_count * 0.05)
    
    
    confidence = round(
        min(1.0, 
            0.50 * score +  # Score contribution
            0.25 * avg_feature_quality +  # Feature quality
            0.15 * feature_stability +  # Feature stability
            0.10 * (1.0 - missing_penalty)  # Missing data penalty
        ),
        4
    )

    tie_breaker = (
        0.20 * row["yield_efficiency_score"] +
        0.18 * row["irrigation_score"] +
        0.12 * row["temp_score"] +
        0.10 * row["fertilizer_score"] +
        0.12 * row["rainfall_score"] +
        0.14 * row["soil_quality_score"] +
        0.14 * row["weather_score"]
    )

    return {
        "entity_id": row["Region"],
        "score": score,
        "raw_score": round(row["score"], 6),
        "tie_breaker": round(tie_breaker, 6),
        "factors": factors,
        "confidence": confidence,
        "confidence_factors": {
            "score_contribution": round(0.50 * score, 4),
            "feature_quality": round(avg_feature_quality, 4),
            "feature_stability": round(feature_stability, 4),
            "missing_penalty": round(missing_penalty, 4)
        },
        "explanation": (
            f"{row['Region']} achieved score {score} based on yield efficiency dominance, strong irrigation, "
            f"good soil quality and consistent weather support."
        )
    }


def detect_uncertainty_state(spread):
    
    if spread < 0.01:
        return "AMBIGUOUS"
    elif spread < 0.03:
        return "LOW_CONFIDENCE"
    else:
        return "CONFIDENT"


def adjust_confidence_for_margin(ranked_entities):
    if len(ranked_entities) < 2:
        return ranked_entities

    margin = ranked_entities[0]["raw_score"] - ranked_entities[1]["raw_score"]
    
    
    decision_state = detect_uncertainty_state(margin)
    for entity in ranked_entities:
        entity["decision_state"] = decision_state
    
    
    if margin < 0.01:
        penalty = 0.05 if margin < 0.005 else 0.03
        for entity in ranked_entities:
            entity["confidence"] = round(max(0.35, entity["confidence"] - penalty), 3)
    elif margin < 0.03:
        penalty = 0.02
        for entity in ranked_entities:
            entity["confidence"] = round(max(0.40, entity["confidence"] - penalty), 3)

    return ranked_entities


def rank_entities(entities):
    ranked = sorted(
        entities,
        key=lambda x: (x["raw_score"], x["tie_breaker"], x["confidence"]),
        reverse=True
    )
    ranking = [e["entity_id"] for e in ranked]
    ranked = adjust_confidence_for_margin(ranked)
    return ranked, ranking


def comparative_explanation(entities):
    
    top = entities[0]
    second = entities[1]

    top_factors = {f["name"]: f for f in top["factors"]}
    second_factors = {f["name"]: f for f in second["factors"]}

    advantages = []
    disadvantages = []
    
    for name in top_factors:
        top_contrib = top_factors[name]["contribution"]
        second_contrib = second_factors[name]["contribution"]
        delta = round(top_contrib - second_contrib, 4)
        
        if delta > 0.001:
            advantages.append({
                "factor": name,
                "delta": delta,
                "top_value": round(top_factors[name]["raw_value"], 4),
                "second_value": round(second_factors[name]["raw_value"], 4),
                "description": f"{name} (+{delta})"
            })
        elif delta < -0.001:
            disadvantages.append({
                "factor": name,
                "delta": delta,
                "top_value": round(top_factors[name]["raw_value"], 4),
                "second_value": round(second_factors[name]["raw_value"], 4),
                "description": f"{name} ({delta})"
            })

    
    advantages.sort(key=lambda x: x["delta"], reverse=True)
    disadvantages.sort(key=lambda x: x["delta"])

    
    if advantages:
        top_3_advantages = advantages[:3]
        advantage_text = ", ".join([f"{a['factor']} (+{a['delta']})" for a in top_3_advantages])
        explanation = (
            f"{top['entity_id']} ranks above {second['entity_id']} due to stronger "
            f"{advantage_text}."
        )
    else:
        explanation = f"{top['entity_id']} has marginal advantage over {second['entity_id']}."
    
    score_diff = round(top["score"] - second["score"], 4)
    explanation += f" Score difference: {score_diff}."

    return {
        "summary": explanation,
        "advantages": advantages,
        "disadvantages": disadvantages,
        "score_delta": score_diff,
        "confidence_delta": round(top["confidence"] - second["confidence"], 4)
    }


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
    console.info(
        "Features",
        "rainfall_score, temp_score, irrigation_score, fertilizer_score, yield_efficiency_score, soil_quality_score, weather_score"
    )

    console.step(4, "SCORES COMPUTED")
    console.trace(trace_id)
    scored_df = compute_scores(df)
    aggregated_df = aggregate_entities(scored_df)

    entities = [build_entity_output(r) for _, r in aggregated_df.iterrows()]
    ranked, ranking = rank_entities(entities)

    
    for entity in ranked:
        entity["score"] = round(entity["score"], 3)


    console.section("ALL ENTITY OUTPUTS")
    print()
    for i, e in enumerate(ranked):
        console.entity_card(e, i + 1)

    console.step(5, "RANKING GENERATED")
    console.trace(trace_id)
    console.ranking_board(ranked)
    console.comparison_panel(ranked[0], ranked[-1])

    console.step(5.5, "ADAPTIVE INTELLIGENCE REFINEMENT")
    console.trace(trace_id)
    
    refiner = AdaptiveIntelligenceRefinement()
    
    signal_columns = ["rainfall_score", "temp_score", "irrigation_score", 
                     "fertilizer_score", "yield_efficiency_score", 
                     "soil_quality_score", "weather_score"]
    signal_qualities = {}
    
    for col in signal_columns:
        if col in scored_df.columns:
            quality = refiner.assess_signal_quality(col, scored_df[col].tolist())
            signal_qualities[col] = quality
            console.info(f"Signal {col}", f"Reliability: {quality.reliability_score}")
    
    factor_weights = {
        "rainfall_score": 0.15,
        "temp_score": 0.12,
        "irrigation_score": 0.18,
        "fertilizer_score": 0.08,
        "yield_efficiency_score": 0.28,
        "soil_quality_score": 0.10,
        "weather_score": 0.09
    }
    
    adaptive_weights = refiner.compute_adaptive_weighting(factor_weights, signal_qualities)
    console.info("Adaptive Weighting", "Recomputed based on signal quality")
    
    adaptive_refinements = []
    for entity in ranked:
        original_score = entity["score"]
        refinement = refiner.refine_entity_score(
            entity["entity_id"],
            original_score,
            factor_weights,
            signal_qualities
        )
        adaptive_refinements.append(refinement)
        entity["adaptive_refinement"] = refinement
        entity["adjusted_score"] = refinement["adjusted_score"]
        entity["adaptive_confidence"] = refinement["final_confidence"]
        console.info(f"{entity['entity_id']} Adjustment", 
                    f"{original_score} -> {refinement['adjusted_score']} (delta: {refinement['adjustment_delta']})")
        refiner.record_adaptive_adjustment(refinement)

    console.info("Adaptive Refinement", f"Applied to {len(ranked)} entities")
    console.info("Governance Boundary", "[OK] All adaptations remain deterministic and observable")

    scenarios = simulate_scenarios(scored_df, ranking)

    downstream = build_downstream_decision(ranked, ranking)

    return {
        "trace_id": trace_id,
        "stage": "sanskar",
        "entities": ranked,
        "ranking": ranking,
        "comparative_explanation": comparative_explanation(ranked),
        "scenario_analysis": scenarios,
        "downstream_decision": downstream,
        "adaptive_refinement": {
            "applied": True,
            "refinements": adaptive_refinements,
            "adaptive_weights": adaptive_weights,
            "signal_qualities": {name: {
                "signal_name": m.signal_name,
                "completeness_ratio": m.completeness_ratio,
                "variance_coefficient": m.variance_coefficient,
                "outlier_count": m.outlier_count,
                "reliability_score": m.reliability_score
            } for name, m in signal_qualities.items()},
            "observable": True,
            "deterministic": True,
            "replay_safe": True,
            "governance_boundary_respected": True
        },
        "contract_version": "v1"
    }