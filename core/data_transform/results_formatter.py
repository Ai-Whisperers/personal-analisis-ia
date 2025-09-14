# -*- coding: utf-8 -*-
"""
Results Formatter - Transform AI results to chart-ready format
Handles the conversion from AI analysis to standardized DataFrame for charts and export
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ResultsFormatter:
    """Transform AI analysis results to standardized DataFrame format"""

    def __init__(self):
        from config import EMOTIONS_16, EMO_CATEGORIES
        self.emotions = EMOTIONS_16
        self.emotion_categories = EMO_CATEGORIES

    def format_for_charts_and_export(self,
                                   clean_df: pd.DataFrame,
                                   ai_results: List[Dict[str, Any]],
                                   nps_categories: List[str]) -> pd.DataFrame:
        """
        Transform AI results to chart-ready format
        Creates columns that charts expect to find
        """
        if len(ai_results) != len(clean_df):
            raise ValueError(f"Data mismatch: {len(ai_results)} AI results vs {len(clean_df)} DataFrame rows")

        logger.info(f"Formatting {len(ai_results)} analysis results for charts and export")

        # Start with cleaned DataFrame
        results_df = clean_df.copy()

        # Add individual emotion columns (direct access for charts)
        logger.info("Adding individual emotion columns")
        for emotion in self.emotions:
            emotion_values = []
            for result in ai_results:
                emotions = result.get('emotions', {})
                emotion_values.append(emotions.get(emotion, 0.0))
            results_df[emotion] = emotion_values

        # Add emotion category aggregations
        logger.info("Creating emotion category aggregations")
        for category_name, category_emotions in self.emotion_categories.items():
            category_scores = []
            for result in ai_results:
                result_emotions = result.get('emotions', {})
                category_avg = np.mean([result_emotions.get(emo, 0.0) for emo in category_emotions])
                category_scores.append(category_avg)
            results_df[f'emo_category_{category_name}'] = category_scores

        # Add core analysis results
        logger.info("Adding core analysis results")
        results_df['sentiment'] = [r.get('sentiment', 'neutral') for r in ai_results]
        results_df['churn_risk'] = [r.get('churn_risk', 0.5) for r in ai_results]

        # Add NPS categories
        results_df['nps_category'] = nps_categories

        # Process pain points for export
        logger.info("Processing pain points for export")
        results_df['pain_points_list'] = [r.get('pain_points', []) for r in ai_results]
        results_df['pain_points_text'] = [
            ', '.join(r.get('pain_points', [])) if r.get('pain_points') else ''
            for r in ai_results
        ]
        results_df['pain_point_count'] = [len(r.get('pain_points', [])) for r in ai_results]

        # Add derived analytics columns
        logger.info("Creating derived analytics columns")
        results_df['dominant_emotion'] = self._get_dominant_emotions(ai_results)
        results_df['emotion_intensity'] = self._get_emotion_intensity(ai_results)
        results_df['sentiment_confidence'] = self._calculate_sentiment_confidence(ai_results)

        # Add business intelligence columns
        results_df['customer_risk_level'] = self._calculate_customer_risk_level(ai_results, nps_categories)
        results_df['retention_priority'] = self._calculate_retention_priority(ai_results, nps_categories)

        logger.info(f"Results formatting completed:")
        logger.info(f"  - Original columns: {len(clean_df.columns)}")
        logger.info(f"  - Final columns: {len(results_df.columns)}")
        logger.info(f"  - Emotion columns added: {len(self.emotions)}")
        logger.info(f"  - Category columns added: {len(self.emotion_categories)}")

        return results_df

    def _get_dominant_emotions(self, ai_results: List[Dict[str, Any]]) -> List[str]:
        """Identify dominant emotion for each analysis result"""
        dominant_emotions = []

        for result in ai_results:
            emotions = result.get('emotions', {})
            if emotions and isinstance(emotions, dict):
                # Find emotion with highest score
                valid_emotions = {k: v for k, v in emotions.items()
                                if isinstance(v, (int, float)) and k in self.emotions}

                if valid_emotions:
                    dominant_emotion = max(valid_emotions.items(), key=lambda x: x[1])
                    dominant_emotions.append(dominant_emotion[0])
                else:
                    dominant_emotions.append('indiferencia')
            else:
                dominant_emotions.append('indiferencia')

        return dominant_emotions

    def _get_emotion_intensity(self, ai_results: List[Dict[str, Any]]) -> List[float]:
        """Calculate overall emotional intensity for each result"""
        intensities = []

        for result in ai_results:
            emotions = result.get('emotions', {})
            if emotions and isinstance(emotions, dict):
                # Calculate intensity as standard deviation (higher = more intense emotions)
                emotion_values = [v for v in emotions.values()
                                if isinstance(v, (int, float))]

                if len(emotion_values) > 1:
                    intensity = np.std(emotion_values)
                else:
                    intensity = 0.0
            else:
                intensity = 0.0

            intensities.append(intensity)

        return intensities

    def _calculate_sentiment_confidence(self, ai_results: List[Dict[str, Any]]) -> List[float]:
        """Calculate confidence level of sentiment classification"""
        confidences = []

        for result in ai_results:
            emotions = result.get('emotions', {})
            sentiment = result.get('sentiment', 'neutral')

            if not emotions:
                confidences.append(0.1)
                continue

            # Calculate sentiment alignment with emotions
            positive_emotions = [emotions.get(emo, 0) for emo in self.emotion_categories.get('positivas', [])]
            negative_emotions = [emotions.get(emo, 0) for emo in self.emotion_categories.get('negativas', [])]

            positive_avg = np.mean(positive_emotions) if positive_emotions else 0
            negative_avg = np.mean(negative_emotions) if negative_emotions else 0

            # Confidence based on sentiment-emotion alignment
            if sentiment == 'positive':
                confidence = positive_avg + max(0, positive_avg - negative_avg) * 0.5
            elif sentiment == 'negative':
                confidence = negative_avg + max(0, negative_avg - positive_avg) * 0.5
            else:  # neutral
                # Neutral confidence when emotions are balanced
                balance = 1.0 - abs(positive_avg - negative_avg)
                confidence = balance * 0.8

            confidences.append(min(0.95, max(0.05, confidence)))

        return confidences

    def _calculate_customer_risk_level(self, ai_results: List[Dict[str, Any]], nps_categories: List[str]) -> List[str]:
        """Calculate overall customer risk level"""
        risk_levels = []

        for result, nps_category in zip(ai_results, nps_categories):
            churn_risk = result.get('churn_risk', 0.5)
            pain_point_count = len(result.get('pain_points', []))

            # Risk calculation combining multiple factors
            if nps_category == 'detractor' and churn_risk > 0.7:
                risk_level = 'CRITICAL'
            elif nps_category == 'detractor' or churn_risk > 0.6:
                risk_level = 'HIGH'
            elif nps_category == 'passive' and pain_point_count > 2:
                risk_level = 'MEDIUM'
            elif nps_category == 'passive' or churn_risk > 0.4:
                risk_level = 'LOW'
            else:
                risk_level = 'MINIMAL'

            risk_levels.append(risk_level)

        return risk_levels

    def _calculate_retention_priority(self, ai_results: List[Dict[str, Any]], nps_categories: List[str]) -> List[int]:
        """Calculate retention priority score (1-10)"""
        priorities = []

        for result, nps_category in zip(ai_results, nps_categories):
            churn_risk = result.get('churn_risk', 0.5)
            pain_point_count = len(result.get('pain_points', []))

            # Base priority from NPS category
            base_priority = {
                'detractor': 8,
                'passive': 5,
                'promoter': 2,
                'unknown': 6
            }.get(nps_category, 6)

            # Adjust for churn risk
            churn_adjustment = int(churn_risk * 3)  # 0-3 points

            # Adjust for pain points
            pain_adjustment = min(2, pain_point_count)  # Max 2 points

            # Calculate final priority
            final_priority = min(10, max(1, base_priority + churn_adjustment + pain_adjustment))
            priorities.append(final_priority)

        return priorities

    def validate_chart_readiness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate that DataFrame is ready for chart generation"""
        validation_results = {
            'emotion_columns_present': 0,
            'missing_emotion_columns': [],
            'nps_data_available': False,
            'sentiment_data_available': False,
            'chart_compatibility_score': 0.0,
            'issues': []
        }

        # Check emotion columns
        for emotion in self.emotions:
            if emotion in df.columns:
                validation_results['emotion_columns_present'] += 1
            else:
                validation_results['missing_emotion_columns'].append(emotion)

        # Check other required columns
        validation_results['nps_data_available'] = 'nps_category' in df.columns
        validation_results['sentiment_data_available'] = 'sentiment' in df.columns

        # Calculate compatibility score
        emotion_score = validation_results['emotion_columns_present'] / len(self.emotions)
        nps_score = 1.0 if validation_results['nps_data_available'] else 0.0
        sentiment_score = 1.0 if validation_results['sentiment_data_available'] else 0.0

        validation_results['chart_compatibility_score'] = (emotion_score * 0.7 + nps_score * 0.2 + sentiment_score * 0.1)

        # Identify issues
        if validation_results['emotion_columns_present'] < len(self.emotions):
            validation_results['issues'].append(f"Missing {len(self.emotions) - validation_results['emotion_columns_present']} emotion columns")

        if not validation_results['nps_data_available']:
            validation_results['issues'].append("NPS category data not available")

        if not validation_results['sentiment_data_available']:
            validation_results['issues'].append("Sentiment data not available")

        logger.info(f"Chart readiness validation: {validation_results['chart_compatibility_score']:.2f} compatibility score")

        return validation_results

# Global instance
results_formatter = ResultsFormatter()

# Convenience function
def format_ai_results_for_charts(clean_df: pd.DataFrame,
                                ai_results: List[Dict[str, Any]],
                                nps_categories: List[str]) -> pd.DataFrame:
    """Convenience function to format AI results for chart consumption"""
    return results_formatter.format_for_charts_and_export(clean_df, ai_results, nps_categories)