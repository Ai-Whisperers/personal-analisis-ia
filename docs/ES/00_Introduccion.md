# Personal Comment Analyzer - Introducción v2.0

## Descripción General

Personal Comment Analyzer es un sistema avanzado de análisis de sentimientos de comentarios usando IA, específicamente diseñado para analizar feedback de clientes con un enfoque en 16 emociones específicas. La versión 2.0 incluye rate limiting inteligente, usage monitoring, y arquitectura production-ready.

## Características Principales

### 🎭 Sistema de 16 Emociones
El sistema analiza cada comentario detectando 16 emociones específicas:

**Positivas (7):**
- alegria, confianza, expectativa, gratitud, aprecio, entusiasmo, esperanza

**Negativas (7):**  
- tristeza, enojo, miedo, desagrado, frustracion, decepcion, verguenza

**Neutras (2):**
- sorpresa, indiferencia

### 📊 Análisis Incluido
- **Distribución de emociones**: Porcentaje de cada emoción individual en todos los comentarios
- **Análisis NPS**: Categorización en Promotores, Pasivos, Detractores
- **Riesgo de Churn**: Probabilidad de abandono del cliente (0-1)
- **Pain Points**: Identificación de problemas específicos
- **Exportación**: Resultados en Excel, CSV o JSON

### ⚡ Performance v2.0
- **Rate Limiting Inteligente**: Prevención proactiva de errores 429
- **Dynamic Batch Sizing**: Ajuste automático basado en token usage
- **SLA Target**: ≤10 segundos para 800-1200 comentarios con monitoring
- **Background Processing**: UI no bloqueante con BackgroundRunner
- **Usage Monitoring**: Tracking detallado de costos y performance
- **Production Config**: Secrets management y configuración robusta

## Tecnologías v2.0

- **Frontend**: Streamlit + CSS Glassmorphism
- **Backend**: Controller-based architecture + Core modules
- **IA**: OpenAI API con rate limiting inteligente
- **Datos**: Excel input/output con validación robusta
- **Visualización**: Plotly charts + Usage dashboards
- **Concurrencia**: ThreadPoolExecutor + BackgroundRunner
- **Monitoring**: RateLimiter + UsageMonitor en tiempo real

## Casos de Uso v2.0

1. **Análisis de Feedback**: Procesar encuestas con cost optimization
2. **Detección de Churn**: Identificar clientes en riesgo con monitoring
3. **NPS Analysis**: Calcular NPS con usage analytics
4. **Pain Points**: Encontrar problemas con rate limiting inteligente
5. **Reporting**: Generar reportes + métricas de API usage
6. **Production Analysis**: Análisis enterprise con background processing

## Requisitos del Sistema v2.0

- Python 3.8+
- Streamlit
- OpenAI API Key con tier configurado para rate limits
- Archivo Excel con columnas: `NPS`, `Nota`, `Comentario Final`
- Configuración de secrets.toml para production
- Variables de entorno para API tier y limits

## Nuevas Características v2.0

### 🎛️ **Controller Architecture**
- `PipelineController`: Centraliza orquestación del pipeline
- `BackgroundRunner`: Procesamiento no bloqueante
- `StateManager`: Manejo avanzado de estado

### 📊 **Rate Limiting & Monitoring**
- `RateLimiter`: Prevención inteligente de errores 429
- `UsageMonitor`: Tracking detallado de costos API
- Dynamic batch sizing basado en token usage
- Alertas automáticas de uso

### 🔧 **Production Features**
- Secrets management robusto
- Configuration by API tier
- Error handling mejorado
- Background processing para UX
- Usage analytics y recommendations

## Navegación

- [01_Arquitectura.md](01_Arquitectura.md) - Detalles técnicos de la arquitectura
- [02_Flujo_Pipeline.md](02_Flujo_Pipeline.md) - Proceso paso a paso del análisis
- [03_Guia_Desarrollo.md](03_Guia_Desarrollo.md) - Guía para desarrolladores  
- [04_Despliegue.md](04_Despliegue.md) - Instrucciones de deployment
- [05_Seguridad_y_Secretos.md](05_Seguridad_y_Secretos.md) - Configuración segura
- [06_FAQ.md](06_FAQ.md) - Preguntas frecuentes