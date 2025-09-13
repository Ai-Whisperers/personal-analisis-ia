# FAQ - Preguntas Frecuentes

## General

### ¿Qué hace el Personal Comment Analyzer?
Analiza comentarios de clientes usando IA para detectar 16 emociones específicas, calcular riesgo de churn, categorizar NPS y identificar pain points. Genera visualizaciones interactivas y reportes exportables.

### ¿Funciona sin API key de OpenAI?
Sí, el sistema tiene un **modo mock** que genera datos simulados realistas para pruebas y demostraciones.

### ¿Qué formato de archivo necesito?
Archivo Excel (.xlsx, .xls) o CSV con las columnas:
- **NPS**: Puntuación 0-10
- **Nota**: Calificación del cliente  
- **Comentario Final**: Texto del comentario a analizar

**ℹ️ Nota**: El sistema maneja automáticamente variaciones en nombres de columnas como "Comentario Final Final", "comentario", "feedback", etc.

### ¿Cuántos comentarios puede procesar?
- **Óptimo**: 800-1200 comentarios (≤10 segundos)
- **Máximo**: 50,000 comentarios
- **Mínimo**: 1 comentario

## Características Técnicas

### ¿Qué son las 16 emociones?
**Positivas (7)**: alegria, confianza, expectativa, gratitud, aprecio, entusiasmo, esperanza  
**Negativas (7)**: tristeza, enojo, miedo, desagrado, frustracion, decepcion, verguenza  
**Neutras (2)**: sorpresa, indiferencia

### ¿Cómo se calculan los porcentajes de emociones?
Cada emoción se mide por comentario (0-1), luego se calcula la media × 100 para obtener el % sobre todos los comentarios.

### ¿Qué es el riesgo de churn?
Probabilidad (0-1) de que el cliente abandone basada en sentiment analysis, keywords negativos y patterns de comportamiento.

## Uso y Operación

### ¿Cómo subo un archivo?
1. Ir a página **"Subir y Analizar Comentarios"**
2. Arrastrar Excel o hacer click en "Browse files"
3. El sistema valida automáticamente las columnas
4. Click **"Iniciar Análisis"**

### ¿Cuánto tarda el análisis?
- **Con API real**: 5-10 segundos para 800-1200 comentarios
- **Modo mock**: 2-3 segundos independiente del tamaño
- **Progreso**: Barra de progreso muestra etapas en tiempo real

### ¿Puedo exportar los resultados?
Sí, en 3 formatos:
- **Excel (.xlsx)**: Datos completos + análisis
- **CSV (.csv)**: Para importar en otras herramientas
- **JSON (.json)**: Para integración API

### ¿Dónde se guardan los exports?
En `local-reports/` (no versionado en Git). Los archivos incluyen timestamp para evitar sobreescritura.

## Configuración

### ¿Cómo configuro mi API key?
**Desarrollo local**: Crear `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "sk-..."
```

**Streamlit Cloud**: Dashboard → Settings → Secrets

### ¿Puedo cambiar el modelo de IA?
Sí, en secrets:
```toml
MODEL_NAME = "gpt-4o-mini"  # Por defecto
# Opciones: gpt-4o-mini, gpt-4, gpt-3.5-turbo
```

### ¿Cómo ajusto el performance?
```toml
MAX_BATCH_SIZE = "100"      # Comentarios por lote
MAX_WORKERS = "12"          # Procesos paralelos
MAX_TOKENS_PER_CALL = "12000"  # Tokens por llamada API
```

## Troubleshooting

### El botón "Iniciar Análisis" da error
**Posibles causas**:
1. **API key inválida**: Verificar en secrets
2. **Archivo mal formateado**: Revisar columnas requeridas
3. **Timeout**: Reducir batch size si dataset es muy grande

**Solución**: Activar modo debug en secrets:
```toml
DEBUG_MODE = true
```

### Los charts no se muestran correctamente
**Causas comunes**:
1. **Sin datos de emociones**: El análisis no completó
2. **Browser cache**: Refrescar página (Ctrl+F5)
3. **JavaScript deshabilitado**: Habilitar JS

### El análisis es muy lento
**Optimizaciones**:
1. **Reducir batch size**: `MAX_BATCH_SIZE = "50"`
2. **Menos workers**: `MAX_WORKERS = "6"`  
3. **Usar modo mock**: Para pruebas rápidas

### Errores de memoria
**En Streamlit Cloud**:
```toml
MAX_BATCH_SIZE = "50"
MAX_WORKERS = "4"
```

**Localmente**:
```bash
# Aumentar memoria disponible
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
```

### No aparecen las emociones en el análisis
**Verificar**:
1. **Análisis completó**: Status debe mostrar "Completado"
2. **Modelo correcto**: Usar gpt-4o-mini o superior
3. **Prompts**: Verificar `core/ai_engine/prompt_templates.py`

## Desarrollo y Customización

### ¿Puedo añadir más emociones?
Sí, modificar `config.py`:
```python
EMOTIONS_16 = [
    "alegria", "tristeza", # ... existentes
    "nueva_emocion"        # añadir aquí
]
```

### ¿Cómo modifico los charts?
Editar `components/ui_components/chart_generator.py`:
```python
def render_emotion_distribution_chart(self, df, chart_type="bar"):
    # Personalizar visualizaciones aquí
```

### ¿Puedo integrar otros LLMs?
Sí, modificar `core/ai_engine/api_call.py`:
```python
class LLMApiClient:
    def __init__(self, api_key, model="gpt-4o-mini", provider="openai"):
        # Añadir soporte para otros providers
```

### ¿Cómo añado nuevos módulos de análisis?
1. Crear `core/ai_engine/nuevo_module.py`
2. Añadir a `engine_controller.py`:
```python
from .nuevo_module import NuevoAnalyzer
# Integrar en pipeline
```

## Performance y Límites

### ¿Cuáles son los límites de OpenAI API?
- **Rate limits**: 3,500 RPM (requests per minute)
- **Token limits**: 1M tokens/día (tier 1)
- **Concurrent**: 12 workers simultáneos máximo

### ¿Cómo optimizo para datasets grandes?
```toml
# Para >5,000 comentarios
MAX_BATCH_SIZE = "200"
MAX_WORKERS = "6"
MAX_TOKENS_PER_CALL = "15000"
```

### ¿Qué hacer si excedo límites de API?
1. **Reducir concurrencia**: `MAX_WORKERS = "3"`
2. **Aumentar delays**: Modificar `RATE_LIMIT_CONFIG` 
3. **Usar tier superior**: Upgrade en OpenAI
4. **Procesar por lotes**: Dividir archivo manualmente

## Seguridad y Privacidad

### ¿Se almacenan mis comentarios?
**No permanentemente**. Los comentarios:
1. Se procesan en memoria
2. Se envían a OpenAI API (según sus términos)
3. Se eliminan archivos temporales al finalizar
4. Solo se guardan resultados agregados en exports

### ¿Es segura mi API key?
Sí:
- Nunca se loggea completa
- Se almacena en secrets encriptados
- No se incluye en código versionado
- Fallback a modo mock si falta

### ¿Cumple con GDPR?
El sistema está diseñado para compliance básico:
- No almacena datos personales permanentemente
- Logs rotan automáticamente  
- Datos sensibles se pueden anonimizar
- **Nota**: Revisar términos de OpenAI para compliance específico

## Integración y API

### ¿Puedo integrar esto en mi sistema?
Sí, usando:
1. **Imports directos**: Usar módulos `core/` en Python
2. **API REST**: Wrapper sobre Streamlit (desarrollo custom)
3. **Batch processing**: Scripts standalone usando `engine_controller.py`

### ¿Hay API REST disponible?
No incluida, pero fácil de implementar:
```python
from core.ai_engine.engine_controller import EngineController

def analyze_comments_api(comments_data):
    controller = EngineController(api_client)
    return controller.run_pipeline(file_path)
```