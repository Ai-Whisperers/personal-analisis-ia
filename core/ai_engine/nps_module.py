# -*- coding: utf-8 -*-
"""
NPS Analysis Module - Handles Net Promoter Score categorization and analysis
"""
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class NPSAnalyzer:
    """Analyzes NPS scores and categorizes customers"""
    
    def __init__(self):
        # NPS categories based on standard scoring
        self.nps_categories = {
            'detractor': (0, 6),    # 0-6: Detractors
            'passive': (7, 8),      # 7-8: Passives  
            'promoter': (9, 10)     # 9-10: Promoters
        }
        
        # Expected sentiment alignment with NPS categories
        self.expected_sentiment = {
            'detractor': 'negative',
            'passive': 'neutral', 
            'promoter': 'positive'
        }
    
    def analyze(self, llm_response: Dict, nps_score: Optional[int]) -> str:
        """Categorize NPS score into detractor/passive/promoter"""
        if nps_score is None:
            logger.warning("NPS score is None, returning 'unknown'")
            return 'unknown'
        
        try:
            nps_int = int(nps_score)
            # Ensure valid NPS range (0-10)
            if nps_int < 0 or nps_int > 10:
                logger.warning(f"NPS score out of range: {nps_int}")
                return 'unknown'
            
            # Categorize based on standard NPS ranges
            for category, (min_score, max_score) in self.nps_categories.items():
                if min_score <= nps_int <= max_score:
                    return category
                    
        except (ValueError, TypeError):
            logger.warning(f"Invalid NPS score format: {nps_score}")
            return 'unknown'
        
        return 'unknown'
    
    def analyze_with_sentiment_alignment(self, llm_response: Dict, nps_score: Optional[int]) -> Dict[str, Any]:
        """Enhanced NPS analysis with sentiment alignment check"""
        nps_category = self.analyze(llm_response, nps_score)
        
        if nps_category == 'unknown':
            return {
                'nps_category': nps_category,
                'nps_score': nps_score,
                'sentiment_alignment': 'unknown',
                'alignment_score': 0.0,
                'insights': []
            }
        
        # Check sentiment alignment
        actual_sentiment = llm_response.get('sentiment', 'neutral')
        expected_sentiment = self.expected_sentiment.get(nps_category, 'neutral')
        
        sentiment_aligned = actual_sentiment == expected_sentiment
        alignment_score = self._calculate_alignment_score(llm_response, nps_category)
        
        # Generate insights
        insights = self._generate_nps_insights(nps_category, sentiment_aligned, llm_response)
        
        return {
            'nps_category': nps_category,
            'nps_score': nps_score,
            'sentiment_alignment': 'aligned' if sentiment_aligned else 'misaligned',
            'expected_sentiment': expected_sentiment,
            'actual_sentiment': actual_sentiment,
            'alignment_score': alignment_score,
            'insights': insights
        }
    
    def _calculate_alignment_score(self, llm_response: Dict, nps_category: str) -> float:
        """Calculate how well sentiment aligns with NPS category"""
        emotions = llm_response.get('emotions', {})
        if not isinstance(emotions, dict):
            return 0.5
        
        # Define expected emotion patterns for each NPS category
        if nps_category == 'promoter':
            positive_emotions = ['alegria', 'gratitud', 'entusiasmo', 'esperanza', 'confianza']
            expected_avg = sum(emotions.get(emotion, 0) for emotion in positive_emotions) / len(positive_emotions)
            return min(1.0, expected_avg + 0.3)  # Boost for promoters
            
        elif nps_category == 'detractor':
            negative_emotions = ['enojo', 'frustracion', 'decepcion', 'tristeza', 'desagrado']
            expected_avg = sum(emotions.get(emotion, 0) for emotion in negative_emotions) / len(negative_emotions)
            return min(1.0, expected_avg + 0.2)  # Moderate boost for clear detractors
            
        else:  # passive
            # Passives should have moderate emotions
            all_emotion_scores = list(emotions.values())
            if all_emotion_scores:
                max_emotion_score = max(all_emotion_scores)
                # Passives aligned if no emotion is too high
                return 1.0 - max(0.0, max_emotion_score - 0.6)
            
        return 0.5
    
    def _generate_nps_insights(self, nps_category: str, sentiment_aligned: bool, llm_response: Dict) -> List[str]:
        """Generate insights based on NPS analysis"""
        insights = []
        
        if nps_category == 'detractor':
            insights.append('Customer is a detractor - high churn risk')
            if sentiment_aligned:
                insights.append('Sentiment aligns with NPS - genuine dissatisfaction')
            else:
                insights.append('Sentiment misalignment - investigate comment context')
            
            pain_points = llm_response.get('pain_points', [])
            if isinstance(pain_points, list) and pain_points:
                insights.append(f'Identified {len(pain_points)} pain points requiring attention')
        
        elif nps_category == 'promoter':
            insights.append('Customer is a promoter - potential advocate')
            if sentiment_aligned:
                insights.append('Strong positive sentiment supports promoter status')
            else:
                insights.append('Unexpected negative sentiment despite high NPS - investigate')
        
        elif nps_category == 'passive':
            insights.append('Customer is passive - opportunity for improvement')
            if not sentiment_aligned:
                insights.append('Mixed sentiment signals - may indicate specific issues')
            else:
                insights.append('Neutral sentiment consistent with passive status')
        
        # Check for churn risk insights
        churn_risk = llm_response.get('churn_risk', 0)
        if isinstance(churn_risk, (int, float)):
            if churn_risk > 0.7 and nps_category != 'detractor':
                insights.append('High churn risk despite NPS category - prioritize retention')
            elif churn_risk < 0.3 and nps_category == 'detractor':
                insights.append('Low churn risk despite detractor status - may be recoverable')
        
        return insights
    
    def calculate_nps_score(self, nps_categories: List[str]) -> Dict[str, Any]:
        """Calculate overall NPS score from category distribution"""
        if not nps_categories:
            return {'nps_score': 0, 'total_responses': 0, 'distribution': {}}
        
        total = len(nps_categories)
        
        # Count each category
        counts = {'promoter': 0, 'passive': 0, 'detractor': 0, 'unknown': 0}
        for category in nps_categories:
            if category in counts:
                counts[category] += 1
            else:
                counts['unknown'] += 1
        
        # Calculate NPS score: % Promoters - % Detractors
        valid_responses = total - counts['unknown']
        if valid_responses == 0:
            nps_score = 0
            promoter_pct = passive_pct = detractor_pct = 0
        else:
            promoter_pct = (counts['promoter'] / valid_responses) * 100
            passive_pct = (counts['passive'] / valid_responses) * 100
            detractor_pct = (counts['detractor'] / valid_responses) * 100
            nps_score = promoter_pct - detractor_pct
        
        # NPS interpretation
        if nps_score >= 50:
            interpretation = 'Excellent'
        elif nps_score >= 0:
            interpretation = 'Good'
        elif nps_score >= -50:
            interpretation = 'Needs Improvement'
        else:
            interpretation = 'Critical'
        
        return {
            'nps_score': round(nps_score, 1),
            'interpretation': interpretation,
            'total_responses': total,
            'valid_responses': valid_responses,
            'distribution': {
                'promoter': {'count': counts['promoter'], 'percentage': round(promoter_pct, 1)},
                'passive': {'count': counts['passive'], 'percentage': round(passive_pct, 1)},
                'detractor': {'count': counts['detractor'], 'percentage': round(detractor_pct, 1)},
                'unknown': {'count': counts['unknown'], 'percentage': round((counts['unknown']/total)*100, 1)}
            }
        }
    
    def identify_nps_improvement_opportunities(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify opportunities to improve NPS based on analysis"""
        if not analysis_results:
            return {'opportunities': [], 'priority_actions': []}
        
        opportunities = []
        priority_actions = []
        
        # Analyze passives for promotion opportunities
        passives = [r for r in analysis_results if r.get('nps_category') == 'passive']
        if passives:
            misaligned_passives = [p for p in passives if p.get('sentiment_alignment') == 'misaligned']
            if misaligned_passives:
                opportunities.append({
                    'type': 'passive_promotion',
                    'count': len(misaligned_passives),
                    'description': 'Passives with positive sentiment could be promoted to promoters'
                })
        
        # Analyze detractors for retention opportunities
        detractors = [r for r in analysis_results if r.get('nps_category') == 'detractor']
        if detractors:
            low_churn_detractors = [d for d in detractors 
                                  if d.get('alignment_score', 1) < 0.7]
            if low_churn_detractors:
                opportunities.append({
                    'type': 'detractor_recovery',
                    'count': len(low_churn_detractors),
                    'description': 'Detractors with low alignment scores may be recoverable'
                })
        
        # Generate priority actions
        if len(detractors) / len(analysis_results) > 0.3:
            priority_actions.append('Address detractor concerns - over 30% detractor rate')
        
        if len(passives) / len(analysis_results) > 0.5:
            priority_actions.append('Focus on passive engagement - large neutral segment')
        
        return {
            'opportunities': opportunities,
            'priority_actions': priority_actions,
            'summary': {
                'total_analyzed': len(analysis_results),
                'promoters': len([r for r in analysis_results if r.get('nps_category') == 'promoter']),
                'passives': len(passives),
                'detractors': len(detractors)
            }
        }