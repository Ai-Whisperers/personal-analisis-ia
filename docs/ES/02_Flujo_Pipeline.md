# Flujo del Pipeline de Análisis

## Diagrama del Pipeline Completo

```mermaid
flowchart TD
    %% Input
    A[📂 Subida Excel\n(NPS | Nota | Comentario Final)] --> B[🔎 Parser\nreader → cleaner → validator → normalizer]

    %% Batching
    B --> C[📦 Batching\n≤100 comentarios/lote]

    %% Paralelismo LLM
    C -->|Paralelo| D[🤖 LLM API Call\n(api_call.py)]
    D --> E1[🎭 Emotions Module\n16 emociones por comentario]
    D --> E2[🩹 Pain Points Module\nkeywords / categorías]
    D --> E3[⚠️ Churn Risk Module\nscore 0–1]
    D --> E4[📊 NPS Module\nDetractor | Pasivo | Promotor]

    %% Merge results
    E1 & E2 & E3 & E4 --> F[🗂 Merge Results\nengine_controller.py]

    %% Postprocess
    F --> G[📑 DataFrame Final\n+ columnas emo_*, pain_points, churn_risk, NPS_category]

    %% Visualization & Export
    G --> H1[📉 Chart Generator\n% de cada emoción (bar chart, pie opcional)]
    G --> H2[📈 Distribución NPS]
    G --> H3[⬇️ Report Exporter\nExcel/CSV en local-reports/]

    %% Progress/State
    B -.-> S[⏱ Progress Tracker\nutils/performance_monitor]
    D -.-> S
    F -.-> S
    G -.-> S
```

## Etapas Detalladas

### 1. 📂 **Carga de Archivo**
**Ubicación**: `components/ui_components/uploader.py`

```python
# Validaciones previas
- Formato: .xlsx, .xls, .csv
- Tamaño máximo: 50MB  
- Columnas requeridas: ["NPS", "Nota", "Comentario Final"]
```

### 2. 🔎 **Procesamiento de Archivos**
**Ubicación**: `core/file_processor/`

#### 2.1 Reader (`reader.py`)
```python
def read_excel(file_path: str) -> pd.DataFrame:
    # Lee Excel/CSV → DataFrame
    # Detecta encoding automáticamente
    # Maneja errores de formato
```

#### 2.2 Cleaner (`cleaner.py`) 
```python
def clean(df: pd.DataFrame) -> pd.DataFrame:
    # Elimina filas vacías
    # Trunca comentarios >2000 chars
    # Normaliza espacios en blanco
```

#### 2.3 Validator (`validator.py`)
```python 
def validate(df: pd.DataFrame) -> pd.DataFrame:
    # Verifica columnas requeridas
    # Valida rango NPS (0-10)
    # Filtra comentarios <5 chars
```

#### 2.4 Normalizer (`normalizer.py`)
```python
def normalize(df: pd.DataFrame) -> pd.DataFrame:
    # Detección de idioma
    # Normalización UTF-8
    # Lower case opcional
```

### 3. 📦 **Batching**
**Ubicación**: `core/ai_engine/engine_controller.py`

```python
def _create_batches(df: pd.DataFrame) -> List[pd.DataFrame]:
    # Divide DataFrame en lotes de ≤100 filas
    # Optimiza para límites de API
    # Mantiene orden original
```

### 4. 🤖 **Llamadas LLM Paralelas**
**Ubicación**: `core/ai_engine/api_call.py`

```python
class LLMApiClient:
    def analyze_batch(self, comments: List[str]) -> List[Dict]:
        # ThreadPoolExecutor para concurrencia
        # Retries automáticos (3 intentos)
        # Fallback a modo mock si falla API
        # JSON response parsing
```

#### Prompt Template
```python
# Analiza los siguientes comentarios y devuelve para cada uno:
{
  "emotions": {
    "alegria": 0.0-1.0,
    "tristeza": 0.0-1.0,
    # ... las 16 emociones
  },
  "pain_points": ["problema1", "problema2"],
  "churn_risk": 0.0-1.0,
  "sentiment_summary": "texto libre"
}
```

### 5. 🎭 **Módulos de Análisis**

#### 5.1 Emotions Module (`emotion_module.py`)
```python
def analyze(llm_response: Dict) -> Dict[str, float]:
    # Extrae scores de 16 emociones
    # Valida rango [0.0, 1.0]
    # Maneja valores faltantes
```

#### 5.2 Pain Points Module (`pain_points_module.py`)  
```python
def analyze(llm_response: Dict) -> List[str]:
    # Extrae lista de pain points
    # Categoriza por tipo
    # Filtra duplicados
```

#### 5.3 Churn Module (`churn_module.py`)
```python
def analyze(llm_response: Dict) -> float:
    # Calcula riesgo de churn [0.0, 1.0]
    # Considera keywords de alto riesgo
    # Pondera con sentiment general
```

#### 5.4 NPS Module (`nps_module.py`)
```python
def analyze(llm_response: Dict, nps_score: int) -> str:
    # Categoriza NPS: detractor, passive, promoter
    # Valida consistencia con sentiment
    # Maneja valores missing
```

### 6. 🗂 **Merge de Resultados**
**Ubicación**: `core/ai_engine/engine_controller.py`

```python
def _merge_results(original_df, results) -> pd.DataFrame:
    # Combina resultados con DataFrame original
    # Crea columnas: emo_alegria, emo_tristeza, etc.
    # Añade: pain_points, churn_risk, nps_category
    # Mantiene índices originales
```

### 7. 📊 **Visualización**
**Ubicación**: `components/ui_components/chart_generator.py`

#### 7.1 Distribución de Emociones
```python
# Bar Chart Horizontal - 16 emociones individuales
# Ordenado por % (descendente)
# Color-coded: verde (positivas), rojo (negativas), azul (neutras)
```

#### 7.2 Análisis NPS
```python  
# Pie Chart: Promotores, Pasivos, Detractores
# Cálculo NPS Score: (Promotores - Detractores) / Total * 100
# Interpretación automática
```

#### 7.3 Riesgo de Churn
```python
# Bar Chart: Bajo, Medio, Alto riesgo
# Thresholds: 0-0.3, 0.3-0.7, 0.7-1.0
# Métricas: promedio, % alto riesgo
```

### 8. ⬇️ **Exportación**
**Ubicación**: `components/ui_components/report_exporter.py`

```python
# Formatos: Excel (.xlsx), CSV (.csv), JSON (.json)  
# Ubicación: local-reports/
# Incluye: datos raw + análisis + timestamp
# Opción: solo resultados o dataset completo
```

## Métricas de Performance

### SLA Targets
- **Pipeline completo**: ≤10 segundos (800-1200 filas)
- **File processing**: ≤2 segundos
- **LLM batch**: ≤8 segundos
- **Chart generation**: ≤2 segundos
- **Data export**: ≤3 segundos

### Monitoreo
```python  
# utils/performance_monitor.py
@monitor.measure_time("pipeline_execution", "pipeline_execution")  
def run_pipeline(file_path: str) -> pd.DataFrame:
    # Tracking automático de tiempos
    # Alertas si excede SLA
    # Logging estructurado
```

## Manejo de Errores

### Niveles de Fallback
1. **API Error** → Modo mock con datos simulados
2. **Parsing Error** → Valores por defecto
3. **File Error** → Mensaje de error claro al usuario
4. **Memory Error** → Reducir batch size automáticamente

### Logging
```python
# Todos los errores son loggeados con contexto
logger.error(f"Failed to process batch {batch_id}: {error}")
# Métricas de error por etapa
# Estado del pipeline siempre visible al usuario
```