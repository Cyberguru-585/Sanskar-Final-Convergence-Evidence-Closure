import json
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class SignalQualityMetrics:
    
    signal_name: str
    completeness_ratio: float
    variance_coefficient: float
    outlier_count: int
    reliability_score: float
    
    def is_low_quality(self) -> bool:
        
        return self.reliability_score < 0.7


@dataclass
class AdaptiveAdjustment:
    
    reason: str
    adjustment_type: str  
    magnitude: float
    feature_name: str
    observable: bool
    timestamp: str
    
    def __post_init__(self):
        if not self.observable:
            raise ValueError("Adaptive adjustments MUST be externally observable")


class AdaptiveIntelligenceRefinement:
   
    
    def __init__(self):
        self.adjustments: List[Dict[str, Any]] = []
        self.quality_assessments: Dict[str, SignalQualityMetrics] = {}
    
    def assess_signal_quality(self, signal_name: str, raw_values: List[float]) -> SignalQualityMetrics:
        
        if not raw_values:
            raise ValueError(f"Cannot assess quality for empty signal {signal_name}")
        
        
        non_null = len([v for v in raw_values if v is not None])
        completeness_ratio = non_null / len(raw_values) if raw_values else 0.0
        
        
        valid_values = [v for v in raw_values if v is not None and isinstance(v, (int, float))]
        if len(valid_values) < 2:
            variance_coefficient = 0.0
        else:
            mean = sum(valid_values) / len(valid_values)
            variance = sum((v - mean) ** 2 for v in valid_values) / len(valid_values)
            std_dev = variance ** 0.5
            variance_coefficient = std_dev / mean if mean != 0 else 0.0
        
        
        outlier_count = 0
        if len(valid_values) >= 3:
            sorted_vals = sorted(valid_values)
            q1 = sorted_vals[len(sorted_vals) // 4]
            q3 = sorted_vals[3 * len(sorted_vals) // 4]
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outlier_count = sum(1 for v in valid_values if v < lower_bound or v > upper_bound)
        
        
        completeness_weight = 0.4
        variance_penalty = max(0, 1 - variance_coefficient / 2) * 0.35
        outlier_penalty = max(0, 1 - (outlier_count / len(valid_values) if valid_values else 0)) * 0.25
        
        reliability_score = (
            completeness_ratio * completeness_weight +
            variance_penalty +
            outlier_penalty
        )
        
        metrics = SignalQualityMetrics(
            signal_name=signal_name,
            completeness_ratio=round(completeness_ratio, 4),
            variance_coefficient=round(variance_coefficient, 4),
            outlier_count=outlier_count,
            reliability_score=round(reliability_score, 4)
        )
        
        self.quality_assessments[signal_name] = metrics
        return metrics
    
    def compute_confidence_penalty(self, quality_metrics: SignalQualityMetrics) -> float:
        
        if quality_metrics.reliability_score >= 0.9:
            penalty = 0.0
        elif quality_metrics.reliability_score >= 0.8:
            penalty = 0.02
        elif quality_metrics.reliability_score >= 0.7:
            penalty = 0.05
        elif quality_metrics.reliability_score >= 0.5:
            penalty = 0.10
        else:
            penalty = 0.20
        
        return round(penalty, 4)
    
    def refine_entity_score(
        self,
        entity_id: str,
        original_score: float,
        factors: Dict[str, float],
        signal_qualities: Dict[str, SignalQualityMetrics]
    ) -> Dict[str, Any]:
        
        adjusted_score = original_score
        applied_adjustments = []
        
        
        feature_confidence_adjustments = {}
        for feature_name, feature_weight in factors.items():
            if feature_name in signal_qualities:
                quality = signal_qualities[feature_name]
                penalty = self.compute_confidence_penalty(quality)
                
                if penalty > 0.0:
                    adjustment = {
                        "feature_name": feature_name,
                        "original_weight": round(feature_weight, 4),
                        "penalty": penalty,
                        "quality_reason": f"Signal reliability: {quality.reliability_score}",
                        "adjusted_weight": round(feature_weight * (1 - penalty), 4)
                    }
                    feature_confidence_adjustments[feature_name] = adjustment
                    applied_adjustments.append(adjustment)
                    
                    
                    adjusted_score -= feature_weight * penalty
        
        adjusted_score = max(0.0, min(1.0, round(adjusted_score, 4)))
        
       
        missing_data_penalty = 0.0
        for signal_name, quality in signal_qualities.items():
            if quality.completeness_ratio < 0.8:
                missing_penalty = (0.8 - quality.completeness_ratio) * 0.15
                missing_data_penalty += missing_penalty
        
        final_confidence = max(0.0, min(1.0, round(1.0 - missing_data_penalty, 4)))
        
        if missing_data_penalty > 0.0:
            applied_adjustments.append({
                "type": "missing_data_normalization",
                "penalty": round(missing_data_penalty, 4),
                "confidence_impact": round(missing_data_penalty, 4)
            })
        
        return {
            "entity_id": entity_id,
            "original_score": original_score,
            "adjusted_score": adjusted_score,
            "adjustment_delta": round(adjusted_score - original_score, 4),
            "final_confidence": final_confidence,
            "applied_adjustments": applied_adjustments,
            "feature_confidence_adjustments": feature_confidence_adjustments,
            "observable": True,
            "deterministic": True,
            "replay_safe": True,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def compute_adaptive_weighting(
        self,
        factors: Dict[str, float],
        signal_qualities: Dict[str, SignalQualityMetrics],
        uncertainty_context: Dict[str, float] = None
    ) -> Dict[str, Any]:
        
        if uncertainty_context is None:
            uncertainty_context = {}
        
        
        quality_multipliers = {}
        original_sum = sum(factors.values())
        
        for feature_name, original_weight in factors.items():
            if feature_name in signal_qualities:
                quality = signal_qualities[feature_name]
                
                multiplier = 0.7 + (quality.reliability_score * 0.3)
                quality_multipliers[feature_name] = round(multiplier, 4)
            else:
                quality_multipliers[feature_name] = 1.0
        
        
        adjusted_factors = {}
        adjustment_sum = sum(
            factors[f] * quality_multipliers[f] for f in factors
        )
        
        for feature_name, original_weight in factors.items():
            if adjustment_sum > 0:
                adjusted_weight = (original_weight * quality_multipliers[feature_name]) / adjustment_sum
            else:
                adjusted_weight = original_weight / len(factors)
            
            adjusted_factors[feature_name] = round(adjusted_weight, 4)
        
        return {
            "original_weights": {k: round(v, 4) for k, v in factors.items()},
            "quality_multipliers": quality_multipliers,
            "adapted_weights": adjusted_factors,
            "weight_sum": round(sum(adjusted_factors.values()), 4),
            "adaptation_reason": "signal-quality-aware feature reweighting",
            "observable": True,
            "deterministic": True,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def record_adaptive_adjustment(self, adjustment: Dict[str, Any]) -> None:
        
        adjustment["recorded_at"] = datetime.utcnow().isoformat() + "Z"
        adjustment["adjustment_id"] = f"ADJ-{len(self.adjustments) + 1}"
        self.adjustments.append(adjustment)
    
    def compute_adjustment_hash(self, adjustment: Dict[str, Any]) -> str:
        
        hashable = {
            "entity_id": adjustment.get("entity_id"),
            "original_score": adjustment.get("original_score"),
            "adjusted_score": adjustment.get("adjusted_score"),
            "applied_adjustments": str(adjustment.get("applied_adjustments", []))
        }
        serialized = json.dumps(hashable, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def get_adjustment_report(self) -> Dict[str, Any]:
        
        return {
            "total_adjustments": len(self.adjustments),
            "adjustments": self.adjustments,
            "quality_assessments": {
                name: asdict(metrics)
                for name, metrics in self.quality_assessments.items()
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "observable": True,
            "deterministic": True,
            "governance_boundary_respected": True
        }
