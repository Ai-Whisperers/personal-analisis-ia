# Seguridad y Manejo de Secretos

## Configuración de Secrets

### Implementación Actual

El sistema usa el patrón recomendado por Streamlit para manejo seguro de secrets:

```python
# config.py - Implementación real
def get_openai_api_key() -> str:
    """Get OpenAI API key from Streamlit secrets or environment variables"""
    try:
        # Streamlit Cloud (recomendado)
        if hasattr(st, 'secrets') and "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
        return st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        # Fallback para desarrollo local
        return os.environ.get("OPENAI_API_KEY", "")

def get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit secrets with fallback to environment"""
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
        return st.secrets.get(key, os.environ.get(key, default))
    except Exception:
        return os.environ.get(key, default)
```

### Jerarquía de Configuración

1. **Streamlit Cloud Secrets** (producción)
2. **Archivo `.streamlit/secrets.toml`** (desarrollo local)
3. **Variables de entorno** (fallback)
4. **Valores por defecto** (último recurso)

## Configuración por Entorno

### 1. **Desarrollo Local**

```bash
# Crear archivo de secrets (NO versionar)
mkdir -p .streamlit
cat > .streamlit/secrets.toml << 'EOF'
# OpenAI Configuration
OPENAI_API_KEY = "sk-..."

# Model Configuration  
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS_PER_CALL = "12000"

# Performance Configuration
MAX_BATCH_SIZE = "100"
MAX_WORKERS = "12"

# Logging
LOG_LEVEL = "DEBUG"
EOF
```

### 2. **Streamlit Cloud**

En el dashboard de Streamlit Cloud → **Settings** → **Secrets**:

```toml
# Secrets para producción
OPENAI_API_KEY = "sk-..."
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS_PER_CALL = "12000"
MAX_BATCH_SIZE = "100"
MAX_WORKERS = "12"
LOG_LEVEL = "INFO"
```

### 3. **Docker/Container**

```bash
# Variables de entorno en container
docker run -e OPENAI_API_KEY=sk-... \
           -e MODEL_NAME=gpt-4o-mini \
           -e LOG_LEVEL=INFO \
           mi-app
```

## Seguridad de API Keys

### Mejores Prácticas Implementadas

#### 1. **Nunca Hardcodear Secrets**
```python
# ❌ PROHIBIDO
OPENAI_API_KEY = "sk-..."  # Nunca en código

# ✅ CORRECTO  
api_key = get_openai_api_key()  # Desde secrets
```

#### 2. **Validación de API Keys**
```python
# config.py - Implementación actual
def is_mock_mode() -> bool:
    """Check if running in mock mode (no API key or mock key)"""
    api_key = get_openai_api_key()
    return (not api_key or 
            api_key in ["", "your_openai_api_key_here", "mock", "test"] or 
            not FEATURE_FLAGS.get("enable_mock_mode", True))
```

#### 3. **Fallback Seguro**
```python
# core/ai_engine/api_call.py - Comportamiento real
if not self.api_key or is_mock_mode():
    logger.info("Using mock mode - no real API calls")
    return self._generate_mock_response(comments)
```

### Rotación de API Keys

#### Proceso Recomendado:
1. **Generar nueva key** en OpenAI dashboard
2. **Actualizar secrets** en Streamlit Cloud  
3. **Verificar funcionamiento** con nueva key
4. **Revocar key anterior** en OpenAI
5. **Actualizar desarrollo local**

#### Script de Verificación:
```python
# test_api_key.py
from config import get_openai_api_key, is_mock_mode
from core.ai_engine.api_call import LLMApiClient

def test_api_key():
    api_key = get_openai_api_key()
    print(f"API Key present: {bool(api_key)}")
    print(f"Mock mode: {is_mock_mode()}")
    
    if not is_mock_mode():
        client = LLMApiClient(api_key)
        # Test simple call
        response = client.test_connection()
        print(f"API Connection: {'✅ OK' if response else '❌ Failed'}")

if __name__ == "__main__":
    test_api_key()
```

## Logs y Auditoría

### Logging Seguro

```python
# utils/logging_helpers.py - NO loggear secrets
def mask_sensitive_data(data: str) -> str:
    """Mask sensitive information in logs"""
    # Mask API keys
    data = re.sub(r'sk-[a-zA-Z0-9]{48}', 'sk-***MASKED***', data)
    # Mask other sensitive patterns
    return data

# Uso correcto en logs
logger.info(f"API call with key: {mask_sensitive_data(api_key)}")
```

### Auditoría de Acceso

```python
# core/ai_engine/api_call.py - Log de uso
def analyze_batch(self, comments: List[str]) -> List[Dict]:
    logger.info(f"Processing batch of {len(comments)} comments")
    logger.info(f"Model: {self.model}, Max tokens: {self.max_tokens}")
    # NO loggear contenido de comentarios completos
```

## Compliance y Privacidad

### Datos Procesados

#### Qué se Procesa:
- Comentarios de clientes (temporalmente)
- Puntuaciones NPS
- Metadata de análisis

#### Qué NO se Almacena:
- API keys en logs
- Contenido completo de comentarios en logs permanentes
- Datos personales identificables

### GDPR Compliance

```python
# core/file_processor/cleaner.py - Limpieza de datos
def anonymize_sensitive_data(df: pd.DataFrame) -> pd.DataFrame:
    """Remove or anonymize sensitive data"""
    # Implementar según requerimientos específicos
    # Ej: emails, teléfonos, nombres propios
    return df
```

### Retención de Datos

- **Archivos temporales**: Eliminados después del procesamiento
- **Resultados exportados**: Almacenados en `local-reports/` (no versionados)
- **Logs**: Rotación automática (5 archivos, 10MB máximo c/u)

## Configuración de Seguridad

### Headers de Seguridad

```toml
# .streamlit/config.toml
[server]
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 50

[browser]
gatherUsageStats = false
```

### Rate Limiting

```python
# core/ai_engine/api_call.py - Configuración actual
RATE_LIMIT_CONFIG = {
    "max_retries": 3,
    "retry_delay": 1,
    "timeout": 30,
    "max_concurrent": 12  # Controlado por MAX_WORKERS
}
```

## Troubleshooting de Seguridad

### Problemas Comunes

#### 1. **API Key No Detectada**
```python
# Debug en streamlit_app.py
if FEATURE_FLAGS.get('enable_debug_mode', False):
    api_key = get_openai_api_key()
    st.write(f"API Key present: {bool(api_key)}")
    st.write(f"Mock mode: {is_mock_mode()}")
```

#### 2. **Permisos de Archivo**
```bash
# Verificar permisos del archivo secrets
ls -la .streamlit/secrets.toml
# Debe ser readable solo por owner
chmod 600 .streamlit/secrets.toml
```

#### 3. **Validar Configuración**
```python
# En config.py - ya implementado
def validate_config() -> bool:
    """Validate configuration consistency"""  
    try:
        # Validaciones de seguridad
        api_key = get_openai_api_key()
        if api_key and api_key.startswith('sk-'):
            logger.info("Valid OpenAI API key format detected")
        return True
    except Exception as e:
        st.error(f"Configuration validation error: {e}")
        return False
```