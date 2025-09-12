"""
Pain Points Analysis Module - Identifies customer issues and problems
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class PainPointsAnalyzer:
    """Analyzes and categorizes customer pain points from LLM responses"""
    
    def __init__(self):
        # Common pain point categories
        self.pain_categories = {
            'product': ['calidad', 'funcionalidad', 'defecto', 'roto', 'no_funciona'],
            'service': ['atencion', 'servicio', 'soporte', 'ayuda', 'respuesta'],
            'delivery': ['entrega', 'envio', 'demora', 'tiempo', 'tardanza'],
            'price': ['precio', 'caro', 'costoso', 'valor', 'dinero'],
            'usability': ['dificil', 'complejo', 'confuso', 'usar', 'interfaz'],
            'communication': ['informacion', 'comunicacion', 'aviso', 'notificar']
        }
    
    def analyze(self, llm_response: Dict) -> List[str]:
        """Extract and categorize pain points from LLM response"""
        pain_points_raw = llm_response.get('pain_points', [])
        
        if not isinstance(pain_points_raw, list):
            logger.warning(f"Expected list for pain_points, got {type(pain_points_raw)}")
            return []
        
        # Clean and validate pain points
        pain_points = []
        for point in pain_points_raw:
            if isinstance(point, str) and point.strip():
                clean_point = point.strip().lower()
                pain_points.append(clean_point)
        
        return pain_points
    
    def categorize_pain_points(self, pain_points: List[str]) -> Dict[str, List[str]]:
        """Categorize pain points into predefined categories"""
        categorized = {category: [] for category in self.pain_categories.keys()}
        uncategorized = []
        
        for pain_point in pain_points:
            categorized_flag = False
            
            for category, keywords in self.pain_categories.items():
                if any(keyword in pain_point for keyword in keywords):
                    categorized[category].append(pain_point)
                    categorized_flag = True
                    break
            
            if not categorized_flag:
                uncategorized.append(pain_point)
        
        if uncategorized:
            categorized['otros'] = uncategorized
        
        # Remove empty categories
        return {k: v for k, v in categorized.items() if v}
    
    def get_pain_point_severity(self, pain_points: List[str], churn_risk: float) -> str:
        """Determine severity level based on pain points and churn risk"""
        if not pain_points:
            return 'none'
        
        num_points = len(pain_points)
        
        if churn_risk > 0.7 or num_points >= 3:
            return 'high'
        elif churn_risk > 0.4 or num_points >= 2:
            return 'medium'
        else:
            return 'low'
    
    def get_most_common_pain_points(self, all_pain_points: List[List[str]], top_n: int = 10) -> List[tuple]:
        """Get most common pain points across all comments"""
        pain_point_counts = {}
        
        for pain_points_list in all_pain_points:
            for pain_point in pain_points_list:
                pain_point_counts[pain_point] = pain_point_counts.get(pain_point, 0) + 1
        
        # Sort by frequency
        sorted_pain_points = sorted(pain_point_counts.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_pain_points[:top_n]
    
    def generate_pain_point_insights(self, categorized_pain_points: Dict[str, List[str]]) -> Dict[str, Any]:
        """Generate insights from categorized pain points"""
        total_pain_points = sum(len(points) for points in categorized_pain_points.values())
        
        if total_pain_points == 0:
            return {'total': 0, 'most_affected_category': None, 'insights': []}
        
        # Find most affected category
        most_affected = max(categorized_pain_points.items(), key=lambda x: len(x[1]))
        
        insights = []
        for category, points in categorized_pain_points.items():
            if points:
                percentage = (len(points) / total_pain_points) * 100
                insights.append({
                    'category': category,
                    'count': len(points),
                    'percentage': round(percentage, 1),
                    'examples': points[:3]  # Top 3 examples
                })
        
        return {
            'total': total_pain_points,
            'most_affected_category': most_affected[0],
            'insights': sorted(insights, key=lambda x: x['count'], reverse=True)
        }