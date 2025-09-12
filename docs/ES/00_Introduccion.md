# Personal Comment Analyzer - Introducción

## Descripción General

Personal Comment Analyzer es un sistema avanzado de análisis de sentimientos de comentarios usando IA, específicamente diseñado para analizar feedback de clientes con un enfoque en 16 emociones específicas.

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

### ⚡ Performance
- **Procesamiento paralelo**: Análisis optimizado por lotes
- **SLA Target**: ≤10 segundos para 800-1200 comentarios  
- **Modo Mock**: Funciona sin API key para pruebas
- **Concurrencia**: ThreadPoolExecutor para máximo rendimiento

## Tecnologías

- **Frontend**: Streamlit + CSS Glassmorphism
- **Backend**: Python core modules
- **IA**: OpenAI API (con fallback mock)
- **Datos**: Excel input/output
- **Visualización**: Plotly charts
- **Concurrencia**: ThreadPoolExecutor

## Casos de Uso

1. **Análisis de Feedback**: Procesar encuestas de satisfacción
2. **Detección de Churn**: Identificar clientes en riesgo de abandono  
3. **NPS Analysis**: Calcular y categorizar Net Promoter Score
4. **Pain Points**: Encontrar problemas específicos en comentarios
5. **Reporting**: Generar reportes ejecutivos con visualizaciones

## Requisitos del Sistema

- Python 3.8+
- Streamlit
- OpenAI API Key (opcional - tiene modo mock)
- Archivo Excel con columnas: `NPS`, `Nota`, `Comentario Final`

## Navegación

- [01_Arquitectura.md](01_Arquitectura.md) - Detalles técnicos de la arquitectura
- [02_Flujo_Pipeline.md](02_Flujo_Pipeline.md) - Proceso paso a paso del análisis
- [03_Guia_Desarrollo.md](03_Guia_Desarrollo.md) - Guía para desarrolladores  
- [04_Despliegue.md](04_Despliegue.md) - Instrucciones de deployment
- [05_Seguridad_y_Secretos.md](05_Seguridad_y_Secretos.md) - Configuración segura
- [06_FAQ.md](06_FAQ.md) - Preguntas frecuentes