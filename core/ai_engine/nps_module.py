"""
Módulo de análisis y validación NPS (Net Promoter Score).
Validación, corrección automática y análisis de consistencia NPS.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class NPSCategory(Enum):
    """Categorías NPS estándar."""
    DETRACTOR = "Detractor"
    PASIVO = "Pasivo"
    PROMOTOR = "Promotor"
    DESCONOCIDO = "Desconocido"

@dataclass
class NPSAnalysis:
    """Análisis completo de NPS para un comentario."""
    nps_score: Optional[float]
    nps_category: str
    original_category: Optional[str]
    category_corrected: bool
    consistency_score: float  # 0-1 consistencia entre score y comentario
    sentiment_alignment: str  # "aligned", "misaligned", "neutral"

# Mapeos estándar NPS
NPS_CATEGORY_MAPPING = {
    (0, 6): NPSCategory.DETRACTOR,
    (7, 8): NPSCategory.PASIVO,
    (9, 10): NPSCategory.PROMOTOR
}

def validate_nps_score(score: Any) -> Optional[float]:
    """
    Valida y normaliza un score NPS.
    
    Args:
        score: Score a validar (puede ser int, float, str)
    
    Returns:
        Score normalizado (0-10) o None si es inválido
    """
    if score is None:
        return None
    
    try:
        # Intentar convertir a float
        numeric_score = float(score)
        
        # Normalizar a escala 0-10
        if 0 <= numeric_score <= 10:
            return numeric_score
        elif 0 <= numeric_score <= 1:
            # Convertir de escala 0-1 a 0-10
            return numeric_score * 10
        elif 0 <= numeric_score <= 100:
            # Convertir de escala 0-100 a 0-10
            return numeric_score / 10
        else:
            logger.warning(f"NPS score out of expected range: {numeric_score}")
            return None
            
    except (ValueError, TypeError):
        logger.warning(f"Cannot convert NPS score to numeric: {score}")
        return None

def map_nps_category(score: Optional[float]) -> str:
    """
    Mapea score NPS a categoría estándar.
    
    Args:
        score: Score NPS (0-10)
    
    Returns:
        Categoría NPS como string
    """
    if score is None:
        return NPSCategory.DESCONOCIDO.value
    
    try:
        score = float(score)
        
        if score <= 6:
            return NPSCategory.DETRACTOR.value
        elif 7 <= score <= 8:
            return NPSCategory.PASIVO.value
        elif score >= 9:
            return NPSCategory.PROMOTOR.value
        else:
            return NPSCategory.DESCONOCIDO.value
            
    except (ValueError, TypeError):
        return NPSCategory.DESCONOCIDO.value

def validate_nps_category(category: str) -> str:
    """
    Valida y normaliza categoría NPS.
    
    Args:
        category: Categoría a validar
    
    Returns:
        Categoría normalizada
    """
    if not isinstance(category, str):
        return NPSCategory.DESCONOCIDO.value
    
    category_clean = category.strip().lower()
    
    # Mapear variaciones comunes
    category_mappings = {
        "detractor": NPSCategory.DETRACTOR.value,
        "detractors": NPSCategory.DETRACTOR.value,
        "critico": NPSCategory.DETRACTOR.value,
        "negativo": NPSCategory.DETRACTOR.value,
        
        "pasivo": NPSCategory.PASIVO.value,
        "pasivos": NPSCategory.PASIVO.value,
        "neutral": NPSCategory.PASIVO.value,
        "neutro": NPSCategory.PASIVO.value,
        
        "promotor": NPSCategory.PROMOTOR.value,
        "promotores": NPSCategory.PROMOTOR.value,
        "promoter": NPSCategory.PROMOTOR.value,
        "positivo": NPSCategory.PROMOTOR.value,
        "defensor": NPSCategory.PROMOTOR.value,
    }
    
    return category_mappings.get(category_clean, NPSCategory.DESCONOCIDO.value)

def detect_sentiment_from_comment(comment: str, emotions: Dict[str, float]) -> str:
    """
    Detecta sentimiento general basado en comentario y emociones.
    
    Args:
        comment: Texto del comentario
        emotions: Diccionario de emociones
    
    Returns:
        Sentimiento: "positive", "negative", "neutral"
    """
    if not comment or not emotions:
        return "neutral"
    
    # Análisis basado en emociones
    positive_emotions = {"alegria", "confianza", "expectativa", "gratitud", "aprecio", "entusiasmo", "esperanza"}
    negative_emotions = {"tristeza", "enojo", "miedo", "desagrado", "frustracion", "decepcion", "verguenza"}
    
    positive_sum = sum(emotions.get(emotion, 0.0) for emotion in positive_emotions)
    negative_sum = sum(emotions.get(emotion, 0.0) for emotion in negative_emotions)
    
    # Análisis básico de texto
    comment_lower = comment.lower()
    positive_words = ["excelente", "bueno", "fantástico", "perfecto", "recomiendo", "feliz", "satisfecho"]
    negative_words = ["malo", "terrible", "horrible", "pésimo", "cancelar", "problema", "quejas"]
    
    positive_word_count = sum(1 for word in positive_words if word in comment_lower)
    negative_word_count = sum(1 for word in negative_words if word in comment_lower)
    
    # Combinar análisis emocional y textual
    total_positive = positive_sum + (positive_word_count * 0.2)
    total_negative = negative_sum + (negative_word_count * 0.2)
    
    if total_positive > total_negative * 1.2:
        return "positive"
    elif total_negative > total_positive * 1.2:
        return "negative"
    else:
        return "neutral"

def calculate_nps_consistency(nps_score: Optional[float], comment: str, emotions: Dict[str, float]) -> float:
    """
    Calcula consistencia entre NPS score y sentimiento del comentario.
    
    Args:
        nps_score: Score NPS
        comment: Comentario
        emotions: Emociones extraídas
    
    Returns:
        Score de consistencia (0-1)
    """
    if nps_score is None:
        return 0.0
    
    # Determinar categoría NPS esperada basada en score
    expected_category = map_nps_category(nps_score)
    
    # Detectar sentimiento del comentario
    detected_sentiment = detect_sentiment_from_comment(comment, emotions)
    
    # Mapear sentimiento a categoría NPS esperada
    sentiment_to_nps = {
        "positive": NPSCategory.PROMOTOR.value,
        "neutral": NPSCategory.PASIVO.value,
        "negative": NPSCategory.DETRACTOR.value
    }
    
    sentiment_category = sentiment_to_nps.get(detected_sentiment, NPSCategory.DESCONOCIDO.value)
    
    # Calcular consistencia
    if expected_category == sentiment_category:
        return 1.0
    elif (expected_category == NPSCategory.PASIVO.value or 
          sentiment_category == NPSCategory.PASIVO.value):
        # Penalizar menos si uno de los dos es neutral
        return 0.5
    else:
        # Inconsistencia total
        return 0.0

def correct_nps_category_with_ai(comment_result: Dict) -> Tuple[str, bool]:
    """
    Corrige categoría NPS basada en análisis de IA.
    
    Args:
        comment_result: Resultado del análisis con emociones y comentario
    
    Returns:
        Tupla (categoría_corregida, fue_corregida)
    """
    original_category = comment_result.get("nps_category")
    comment = comment_result.get("comentario", "")
    emotions = comment_result.get("emociones", {})
    
    # Validar categoría original
    normalized_category = validate_nps_category(original_category or "")
    
    # Si no hay datos suficientes, mantener original
    if not comment or not emotions:
        return normalized_category, False
    
    # Detectar sentimiento
    detected_sentiment = detect_sentiment_from_comment(comment, emotions)
    
    # Mapear sentimiento a categoría NPS
    sentiment_to_nps = {
        "positive": NPSCategory.PROMOTOR.value,
        "neutral": NPSCategory.PASIVO.value,
        "negative": NPSCategory.DETRACTOR.value
    }
    
    suggested_category = sentiment_to_nps.get(detected_sentiment, normalized_category)
    
    # Corregir solo si hay una fuerte inconsistencia
    if (normalized_category == NPSCategory.PROMOTOR.value and detected_sentiment == "negative") or \
       (normalized_category == NPSCategory.DETRACTOR.value and detected_sentiment == "positive"):
        logger.info(f"Correcting NPS category from {normalized_category} to {suggested_category}")
        return suggested_category, True
    
    return normalized_category, False

def process_single_nps_analysis(comment_result: Dict, nps_score: Optional[float] = None) -> NPSAnalysis:
    """
    Procesa análisis NPS para un solo comentario.
    
    Args:
        comment_result: Resultado del análisis del comentario
        nps_score: Score NPS opcional (si está disponible)
    
    Returns:
        Análisis estructurado de NPS
    """
    # Extraer datos
    comment = comment_result.get("comentario", "")
    emotions = comment_result.get("emociones", {})
    original_category = comment_result.get("nps_category")
    
    # Validar y normalizar score
    validated_score = validate_nps_score(nps_score)
    
    # Corregir categoría con IA
    corrected_category, was_corrected = correct_nps_category_with_ai(comment_result)
    
    # Calcular consistencia
    consistency = calculate_nps_consistency(validated_score, comment, emotions)
    
    # Determinar alineación sentimiento-NPS
    detected_sentiment = detect_sentiment_from_comment(comment, emotions)
    if consistency >= 0.8:
        sentiment_alignment = "aligned"
    elif consistency >= 0.4:
        sentiment_alignment = "neutral"
    else:
        sentiment_alignment = "misaligned"
    
    return NPSAnalysis(
        nps_score=validated_score,
        nps_category=corrected_category,
        original_category=original_category,
        category_corrected=was_corrected,
        consistency_score=consistency,
        sentiment_alignment=sentiment_alignment
    )

def analyze_nps_batch(batch_results: List[Dict], nps_scores: Optional[List[float]] = None) -> List[Dict]:
    """
    Analiza y enriquece datos NPS para un lote de comentarios.
    
    Args:
        batch_results: Lista de resultados de análisis
        nps_scores: Scores NPS opcionales correspondientes
    
    Returns:
        Lista enriquecida con análisis NPS
    """
    enriched_results = []
    
    for i, result in enumerate(batch_results):
        try:
            # Obtener score NPS si está disponible
            score = None
            if nps_scores and i < len(nps_scores):
                score = nps_scores[i]
            
            # Procesar análisis NPS
            nps_analysis = process_single_nps_analysis(result, score)
            
            # Enriquecer resultado original
            enriched_result = result.copy()
            enriched_result.update({
                "nps_category": nps_analysis.nps_category,  # categoría corregida
                "nps_metadata": {
                    "nps_score": nps_analysis.nps_score,
                    "original_category": nps_analysis.original_category,
                    "category_corrected": nps_analysis.category_corrected,
                    "consistency_score": nps_analysis.consistency_score,
                    "sentiment_alignment": nps_analysis.sentiment_alignment
                }
            })
            
            enriched_results.append(enriched_result)
            
        except Exception as e:
            logger.error(f"Error processing NPS analysis for comment {i}: {e}")
            # En caso de error, mantener resultado original
            enriched_results.append(result)
    
    logger.info(f"Processed NPS analysis for {len(enriched_results)} comments")
    return enriched_results

def calculate_nps_score_aggregate(results: List[Dict]) -> Dict[str, Any]:
    """
    Calcula NPS score agregado y métricas relacionadas.
    
    Args:
        results: Lista de resultados con análisis NPS
    
    Returns:
        Diccionario con métricas NPS agregadas
    """
    if not results:
        return {}
    
    # Contar categorías
    category_counts = {
        NPSCategory.PROMOTOR.value: 0,
        NPSCategory.PASIVO.value: 0,
        NPSCategory.DETRACTOR.value: 0,
        NPSCategory.DESCONOCIDO.value: 0
    }
    
    consistencies = []
    corrections_made = 0
    
    for result in results:
        # Contar categorías
        category = result.get("nps_category", NPSCategory.DESCONOCIDO.value)
        if category in category_counts:
            category_counts[category] += 1
        
        # Recopilar métricas
        metadata = result.get("nps_metadata", {})
        if metadata.get("consistency_score") is not None:
            consistencies.append(metadata["consistency_score"])
        
        if metadata.get("category_corrected", False):
            corrections_made += 1
    
    total_responses = sum(category_counts.values()) - category_counts[NPSCategory.DESCONOCIDO.value]
    
    if total_responses == 0:
        return {
            "total_responses": 0,
            "nps_score": 0,
            "category_distribution": category_counts,
            "avg_consistency": 0.0,
            "corrections_made": corrections_made
        }
    
    # Calcular NPS score: (% Promotores - % Detractores)
    promoter_pct = (category_counts[NPSCategory.PROMOTOR.value] / total_responses) * 100
    detractor_pct = (category_counts[NPSCategory.DETRACTOR.value] / total_responses) * 100
    nps_score = promoter_pct - detractor_pct
    
    # Consistencia promedio
    avg_consistency = sum(consistencies) / len(consistencies) if consistencies else 0.0
    
    return {
        "total_responses": total_responses,
        "nps_score": round(nps_score, 2),
        "category_distribution": category_counts,
        "category_percentages": {
            NPSCategory.PROMOTOR.value: round(promoter_pct, 2),
            NPSCategory.PASIVO.value: round((category_counts[NPSCategory.PASIVO.value] / total_responses) * 100, 2),
            NPSCategory.DETRACTOR.value: round(detractor_pct, 2)
        },
        "avg_consistency": round(avg_consistency, 3),
        "corrections_made": corrections_made,
        "correction_rate": round(corrections_made / len(results) * 100, 2) if results else 0
    }
