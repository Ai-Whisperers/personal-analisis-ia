"""
Configuración global del proyecto usando variables de entorno.
Todas las configuraciones se cargan desde .env - NO hay valores hardcodeados.
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Función para obtener variables de entorno con validación
def get_env_var(key: str, default: Any = None, required: bool = False, var_type: type = str) -> Any:
    """
    Obtiene variable de entorno con validación de tipo.
    
    Args:
        key: Nombre de la variable de entorno
        default: Valor por defecto
        required: Si es requerida (lanza error si no existe)
        var_type: Tipo esperado (str, int, float, bool, list)
    
    Returns:
        Valor de la variable convertido al tipo especificado
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Variable de entorno requerida no encontrada: {key}")
    
    if value is None:
        return default
    
    # Convertir tipo
    try:
        if var_type == bool:
            return str(value).lower() in ('true', '1', 'yes', 'on')
        elif var_type == int:
            return int(value)
        elif var_type == float:
            return float(value)
        elif var_type == list:
            return [item.strip() for item in str(value).split(',')]
        else:
            return str(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Error convirtiendo variable {key}={value} a {var_type.__name__}: {e}")

# ==== CONFIGURACIÓN DE EMOCIONES ====
# Lista fija de 16 emociones (no configurable por seguridad)
EMOTIONS_16 = [
    "alegria", "tristeza", "enojo", "miedo", "confianza", "desagrado", 
    "sorpresa", "expectativa", "frustracion", "gratitud", "aprecio", 
    "indiferencia", "decepcion", "entusiasmo", "verguenza", "esperanza"
]

# ==== CONFIGURACIÓN DE IA ====
MODEL_NAME = get_env_var("MODEL_NAME", "gpt-4o-mini")
MAX_BATCH_SIZE = get_env_var("MAX_BATCH_SIZE", 100, var_type=int)
MAX_TOKENS_PER_CALL = get_env_var("MAX_TOKENS_PER_CALL", 12000, var_type=int)
MAX_WORKERS = get_env_var("MAX_WORKERS", 12, var_type=int)

# ==== CONFIGURACIÓN DE IDIOMAS ====
SUPPORTED_LANGS = get_env_var("SUPPORTED_LANGS", ["es", "gn", "en"], var_type=list)
DEFAULT_LANG = get_env_var("DEFAULT_LANG", "es")

# Validar idioma por defecto
if DEFAULT_LANG not in SUPPORTED_LANGS:
    raise ValueError(f"DEFAULT_LANG '{DEFAULT_LANG}' no está en SUPPORTED_LANGS {SUPPORTED_LANGS}")

# Backward compatibility
LANGS = SUPPORTED_LANGS  # Para código existente

# ==== CONFIGURACIÓN DE PERFORMANCE ====
PERFORMANCE_SLA_TARGET_SECONDS = get_env_var("PERFORMANCE_SLA_TARGET_SECONDS", 10, var_type=int)
PERFORMANCE_SLA_PERCENTILE = get_env_var("PERFORMANCE_SLA_PERCENTILE", 50, var_type=int)

# ==== CONFIGURACIÓN DE CACHE ====
ENABLE_CACHE = get_env_var("ENABLE_CACHE", True, var_type=bool)
CACHE_TTL_SECONDS = get_env_var("CACHE_TTL_SECONDS", 3600, var_type=int)

# ==== CONFIGURACIÓN DE LOGGING ====
LOG_LEVEL = get_env_var("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = get_env_var("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# ==== CONFIGURACIÓN DE DESARROLLO ====
DEBUG_MODE = get_env_var("DEBUG_MODE", False, var_type=bool)
MOCK_FALLBACK_ENABLED = get_env_var("MOCK_FALLBACK_ENABLED", True, var_type=bool)

# ==== CONFIGURACIÓN DE SEGURIDAD ====
VALIDATE_INPUT = get_env_var("VALIDATE_INPUT", True, var_type=bool)
SANITIZE_OUTPUTS = get_env_var("SANITIZE_OUTPUTS", True, var_type=bool)
MAX_COMMENT_LENGTH = get_env_var("MAX_COMMENT_LENGTH", 10000, var_type=int)

# ==== VALIDACIONES DE CONFIGURACIÓN ====
def validate_config():
    """Valida que toda la configuración sea coherente."""
    errors = []
    
    # Validar rangos numéricos
    if not (1 <= MAX_BATCH_SIZE <= 1000):
        errors.append(f"MAX_BATCH_SIZE debe estar entre 1 y 1000, actual: {MAX_BATCH_SIZE}")
    
    if not (100 <= MAX_TOKENS_PER_CALL <= 100000):
        errors.append(f"MAX_TOKENS_PER_CALL debe estar entre 100 y 100000, actual: {MAX_TOKENS_PER_CALL}")
    
    if not (1 <= MAX_WORKERS <= 50):
        errors.append(f"MAX_WORKERS debe estar entre 1 y 50, actual: {MAX_WORKERS}")
    
    if not (1000 <= MAX_COMMENT_LENGTH <= 100000):
        errors.append(f"MAX_COMMENT_LENGTH debe estar entre 1000 y 100000, actual: {MAX_COMMENT_LENGTH}")
    
    # Validar idiomas
    valid_langs = ["es", "en", "gn", "pt", "fr"]  # Idiomas soportados
    invalid_langs = [lang for lang in SUPPORTED_LANGS if lang not in valid_langs]
    if invalid_langs:
        errors.append(f"Idiomas no válidos en SUPPORTED_LANGS: {invalid_langs}")
    
    # Validar log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if LOG_LEVEL not in valid_log_levels:
        errors.append(f"LOG_LEVEL debe ser uno de {valid_log_levels}, actual: {LOG_LEVEL}")
    
    if errors:
        raise ValueError("Errores de configuración:\n" + "\n".join(f"  - {error}" for error in errors))

# Ejecutar validación al importar
validate_config()

# ==== CONFIGURACIÓN DERIVADA (CALCULADA) ====
# Configuración que se calcula a partir de variables base
OPENAI_ENABLED = bool(os.getenv("OPENAI_API_KEY"))
BATCH_PROCESSING_ENABLED = MAX_BATCH_SIZE > 1
PARALLEL_PROCESSING_ENABLED = MAX_WORKERS > 1

# ==== FUNCIÓN DE DIAGNÓSTICO ====
def get_config_summary() -> Dict[str, Any]:
    """Retorna resumen de configuración para debugging (sin secretos)."""
    return {
        "ai_engine": {
            "model_name": MODEL_NAME,
            "max_batch_size": MAX_BATCH_SIZE,
            "max_tokens_per_call": MAX_TOKENS_PER_CALL,
            "max_workers": MAX_WORKERS,
            "openai_enabled": OPENAI_ENABLED
        },
        "languages": {
            "supported": SUPPORTED_LANGS,
            "default": DEFAULT_LANG
        },
        "performance": {
            "sla_target_seconds": PERFORMANCE_SLA_TARGET_SECONDS,
            "sla_percentile": PERFORMANCE_SLA_PERCENTILE
        },
        "features": {
            "cache_enabled": ENABLE_CACHE,
            "debug_mode": DEBUG_MODE,
            "mock_fallback": MOCK_FALLBACK_ENABLED,
            "input_validation": VALIDATE_INPUT,
            "output_sanitization": SANITIZE_OUTPUTS
        },
        "limits": {
            "max_comment_length": MAX_COMMENT_LENGTH,
            "cache_ttl_seconds": CACHE_TTL_SECONDS
        }
    }
