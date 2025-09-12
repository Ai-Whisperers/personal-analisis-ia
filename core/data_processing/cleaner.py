"""
Módulo de limpieza de datos de comentarios.
Limpia comentarios HTML, caracteres especiales, duplicados y normaliza contenido.
"""

import re
import html
import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
from config import MAX_COMMENT_LENGTH, SANITIZE_OUTPUTS

logger = logging.getLogger(__name__)

@dataclass
class CleaningStats:
    """Estadísticas del proceso de limpieza."""
    total_comments: int
    cleaned_comments: int
    removed_duplicates: int
    removed_empty: int
    removed_too_long: int
    removed_spam: int
    html_cleaned: int
    special_chars_cleaned: int

# Patrones de spam y contenido no deseado
SPAM_PATTERNS = [
    r'\b(click here|clickea aquí|haz click)\b',
    r'\b(buy now|compra ahora|oferta limitada)\b',
    r'\b(free money|dinero gratis|gana dinero)\b',
    r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)',
    r'\b(bitcoin|crypto|cryptocurrency)\b.*\b(invest|inversión|trading)\b',
    r'(\w)\1{4,}',  # Caracteres repetidos (aaaaa)
]

# Caracteres especiales a limpiar/normalizar
SPECIAL_CHAR_REPLACEMENTS = {
    # Espacios especiales
    '\u00A0': ' ',      # Non-breaking space
    '\u2000': ' ',      # En quad
    '\u2001': ' ',      # Em quad
    '\u2002': ' ',      # En space
    '\u2003': ' ',      # Em space
    '\u2009': ' ',      # Thin space
    '\u200A': ' ',      # Hair space
    '\u200B': '',       # Zero width space
    '\u200C': '',       # Zero width non-joiner
    '\u200D': '',       # Zero width joiner
    '\u2060': '',       # Word joiner
    '\uFEFF': '',       # Zero width no-break space
    
    # Comillas especiales
    '\u201C': '"',      # Left double quotation mark
    '\u201D': '"',      # Right double quotation mark
    '\u2018': "'",      # Left single quotation mark  
    '\u2019': "'",      # Right single quotation mark
    '\u00AB': '"',      # Left-pointing double angle quotation mark
    '\u00BB': '"',      # Right-pointing double angle quotation mark
    
    # Guiones especiales
    '\u2013': '-',      # En dash
    '\u2014': '-',      # Em dash
    '\u2015': '-',      # Horizontal bar
    
    # Puntos especiales
    '\u2026': '...',    # Horizontal ellipsis
    '\u2022': '•',      # Bullet
    '\u2023': '▸',      # Triangular bullet
}

def remove_html_tags(text: str) -> str:
    """
    Remueve tags HTML y decodifica entidades HTML.
    
    Args:
        text: Texto con posibles tags HTML
        
    Returns:
        Texto limpio sin HTML
    """
    if not text:
        return ""
    
    # Decodificar entidades HTML primero
    text = html.unescape(text)
    
    # Remover tags HTML
    clean_text = re.sub(r'<[^>]+>', ' ', text)
    
    # Remover comentarios HTML
    clean_text = re.sub(r'<!--.*?-->', '', clean_text, flags=re.DOTALL)
    
    # Normalizar espacios
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text

def normalize_special_characters(text: str) -> str:
    """
    Normaliza caracteres especiales a equivalentes estándar.
    
    Args:
        text: Texto con caracteres especiales
        
    Returns:
        Texto normalizado
    """
    if not text:
        return ""
    
    # Aplicar reemplazos de caracteres especiales
    for special_char, replacement in SPECIAL_CHAR_REPLACEMENTS.items():
        text = text.replace(special_char, replacement)
    
    # Normalizar múltiples espacios
    text = re.sub(r'\s+', ' ', text)
    
    # Normalizar múltiples puntos/comas
    text = re.sub(r'\.{4,}', '...', text)
    text = re.sub(r',{2,}', ',', text)
    
    return text.strip()

def remove_excess_whitespace(text: str) -> str:
    """
    Remueve espacios en blanco excesivos.
    
    Args:
        text: Texto con espacios excesivos
        
    Returns:
        Texto con espacios normalizados
    """
    if not text:
        return ""
    
    # Remover espacios al inicio y final
    text = text.strip()
    
    # Normalizar espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    
    # Remover espacios antes de puntuación
    text = re.sub(r'\s+([,.;:!?])', r'\1', text)
    
    # Asegurar espacio después de puntuación
    text = re.sub(r'([,.;:!?])([^\s\d])', r'\1 \2', text)
    
    return text

def detect_spam_content(text: str) -> bool:
    """
    Detecta si el comentario contiene spam o contenido no deseado.
    
    Args:
        text: Texto a analizar
        
    Returns:
        True si es spam, False en caso contrario
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Verificar patrones de spam
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    
    # Verificar si es demasiado repetitivo
    words = text_lower.split()
    if len(words) > 5:
        word_counts = Counter(words)
        most_common_word_count = word_counts.most_common(1)[0][1]
        if most_common_word_count > len(words) * 0.5:  # Más del 50% es la misma palabra
            return True
    
    # Verificar proporción de caracteres especiales vs texto
    special_chars = sum(1 for char in text if not char.isalnum() and not char.isspace())
    total_chars = len(text)
    
    if total_chars > 0 and special_chars / total_chars > 0.5:  # Más del 50% caracteres especiales
        return True
    
    return False

def is_meaningful_comment(text: str, min_words: int = 2) -> bool:
    """
    Determina si un comentario tiene contenido significativo.
    
    Args:
        text: Texto a evaluar
        min_words: Número mínimo de palabras significativas
        
    Returns:
        True si es significativo, False en caso contrario
    """
    if not text or len(text.strip()) < 3:
        return False
    
    # Remover puntuación y contar palabras significativas
    words = re.findall(r'\b\w{2,}\b', text.lower())  # Palabras de 2+ caracteres
    
    # Filtrar palabras muy comunes que por sí solas no son significativas
    filler_words = {'el', 'la', 'en', 'de', 'que', 'y', 'a', 'es', 'se', 'no', 'te', 'lo', 'le',
                   'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'un', 'una',
                   'the', 'is', 'at', 'of', 'on', 'and', 'or', 'but', 'in', 'to', 'it', 'be'}
    
    meaningful_words = [word for word in words if word not in filler_words and len(word) >= 3]
    
    return len(meaningful_words) >= min_words

def sanitize_comment(comment: str) -> str:
    """
    Sanitiza un comentario individual aplicando todas las limpiezas.
    
    Args:
        comment: Comentario a limpiar
        
    Returns:
        Comentario limpio y sanitizado
    """
    if not comment:
        return ""
    
    # Aplicar todas las limpiezas en orden
    clean_comment = comment
    
    # 1. Remover HTML
    clean_comment = remove_html_tags(clean_comment)
    
    # 2. Normalizar caracteres especiales
    clean_comment = normalize_special_characters(clean_comment)
    
    # 3. Normalizar espacios
    clean_comment = remove_excess_whitespace(clean_comment)
    
    # 4. Truncar si es muy largo
    if len(clean_comment) > MAX_COMMENT_LENGTH:
        clean_comment = clean_comment[:MAX_COMMENT_LENGTH].rsplit(' ', 1)[0] + '...'
    
    return clean_comment.strip()

def detect_duplicates(comments: List[str], similarity_threshold: float = 0.9) -> Set[int]:
    """
    Detecta comentarios duplicados o muy similares.
    
    Args:
        comments: Lista de comentarios
        similarity_threshold: Umbral de similaridad (0-1)
        
    Returns:
        Set de índices de comentarios a remover
    """
    duplicates_to_remove = set()
    
    for i in range(len(comments)):
        if i in duplicates_to_remove:
            continue
            
        comment_i = comments[i].lower().strip()
        if not comment_i:
            continue
            
        for j in range(i + 1, len(comments)):
            if j in duplicates_to_remove:
                continue
                
            comment_j = comments[j].lower().strip()
            if not comment_j:
                continue
            
            # Calcular similaridad simple (Jaccard)
            words_i = set(comment_i.split())
            words_j = set(comment_j.split())
            
            if len(words_i | words_j) > 0:
                similarity = len(words_i & words_j) / len(words_i | words_j)
                
                if similarity >= similarity_threshold:
                    # Mantener el comentario más largo/completo
                    if len(comments[j]) > len(comments[i]):
                        duplicates_to_remove.add(i)
                        break
                    else:
                        duplicates_to_remove.add(j)
    
    return duplicates_to_remove

def clean_comments_batch(comments: List[str], remove_duplicates: bool = True, 
                        remove_spam: bool = True) -> Tuple[List[str], CleaningStats]:
    """
    Limpia un lote de comentarios aplicando todas las validaciones y limpiezas.
    
    Args:
        comments: Lista de comentarios a limpiar
        remove_duplicates: Si remover duplicados
        remove_spam: Si remover spam
        
    Returns:
        Tupla (comentarios_limpios, estadísticas)
    """
    if not comments:
        return [], CleaningStats(0, 0, 0, 0, 0, 0, 0, 0)
    
    logger.info(f"Iniciando limpieza de {len(comments)} comentarios")
    
    stats = CleaningStats(
        total_comments=len(comments),
        cleaned_comments=0,
        removed_duplicates=0,
        removed_empty=0,
        removed_too_long=0,
        removed_spam=0,
        html_cleaned=0,
        special_chars_cleaned=0
    )
    
    cleaned_comments = []
    indices_to_remove = set()
    
    # Paso 1: Limpiar cada comentario individualmente
    for i, comment in enumerate(comments):
        if not comment:
            indices_to_remove.add(i)
            stats.removed_empty += 1
            continue
        
        original_comment = comment
        
        # Detectar HTML antes de limpieza
        if '<' in comment and '>' in comment:
            stats.html_cleaned += 1
        
        # Detectar caracteres especiales antes de limpieza  
        if any(char in comment for char in SPECIAL_CHAR_REPLACEMENTS):
            stats.special_chars_cleaned += 1
        
        # Aplicar limpieza
        clean_comment = sanitize_comment(comment)
        
        # Verificar si queda contenido meaningful
        if not is_meaningful_comment(clean_comment):
            indices_to_remove.add(i)
            stats.removed_empty += 1
            continue
        
        # Verificar longitud después de limpieza
        if len(clean_comment) > MAX_COMMENT_LENGTH:
            indices_to_remove.add(i)
            stats.removed_too_long += 1
            continue
        
        # Detectar spam
        if remove_spam and detect_spam_content(clean_comment):
            indices_to_remove.add(i)
            stats.removed_spam += 1
            continue
        
        cleaned_comments.append(clean_comment)
    
    # Paso 2: Detectar y remover duplicados
    if remove_duplicates and cleaned_comments:
        duplicate_indices = detect_duplicates(cleaned_comments)
        
        # Remover duplicados (en orden inverso para mantener índices)
        for idx in sorted(duplicate_indices, reverse=True):
            cleaned_comments.pop(idx)
            stats.removed_duplicates += 1
    
    stats.cleaned_comments = len(cleaned_comments)
    
    logger.info(f"Limpieza completada: {stats.cleaned_comments}/{stats.total_comments} comentarios conservados")
    
    if SANITIZE_OUTPUTS:
        # Log de estadísticas detalladas
        logger.info(f"Estadísticas de limpieza: "
                   f"HTML limpiado: {stats.html_cleaned}, "
                   f"Caracteres especiales: {stats.special_chars_cleaned}, "
                   f"Spam removido: {stats.removed_spam}, "
                   f"Duplicados removidos: {stats.removed_duplicates}")
    
    return cleaned_comments, stats

def get_cleaning_report(stats: CleaningStats) -> Dict[str, any]:
    """
    Genera reporte detallado de limpieza.
    
    Args:
        stats: Estadísticas de limpieza
        
    Returns:
        Diccionario con reporte detallado
    """
    total = stats.total_comments
    if total == 0:
        return {"error": "No comments to analyze"}
    
    return {
        "summary": {
            "total_input": total,
            "total_output": stats.cleaned_comments,
            "retention_rate": round((stats.cleaned_comments / total) * 100, 2)
        },
        "removed": {
            "empty_comments": stats.removed_empty,
            "too_long": stats.removed_too_long,  
            "duplicates": stats.removed_duplicates,
            "spam": stats.removed_spam,
            "total_removed": total - stats.cleaned_comments
        },
        "cleaning_applied": {
            "html_cleaned": stats.html_cleaned,
            "special_chars_normalized": stats.special_chars_cleaned
        },
        "percentages": {
            "empty_removed": round((stats.removed_empty / total) * 100, 2),
            "duplicates_removed": round((stats.removed_duplicates / total) * 100, 2),
            "spam_removed": round((stats.removed_spam / total) * 100, 2),
            "html_found": round((stats.html_cleaned / total) * 100, 2)
        }
    }