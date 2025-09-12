"""
Módulo de análisis y predicción de churn risk.
Calcula riesgo de churn agregando features contextuales y algoritmos predictivos.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import math

logger = logging.getLogger(__name__)

class ChurnRiskLevel(Enum):
    """Niveles de riesgo de churn."""
    LOW = "low"          # 0.0 - 0.3
    MEDIUM = "medium"    # 0.3 - 0.6
    HIGH = "high"        # 0.6 - 0.8
    CRITICAL = "critical" # 0.8 - 1.0

@dataclass
class ChurnAnalysis:
    """Análisis completo de churn risk para un comentario."""
    churn_risk: float                    # 0-1 score final
    risk_level: str                      # "low", "medium", "high", "critical"
    contributing_factors: Dict[str, float]  # factores que contribuyen al riesgo
    risk_indicators: List[str]           # indicadores específicos detectados
    confidence_score: float              # 0-1 confianza en la predicción
    recommendation: str                  # recomendación de acción

# Factores de riesgo basados en emociones
EMOTION_RISK_WEIGHTS = {
    "enojo": 0.9,
    "frustracion": 0.8,
    "decepcion": 0.7,
    "desagrado": 0.6,
    "verguenza": 0.5,
    "tristeza": 0.4,
    "miedo": 0.3,
    "indiferencia": 0.2,
    # Emociones positivas que reducen riesgo
    "confianza": -0.3,
    "gratitud": -0.4,
    "aprecio": -0.5,
    "alegria": -0.6,
    "entusiasmo": -0.7,
    "esperanza": -0.3
}

# Palabras clave que indican alto riesgo de churn
HIGH_RISK_KEYWORDS = {
    "cancelar": 0.9,
    "cancelaré": 0.9,
    "dejar": 0.8,
    "abandonar": 0.8,
    "cambiar": 0.7,
    "competencia": 0.7,
    "otro proveedor": 0.8,
    "otra empresa": 0.8,
    "no recomiendo": 0.6,
    "no vuelvo": 0.8,
    "nunca más": 0.7,
    "pésimo": 0.6,
    "horrible": 0.6,
    "terrible": 0.6,
    "inaceptable": 0.7,
    "decepcionado": 0.5,
    "estafado": 0.8,
    "engañado": 0.7
}

# Palabras que indican bajo riesgo
LOW_RISK_KEYWORDS = {
    "recomiendo": -0.5,
    "excelente": -0.6,
    "fantástico": -0.5,
    "perfecto": -0.4,
    "satisfecho": -0.4,
    "feliz": -0.3,
    "volveré": -0.7,
    "seguiré": -0.6,
    "continuaré": -0.6
}

def calculate_emotion_based_churn_risk(emotions: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """
    Calcula riesgo de churn basado en emociones.
    
    Args:
        emotions: Diccionario de emociones validadas
    
    Returns:
        Tupla (risk_score, contributing_emotions)
    """
    emotion_contribution = {}
    total_risk = 0.0
    
    for emotion, value in emotions.items():
        weight = EMOTION_RISK_WEIGHTS.get(emotion, 0.0)
        if weight != 0:
            contribution = value * weight
            emotion_contribution[emotion] = contribution
            total_risk += contribution
    
    # Normalizar a rango 0-1
    normalized_risk = max(0.0, min(1.0, total_risk))
    
    return normalized_risk, emotion_contribution

def calculate_text_based_churn_risk(comment: str) -> Tuple[float, List[str]]:
    """
    Calcula riesgo de churn basado en análisis de texto.
    
    Args:
        comment: Texto del comentario
    
    Returns:
        Tupla (risk_score, detected_indicators)
    """
    if not comment:
        return 0.0, []
    
    comment_lower = comment.lower()
    risk_score = 0.0
    detected_indicators = []
    
    # Buscar keywords de alto riesgo
    for keyword, weight in HIGH_RISK_KEYWORDS.items():
        if keyword in comment_lower:
            risk_score += weight
            detected_indicators.append(f"high_risk_keyword: {keyword}")
    
    # Buscar keywords de bajo riesgo
    for keyword, weight in LOW_RISK_KEYWORDS.items():
        if keyword in comment_lower:
            risk_score += weight  # weight es negativo
            detected_indicators.append(f"low_risk_keyword: {keyword}")
    
    # Normalizar
    normalized_risk = max(0.0, min(1.0, risk_score))
    
    return normalized_risk, detected_indicators

def calculate_nps_based_churn_risk(nps_category: str, nps_score: Optional[float] = None) -> float:
    """
    Calcula riesgo de churn basado en categoría y score NPS.
    
    Args:
        nps_category: Categoría NPS
        nps_score: Score NPS opcional
    
    Returns:
        Risk score basado en NPS
    """
    # Mapeo base por categoría
    category_risk = {
        "Detractor": 0.8,
        "Pasivo": 0.4,
        "Promotor": 0.1,
        "Desconocido": 0.5
    }
    
    base_risk = category_risk.get(nps_category, 0.5)
    
    # Ajustar con score específico si está disponible
    if nps_score is not None:
        try:
            score = float(nps_score)
            if score <= 3:
                base_risk = max(base_risk, 0.9)  # Muy alto riesgo
            elif score <= 6:
                base_risk = max(base_risk, 0.7)  # Alto riesgo
            elif score >= 9:
                base_risk = min(base_risk, 0.2)  # Bajo riesgo
        except (ValueError, TypeError):
            pass
    
    return base_risk

def calculate_pain_points_churn_risk(pain_points: List[Dict]) -> Tuple[float, List[str]]:
    """
    Calcula riesgo de churn basado en pain points identificados.
    
    Args:
        pain_points: Lista de pain points con categoría y severidad
    
    Returns:
        Tupla (risk_score, risk_factors)
    """
    if not pain_points:
        return 0.0, []
    
    # Pesos por severidad
    severity_weights = {
        "alta": 0.3,
        "media": 0.2,
        "baja": 0.1
    }
    
    # Pesos por categoría
    category_weights = {
        "servicio": 0.8,
        "producto": 0.7,
        "precio": 0.6,
        "proceso": 0.5,
        "comunicacion": 0.4
    }
    
    total_risk = 0.0
    risk_factors = []
    
    for pain_point in pain_points:
        if not isinstance(pain_point, dict):
            continue
            
        categoria = pain_point.get("categoria", "").lower()
        severidad = pain_point.get("severidad", "").lower()
        descripcion = pain_point.get("descripcion", "")
        
        # Calcular peso del pain point
        category_weight = category_weights.get(categoria, 0.3)
        severity_weight = severity_weights.get(severidad, 0.1)
        
        pain_risk = category_weight * severity_weight
        total_risk += pain_risk
        
        risk_factors.append(f"{categoria}_{severidad}: {descripcion}")
    
    # Normalizar considerando que múltiples pain points aumentan el riesgo
    normalized_risk = min(1.0, total_risk * (1 + len(pain_points) * 0.1))
    
    return normalized_risk, risk_factors

def calculate_consistency_churn_risk(nps_metadata: Dict) -> float:
    """
    Calcula riesgo adicional basado en inconsistencias en datos NPS.
    
    Args:
        nps_metadata: Metadatos del análisis NPS
    
    Returns:
        Risk score por inconsistencias
    """
    if not nps_metadata:
        return 0.0
    
    consistency_score = nps_metadata.get("consistency_score", 1.0)
    sentiment_alignment = nps_metadata.get("sentiment_alignment", "aligned")
    
    # Si hay baja consistencia, puede indicar confusión o frustración
    risk_from_inconsistency = 0.0
    
    if consistency_score < 0.3:
        risk_from_inconsistency = 0.3  # Inconsistencia alta
    elif consistency_score < 0.6:
        risk_from_inconsistency = 0.15  # Inconsistencia media
    
    if sentiment_alignment == "misaligned":
        risk_from_inconsistency += 0.2
    
    return min(1.0, risk_from_inconsistency)

def aggregate_churn_factors(emotion_risk: float, text_risk: float, nps_risk: float, 
                           pain_points_risk: float, consistency_risk: float) -> Dict[str, float]:
    """
    Agrega y pesa diferentes factores de riesgo.
    
    Args:
        emotion_risk: Riesgo basado en emociones
        text_risk: Riesgo basado en texto
        nps_risk: Riesgo basado en NPS
        pain_points_risk: Riesgo basado en pain points
        consistency_risk: Riesgo basado en inconsistencias
    
    Returns:
        Diccionario con factores ponderados
    """
    # Pesos para cada factor
    weights = {
        "emotions": 0.3,
        "text_keywords": 0.25,
        "nps_analysis": 0.25,
        "pain_points": 0.15,
        "consistency": 0.05
    }
    
    weighted_factors = {
        "emotions": emotion_risk * weights["emotions"],
        "text_keywords": text_risk * weights["text_keywords"],
        "nps_analysis": nps_risk * weights["nps_analysis"],
        "pain_points": pain_points_risk * weights["pain_points"],
        "consistency": consistency_risk * weights["consistency"]
    }
    
    return weighted_factors

def calculate_confidence_score(factors: Dict[str, float], indicators: List[str]) -> float:
    """
    Calcula confianza en la predicción de churn.
    
    Args:
        factors: Factores de riesgo calculados
        indicators: Indicadores detectados
    
    Returns:
        Score de confianza (0-1)
    """
    # Más factores activos = mayor confianza
    active_factors = sum(1 for value in factors.values() if value > 0.1)
    factor_confidence = min(1.0, active_factors / len(factors))
    
    # Más indicadores específicos = mayor confianza
    indicator_confidence = min(1.0, len(indicators) / 5.0)
    
    # Combinar
    confidence = (factor_confidence * 0.7) + (indicator_confidence * 0.3)
    
    return confidence

def determine_risk_level(churn_risk: float) -> str:
    """
    Determina nivel de riesgo categórico.
    
    Args:
        churn_risk: Score de riesgo (0-1)
    
    Returns:
        Nivel de riesgo
    """
    if churn_risk >= 0.8:
        return ChurnRiskLevel.CRITICAL.value
    elif churn_risk >= 0.6:
        return ChurnRiskLevel.HIGH.value
    elif churn_risk >= 0.3:
        return ChurnRiskLevel.MEDIUM.value
    else:
        return ChurnRiskLevel.LOW.value

def generate_churn_recommendation(risk_level: str, indicators: List[str]) -> str:
    """
    Genera recomendación de acción basada en nivel de riesgo.
    
    Args:
        risk_level: Nivel de riesgo
        indicators: Indicadores detectados
    
    Returns:
        Recomendación de acción
    """
    recommendations = {
        ChurnRiskLevel.CRITICAL.value: "Acción inmediata requerida. Contactar cliente urgentemente para retención.",
        ChurnRiskLevel.HIGH.value: "Alto riesgo. Implementar estrategia de retención personalizada.",
        ChurnRiskLevel.MEDIUM.value: "Monitorear de cerca. Mejorar experiencia en áreas problemáticas.",
        ChurnRiskLevel.LOW.value: "Cliente estable. Mantener calidad de servicio actual."
    }
    
    base_recommendation = recommendations.get(risk_level, "Evaluar situación específica.")
    
    # Agregar contexto específico si hay indicadores
    if "high_risk_keyword: cancelar" in indicators:
        base_recommendation += " Cliente menciona intención de cancelar."
    
    return base_recommendation

def process_single_churn_analysis(comment_result: Dict) -> ChurnAnalysis:
    """
    Procesa análisis de churn para un solo comentario.
    
    Args:
        comment_result: Resultado del análisis del comentario
    
    Returns:
        Análisis estructurado de churn
    """
    # Extraer datos
    comment = comment_result.get("comentario", "")
    emotions = comment_result.get("emociones", {})
    nps_category = comment_result.get("nps_category", "Desconocido")
    pain_points = comment_result.get("pain_points", [])
    nps_metadata = comment_result.get("nps_metadata", {})
    ai_churn_risk = comment_result.get("churn_risk", 0.0)  # del LLM
    
    # Calcular riesgos por factor
    emotion_risk, emotion_contrib = calculate_emotion_based_churn_risk(emotions)
    text_risk, text_indicators = calculate_text_based_churn_risk(comment)
    nps_risk = calculate_nps_based_churn_risk(nps_category, nps_metadata.get("nps_score"))
    pain_points_risk, pain_indicators = calculate_pain_points_churn_risk(pain_points)
    consistency_risk = calculate_consistency_churn_risk(nps_metadata)
    
    # Agregar factores
    weighted_factors = aggregate_churn_factors(
        emotion_risk, text_risk, nps_risk, pain_points_risk, consistency_risk
    )
    
    # Calcular score final (combinar con predicción del LLM)
    heuristic_risk = sum(weighted_factors.values())
    
    # Combinar con predicción del LLM (70% heurística, 30% LLM)
    try:
        ai_risk = max(0.0, min(1.0, float(ai_churn_risk)))
        final_risk = (heuristic_risk * 0.7) + (ai_risk * 0.3)
    except (ValueError, TypeError):
        final_risk = heuristic_risk
    
    final_risk = max(0.0, min(1.0, final_risk))
    
    # Compilar todos los indicadores
    all_indicators = text_indicators + pain_indicators
    
    # Calcular confianza
    confidence = calculate_confidence_score(weighted_factors, all_indicators)
    
    # Determinar nivel y recomendación
    risk_level = determine_risk_level(final_risk)
    recommendation = generate_churn_recommendation(risk_level, all_indicators)
    
    return ChurnAnalysis(
        churn_risk=final_risk,
        risk_level=risk_level,
        contributing_factors=weighted_factors,
        risk_indicators=all_indicators,
        confidence_score=confidence,
        recommendation=recommendation
    )

def compute_churn(batch_results: List[Dict]) -> List[Dict]:
    """
    Analiza y enriquece análisis de churn para un lote de comentarios.
    
    Args:
        batch_results: Lista de resultados de análisis
    
    Returns:
        Lista enriquecida con análisis detallado de churn
    """
    enriched_results = []
    
    for result in batch_results:
        try:
            # Procesar análisis de churn
            churn_analysis = process_single_churn_analysis(result)
            
            # Enriquecer resultado original
            enriched_result = result.copy()
            enriched_result.update({
                "churn_risk": churn_analysis.churn_risk,  # score actualizado
                "churn_metadata": {
                    "risk_level": churn_analysis.risk_level,
                    "contributing_factors": churn_analysis.contributing_factors,
                    "risk_indicators": churn_analysis.risk_indicators,
                    "confidence_score": churn_analysis.confidence_score,
                    "recommendation": churn_analysis.recommendation
                }
            })
            
            enriched_results.append(enriched_result)
            
        except Exception as e:
            logger.error(f"Error processing churn analysis for comment: {e}")
            # En caso de error, mantener resultado original
            enriched_results.append(result)
    
    logger.info(f"Processed churn analysis for {len(enriched_results)} comments")
    return enriched_results

def aggregate_churn_insights(results: List[Dict]) -> Dict[str, Any]:
    """
    Agrega insights de churn a nivel de dataset.
    
    Args:
        results: Lista de resultados con análisis de churn
    
    Returns:
        Diccionario con insights agregados de churn
    """
    if not results:
        return {}
    
    # Métricas básicas
    total_comments = len(results)
    risk_levels = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    churn_risks = []
    confidence_scores = []
    top_risk_factors = {}
    
    for result in results:
        churn_metadata = result.get("churn_metadata", {})
        churn_risk = result.get("churn_risk", 0.0)
        
        # Contar niveles de riesgo
        risk_level = churn_metadata.get("risk_level", "low")
        if risk_level in risk_levels:
            risk_levels[risk_level] += 1
        
        # Recopilar métricas
        churn_risks.append(churn_risk)
        confidence_scores.append(churn_metadata.get("confidence_score", 0.0))
        
        # Agregar factores de riesgo
        factors = churn_metadata.get("contributing_factors", {})
        for factor, value in factors.items():
            if factor not in top_risk_factors:
                top_risk_factors[factor] = []
            top_risk_factors[factor].append(value)
    
    # Calcular promedios
    avg_churn_risk = sum(churn_risks) / len(churn_risks) if churn_risks else 0.0
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    
    # Factores de riesgo promedio
    avg_risk_factors = {}
    for factor, values in top_risk_factors.items():
        avg_risk_factors[factor] = sum(values) / len(values)
    
    # Calcular churn rate estimado (comentarios con riesgo alto/crítico)
    high_risk_count = risk_levels["high"] + risk_levels["critical"]
    estimated_churn_rate = (high_risk_count / total_comments) * 100 if total_comments > 0 else 0
    
    return {
        "total_comments": total_comments,
        "avg_churn_risk": round(avg_churn_risk, 3),
        "estimated_churn_rate": round(estimated_churn_rate, 2),
        "risk_level_distribution": risk_levels,
        "risk_level_percentages": {
            level: round((count / total_comments) * 100, 2)
            for level, count in risk_levels.items()
        },
        "avg_confidence": round(avg_confidence, 3),
        "top_risk_factors": {
            factor: round(value, 3)
            for factor, value in sorted(avg_risk_factors.items(), key=lambda x: x[1], reverse=True)
        },
        "high_risk_customers": high_risk_count,
        "immediate_action_required": risk_levels["critical"]
    }
