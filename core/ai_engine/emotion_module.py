# -*- coding: utf-8 -*-
"""
Emotion Analysis Module - Handles 16 emotion classification system
"""
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class EmotionAnalyzer:
    """Analyzes and processes emotion scores from LLM responses"""
    
    def __init__(self):
        # 16 emotions as defined in the blueprint
        self.emotions = [
            "alegria", "tristeza", "enojo", "miedo", "confianza", "desagrado", 
            "sorpresa", "expectativa", "frustracion", "gratitud", "aprecio", 
            "indiferencia", "decepcion", "entusiasmo", "verguenza", "esperanza"
        ]
        
        self.emotion_categories = {
            "positivas": ["alegria", "confianza", "expectativa", "gratitud", "aprecio", "entusiasmo", "esperanza"],
            "negativas": ["tristeza", "enojo", "miedo", "desagrado", "frustracion", "decepcion", "verguenza"],
            "neutras": ["sorpresa", "indiferencia"]
        }
    
    def analyze(self, llm_response: Dict) -> Dict[str, float]:
        """Extract and validate emotion scores from LLM response"""
        emotions_data = llm_response.get('emotions', {})
        
        # Initialize all emotions with 0.0
        result = {emotion: 0.0 for emotion in self.emotions}
        
        # Update with LLM response values, ensuring they're in valid range
        for emotion in self.emotions:
            if emotion in emotions_data:
                score = emotions_data[emotion]
                try:
                    score = float(score)
                    # Clamp to valid range [0, 1]
                    result[emotion] = max(0.0, min(1.0, score))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid emotion score for {emotion}: {score}")
                    result[emotion] = 0.0
        
        return result
    
    def get_emotions(self) -> List[str]:
        """Return list of all 16 emotions"""
        return self.emotions.copy()
    
    def get_emotion_categories(self) -> Dict[str, List[str]]:
        """Return emotion categorization"""
        return self.emotion_categories.copy()
    
    def calculate_category_scores(self, emotion_scores: Dict[str, float]) -> Dict[str, float]:
        """Calculate average scores for positive/negative/neutral categories"""
        category_scores = {}
        
        for category, emotions_in_category in self.emotion_categories.items():
            if emotions_in_category:
                total_score = sum(emotion_scores.get(emotion, 0.0) for emotion in emotions_in_category)
                category_scores[category] = total_score / len(emotions_in_category)
            else:
                category_scores[category] = 0.0
        
        return category_scores
    
    def get_dominant_emotions(self, emotion_scores: Dict[str, float], top_n: int = 3) -> List[tuple]:
        """Get the top N emotions by score"""
        sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_emotions[:top_n]
    
    def validate_emotion_scores(self, emotion_scores: Dict[str, float]) -> bool:
        """Validate that emotion scores are properly formatted"""
        if not isinstance(emotion_scores, dict):
            return False
        
        # Check all emotions are present
        for emotion in self.emotions:
            if emotion not in emotion_scores:
                return False
            
            score = emotion_scores[emotion]
            if not isinstance(score, (int, float)) or score < 0 or score > 1:
                return False
        
        return True