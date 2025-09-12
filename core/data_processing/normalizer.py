"""
Módulo de normalización de datos.
Normaliza texto, encoding, formatos y estructura de datos para análisis consistente.
"""

import re
import unicodedata
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from config import DEFAULT_LANG, SUPPORTED_LANGS

logger = logging.getLogger(__name__)

@dataclass
class NormalizationStats:
    """Estadísticas del proceso de normalización."""
    total_comments: int
    normalized_comments: int
    encoding_fixes: int
    language_detections: int
    format_standardizations: int
    text_normalizations: int

# Mapeos de normalización de texto
ACCENT_NORMALIZATIONS = {
    'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a', 'ā': 'a', 'ă': 'a', 'ą': 'a',
    'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e', 'ē': 'e', 'ĕ': 'e', 'ę': 'e', 'ė': 'e',
    'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i', 'ī': 'i', 'ĭ': 'i', 'į': 'i',
    'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o', 'ō': 'o', 'ŏ': 'o', 'ő': 'o',
    'ú': 'u', 'ù': 'u', 'ü': 'u', 'û': 'u', 'ū': 'u', 'ŭ': 'u', 'ů': 'u', 'ű': 'u', 'ų': 'u',
    'ý': 'y', 'ỳ': 'y', 'ÿ': 'y', 'ŷ': 'y',
    'ñ': 'n', 'ń': 'n', 'ň': 'n', 'ņ': 'n',
    'ç': 'c', 'ć': 'c', 'č': 'c', 'ĉ': 'c', 'ċ': 'c',
    'ß': 'ss', 'đ': 'd', 'ð': 'd', 'ł': 'l', 'ř': 'r', 'ś': 's', 'š': 's', 'ť': 't', 'ž': 'z'
}

# Patrones de idioma (básico)
LANGUAGE_PATTERNS = {
    'es': [
        r'\b(que|con|por|para|desde|hasta|este|esta|muy|más|también|donde|cuando|como|porque)\b',
        r'\b(el|la|los|las|un|una|de|en|y|a|es|se|no|te|lo|le|da|su|son|al|del)\b'
    ],
    'en': [
        r'\b(the|and|or|but|in|on|at|to|for|of|with|by|from|that|this|these|those)\b',
        r'\b(is|are|was|were|have|has|had|do|does|did|will|would|can|could|should|may|might)\b'
    ],
    'gn': [
        r'\b(ha|ndive|ko|pe|rehe|gui|ndi|che|nde|upe|upégui|upévare|hese|hesegui)\b',
        r'\b(oiko|aiko|aime|upei|araka|amo|jey|ko|kuri|pytyvõ|porã|ikatú)\b'
    ]
}

def normalize_unicode(text: str) -> str:
    """
    Normaliza caracteres Unicode a forma estándar.
    
    Args:
        text: Texto con posibles caracteres Unicode no estándar
        
    Returns:
        Texto normalizado
    """
    if not text:
        return ""
    
    # Normalización NFD (Canonical Decomposition)
    normalized = unicodedata.normalize('NFD', text)
    
    # Remover marcas de combinación (acentos)
    # Mantener algunos caracteres importantes del español/guaraní
    result = []
    for char in normalized:
        if unicodedata.category(char) != 'Mn':  # No es marca de combinación
            result.append(char)
        elif char in 'ñÑ':  # Mantener ñ
            result.append(char)
    
    return ''.join(result)

def normalize_text_case(text: str, preserve_proper_nouns: bool = True) -> str:
    """
    Normaliza capitalización manteniendo nombres propios.
    
    Args:
        text: Texto a normalizar
        preserve_proper_nouns: Si preservar nombres propios
        
    Returns:
        Texto con capitalización normalizada
    """
    if not text:
        return ""
    
    # Si no preservar nombres propios, simplemente lowercase
    if not preserve_proper_nouns:
        return text.lower()
    
    # Palabras que probablemente sean nombres propios (empiezan con mayúscula y están en medio de oración)
    sentences = re.split(r'[.!?]+', text)
    normalized_sentences = []
    
    for sentence in sentences:
        words = sentence.strip().split()
        if not words:
            continue
            
        # Primera palabra de oración en title case
        normalized_words = []
        
        for i, word in enumerate(words):
            # Limpiar puntuación para análisis
            clean_word = re.sub(r'[^\w\s]', '', word).strip()
            
            if i == 0:
                # Primera palabra: title case
                normalized_word = word.lower()
                if clean_word:
                    normalized_word = word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper()
            else:
                # Otras palabras: detectar si es nombre propio
                if (len(clean_word) > 2 and 
                    clean_word.istitle() and 
                    not clean_word.lower() in ['que', 'con', 'por', 'para', 'desde', 'hasta', 'este', 'esta']):
                    # Probablemente nombre propio, mantener title case
                    normalized_word = word
                else:
                    normalized_word = word.lower()
            
            normalized_words.append(normalized_word)
        
        normalized_sentences.append(' '.join(normalized_words))
    
    return '. '.join(normalized_sentences).strip()

def detect_language(text: str) -> str:
    """
    Detecta idioma del texto basado en patrones simples.
    
    Args:
        text: Texto a analizar
        
    Returns:
        Código de idioma detectado ("es", "en", "gn") o DEFAULT_LANG
    """
    if not text:
        return DEFAULT_LANG
    
    text_lower = text.lower()
    scores = {}
    
    for lang, patterns in LANGUAGE_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, text_lower))
            score += matches
        
        # Normalizar por longitud de texto
        text_words = len(text_lower.split())
        scores[lang] = score / max(text_words, 1)
    
    # Retornar idioma con mayor score, o default si no hay matches claros
    if not scores or max(scores.values()) < 0.1:
        return DEFAULT_LANG
    
    return max(scores.items(), key=lambda x: x[1])[0]

def normalize_punctuation(text: str) -> str:
    """
    Normaliza puntuación y espacios alrededor de signos.
    
    Args:
        text: Texto con puntuación a normalizar
        
    Returns:
        Texto con puntuación normalizada
    """
    if not text:
        return ""
    
    # Espacios antes de puntuación
    text = re.sub(r'\s+([,.;:!?])', r'\1', text)
    
    # Espacios después de puntuación
    text = re.sub(r'([,.;:!?])([^\s])', r'\1 \2', text)
    
    # Normalizar múltiples signos
    text = re.sub(r'[!]{2,}', '!', text)
    text = re.sub(r'[?]{2,}', '?', text)
    text = re.sub(r'[.]{4,}', '...', text)
    
    # Espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def normalize_numbers_and_dates(text: str) -> str:
    """
    Normaliza formatos de números y fechas.
    
    Args:
        text: Texto con números/fechas a normalizar
        
    Returns:
        Texto con formatos normalizados
    """
    if not text:
        return ""
    
    # Normalizar separadores decimales (coma a punto para consistencia)
    text = re.sub(r'(\d+),(\d{1,2})\b', r'\1.\2', text)
    
    # Normalizar fechas DD/MM/YYYY o DD-MM-YYYY a formato consistente
    text = re.sub(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', r'\1/\2/\3', text)
    
    # Normalizar números de teléfono (quitar espacios y guiones excesivos)
    text = re.sub(r'(\d+)\s*[-\s]\s*(\d+)\s*[-\s]\s*(\d+)', r'\1-\2-\3', text)
    
    return text

def normalize_contractions(text: str, lang: str = None) -> str:
    """
    Normaliza contracciones y formas abreviadas.
    
    Args:
        text: Texto con contracciones
        lang: Idioma específico
        
    Returns:
        Texto con contracciones normalizadas
    """
    if not text:
        return ""
    
    if not lang:
        lang = detect_language(text)
    
    contractions = {}
    
    if lang == 'es':
        contractions = {
            r'\bpa\b': 'para',
            r'\bx\b': 'por',
            r'\bq\b': 'que',
            r'\btb\b': 'también',
            r'\bd\b': 'de',
            r'\bn\b': 'no',
            r'\bk\b': 'que',
            r'\bxq\b': 'porque',
            r'\bmuy\s+bn\b': 'muy bien',
            r'\bbn\b': 'bien'
        }
    elif lang == 'en':
        contractions = {
            r"\bcan't\b": 'cannot',
            r"\bwon't\b": 'will not',
            r"\bn't\b": ' not',
            r"\b'm\b": ' am',
            r"\b're\b": ' are',
            r"\b've\b": ' have',
            r"\b'll\b": ' will',
            r"\b'd\b": ' would'
        }
    
    # Aplicar reemplazos
    for contraction, expansion in contractions.items():
        text = re.sub(contraction, expansion, text, flags=re.IGNORECASE)
    
    return text

def normalize_single_comment(comment: str, target_lang: str = None, 
                           preserve_case: bool = False) -> Tuple[str, Dict[str, Any]]:
    """
    Normaliza un comentario individual con todas las transformaciones.
    
    Args:
        comment: Comentario a normalizar
        target_lang: Idioma objetivo (None para auto-detectar)
        preserve_case: Si preservar capitalización original
        
    Returns:
        Tupla (comentario_normalizado, metadatos)
    """
    if not comment:
        return "", {"detected_language": DEFAULT_LANG, "transformations": []}
    
    original_comment = comment
    transformations = []
    
    # 1. Normalizar Unicode
    if any(ord(char) > 127 for char in comment):
        comment = normalize_unicode(comment)
        transformations.append("unicode_normalized")
    
    # 2. Detectar idioma
    detected_lang = detect_language(comment)
    if not target_lang:
        target_lang = detected_lang
    
    # 3. Normalizar contracciones
    old_comment = comment
    comment = normalize_contractions(comment, target_lang)
    if comment != old_comment:
        transformations.append("contractions_expanded")
    
    # 4. Normalizar puntuación
    old_comment = comment
    comment = normalize_punctuation(comment)
    if comment != old_comment:
        transformations.append("punctuation_normalized")
    
    # 5. Normalizar números y fechas
    old_comment = comment
    comment = normalize_numbers_and_dates(comment)
    if comment != old_comment:
        transformations.append("numbers_normalized")
    
    # 6. Normalizar capitalización
    if not preserve_case:
        old_comment = comment
        comment = normalize_text_case(comment)
        if comment != old_comment:
            transformations.append("case_normalized")
    
    metadata = {
        "detected_language": detected_lang,
        "target_language": target_lang,
        "transformations": transformations,
        "length_change": len(comment) - len(original_comment)
    }
    
    return comment.strip(), metadata

def normalize_comments_batch(comments: List[str], target_lang: str = None, 
                           preserve_case: bool = False) -> Tuple[List[str], NormalizationStats, List[Dict]]:
    """
    Normaliza un lote de comentarios.
    
    Args:
        comments: Lista de comentarios a normalizar
        target_lang: Idioma objetivo (None para auto-detectar cada uno)
        preserve_case: Si preservar capitalización
        
    Returns:
        Tupla (comentarios_normalizados, estadísticas, metadatos_por_comentario)
    """
    if not comments:
        return [], NormalizationStats(0, 0, 0, 0, 0, 0), []
    
    logger.info(f"Iniciando normalización de {len(comments)} comentarios")
    
    normalized_comments = []
    all_metadata = []
    
    stats = NormalizationStats(
        total_comments=len(comments),
        normalized_comments=0,
        encoding_fixes=0,
        language_detections=0,
        format_standardizations=0,
        text_normalizations=0
    )
    
    for comment in comments:
        normalized_comment, metadata = normalize_single_comment(
            comment, target_lang, preserve_case
        )
        
        normalized_comments.append(normalized_comment)
        all_metadata.append(metadata)
        
        # Actualizar estadísticas
        if normalized_comment != comment:
            stats.normalized_comments += 1
        
        if "unicode_normalized" in metadata["transformations"]:
            stats.encoding_fixes += 1
        
        if metadata["detected_language"] != DEFAULT_LANG:
            stats.language_detections += 1
        
        if any(t in metadata["transformations"] for t in ["punctuation_normalized", "numbers_normalized"]):
            stats.format_standardizations += 1
        
        if "case_normalized" in metadata["transformations"]:
            stats.text_normalizations += 1
    
    stats.normalized_comments = len([c for c in normalized_comments if c])
    
    logger.info(f"Normalización completada: {stats.normalized_comments} comentarios procesados")
    
    return normalized_comments, stats, all_metadata

def get_normalization_report(stats: NormalizationStats, metadata_list: List[Dict]) -> Dict[str, Any]:
    """
    Genera reporte de normalización.
    
    Args:
        stats: Estadísticas de normalización
        metadata_list: Lista de metadatos por comentario
        
    Returns:
        Diccionario con reporte detallado
    """
    if stats.total_comments == 0:
        return {"error": "No comments to analyze"}
    
    # Analizar distribución de idiomas
    language_counts = {}
    transformation_counts = {}
    
    for metadata in metadata_list:
        lang = metadata["detected_language"]
        language_counts[lang] = language_counts.get(lang, 0) + 1
        
        for transformation in metadata["transformations"]:
            transformation_counts[transformation] = transformation_counts.get(transformation, 0) + 1
    
    return {
        "summary": {
            "total_comments": stats.total_comments,
            "normalized_comments": stats.normalized_comments,
            "normalization_rate": round((stats.normalized_comments / stats.total_comments) * 100, 2)
        },
        "language_detection": {
            "detected_languages": language_counts,
            "primary_language": max(language_counts.items(), key=lambda x: x[1])[0] if language_counts else DEFAULT_LANG
        },
        "transformations_applied": {
            "encoding_fixes": stats.encoding_fixes,
            "format_standardizations": stats.format_standardizations,  
            "text_normalizations": stats.text_normalizations,
            "transformation_details": transformation_counts
        },
        "percentages": {
            "encoding_fixed": round((stats.encoding_fixes / stats.total_comments) * 100, 2),
            "format_standardized": round((stats.format_standardizations / stats.total_comments) * 100, 2),
            "text_normalized": round((stats.text_normalizations / stats.total_comments) * 100, 2)
        }
    }