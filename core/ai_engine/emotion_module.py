"""
Módulo de análisis y validación de emociones.
Parser JSON de emociones con validación de rangos y normalización.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from config import EMOTIONS_16

logger = logging.getLogger(__name__)

@dataclass
class EmotionAnalysis:
    """Análisis estructurado de emociones para un comentario."""
    emociones: Dict[str, float]
    emotion_intensity: float  # 0-1 intensidad emocional general
    dominant_emotion: str     # emoción dominante
    emotion_category: str     # "positive", "negative", "neutral"
    emotional_balance: float  # balance positivo/negativo (-1 a 1)

# Categorización de emociones
POSITIVE_EMOTIONS = {"alegria", "confianza", "expectativa", "gratitud", "aprecio", "entusiasmo", "esperanza"}
NEGATIVE_EMOTIONS = {"tristeza", "enojo", "miedo", "desagrado", "frustracion", "decepcion", "verguenza"}
NEUTRAL_EMOTIONS = {"sorpresa", "indiferencia"}

def validate_emotion_values(emotions: Dict[str, float]) -> Dict[str, float]:
    """
    Valida y normaliza valores de emociones.
    
    Args:
        emotions: Diccionario de emociones con valores
    
    Returns:
        Diccionario validado con todas las 16 emociones
    """
    validated = {}
    
    for emotion in EMOTIONS_16:
        value = emotions.get(emotion, 0.0)
        
        # Convertir a float si es string
        try:
            value = float(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid emotion value for {emotion}: {value}, setting to 0.0")
            value = 0.0
        
        # Clamp to 0-1 range
        value = max(0.0, min(1.0, value))
        validated[emotion] = value
    
    return validated

def calculate_emotion_intensity(emotions: Dict[str, float]) -> float:
    """
    Calcula la intensidad emocional general basada en la suma de emociones.
    
    Args:
        emotions: Diccionario validado de emociones
    
    Returns:
        Intensidad emocional (0-1)
    """
    # Usar la suma de todas las emociones, normalizada
    total_emotion = sum(emotions.values())
    # Normalizar considerando que máximo realista sería ~8 (la mitad de las emociones activas)
    intensity = min(1.0, total_emotion / 8.0)
    return intensity

def find_dominant_emotion(emotions: Dict[str, float]) -> str:
    """
    Encuentra la emoción dominante (con mayor valor).
    
    Args:
        emotions: Diccionario validado de emociones
    
    Returns:
        Nombre de la emoción dominante
    """
    if not emotions:
        return "indiferencia"
    
    dominant = max(emotions.items(), key=lambda x: x[1])
    return dominant[0]

def categorize_emotion_valence(emotions: Dict[str, float]) -> str:
    """
    Categoriza las emociones como positivas, negativas o neutrales.
    
    Args:
        emotions: Diccionario validado de emociones
    
    Returns:
        Categoría: "positive", "negative", "neutral"
    """
    positive_sum = sum(emotions.get(emotion, 0.0) for emotion in POSITIVE_EMOTIONS)
    negative_sum = sum(emotions.get(emotion, 0.0) for emotion in NEGATIVE_EMOTIONS)
    neutral_sum = sum(emotions.get(emotion, 0.0) for emotion in NEUTRAL_EMOTIONS)
    
    if positive_sum > negative_sum and positive_sum > neutral_sum:
        return "positive"
    elif negative_sum > positive_sum and negative_sum > neutral_sum:
        return "negative"
    else:
        return "neutral"

def calculate_emotional_balance(emotions: Dict[str, float]) -> float:
    """
    Calcula balance emocional (-1 negativo, 0 neutral, +1 positivo).
    
    Args:
        emotions: Diccionario validado de emociones
    
    Returns:
        Balance emocional (-1 a 1)
    """
    positive_sum = sum(emotions.get(emotion, 0.0) for emotion in POSITIVE_EMOTIONS)
    negative_sum = sum(emotions.get(emotion, 0.0) for emotion in NEGATIVE_EMOTIONS)
    
    # Evitar división por cero
    total = positive_sum + negative_sum
    if total == 0:
        return 0.0
    
    # Balance: (positivo - negativo) / total
    balance = (positive_sum - negative_sum) / total
    return balance

def analyze_emotion_patterns(emotions: Dict[str, float]) -> Dict[str, any]:
    """
    Analiza patrones emocionales complejos.
    
    Args:
        emotions: Diccionario validado de emociones
    
    Returns:
        Diccionario con análisis de patrones
    """
    patterns = {
        "mixed_emotions": False,
        "emotional_conflict": False,
        "high_arousal": False,
        "emotional_complexity": 0.0
    }
    
    # Detectar emociones mixtas (múltiples emociones altas)
    high_emotions = [emotion for emotion, value in emotions.items() if value > 0.6]
    if len(high_emotions) > 2:
        patterns["mixed_emotions"] = True
    
    # Detectar conflicto emocional (alta positiva Y alta negativa)
    max_positive = max((emotions.get(emotion, 0.0) for emotion in POSITIVE_EMOTIONS), default=0.0)
    max_negative = max((emotions.get(emotion, 0.0) for emotion in NEGATIVE_EMOTIONS), default=0.0)
    
    if max_positive > 0.5 and max_negative > 0.5:
        patterns["emotional_conflict"] = True
    
    # Detectar alta activación emocional
    high_arousal_emotions = {"enojo", "miedo", "entusiasmo", "sorpresa"}
    arousal_sum = sum(emotions.get(emotion, 0.0) for emotion in high_arousal_emotions)
    if arousal_sum > 1.5:
        patterns["high_arousal"] = True
    
    # Calcular complejidad emocional (número de emociones activas)
    active_emotions = sum(1 for value in emotions.values() if value > 0.1)
    patterns["emotional_complexity"] = active_emotions / len(EMOTIONS_16)
    
    return patterns

def process_single_emotion_analysis(comment_result: Dict) -> EmotionAnalysis:
    """
    Procesa análisis de emociones para un solo comentario.
    
    Args:
        comment_result: Resultado del análisis de un comentario
    
    Returns:
        Análisis estructurado de emociones
    """
    # Extraer y validar emociones
    raw_emotions = comment_result.get("emociones", {})
    validated_emotions = validate_emotion_values(raw_emotions)
    
    # Calcular métricas
    intensity = calculate_emotion_intensity(validated_emotions)
    dominant = find_dominant_emotion(validated_emotions)
    category = categorize_emotion_valence(validated_emotions)
    balance = calculate_emotional_balance(validated_emotions)
    
    return EmotionAnalysis(
        emociones=validated_emotions,
        emotion_intensity=intensity,
        dominant_emotion=dominant,
        emotion_category=category,
        emotional_balance=balance
    )

def extract_emotions(batch_results: List[Dict]) -> List[Dict]:
    """
    Procesa y enriquece análisis de emociones para un lote de comentarios.
    
    Args:
        batch_results: Lista de resultados del análisis de comentarios
    
    Returns:
        Lista enriquecida con análisis detallado de emociones
    """
    enriched_results = []
    
    for result in batch_results:
        try:
            # Procesar análisis individual
            emotion_analysis = process_single_emotion_analysis(result)
            
            # Analizar patrones
            emotion_patterns = analyze_emotion_patterns(emotion_analysis.emociones)
            
            # Enriquecer resultado original
            enriched_result = result.copy()
            enriched_result.update({
                "emociones": emotion_analysis.emociones,  # emociones validadas
                "emotion_metadata": {
                    "intensity": emotion_analysis.emotion_intensity,
                    "dominant_emotion": emotion_analysis.dominant_emotion,
                    "category": emotion_analysis.emotion_category,
                    "emotional_balance": emotion_analysis.emotional_balance,
                    "patterns": emotion_patterns
                }
            })
            
            enriched_results.append(enriched_result)
            
        except Exception as e:
            logger.error(f"Error processing emotion analysis for comment: {e}")
            # En caso de error, mantener resultado original
            enriched_results.append(result)
    
    logger.info(f"Processed emotion analysis for {len(enriched_results)} comments")
    return enriched_results

def aggregate_emotion_insights(results: List[Dict]) -> Dict[str, any]:
    """
    Agrega insights emocionales a nivel de dataset.
    
    Args:
        results: Lista de resultados con análisis de emociones
    
    Returns:
        Diccionario con insights agregados
    """
    if not results:
        return {}
    
    # Agregaciones básicas
    total_comments = len(results)
    emotion_sums = {emotion: 0.0 for emotion in EMOTIONS_16}
    categories = {"positive": 0, "negative": 0, "neutral": 0}
    patterns = {"mixed_emotions": 0, "emotional_conflict": 0, "high_arousal": 0}
    
    intensities = []
    balances = []
    
    for result in results:
        metadata = result.get("emotion_metadata", {})
        emotions = result.get("emociones", {})
        
        # Sumar emociones
        for emotion in EMOTIONS_16:
            emotion_sums[emotion] += emotions.get(emotion, 0.0)
        
        # Contar categorías
        category = metadata.get("category", "neutral")
        if category in categories:
            categories[category] += 1
        
        # Contar patrones
        result_patterns = metadata.get("patterns", {})
        for pattern in patterns:
            if result_patterns.get(pattern, False):
                patterns[pattern] += 1
        
        # Recopilar métricas
        intensities.append(metadata.get("intensity", 0.0))
        balances.append(metadata.get("emotional_balance", 0.0))
    
    # Calcular promedios
    emotion_averages = {emotion: total / total_comments for emotion, total in emotion_sums.items()}
    avg_intensity = sum(intensities) / len(intensities) if intensities else 0.0
    avg_balance = sum(balances) / len(balances) if balances else 0.0
    
    return {
        "total_comments": total_comments,
        "emotion_averages": emotion_averages,
        "category_distribution": categories,
        "pattern_counts": patterns,
        "avg_emotional_intensity": avg_intensity,
        "avg_emotional_balance": avg_balance,
        "dominant_emotion_overall": max(emotion_averages.items(), key=lambda x: x[1])[0]
    }
