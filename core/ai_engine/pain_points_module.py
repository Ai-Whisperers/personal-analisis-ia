"""
Módulo de extracción y análisis de pain points.
Extrae, categoriza y rankea pain points de comentarios de clientes.
"""

import logging
import re
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

@dataclass
class PainPoint:
    """Representación estructurada de un pain point."""
    descripcion: str
    categoria: str
    severidad: str
    frecuencia: int
    impact_score: float  # 0-1 score de impacto calculado
    keywords: List[str]  # palabras clave que lo identifican

class PainPointCategory:
    """Categorías estándar de pain points."""
    SERVICIO = "servicio"
    PRODUCTO = "producto"
    PRECIO = "precio"
    PROCESO = "proceso"
    COMUNICACION = "comunicacion"
    TIEMPO = "tiempo"
    CALIDAD = "calidad"
    PERSONAL = "personal"

class Severity:
    """Niveles de severidad."""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

# Patrones de texto que indican pain points específicos
PAIN_POINT_PATTERNS = {
    PainPointCategory.SERVICIO: {
        "lento": ["lento", "demora", "tardanza", "esperé", "waiting"],
        "malo": ["mal servicio", "pésimo servicio", "servicio horrible"],
        "indisponible": ["no funciona", "caído", "sin servicio", "indisponible"],
        "complicado": ["complicado", "difícil", "confuso", "no entiendo"]
    },
    
    PainPointCategory.PRODUCTO: {
        "defectuoso": ["defectuoso", "roto", "no funciona bien", "falla"],
        "limitado": ["limitado", "no tiene", "falta", "no permite"],
        "obsoleto": ["obsoleto", "viejo", "desactualizado", "anticuado"],
        "buggy": ["error", "bug", "falla", "no responde"]
    },
    
    PainPointCategory.PRECIO: {
        "caro": ["caro", "costoso", "precio alto", "muy caro"],
        "no_vale": ["no vale la pena", "sobreprecio", "no justifica"],
        "aumentos": ["aumentó", "subió el precio", "más caro que antes"],
        "hidden_fees": ["cargo extra", "cobro adicional", "fee oculto"]
    },
    
    PainPointCategory.PROCESO: {
        "complicado": ["proceso complicado", "muchos pasos", "burocrático"],
        "lento": ["proceso lento", "demora mucho", "tarda"],
        "confuso": ["no entiendo", "confuso", "mal explicado"],
        "requiere_mucho": ["pide muchos datos", "muchos requisitos"]
    },
    
    PainPointCategory.COMUNICACION: {
        "no_responden": ["no responden", "no contestan", "sin respuesta"],
        "mala_info": ["mala información", "info incorrecta", "mal informado"],
        "no_entienden": ["no me entienden", "no comprenden", "malentendido"],
        "prepotente": ["prepotente", "grosero", "mala actitud"]
    },
    
    PainPointCategory.TIEMPO: {
        "demora": ["demora", "tardanza", "lento", "mucho tiempo"],
        "horarios": ["horario malo", "cierran temprano", "no atienden"],
        "espera": ["mucha espera", "cola larga", "esperé mucho"]
    },
    
    PainPointCategory.CALIDAD: {
        "baja": ["mala calidad", "baja calidad", "calidad pobre"],
        "inconsistente": ["inconsistente", "a veces bien", "varía"],
        "deterioro": ["empeoró", "ya no es como antes", "perdió calidad"]
    },
    
    PainPointCategory.PERSONAL: {
        "no_capacitado": ["no sabe", "no conoce", "sin capacitación"],
        "mala_actitud": ["mala actitud", "grosero", "antipático"],
        "pocos": ["poco personal", "falta gente", "solo uno atendiendo"]
    }
}

# Palabras que indican severidad alta
HIGH_SEVERITY_KEYWORDS = {
    "inaceptable", "horrible", "pésimo", "terrible", "desastroso", 
    "cancelar", "nunca más", "estafa", "fraude", "engaño"
}

MEDIUM_SEVERITY_KEYWORDS = {
    "malo", "problema", "molesto", "incómodo", "decepcionante", 
    "frustrante", "preocupante"
}

def detect_pain_points_from_text(comment: str) -> List[Dict[str, Any]]:
    """
    Detecta pain points desde el texto usando patrones y keywords.
    
    Args:
        comment: Texto del comentario
    
    Returns:
        Lista de pain points detectados
    """
    if not comment:
        return []
    
    comment_lower = comment.lower()
    detected_pain_points = []
    
    for category, patterns in PAIN_POINT_PATTERNS.items():
        for pain_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in comment_lower:
                    # Extraer contexto alrededor de la palabra clave
                    context = extract_context_around_keyword(comment, keyword)
                    
                    # Determinar severidad basada en keywords
                    severity = determine_severity_from_context(context)
                    
                    pain_point = {
                        "descripcion": context or f"Problema relacionado con {pain_type}",
                        "categoria": category,
                        "severidad": severity,
                        "keywords": [keyword],
                        "detected_by": "text_analysis"
                    }
                    
                    detected_pain_points.append(pain_point)
                    break  # Evitar duplicados para la misma categoría
    
    return detected_pain_points

def extract_context_around_keyword(text: str, keyword: str, window: int = 50) -> str:
    """
    Extrae contexto alrededor de una palabra clave.
    
    Args:
        text: Texto completo
        keyword: Palabra clave
        window: Ventana de caracteres alrededor
    
    Returns:
        Contexto extraído
    """
    try:
        index = text.lower().find(keyword.lower())
        if index == -1:
            return ""
        
        start = max(0, index - window)
        end = min(len(text), index + len(keyword) + window)
        
        context = text[start:end].strip()
        
        # Limpiar y normalizar
        context = re.sub(r'\s+', ' ', context)
        return context
        
    except Exception:
        return ""

def determine_severity_from_context(context: str) -> str:
    """
    Determina severidad basada en el contexto.
    
    Args:
        context: Contexto del pain point
    
    Returns:
        Nivel de severidad
    """
    if not context:
        return Severity.MEDIA
    
    context_lower = context.lower()
    
    # Buscar palabras de alta severidad
    if any(word in context_lower for word in HIGH_SEVERITY_KEYWORDS):
        return Severity.ALTA
    
    # Buscar palabras de media severidad
    if any(word in context_lower for word in MEDIUM_SEVERITY_KEYWORDS):
        return Severity.MEDIA
    
    # Por defecto, severidad baja
    return Severity.BAJA

def validate_and_clean_pain_points(pain_points: List[Dict]) -> List[Dict]:
    """
    Valida y limpia pain points de la respuesta del LLM.
    
    Args:
        pain_points: Lista de pain points del LLM
    
    Returns:
        Lista validada y limpia
    """
    if not pain_points:
        return []
    
    cleaned_pain_points = []
    
    for pain_point in pain_points:
        if not isinstance(pain_point, dict):
            continue
        
        # Validar campos requeridos
        descripcion = pain_point.get("descripcion", "").strip()
        if not descripcion:
            continue
        
        # Normalizar categoría
        categoria = pain_point.get("categoria", "").lower().strip()
        if not categoria:
            categoria = categorize_pain_point_by_content(descripcion)
        
        # Validar categoría
        valid_categories = [
            PainPointCategory.SERVICIO, PainPointCategory.PRODUCTO, 
            PainPointCategory.PRECIO, PainPointCategory.PROCESO,
            PainPointCategory.COMUNICACION, PainPointCategory.TIEMPO,
            PainPointCategory.CALIDAD, PainPointCategory.PERSONAL
        ]
        
        if categoria not in valid_categories:
            categoria = PainPointCategory.SERVICIO  # default
        
        # Normalizar severidad
        severidad = pain_point.get("severidad", "").lower().strip()
        valid_severities = [Severity.BAJA, Severity.MEDIA, Severity.ALTA, Severity.CRITICA]
        
        if severidad not in valid_severities:
            severidad = determine_severity_from_context(descripcion)
        
        cleaned_pain_point = {
            "descripcion": descripcion,
            "categoria": categoria,
            "severidad": severidad,
            "source": "llm_analysis"
        }
        
        cleaned_pain_points.append(cleaned_pain_point)
    
    return cleaned_pain_points

def categorize_pain_point_by_content(descripcion: str) -> str:
    """
    Categoriza un pain point basado en su contenido.
    
    Args:
        descripcion: Descripción del pain point
    
    Returns:
        Categoría inferida
    """
    descripcion_lower = descripcion.lower()
    
    # Buscar en patrones conocidos
    for category, patterns in PAIN_POINT_PATTERNS.items():
        for pain_type, keywords in patterns.items():
            if any(keyword in descripcion_lower for keyword in keywords):
                return category
    
    # Categorización por palabras clave generales
    if any(word in descripcion_lower for word in ["precio", "caro", "costoso", "cobro"]):
        return PainPointCategory.PRECIO
    elif any(word in descripcion_lower for word in ["producto", "funciona", "feature", "característica"]):
        return PainPointCategory.PRODUCTO
    elif any(word in descripcion_lower for word in ["proceso", "trámite", "procedimiento"]):
        return PainPointCategory.PROCESO
    elif any(word in descripcion_lower for word in ["comunicación", "respuesta", "información"]):
        return PainPointCategory.COMUNICACION
    elif any(word in descripcion_lower for word in ["tiempo", "demora", "espera"]):
        return PainPointCategory.TIEMPO
    elif any(word in descripcion_lower for word in ["calidad", "mal hecho"]):
        return PainPointCategory.CALIDAD
    elif any(word in descripcion_lower for word in ["personal", "empleado", "atención"]):
        return PainPointCategory.PERSONAL
    else:
        return PainPointCategory.SERVICIO

def merge_pain_points(llm_pain_points: List[Dict], text_pain_points: List[Dict]) -> List[Dict]:
    """
    Combina pain points del LLM y análisis de texto.
    
    Args:
        llm_pain_points: Pain points del LLM
        text_pain_points: Pain points del análisis de texto
    
    Returns:
        Lista combinada sin duplicados
    """
    all_pain_points = []
    seen_descriptions = set()
    
    # Priorizar pain points del LLM
    for pain_point in llm_pain_points:
        desc_key = pain_point.get("descripcion", "").lower().strip()
        if desc_key and desc_key not in seen_descriptions:
            all_pain_points.append(pain_point)
            seen_descriptions.add(desc_key)
    
    # Agregar pain points únicos del análisis de texto
    for pain_point in text_pain_points:
        desc_key = pain_point.get("descripcion", "").lower().strip()
        if desc_key and desc_key not in seen_descriptions:
            # Verificar si es similar a alguno existente
            is_similar = any(
                calculate_similarity(desc_key, existing.get("descripcion", "").lower()) > 0.7
                for existing in all_pain_points
            )
            
            if not is_similar:
                all_pain_points.append(pain_point)
                seen_descriptions.add(desc_key)
    
    return all_pain_points[:5]  # Máximo 5 como dice el blueprint

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calcula similaridad básica entre dos textos.
    
    Args:
        text1: Primer texto
        text2: Segundo texto
    
    Returns:
        Score de similaridad (0-1)
    """
    if not text1 or not text2:
        return 0.0
    
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    intersection = words1 & words2
    union = words1 | words2
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)

def calculate_pain_point_impact(pain_point: Dict, emotions: Dict[str, float]) -> float:
    """
    Calcula el impacto de un pain point basado en severidad, categoría y emociones.
    
    Args:
        pain_point: Pain point a evaluar
        emotions: Emociones del comentario
    
    Returns:
        Score de impacto (0-1)
    """
    # Pesos por severidad
    severity_weights = {
        Severity.BAJA: 0.3,
        Severity.MEDIA: 0.6,
        Severity.ALTA: 0.8,
        Severity.CRITICA: 1.0
    }
    
    # Pesos por categoría (importancia para el negocio)
    category_weights = {
        PainPointCategory.SERVICIO: 0.9,
        PainPointCategory.PRODUCTO: 0.8,
        PainPointCategory.PRECIO: 0.7,
        PainPointCategory.CALIDAD: 0.8,
        PainPointCategory.PROCESO: 0.6,
        PainPointCategory.COMUNICACION: 0.7,
        PainPointCategory.TIEMPO: 0.5,
        PainPointCategory.PERSONAL: 0.6
    }
    
    severidad = pain_point.get("severidad", Severity.MEDIA)
    categoria = pain_point.get("categoria", PainPointCategory.SERVICIO)
    
    # Calcular impacto base
    severity_score = severity_weights.get(severidad, 0.6)
    category_score = category_weights.get(categoria, 0.6)
    
    # Ajustar con emociones negativas relacionadas
    emotion_multiplier = 1.0
    negative_emotions = ["enojo", "frustracion", "decepcion", "desagrado"]
    
    total_negative_emotion = sum(emotions.get(emotion, 0.0) for emotion in negative_emotions)
    if total_negative_emotion > 0:
        emotion_multiplier = 1.0 + (total_negative_emotion * 0.5)  # Aumentar hasta 50%
    
    # Combinar factores
    impact_score = (severity_score * 0.5) + (category_score * 0.3)
    impact_score *= min(emotion_multiplier, 1.5)  # Cap at 1.5x
    
    return min(1.0, impact_score)

def process_single_pain_point_analysis(comment_result: Dict) -> Dict:
    """
    Procesa análisis de pain points para un solo comentario.
    
    Args:
        comment_result: Resultado del análisis del comentario
    
    Returns:
        Resultado enriquecido con análisis de pain points
    """
    comment = comment_result.get("comentario", "")
    emotions = comment_result.get("emociones", {})
    llm_pain_points = comment_result.get("pain_points", [])
    
    # Limpiar pain points del LLM
    cleaned_llm_pain_points = validate_and_clean_pain_points(llm_pain_points)
    
    # Detectar pain points adicionales del texto
    text_pain_points = detect_pain_points_from_text(comment)
    
    # Combinar y deduplicar
    final_pain_points = merge_pain_points(cleaned_llm_pain_points, text_pain_points)
    
    # Calcular impacto para cada pain point
    enriched_pain_points = []
    for pain_point in final_pain_points:
        impact_score = calculate_pain_point_impact(pain_point, emotions)
        
        enriched_pain_point = pain_point.copy()
        enriched_pain_point["impact_score"] = impact_score
        
        enriched_pain_points.append(enriched_pain_point)
    
    # Ordenar por impacto (mayor a menor)
    enriched_pain_points.sort(key=lambda x: x.get("impact_score", 0), reverse=True)
    
    return enriched_pain_points

def extract_pain_points(batch_results: List[Dict]) -> List[Dict]:
    """
    Extrae, categoriza y rankea pain points para un lote de comentarios.
    
    Args:
        batch_results: Lista de resultados de análisis
    
    Returns:
        Lista enriquecida con análisis detallado de pain points
    """
    enriched_results = []
    
    for result in batch_results:
        try:
            # Procesar pain points
            enriched_pain_points = process_single_pain_point_analysis(result)
            
            # Enriquecer resultado original
            enriched_result = result.copy()
            enriched_result.update({
                "pain_points": enriched_pain_points,  # pain points enriquecidos
                "pain_points_metadata": {
                    "total_pain_points": len(enriched_pain_points),
                    "high_impact_count": len([p for p in enriched_pain_points if p.get("impact_score", 0) > 0.7]),
                    "top_category": enriched_pain_points[0].get("categoria") if enriched_pain_points else None,
                    "max_impact_score": max([p.get("impact_score", 0) for p in enriched_pain_points], default=0.0)
                }
            })
            
            enriched_results.append(enriched_result)
            
        except Exception as e:
            logger.error(f"Error processing pain points analysis for comment: {e}")
            # En caso de error, mantener resultado original
            enriched_results.append(result)
    
    logger.info(f"Processed pain points analysis for {len(enriched_results)} comments")
    return enriched_results

def aggregate_pain_points_insights(results: List[Dict]) -> Dict[str, Any]:
    """
    Agrega insights de pain points a nivel de dataset.
    
    Args:
        results: Lista de resultados con análisis de pain points
    
    Returns:
        Diccionario con insights agregados de pain points
    """
    if not results:
        return {}
    
    # Recopilar todos los pain points
    all_pain_points = []
    category_counts = defaultdict(int)
    severity_counts = defaultdict(int)
    impact_scores = []
    
    for result in results:
        pain_points = result.get("pain_points", [])
        
        for pain_point in pain_points:
            if isinstance(pain_point, dict):
                all_pain_points.append(pain_point)
                
                categoria = pain_point.get("categoria", "unknown")
                severidad = pain_point.get("severidad", "unknown")
                impact_score = pain_point.get("impact_score", 0.0)
                
                category_counts[categoria] += 1
                severity_counts[severidad] += 1
                impact_scores.append(impact_score)
    
    if not all_pain_points:
        return {
            "total_pain_points": 0,
            "avg_pain_points_per_comment": 0,
            "category_distribution": {},
            "severity_distribution": {},
            "top_pain_points": []
        }
    
    # Calcular métricas agregadas
    total_pain_points = len(all_pain_points)
    avg_pain_points_per_comment = total_pain_points / len(results)
    avg_impact_score = sum(impact_scores) / len(impact_scores) if impact_scores else 0.0
    
    # Top pain points por descripción similar
    pain_point_descriptions = [p.get("descripcion", "") for p in all_pain_points]
    description_counter = Counter(pain_point_descriptions)
    
    top_pain_points = [
        {
            "descripcion": desc,
            "frecuencia": count,
            "porcentaje": round((count / total_pain_points) * 100, 2)
        }
        for desc, count in description_counter.most_common(10)
        if desc.strip()
    ]
    
    return {
        "total_pain_points": total_pain_points,
        "avg_pain_points_per_comment": round(avg_pain_points_per_comment, 2),
        "avg_impact_score": round(avg_impact_score, 3),
        "category_distribution": dict(category_counts),
        "severity_distribution": dict(severity_counts),
        "category_percentages": {
            cat: round((count / total_pain_points) * 100, 2)
            for cat, count in category_counts.items()
        },
        "high_impact_pain_points": len([s for s in impact_scores if s > 0.7]),
        "top_pain_points": top_pain_points,
        "most_problematic_category": max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
    }
