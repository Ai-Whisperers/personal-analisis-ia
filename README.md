# Personal Comment Analyzer

Sistema de análisis de sentimientos de comentarios usando IA con 16 emociones específicas, análisis NPS, detección de churn y pain points.

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

### ⚡ **Performance**
- **SLA Target**: ≤10 segundos para 800-1200 comentarios
- **Procesamiento paralelo**: ThreadPoolExecutor con batches ≤100
- **Modo Mock**: Funciona sin API key para pruebas
- **Exportación**: Excel, CSV, JSON

## 🚀 **Quick Start**

### Requisitos
- Python 3.8+
- Streamlit
- OpenAI API Key (opcional - tiene modo mock)

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

## 🏗️ **Arquitectura**

### Separación Estricta UI/Core
- **UI Layer**: `pages/`, `components/ui_components/` (solo Streamlit)
- **Core Layer**: `core/` (lógica pura, sin dependencias UI)
- **Integration**: `utils/`, `config.py` (conectores seguros)

### Pipeline
```
Excel → Parser → Validator → Batching (≤100) → LLM Paralelo → Análisis → Charts + Export
```

### Estructura del Proyecto
```
├── streamlit_app.py          # Entry point
├── config.py                 # Configuración centralizada (16 emociones, SLA, etc)
├── pages/
│   ├── 1_Landing_Page.py     # UI: portada
│   └── 2_Subir.py            # UI: upload y análisis
├── core/                     # Lógica pura (sin Streamlit)
│   ├── ai_engine/            # IA y procesamiento LLM
│   ├── file_processor/       # Excel → DataFrame  
│   └── progress/             # Tracking sin UI
├── components/ui_components/ # Componentes Streamlit
├── static/css/               # Estilos glassmorphism
├── utils/                    # Performance, logging, helpers
├── docs/ES/                  # Documentación completa
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

### Secrets (`.streamlit/secrets.toml`)
```toml
# OpenAI
OPENAI_API_KEY = "sk-..."
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS_PER_CALL = "12000"

# Performance  
MAX_BATCH_SIZE = "100"
MAX_WORKERS = "12"

# Logging
LOG_LEVEL = "INFO"
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

### Docs Completas
- **[00_Introduccion.md](docs/ES/00_Introduccion.md)** - Overview y características
- **[01_Arquitectura.md](docs/ES/01_Arquitectura.md)** - Detalles técnicos
- **[02_Flujo_Pipeline.md](docs/ES/02_Flujo_Pipeline.md)** - Proceso paso a paso  
- **[03_Guia_Desarrollo.md](docs/ES/03_Guia_Desarrollo.md)** - Para desarrolladores
- **[04_Despliegue.md](docs/ES/04_Despliegue.md)** - Deployment en Streamlit Cloud
- **[05_Seguridad_y_Secretos.md](docs/ES/05_Seguridad_y_Secretos.md)** - Manejo seguro de API keys
- **[06_FAQ.md](docs/ES/06_FAQ.md)** - Preguntas frecuentes

## 🚀 **Deploy**

### Streamlit Cloud (Recomendado)
1. Push a GitHub
2. Conectar repo en [share.streamlit.io](https://share.streamlit.io)
3. Configurar secrets en dashboard
4. Deploy automático

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
3. Seguir estándares de código (≤480 líneas, separación UI/Core)
4. Test localmente
5. Pull request con descripción

## 📄 **Licencia**

MIT License - Ver [LICENSE](LICENSE) para detalles.

## 🔗 **Links**

- **Demo**: [personal-analisis-ia.streamlit.app](https://personal-analisis-ia.streamlit.app) 
- **Repositorio**: [GitHub](https://github.com/Ai-Whisperers/personal-analisis-ia)
- **Issues**: [GitHub Issues](https://github.com/Ai-Whisperers/personal-analisis-ia/issues)
- **Documentación**: [docs/ES/](docs/ES/)

---

**Desarrollado por AI Whisperers** | v2.0.0