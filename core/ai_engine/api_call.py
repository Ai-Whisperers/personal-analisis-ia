"""
API integration para análisis de comentarios con OpenAI.
Implementa concurrencia paralela, retry logic y mock fallback.
"""

import os
import time
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from .prompt_templates import build_analysis_prompt, JSON_RESPONSE_TEMPLATE
from config import MODEL_NAME, MAX_TOKENS_PER_CALL, MAX_BATCH_SIZE, EMOTIONS_16

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de retry
@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0

# Configuración de concurrencia
MAX_WORKERS = min(12, os.cpu_count() or 4)

def _mock_response_for_batch(comments: List[str]) -> List[Dict]:
    """
    Genera respuesta mock determinista para testing sin API key.
    """
    results = []
    for comment in comments:
        # Simular análisis basado en longitud y palabras clave
        text_lower = comment.lower()
        base_emotion = 0.1 + min(0.8, len(comment) / 2000.0)
        
        # Detectar emociones básicas por palabras clave
        emotions = {emotion: 0.05 for emotion in EMOTIONS_16}
        
        if any(word in text_lower for word in ["bueno", "excelente", "fantástico", "perfecto"]):
            emotions.update({"alegria": 0.8, "confianza": 0.6, "aprecio": 0.7})
        elif any(word in text_lower for word in ["malo", "terrible", "horrible", "pésimo"]):
            emotions.update({"enojo": 0.7, "frustracion": 0.8, "desagrado": 0.6})
        elif any(word in text_lower for word in ["triste", "decepcionado", "lamento"]):
            emotions.update({"tristeza": 0.7, "decepcion": 0.6})
        
        # Mock pain points
        pain_points = []
        if "lento" in text_lower or "demora" in text_lower:
            pain_points.append({
                "descripcion": "Lentitud en el servicio",
                "categoria": "proceso",
                "severidad": "media"
            })
        if "caro" in text_lower or "precio" in text_lower:
            pain_points.append({
                "descripcion": "Precios elevados",
                "categoria": "precio", 
                "severidad": "alta"
            })
        
        # Mock churn risk
        churn_risk = min(1.0, base_emotion)
        if any(word in text_lower for word in ["cancelar", "dejar", "cambiar", "otro"]):
            churn_risk = min(1.0, churn_risk + 0.3)
        
        # Mock NPS category
        if base_emotion > 0.7:
            nps_category = "Promotor"
        elif base_emotion < 0.4:
            nps_category = "Detractor"
        else:
            nps_category = "Pasivo"
        
        results.append({
            "comentario": comment,
            "emociones": emotions,
            "pain_points": pain_points,
            "churn_risk": churn_risk,
            "nps_category": nps_category,
            "reasoning": f"Análisis mock basado en longitud: {len(comment)} caracteres"
        })
    
    # Simular latencia de red proporcional al batch
    time.sleep(0.1 * len(comments))
    return results

def _call_openai_with_retry(messages: List[Dict[str, str]], retry_config: RetryConfig = RetryConfig()) -> Optional[str]:
    """
    Realiza llamada a OpenAI con retry logic y manejo de errores.
    """
    try:
        import openai
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        for attempt in range(retry_config.max_retries):
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    max_tokens=MAX_TOKENS_PER_CALL,
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                
                return response.choices[0].message.content
                
            except openai.RateLimitError as e:
                delay = min(
                    retry_config.base_delay * (retry_config.exponential_base ** attempt),
                    retry_config.max_delay
                )
                logger.warning(f"Rate limit hit, waiting {delay}s before retry {attempt + 1}")
                time.sleep(delay)
                
            except openai.APIError as e:
                if attempt == retry_config.max_retries - 1:
                    logger.error(f"OpenAI API error after {retry_config.max_retries} attempts: {e}")
                    return None
                
                delay = retry_config.base_delay * (retry_config.exponential_base ** attempt)
                logger.warning(f"API error, retrying in {delay}s: {e}")
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Unexpected error calling OpenAI: {e}")
                return None
        
        return None
        
    except ImportError:
        logger.error("OpenAI library not installed. Install with: pip install openai")
        return None

def _parse_openai_response(response_text: str, expected_count: int) -> List[Dict]:
    """
    Parsea y valida la respuesta de OpenAI.
    """
    try:
        # Intentar parsear como JSON
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(response_text)
        
        # Validar que sea una lista
        if not isinstance(data, list):
            logger.warning("Response is not a list, wrapping in array")
            data = [data]
        
        # Validar cantidad de elementos
        if len(data) != expected_count:
            logger.warning(f"Expected {expected_count} results, got {len(data)}")
        
        # Validar estructura de cada elemento
        validated_results = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                logger.warning(f"Item {i} is not a dictionary, skipping")
                continue
                
            # Validar campos requeridos
            required_fields = ["comentario", "emociones", "pain_points", "churn_risk", "nps_category"]
            if not all(field in item for field in required_fields):
                logger.warning(f"Item {i} missing required fields, skipping")
                continue
            
            # Validar emociones
            emotions = item.get("emociones", {})
            if not isinstance(emotions, dict):
                logger.warning(f"Item {i} has invalid emotions structure")
                emotions = {emotion: 0.0 for emotion in EMOTIONS_16}
            
            # Asegurar todas las 16 emociones
            for emotion in EMOTIONS_16:
                if emotion not in emotions:
                    emotions[emotion] = 0.0
                # Validar rango 0-1
                emotions[emotion] = max(0.0, min(1.0, float(emotions[emotion])))
            
            # Validar churn_risk
            churn_risk = max(0.0, min(1.0, float(item.get("churn_risk", 0.0))))
            
            # Validar NPS category
            nps_category = item.get("nps_category", "Pasivo")
            if nps_category not in ["Promotor", "Pasivo", "Detractor"]:
                nps_category = "Pasivo"
            
            validated_results.append({
                "comentario": item.get("comentario", ""),
                "emociones": emotions,
                "pain_points": item.get("pain_points", []),
                "churn_risk": churn_risk,
                "nps_category": nps_category,
                "reasoning": item.get("reasoning", "")
            })
        
        return validated_results
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return []
    except Exception as e:
        logger.error(f"Error parsing OpenAI response: {e}")
        return []

def _analyze_single_batch(comments: List[str], lang: str = "es") -> List[Dict]:
    """
    Analiza un solo batch de comentarios.
    """
    # Si no hay API key, usar mock
    if not os.getenv("OPENAI_API_KEY"):
        logger.info(f"No OpenAI API key found, using mock response for {len(comments)} comments")
        return _mock_response_for_batch(comments)
    
    try:
        # Construir prompt
        messages = build_analysis_prompt(comments, lang)
        
        # Llamar a OpenAI
        response_text = _call_openai_with_retry(messages)
        
        if response_text is None:
            logger.warning("OpenAI call failed, falling back to mock")
            return _mock_response_for_batch(comments)
        
        # Parsear respuesta
        results = _parse_openai_response(response_text, len(comments))
        
        if len(results) == 0:
            logger.warning("Failed to parse OpenAI response, falling back to mock")
            return _mock_response_for_batch(comments)
        
        logger.info(f"Successfully analyzed {len(results)} comments via OpenAI")
        return results
        
    except Exception as e:
        logger.error(f"Error in single batch analysis: {e}, falling back to mock")
        return _mock_response_for_batch(comments)

def analyze_batch_via_llm(comments: List[str], lang: str = "es", max_workers: int = MAX_WORKERS) -> List[Dict]:
    """
    Analiza lote de comentarios usando OpenAI con concurrencia paralela.
    
    Args:
        comments: Lista de comentarios a analizar
        lang: Idioma para prompts ("es", "en", "gn")
        max_workers: Número máximo de workers paralelos
    
    Returns:
        Lista de diccionarios con análisis de cada comentario
    """
    if not comments:
        return []
    
    # Dividir en batches
    batches = []
    for i in range(0, len(comments), MAX_BATCH_SIZE):
        batch = comments[i:i + MAX_BATCH_SIZE]
        batches.append(batch)
    
    logger.info(f"Processing {len(comments)} comments in {len(batches)} batches with {max_workers} workers")
    
    # Procesar batches en paralelo
    all_results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todos los batches
        future_to_batch = {
            executor.submit(_analyze_single_batch, batch, lang): i 
            for i, batch in enumerate(batches)
        }
        
        # Recolectar resultados manteniendo el orden
        batch_results = {}
        for future in as_completed(future_to_batch):
            batch_index = future_to_batch[future]
            try:
                result = future.result()
                batch_results[batch_index] = result
                logger.info(f"Completed batch {batch_index + 1}/{len(batches)}")
            except Exception as e:
                logger.error(f"Batch {batch_index} failed: {e}")
                # Usar mock para batch fallido
                batch_results[batch_index] = _mock_response_for_batch(batches[batch_index])
    
    # Combinar resultados en orden
    for i in range(len(batches)):
        if i in batch_results:
            all_results.extend(batch_results[i])
        else:
            logger.error(f"Missing results for batch {i}, using mock")
            all_results.extend(_mock_response_for_batch(batches[i]))
    
    logger.info(f"Analysis completed. Processed {len(all_results)} total comments")
    return all_results
