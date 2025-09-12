"""
Churn Risk Analysis Module - Predicts customer abandonment probability
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class ChurnAnalyzer:
    """Analyzes customer churn risk based on sentiment and behavioral indicators"""
    
    def __init__(self):
        # High-risk keywords that indicate churn probability
        self.high_risk_keywords = [
            'cancelar', 'cerrar cuenta', 'dar de baja', 'nunca más', 'no vuelvo',
            'pésimo servicio', 'horrible', 'terrible', 'odio', 'detesto',
            'cambiar de proveedor', 'buscar alternativa', 'competencia',
            'no recomiendo', 'perdieron cliente', 'última vez'
        ]
        
        # Medium-risk indicators
        self.medium_risk_keywords = [
            'decepcionado', 'frustrado', 'molesto', 'insatisfecho',
            'problema', 'queja', 'reclamo', 'mal servicio',
            'no cumple', 'esperaba más', 'no vale la pena'
        ]
        
        # Churn risk categories
        self.risk_categories = {
            'low': (0.0, 0.3),
            'medium': (0.3, 0.7),
            'high': (0.7, 1.0)
        }
    
    def analyze(self, llm_response: Dict) -> float:
        """Calculate churn risk score from LLM response"""
        # Get base churn risk from LLM
        base_churn_risk = llm_response.get('churn_risk', 0.5)
        
        try:
            churn_risk = float(base_churn_risk)
            # Ensure valid range [0, 1]
            churn_risk = max(0.0, min(1.0, churn_risk))
        except (ValueError, TypeError):
            logger.warning(f"Invalid churn_risk value: {base_churn_risk}")
            churn_risk = 0.5
        
        return churn_risk
    
    def analyze_with_context(self, llm_response: Dict, comment: str, nps_score: int = None) -> Dict[str, Any]:
        """Enhanced churn analysis with additional context"""
        base_churn_risk = self.analyze(llm_response)
        
        # Adjust based on keyword analysis
        keyword_risk = self._analyze_keywords(comment)
        
        # Adjust based on NPS score if available
        nps_risk = self._analyze_nps_risk(nps_score) if nps_score is not None else 0.0
        
        # Weighted combination
        final_risk = (base_churn_risk * 0.6) + (keyword_risk * 0.3) + (nps_risk * 0.1)
        final_risk = max(0.0, min(1.0, final_risk))
        
        # Determine risk category
        risk_category = self._get_risk_category(final_risk)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(comment, llm_response)
        
        return {
            'churn_risk': final_risk,
            'risk_category': risk_category,
            'risk_factors': risk_factors,
            'components': {
                'llm_base': base_churn_risk,
                'keywords': keyword_risk,
                'nps_adjustment': nps_risk
            }
        }
    
    def _analyze_keywords(self, comment: str) -> float:
        """Analyze comment for churn-indicating keywords"""
        if not comment:
            return 0.0
        
        comment_lower = comment.lower()
        
        # Count high-risk keywords
        high_risk_count = sum(1 for keyword in self.high_risk_keywords if keyword in comment_lower)
        
        # Count medium-risk keywords
        medium_risk_count = sum(1 for keyword in self.medium_risk_keywords if keyword in comment_lower)
        
        # Calculate keyword-based risk
        keyword_risk = min(1.0, (high_risk_count * 0.3) + (medium_risk_count * 0.1))
        
        return keyword_risk
    
    def _analyze_nps_risk(self, nps_score: int) -> float:
        """Calculate churn risk adjustment based on NPS score"""
        if nps_score is None:
            return 0.0
        
        if nps_score <= 6:  # Detractors
            return 0.2
        elif nps_score <= 8:  # Passives
            return 0.1
        else:  # Promoters (9-10)
            return -0.1  # Reduce risk for promoters
    
    def _get_risk_category(self, risk_score: float) -> str:
        """Determine risk category based on score"""
        for category, (min_val, max_val) in self.risk_categories.items():
            if min_val <= risk_score < max_val:
                return category
        return 'high'  # Default to high if score is 1.0
    
    def _identify_risk_factors(self, comment: str, llm_response: Dict) -> List[str]:
        """Identify specific risk factors from comment and LLM response"""
        risk_factors = []
        
        if not comment:
            return risk_factors
        
        comment_lower = comment.lower()
        
        # Check for specific risk indicators
        if any(keyword in comment_lower for keyword in self.high_risk_keywords):
            risk_factors.append('explicit_cancellation_intent')
        
        if any(keyword in comment_lower for keyword in self.medium_risk_keywords):
            risk_factors.append('dissatisfaction_indicators')
        
        # Check sentiment
        sentiment = llm_response.get('sentiment', '')
        if sentiment == 'negative':
            risk_factors.append('negative_sentiment')
        
        # Check emotion patterns
        emotions = llm_response.get('emotions', {})
        if isinstance(emotions, dict):
            # High negative emotions
            negative_emotions = ['enojo', 'frustracion', 'decepcion', 'tristeza']
            high_negative_count = sum(1 for emotion in negative_emotions 
                                    if emotions.get(emotion, 0) > 0.6)
            
            if high_negative_count >= 2:
                risk_factors.append('high_negative_emotions')
            
            # Low positive emotions
            positive_emotions = ['alegria', 'gratitud', 'entusiasmo', 'esperanza']
            avg_positive = sum(emotions.get(emotion, 0) for emotion in positive_emotions) / len(positive_emotions)
            
            if avg_positive < 0.2:
                risk_factors.append('low_positive_emotions')
        
        # Check pain points
        pain_points = llm_response.get('pain_points', [])
        if isinstance(pain_points, list) and len(pain_points) >= 3:
            risk_factors.append('multiple_pain_points')
        
        return risk_factors
    
    def calculate_churn_probability_distribution(self, all_churn_risks: List[float]) -> Dict[str, Any]:
        """Calculate distribution statistics for churn risks"""
        if not all_churn_risks:
            return {'total': 0, 'distribution': {}, 'statistics': {}}
        
        total = len(all_churn_risks)
        
        # Count by category
        distribution = {'low': 0, 'medium': 0, 'high': 0}
        for risk in all_churn_risks:
            category = self._get_risk_category(risk)
            distribution[category] += 1
        
        # Convert to percentages
        distribution_pct = {k: round((v / total) * 100, 1) for k, v in distribution.items()}
        
        # Calculate statistics
        avg_risk = sum(all_churn_risks) / total
        sorted_risks = sorted(all_churn_risks)
        median_risk = sorted_risks[len(sorted_risks) // 2]
        
        return {
            'total': total,
            'distribution': distribution_pct,
            'statistics': {
                'average_risk': round(avg_risk, 3),
                'median_risk': round(median_risk, 3),
                'min_risk': round(min(all_churn_risks), 3),
                'max_risk': round(max(all_churn_risks), 3)
            }
        }