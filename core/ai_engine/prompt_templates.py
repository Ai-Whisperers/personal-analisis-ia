"""
Prompt templates para análisis multilenguaje de comentarios.
Soporte para ES/GN/EN con 16 emociones, pain points y churn risk.
"""

import json
from typing import Dict, List
from config import EMOTIONS_16, LANGS

# Templates de sistema por idioma
SYSTEM_PROMPTS = {
    "es": """Eres un experto analista de sentimientos y experiencia del cliente. Analiza comentarios en español, guaraní o inglés y proporciona:

1. EMOCIONES (16 categorías, valores 0-1):
   - Positivas: alegria, confianza, expectativa, gratitud, aprecio, entusiasmo, esperanza
   - Negativas: tristeza, enojo, miedo, desagrado, frustracion, decepcion, verguenza
   - Neutras: sorpresa, indiferencia

2. PAIN POINTS: Extrae hasta 5 problemas específicos mencionados, categorizados por área.

3. CHURN RISK: Probabilidad 0-1 de que el cliente abandone el servicio.

4. NPS CATEGORY: Clasifica como "Promotor", "Pasivo" o "Detractor".

Responde únicamente en JSON válido.""",

    "en": """You are an expert sentiment analyst and customer experience specialist. Analyze comments in Spanish, Guarani, or English and provide:

1. EMOTIONS (16 categories, values 0-1):
   - Positive: alegria, confianza, expectativa, gratitud, aprecio, entusiasmo, esperanza
   - Negative: tristeza, enojo, miedo, desagrado, frustracion, decepcion, verguenza
   - Neutral: sorpresa, indiferencia

2. PAIN POINTS: Extract up to 5 specific problems mentioned, categorized by area.

3. CHURN RISK: Probability 0-1 that customer will abandon the service.

4. NPS CATEGORY: Classify as "Promotor", "Pasivo" or "Detractor".

Respond only in valid JSON.""",

    "gn": """Nde analista tembiapokatúva ñe'ẽme ha costumer experiencia-pe. Emongu'e comentario español, guaraní térã inglés-pe ha eme'ẽ:

1. EMOCIONES (16 categoría, valores 0-1):
   - Positivas: alegria, confianza, expectativa, gratitud, aprecio, entusiasmo, esperanza
   - Negativas: tristeza, enojo, miedo, desagrado, frustracion, decepcion, verguenza
   - Neutras: sorpresa, indiferencia

2. PAIN POINTS: Gueraha 5 peve problema específico oñe'ẽva, categorizada área rupive.

3. CHURN RISK: Probabilidad 0-1 kostumer oheja hag̃ua servicio.

4. NPS CATEGORY: Clasificar "Promotor", "Pasivo" térã "Detractor".

Ñembohovái añónte JSON oikóva."""
}

# Template de ejemplo de respuesta JSON
JSON_RESPONSE_TEMPLATE = {
    "comentario": "texto del comentario original",
    "emociones": {emotion: 0.0 for emotion in EMOTIONS_16},
    "pain_points": [
        {
            "descripcion": "problema específico mencionado",
            "categoria": "servicio|producto|proceso|comunicacion|precio",
            "severidad": "alta|media|baja"
        }
    ],
    "churn_risk": 0.0,
    "nps_category": "Promotor|Pasivo|Detractor",
    "reasoning": "breve explicación del análisis"
}

def build_analysis_prompt(comments: List[str], lang: str = "es") -> List[Dict[str, str]]:
    """
    Construye el prompt para análisis de lote de comentarios.
    
    Args:
        comments: Lista de comentarios a analizar
        lang: Idioma del prompt ("es", "en", "gn")
    
    Returns:
        Lista de mensajes para OpenAI Chat API
    """
    if lang not in LANGS:
        lang = "es"  # fallback
    
    # Mensaje de sistema
    system_msg = SYSTEM_PROMPTS[lang]
    
    # Construir mensaje de usuario con batch de comentarios
    user_content = f"""Analiza los siguientes {len(comments)} comentarios y devuelve un array JSON con el análisis de cada uno:

COMENTARIOS:
"""
    
    for i, comment in enumerate(comments, 1):
        user_content += f"{i}. {comment}\n"
    
    user_content += f"""

FORMATO DE RESPUESTA REQUERIDO:
```json
[
  {json.dumps(JSON_RESPONSE_TEMPLATE, ensure_ascii=False, indent=2)}
]
```

IMPORTANTE: 
- Devuelve exactamente {len(comments)} objetos JSON en el array
- Mantén el orden de los comentarios
- Valores de emociones entre 0 y 1 (suma no necesita ser 1)
- Pain points máximo 5 por comentario
- Churn risk entre 0 y 1
- Solo JSON válido, sin explicaciones adicionales
"""

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_content}
    ]

def build_emotion_validation_prompt(emotions_data: Dict, lang: str = "es") -> List[Dict[str, str]]:
    """
    Construye prompt para validar y corregir datos de emociones.
    """
    if lang not in LANGS:
        lang = "es"
    
    validation_prompts = {
        "es": "Valida y corrige si es necesario los siguientes datos de emociones. Asegúrate de que todos los valores estén entre 0 y 1:",
        "en": "Validate and correct if necessary the following emotion data. Ensure all values are between 0 and 1:",
        "gn": "Moañete ha myatyrõ tekotevẽramo ko emoción datos. Ehechauka opaite valor 0 ha 1 mbytépe:"
    }
    
    return [
        {"role": "system", "content": SYSTEM_PROMPTS[lang]},
        {"role": "user", "content": f"{validation_prompts[lang]}\n\n{json.dumps(emotions_data, ensure_ascii=False, indent=2)}"}
    ]

def build_churn_analysis_prompt(comment: str, nps_score: float, lang: str = "es") -> List[Dict[str, str]]:
    """
    Construye prompt especializado para análisis de churn risk.
    """
    if lang not in LANGS:
        lang = "es"
    
    churn_prompts = {
        "es": f"Analiza el riesgo de churn (0-1) basado en este comentario y puntaje NPS {nps_score}. Considera: insatisfacción, intención de cambio, problemas graves mencionados.",
        "en": f"Analyze churn risk (0-1) based on this comment and NPS score {nps_score}. Consider: dissatisfaction, switching intent, serious problems mentioned.",
        "gn": f"Mone'ẽ churn risk (0-1) ko comentario ha NPS puntaje {nps_score} rupive. Hecha: ndovy'ái, moambue potápe, problema tuichavéva."
    }
    
    return [
        {"role": "system", "content": SYSTEM_PROMPTS[lang]},
        {"role": "user", "content": f"{churn_prompts[lang]}\n\nCOMENTARIO: {comment}\n\nDevuelve solo un número entre 0 y 1."}
    ]
