# Personal Comment Analyzer v2.0

Sistema avanzado de análisis de sentimientos de comentarios usando IA con 16 emociones específicas, análisis NPS, detección de churn y pain points. La versión 2.0 incluye rate limiting inteligente, usage monitoring, y arquitectura production-ready.

## 🎯 **Características Principales**

### 🎭 **Sistema de 16 Emociones**
- **Positivas (7)**: alegria, confianza, expectativa, gratitud, aprecio, entusiasmo, esperanza
- **Negativas (7)**: tristeza, enojo, miedo, desagrado, frustracion, decepcion, verguenza  
- **Neutras (2)**: sorpresa, indiferencia
- **Charts**: Muestra % individual de cada emoción (no solo categorías)

### 📊 **Análisis Completo**
- **NPS Analysis**: Categorización Promotores/Pasivos/Detractores + score
- **Churn Risk**: Probabilidad de abandono (0-1) basada en sentiment
- **Pain Points**: Identificación automática de problemas específicos
- **Visualización**: Charts interactivos con Plotly

### ⚡ **Performance v2.0**
- **Rate Limiting Inteligente**: Prevención proactiva de errores 429
- **Dynamic Batch Sizing**: Ajuste automático basado en token usage
- **SLA Target**: ≤10 segundos para 800-1200 comentarios con monitoring
- **Background Processing**: UI no bloqueante con BackgroundRunner
- **Usage Monitoring**: Tracking detallado de costos y performance
- **Production-Ready**: Configuración robusta para despliegue
- **Exportación Avanzada**: Excel, CSV, JSON + usage analytics

## 🚀 **Quick Start**

### Requisitos v2.0
- Python 3.8+
- Streamlit
- OpenAI API Key con tier configurado para rate limits
- Configuración de secrets.toml para production
- Variables de entorno para API tier y limits

### Instalación Local
```bash
git clone https://github.com/Ai-Whisperers/personal-analisis-ia
cd Comment-Analizer-Personal

# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Dependencies
pip install -r requirements.txt

# Configurar API key (opcional)
mkdir .streamlit
echo 'OPENAI_API_KEY = "sk-..."' > .streamlit/secrets.toml

# Ejecutar
streamlit run streamlit_app.py
```

### Formato de Archivo Requerido
Excel (.xlsx, .xls) o CSV con columnas:
- **NPS**: Puntuación 0-10
- **Nota**: Calificación del cliente  
- **Comentario Final**: Texto del comentario a analizar

📝 **Nota**: El sistema maneja automáticamente variaciones en nombres como "Comentario Final Final", "comentario", "feedback", etc.

## 🏗️ **Arquitectura v2.0**

### Separación Estricta UI/Core/Controller
- **UI Layer**: `pages/`, `components/ui_components/` (solo Streamlit)
- **Controller Layer**: `controller/` (orquestación y background processing)
- **Core Layer**: `core/` (lógica pura, sin dependencias UI)
- **Integration**: `utils/` con rate limiting, usage monitoring, performance

### Pipeline v2.0
```
Excel → PipelineController → BackgroundRunner → FileProcessor → RateLimiter → Dynamic Batching → LLM con Monitoring → Enhanced Analysis → Charts + Usage Dashboard → Smart Export
```

### Estructura del Proyecto
```
├── streamlit_app.py          # Entry point
├── config.py                 # Configuración dinámica + rate limits
├── controller/               # NUEVO: Controller Architecture
│   ├── controller.py         # PipelineController principal
│   ├── background_runner.py  # Background processing
│   ├── state_manager.py      # State management avanzado
│   └── interfaces.py         # Interfaces y contratos
├── pages/
│   ├── 1_Landing_Page.py     # UI: portada
│   └── 2_Subir.py            # UI: upload y análisis
├── core/                     # Lógica pura (sin Streamlit)
│   ├── ai_engine/            # IA con rate limiting integrado
│   ├── file_processor/       # Excel → DataFrame robusto
│   └── progress/             # Tracking sin UI
├── components/ui_components/ # Componentes Streamlit + usage dashboards
├── static/css/               # Estilos glassmorphism
├── utils/                    # NUEVO: Rate limiting, usage monitoring, performance
│   ├── rate_limiter.py       # Rate limiting inteligente
│   ├── usage_monitor.py      # Usage tracking y alertas
│   └── performance_monitor.py# Performance con usage metrics
├── docs/                     # Documentación completa
│   ├── ES/                   # Documentación en español
│   └── EN/                   # NUEVO: Documentación en inglés
└── local-reports/            # Outputs (no versionado)
```

## 📊 **Uso**

### 1. Subir Archivo
1. Ir a **"Subir y Analizar Comentarios"**
2. Subir Excel con columnas requeridas
3. Validación automática

### 2. Ejecutar Análisis  
1. Elegir modo (API real o mock)
2. Click **"Iniciar Análisis"**
3. Ver progreso en tiempo real

### 3. Ver Resultados
- **Charts interactivos**: 16 emociones, NPS, churn risk
- **Métricas**: Top emociones, categorías, riesgos
- **Export**: Descargar en Excel/CSV/JSON

## ⚙️ **Configuración**

### Secrets v2.0 (`.streamlit/secrets.toml`)
```toml
# API Configuration
[API_CONFIG]
OPENAI_API_KEY = "sk-..."
API_PROVIDER = "openai"
API_TIER = "tier_2"  # tier_1, tier_2, tier_3, tier_4, tier_5
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS_PER_CALL = "12000"

# Production Settings
[PRODUCTION]
LOG_LEVEL = "INFO"
ENABLE_MOCK_MODE = false
ENABLE_PERFORMANCE_MONITORING = true

# Rate Limits (auto-detected from API_TIER)
[BATCH_CONFIG]
MAX_BATCH_SIZE = "100"
MAX_WORKERS = "6"
AVG_TOKENS_PER_COMMENT = "150"

# Security
[SECURITY]
MAX_DAILY_COST = 100.0
ENABLE_USAGE_MONITORING = true
```

### Streamlit Cloud
Dashboard → Settings → Secrets (mismo formato TOML)

## 🔧 **Desarrollo**

### Estándares
- **≤480 líneas por archivo** (actualmente todos cumplen)
- **Sin imports cíclicos** (UI nunca importa de UI, Core es independiente)
- **Separación UI/Core estricta**
- **Configuration-driven** (todo en `config.py`)

### Testing
```bash
# Verificar límites de líneas
find . -name "*.py" -exec wc -l {} + | sort -n

# Test configuración
python -c "from config import validate_config; validate_config()"

# Run local
streamlit run streamlit_app.py
```

## 📚 **Documentación**

### Docs Completas v2.0

#### 🇪🇸 Documentación en Español
- **[00_Introduccion.md](docs/ES/00_Introduccion.md)** - Overview y características v2.0
- **[01_Arquitectura.md](docs/ES/01_Arquitectura.md)** - Controller architecture y rate limiting
- **[02_Flujo_Pipeline.md](docs/ES/02_Flujo_Pipeline.md)** - Pipeline con usage monitoring
- **[03_Guia_Desarrollo.md](docs/ES/03_Guia_Desarrollo.md)** - Para desarrolladores
- **[04_Despliegue.md](docs/ES/04_Despliegue.md)** - Deployment production-ready
- **[05_Seguridad_y_Secretos.md](docs/ES/05_Seguridad_y_Secretos.md)** - Seguridad avanzada
- **[06_FAQ.md](docs/ES/06_FAQ.md)** - FAQ con rate limiting

#### 🇺🇸 English Documentation (NEW)
- **[00_Introduction.md](docs/EN/00_Introduction.md)** - Overview and v2.0 features
- **[01_Architecture.md](docs/EN/01_Architecture.md)** - Technical architecture details
- **[02_Pipeline_Flow.md](docs/EN/02_Pipeline_Flow.md)** - Step-by-step analysis process
- **[03_Dev_Guide.md](docs/EN/03_Dev_Guide.md)** - Developer guide
- **[04_Deployment.md](docs/EN/04_Deployment.md)** - Production deployment
- **[05_Security_and_Secrets.md](docs/EN/05_Security_and_Secrets.md)** - Security & secrets management
- **[06_FAQ.md](docs/EN/06_FAQ.md)** - Frequently asked questions

## 🚀 **Deploy v2.0**

### Streamlit Cloud (Recomendado)
1. Push a GitHub
2. Conectar repo en [share.streamlit.io](https://share.streamlit.io)
3. Configurar secrets v2.0 en dashboard (incluir API_TIER)
4. Deploy automático con rate limiting

### Production Checklist
- [ ] API tier configurado correctamente
- [ ] Rate limits documentados
- [ ] Usage monitoring habilitado
- [ ] Billing alerts configuradas
- [ ] Secrets management configurado

### Local con Docker
```dockerfile  
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["streamlit", "run", "streamlit_app.py"]
```

## 🤝 **Contribución**

1. Fork del repositorio
2. Crear branch: `git checkout -b feature/nueva-funcionalidad`
3. Seguir estándares v2.0 (≤480 líneas, Controller pattern, rate limiting)
4. Test localmente con usage monitoring
5. Pull request con descripción y performance impact

## 📄 **Licencia**

MIT License - Ver [LICENSE](LICENSE) para detalles.

## 🔗 **Links**

- **Demo**: [personal-analisis-ia.streamlit.app](https://personal-analisis-ia.streamlit.app) 
- **Repositorio**: [GitHub](https://github.com/Ai-Whisperers/personal-analisis-ia)
- **Issues**: [GitHub Issues](https://github.com/Ai-Whisperers/personal-analisis-ia/issues)
- **Documentación**: [docs/ES/](docs/ES/)

---

**Desarrollado por AI Whisperers** | v2.0.0

## 🆕 **Nuevas Características v2.0**

### 🎛️ **Controller Architecture**
- **PipelineController**: Centraliza orquestación del pipeline
- **BackgroundRunner**: Procesamiento no bloqueante
- **StateManager**: Manejo avanzado de estado

### 📊 **Rate Limiting & Monitoring**
- **RateLimiter**: Prevención inteligente de errores 429
- **UsageMonitor**: Tracking detallado de costos API
- **Dynamic batch sizing** basado en token usage
- **Alertas automáticas** de uso

### 🔧 **Production Features**
- **Secrets management** robusto
- **Configuration by API tier** (tier_1 a tier_5)
- **Error handling** mejorado
- **Background processing** para UX
- **Usage analytics** y recommendations
- **Documentación completa** en inglés y español

### 🚀 **Performance Improvements**
- **Token counting preciso** con tiktoken
- **Intelligent backoff** con jitter
- **Cost optimization** automática
- **Production-ready** deployment
- **Enhanced monitoring** dashboards

### ⚡ **Changelog v2.0**
- ✅ **Controller Architecture**: Separación clara UI/Business Logic
- ✅ **Rate Limiting**: Prevención inteligente de errores 429
- ✅ **Usage Monitoring**: Tracking detallado de costos API
- ✅ **Background Processing**: UI no bloqueante
- ✅ **Dynamic Batching**: Optimización basada en token usage
- ✅ **Production Config**: Secrets management robusto
- ✅ **English Docs**: Documentación completa en inglés
- ✅ **Enhanced Export**: Reports con usage analytics