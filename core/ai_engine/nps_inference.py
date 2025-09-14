# -*- coding: utf-8 -*-
"""
NPS Inference Engine - Calculate missing NPS scores from emotion analysis
Executes ONLY post-AI as requested - not part of AI pipeline
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class NPSInferenceEngine:
    """Infers missing NPS scores from emotion analysis results"""

    def __init__(self):
        # Emotion weights for NPS calculation (based on sentiment research)
        self.emotion_weights = {
            # Highly positive emotions (strong promoter indicators)
            'entusiasmo': 2.8,      # Strongest positive indicator
            'gratitud': 2.5,        # Strong loyalty signal
            'alegria': 2.2,         # Clear positive sentiment
            'esperanza': 2.0,       # Future positive outlook
            'aprecio': 1.8,         # Recognition/value
            'confianza': 1.6,       # Trust signal
            'expectativa': 1.3,     # Anticipation

            # Highly negative emotions (strong detractor indicators)
            'enojo': -3.0,          # Strongest negative indicator
            'frustracion': -2.7,    # High dissatisfaction
            'decepcion': -2.4,      # Unmet expectations
            'desagrado': -2.1,      # Clear negative reaction
            'verguenza': -1.8,      # Negative self-perception
            'tristeza': -1.5,       # Emotional distress
            'miedo': -1.2,          # Uncertainty/anxiety

            # Neutral emotions
            'sorpresa': 0.2,        # Can be positive or negative
            'indiferencia': -0.3,   # Slightly negative for NPS context
        }

        # Confidence thresholds
        self.high_confidence_threshold = 0.75
        self.medium_confidence_threshold = 0.50

    def infer_missing_nps(self,
                         df_results: List[Dict[str, Any]],
                         original_nps: List[Optional[float]]) -> List[Optional[float]]:
        """
        Infer missing NPS scores from emotion analysis
        ONLY runs post-AI analysis as requested
        """
        if len(df_results) != len(original_nps):
            logger.error(f"Data mismatch: {len(df_results)} AI results vs {len(original_nps)} NPS values")
            return original_nps

        inferred_nps = []
        inference_count = 0
        confidence_scores = []

        for i, (ai_result, original_nps_val) in enumerate(zip(df_results, original_nps)):
            # Use original NPS if valid
            if original_nps_val is not None and not np.isnan(original_nps_val):
                if 0 <= original_nps_val <= 10:
                    inferred_nps.append(original_nps_val)
                    continue

            # Infer from emotions (post-AI only)
            inferred_score, confidence = self._calculate_nps_from_emotions(ai_result)
            inferred_nps.append(inferred_score)
            confidence_scores.append(confidence)
            inference_count += 1

            logger.debug(f"Row {i+1}: Inferred NPS {inferred_score:.1f} (confidence: {confidence:.2f})")

        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0

        logger.info(f"NPS Inference completed:")
        logger.info(f"  - Original valid: {len(original_nps) - inference_count}")
        logger.info(f"  - Newly inferred: {inference_count}")
        logger.info(f"  - Average confidence: {avg_confidence:.2f}")
        logger.info(f"  - High confidence inferences: {sum(1 for c in confidence_scores if c > self.high_confidence_threshold)}")

        return inferred_nps

    def _calculate_nps_from_emotions(self, ai_result: Dict[str, Any]) -> tuple[float, float]:
        """
        Calculate NPS score from emotion analysis
        Returns: (nps_score, confidence_level)
        """
        emotions = ai_result.get('emotions', {})
        if not emotions:
            return 5.0, 0.1  # Neutral fallback with low confidence

        # Calculate weighted emotion score
        weighted_score = 0.0
        total_weight = 0.0
        valid_emotions = 0

        for emotion, intensity in emotions.items():
            if emotion in self.emotion_weights and isinstance(intensity, (int, float)):
                weight = self.emotion_weights[emotion]
                weighted_score += intensity * weight
                total_weight += abs(weight)
                valid_emotions += 1

        if total_weight == 0 or valid_emotions < 5:
            return 5.0, 0.2  # Neutral with low confidence

        # Normalize weighted score to [-1, 1] range
        emotion_score = weighted_score / total_weight

        # Sentiment alignment boost/penalty
        sentiment = ai_result.get('sentiment', 'neutral')
        sentiment_factor = {
            'positive': 0.4,    # Boost positive sentiment
            'negative': -0.4,   # Penalize negative sentiment
            'neutral': 0.0      # No change
        }.get(sentiment, 0.0)

        # Churn risk penalty (inverse relationship with NPS)
        churn_risk = ai_result.get('churn_risk', 0.5)
        if isinstance(churn_risk, (int, float)):
            churn_penalty = -(churn_risk - 0.5) * 0.6  # Higher churn = lower NPS
        else:
            churn_penalty = 0.0

        # Combine all factors
        combined_score = emotion_score + sentiment_factor + churn_penalty

        # Convert to NPS scale (0-10)
        # Mapping: -1.5 = 0 (strong detractor), 0 = 5 (neutral), 1.5 = 10 (strong promoter)
        nps_score = 5 + (combined_score * 3.33)  # Scale factor for 0-10 range

        # Clamp to valid range
        nps_score = max(0.0, min(10.0, nps_score))

        # Calculate confidence based on emotion clarity
        confidence = self._calculate_inference_confidence(emotions, sentiment, churn_risk)

        return round(nps_score, 1), confidence

    def _calculate_inference_confidence(self,
                                      emotions: Dict[str, Any],
                                      sentiment: str,
                                      churn_risk: float) -> float:
        """Calculate confidence level of NPS inference"""

        # Base confidence from emotion variance (clear emotions = high confidence)
        emotion_values = [v for v in emotions.values() if isinstance(v, (int, float))]
        if not emotion_values:
            return 0.1  # Very low confidence

        # High variance = mixed emotions = low confidence
        emotion_std = np.std(emotion_values)
        max_emotion = max(emotion_values)

        # Strong clear emotions = high confidence
        clarity_score = max_emotion - emotion_std

        # Sentiment consistency boost
        sentiment_boost = 0.2 if sentiment != 'neutral' else 0.0

        # Churn risk consistency (extreme values indicate clarity)
        churn_clarity = abs(churn_risk - 0.5) * 0.4  # Distance from neutral

        # Combine confidence factors
        confidence = min(0.95, max(0.1,
            clarity_score * 0.6 + sentiment_boost + churn_clarity
        ))

        return confidence

    def get_inference_statistics(self,
                               original_nps: List[Optional[float]],
                               inferred_nps: List[Optional[float]]) -> Dict[str, Any]:
        """Get detailed statistics about NPS inference process"""

        original_valid = sum(1 for nps in original_nps
                           if nps is not None and not np.isnan(nps))
        total_count = len(original_nps)
        inferred_count = total_count - original_valid

        inferred_valid = sum(1 for nps in inferred_nps
                           if nps is not None and not np.isnan(nps))

        return {
            'total_rows': total_count,
            'original_valid_nps': original_valid,
            'values_requiring_inference': inferred_count,
            'final_valid_nps': inferred_valid,
            'coverage_improvement': {
                'before_percent': (original_valid / total_count * 100) if total_count > 0 else 0,
                'after_percent': (inferred_valid / total_count * 100) if total_count > 0 else 0,
                'improvement_points': ((inferred_valid - original_valid) / total_count * 100) if total_count > 0 else 0
            },
            'inference_method': 'emotion_weighted_calculation',
            'algorithm_version': '2.0'
        }

    def validate_inference_quality(self,
                                 inferred_nps: List[Optional[float]],
                                 confidence_scores: List[float]) -> Dict[str, Any]:
        """Validate the quality of NPS inference"""

        if not confidence_scores:
            return {'validation': 'NO_INFERENCES', 'quality_score': 0.0}

        # Distribution analysis
        high_confidence = sum(1 for c in confidence_scores if c > self.high_confidence_threshold)
        medium_confidence = sum(1 for c in confidence_scores if self.medium_confidence_threshold <= c <= self.high_confidence_threshold)
        low_confidence = len(confidence_scores) - high_confidence - medium_confidence

        avg_confidence = np.mean(confidence_scores)

        # NPS distribution reasonableness
        valid_nps = [nps for nps in inferred_nps if nps is not None and not np.isnan(nps)]
        nps_std = np.std(valid_nps) if len(valid_nps) > 1 else 0

        # Quality assessment
        if avg_confidence > 0.7 and high_confidence / len(confidence_scores) > 0.6:
            quality = "EXCELLENT"
        elif avg_confidence > 0.5 and (high_confidence + medium_confidence) / len(confidence_scores) > 0.7:
            quality = "GOOD"
        else:
            quality = "ACCEPTABLE"

        return {
            'validation': 'COMPLETED',
            'quality_score': avg_confidence,
            'quality_rating': quality,
            'confidence_distribution': {
                'high_confidence': high_confidence,
                'medium_confidence': medium_confidence,
                'low_confidence': low_confidence
            },
            'nps_distribution_std': nps_std,
            'recommendations': self._get_quality_recommendations(avg_confidence, quality)
        }

    def _get_quality_recommendations(self, avg_confidence: float, quality: str) -> List[str]:
        """Get recommendations for improving inference quality"""
        recommendations = []

        if avg_confidence < 0.5:
            recommendations.append("Consider improving emotion analysis prompt for clearer emotional signals")

        if quality == "ACCEPTABLE":
            recommendations.append("Review emotion weights - may need calibration for your domain")

        recommendations.append(f"Current inference quality: {quality} (avg confidence: {avg_confidence:.2f})")

        return recommendations

# Global instance
nps_inference_engine = NPSInferenceEngine()

# Convenience function
def infer_missing_nps_scores(ai_results: List[Dict[str, Any]],
                           original_nps: List[Optional[float]]) -> tuple[List[Optional[float]], Dict[str, Any]]:
    """
    Convenience function for NPS inference with statistics
    Returns: (inferred_nps_list, inference_statistics)
    """
    inferred_nps = nps_inference_engine.infer_missing_nps(ai_results, original_nps)
    stats = nps_inference_engine.get_inference_statistics(original_nps, inferred_nps)

    return inferred_nps, stats