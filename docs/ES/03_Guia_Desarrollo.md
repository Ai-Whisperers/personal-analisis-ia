# Guía de Desarrollo

## Estándares del Código

### 1. **Límites por Archivo** ✅
- **≤480 líneas por archivo** (máximo estricto)
- **Estado actual**: Todos los archivos cumplen (verificado 2025-09-12)
- Si un archivo excede, debe dividirse en módulos
- Usar herramientas como `wc -l *.py` para verificar

**Archivos principales mantenidos bajo límite:**
- `components/ui_components/chart_generator.py`: < 400 líneas ✅
- `pages/2_Subir.py`: < 400 líneas ✅  
- `utils/streamlit_helpers.py`: Expandido con CSS resolver pero mantenido bajo límite ✅
- `core/file_processor/cleaner.py`: Mejorado con column mapping ✅

### 2. **Imports Cíclicos**
```python
# ❌ EVITAR
from components.ui_components import chart_generator
from core.ai_engine import engine_controller  # que luego importa components

# ✅ CORRECTO  
from core.ai_engine import engine_controller
# UI components solo importan desde core, nunca al revés
```

### 3. **Separación UI/Core**
```python
# ❌ PROHIBIDO en core/
import streamlit as st

# ✅ CORRECTO en core/
def analyze_emotions(data: Dict) -> Dict[str, float]:
    # Lógica pura, sin dependencias UI
    return results

# ✅ UI layer puede importar core
from core.ai_engine import emotion_module
```

## Estructura de Desarrollo

### Setup Inicial
```bash
# Clone y setup
git clone https://github.com/Ai-Whisperers/personal-analisis-ia
cd Comment-Analizer-Personal

# Crear virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar secrets (crear .streamlit/secrets.toml)
echo 'OPENAI_API_KEY = "tu_api_key_aqui"' > .streamlit/secrets.toml
```

### Variables de Entorno
```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "sk-..."
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS_PER_CALL = "12000"
MAX_BATCH_SIZE = "100"
MAX_WORKERS = "12"
LOG_LEVEL = "INFO"
```

## Flujo de Desarrollo

### 1. **Feature Development**
```bash
# Crear rama
git checkout -b feature/nueva-funcionalidad

# Desarrollar siguiendo límites
# - Máximo 480 líneas por archivo
# - No imports cíclicos
# - Separación UI/Core estricta

# Verificar límites
find . -name "*.py" -exec wc -l {} + | sort -n
```

### 2. **Testing Local**
```bash
# Ejecutar aplicación
streamlit run streamlit_app.py

# Verificar en localhost:8501
# Probar con archivos Excel de prueba
```

### 3. **Code Review Checklist**

#### Arquitectura
- [ ] Separación UI/Core respetada
- [ ] No imports cíclicos
- [ ] Archivos ≤480 líneas
- [ ] Configuración en `config.py`

#### Performance  
- [ ] Uso de ThreadPoolExecutor para concurrencia
- [ ] Batches ≤100 comentarios
- [ ] Timeouts configurados
- [ ] Logging apropiado

#### UI/UX
- [ ] Solo texto plano (no emojis/símbolos)
- [ ] Manejo de errores visible
- [ ] Progress tracking funcional
- [ ] Export funciona correctamente

## Módulos Principales

### 1. **Core Modules**
```python
# core/ai_engine/engine_controller.py
class EngineController:
    def run_pipeline(self, file_path: str) -> pd.DataFrame:
        # Orquesta todo el flujo
        # Debe ser independiente de UI
        pass
```

### 2. **UI Components**  
```python
# components/ui_components/chart_generator.py
def render_emotion_distribution_chart(df: pd.DataFrame):
    # Muestra % de cada emoción individual
    # Usa Plotly para charts interactivos
    pass
```

### 3. **Configuration**
```python
# config.py - Toda la configuración centralizada
EMOTIONS_16 = [...]  # Las 16 emociones exactas
BATCH_CONFIG = {...}  # Configuración de batching
SLA_TARGETS = {...}   # Objetivos de performance
```

## Debugging

### 1. **Logging**
```python
from utils.logging_helpers import get_logger
logger = get_logger(__name__)

# Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.info("Pipeline started")
logger.error(f"Failed to process: {error}")
```

### 2. **Performance Monitoring**
```python  
from utils.performance_monitor import monitor

@monitor.measure_time("custom_function", "custom_category")
def my_function():
    # Automáticamente mide tiempo de ejecución
    # Compara contra SLA targets
    pass
```

### 3. **Debug Mode**
```toml
# .streamlit/secrets.toml
DEBUG_MODE = true
```

```python
# En streamlit_app.py se mostrará debug info
if FEATURE_FLAGS.get('enable_debug_mode', False):
    st.expander("Debug Information")
```

## Deployment

### Local Testing
```bash  
streamlit run streamlit_app.py
```

### Streamlit Cloud
1. Push código a GitHub
2. Conectar repositorio en Streamlit Cloud
3. Configurar secrets en dashboard
4. Deploy automático

### Secrets en Streamlit Cloud
```toml
# Desde Streamlit Cloud dashboard → Settings → Secrets
OPENAI_API_KEY = "sk-..."
MODEL_NAME = "gpt-4o-mini"  
MAX_TOKENS_PER_CALL = "12000"
```

## Troubleshooting

### Errores Comunes

#### 1. **Import Cíclico**
```bash
# Error: ImportError: cannot import name 'X' from partially initialized module
# Solución: Revisar dependency graph, mover imports
```

#### 2. **Context Manager Error**
```python
# ❌ INCORRECTO
with monitor.measure_time():
    pass

# ✅ CORRECTO  
@monitor.measure_time("function_name", "category")
def my_function():
    pass
```

#### 3. **Caracteres Unicode Rotos**
```bash
# Limpiar archivos
sed -i 's/[^\x20-\x7E]//g' archivo.py
```

#### 4. **Performance Issues**
```python
# Revisar SLA compliance
stats = monitor.get_summary_stats("pipeline_execution")
if stats['p50_duration'] > 10:
    # Optimizar batching o reducir batch_size
```

### Herramientas de Debug

```bash
# Ver estructura de archivos
tree -I '__pycache__|.git'

# Contar líneas por archivo
find . -name "*.py" -exec wc -l {} + | sort -n

# Buscar imports cíclicos
grep -r "from core" components/
grep -r "from components" core/

# Verificar caracteres no-ASCII
grep -P "[^\x20-\x7E]" *.py
```

## Contribución

### Pull Request Process
1. Fork del repositorio
2. Crear branch con nombre descriptivo  
3. Seguir estándares de código
4. Probar localmente
5. Crear PR with description
6. Code review
7. Merge cuando aprobado

### Commit Messages
```bash
# Formato: tipo: descripción breve
feat: add emotion heatmap visualization
fix: resolve context manager error in pipeline
refactor: split large chart_generator file
docs: update API documentation
```