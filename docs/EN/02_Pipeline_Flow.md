# Analysis Pipeline Flow v2.0

## Complete Pipeline Diagram

```mermaid
flowchart TD
    %% Input
    A[📂 Excel Upload\n(NPS | Nota | Comentario Final)] --> B[🎛️ PipelineController\nCentralized orchestration]

    %% Background Processing
    B --> C[🔄 BackgroundRunner\nNon-blocking processing]

    %% File Processing
    C --> D[🔎 FileProcessor\nreader → cleaner → validator → normalizer]

    %% Rate Limiting Check
    D --> E[📊 RateLimiter\nToken counting + API limits check]

    %% Dynamic Batching
    E --> F[📦 Dynamic Batching\nOptimized size by usage]

    %% LLM with Monitoring
    F --> G[🤖 LLM API Call\nWith UsageMonitor + RateLimiter]
    G --> H[📈 UsageMonitor\nReal-time tracking]

    %% Analysis Modules
    G --> I1[🎭 Emotions Module\n16 emotions per comment]
    G --> I2[🩹 Pain Points Module\nkeywords / categories]
    G --> I3[⚠️ Churn Risk Module\nscore 0–1]
    G --> I4[📊 NPS Module\nDetractor | Passive | Promoter]

    %% Enhanced Results
    I1 & I2 & I3 & I4 --> J[🗂 Enhanced Merge\nResults + Usage Metrics]

    %% Enhanced Output
    J --> K[📁 DataFrame + Analytics\n+ usage_stats, cost_analysis]

    %% Visualization with Monitoring
    K --> L1[📉 Enhanced Charts\nEmotions + Usage Dashboard]
    K --> L2[📈 NPS + Cost Analysis]
    K --> L3[⬇️ Smart Export\nData + Usage Report]

    %% Usage Recommendations
    H --> M[🎤 Usage Recommendations\nOptimization suggestions]
    M --> N[UI Alerts\nCost & Performance]

    %% Advanced State Management
    C -.-> O[💾 StateManager\nAdvanced state]
    G -.-> O
    J -.-> O
```

## Detailed Stages

### 1. 📂 **File Upload**

**Input**: Excel/CSV with columns: `NPS`, `Nota`, `Comentario Final`
- **Reader**: `core/file_processor/reader.py` - Reads the file
- **Cleaner**: `core/file_processor/cleaner.py` - Normalizes columns (e.g., 'Comentario Final Final' → 'Comentario Final')
- **Validator**: `core/file_processor/validator.py` - Validates structure and quality
- **Normalizer**: `core/file_processor/normalizer.py` - Text cleaning

**Output**: Clean and validated DataFrame
**Location**: `components/ui_components/uploader.py`

```python
# Prior validations
- Format: .xlsx, .xls, .csv
- Max size: 50MB
- Required columns: ["NPS", "Nota", "Comentario Final"]
```

### 2. 🎛️ **Pipeline Controller (NEW)**
**Location**: `controller/controller.py`

```python
class PipelineController:
    def run_pipeline(self, file_path: str) -> Dict[str, Any]:
        # Centralized orchestration
        # Background processing coordination
        # State management integration
        # Enhanced error handling
```

### 3. 🔄 **Background Runner (NEW)**
**Location**: `controller/background_runner.py`

```python
class BackgroundPipelineRunner:
    def run_pipeline_async(self, pipeline_func, file_path, timeout_seconds):
        # Non-blocking processing
        # UI responsiveness preservation
        # Progress tracking
        # Cancellation support
```

### 4. 🔎 **File Processing**
**Location**: `core/file_processor/`

#### 4.1 Reader (`reader.py`)
```python
def read_excel(file_path: str) -> pd.DataFrame:
    # Reads Excel/CSV → DataFrame
    # Automatic encoding detection
    # Format error handling
```

#### 4.2 Cleaner (`cleaner.py`)
```python
def clean(df: pd.DataFrame) -> pd.DataFrame:
    # Removes empty rows
    # Truncates comments >2000 chars
    # Normalizes whitespace
```

#### 4.3 Validator (`validator.py`)
```python
def validate(df: pd.DataFrame) -> pd.DataFrame:
    # Verifies required columns
    # Validates NPS range (0-10)
    # Filters comments <5 chars
```

#### 4.4 Normalizer (`normalizer.py`)
```python
def normalize(df: pd.DataFrame) -> pd.DataFrame:
    # Language detection
    # UTF-8 normalization
    # Optional lower case
```

### 5. 📊 **Rate Limiting Check (NEW)**
**Location**: `utils/rate_limiter.py`

```python
class RateLimiter:
    def can_make_request(self, comments: List[str]) -> tuple[bool, str]:
        # Precise token counting with tiktoken
        # API tier awareness (tier_1, tier_2, etc.)
        # Proactive 429 prevention
        # Dynamic batch size recommendations
```

#### Rate Limiting Features
- **Token Estimation**: Using tiktoken for precise counting
- **API Tier Support**: Automatic limits based on OpenAI/Azure tier
- **Dynamic Backoff**: Short retries with jitter (max 2s)
- **Usage Tracking**: Real-time monitoring of requests/tokens

### 6. 📦 **Dynamic Batching (ENHANCED)**
**Location**: `core/ai_engine/engine_controller.py`

```python
def _create_optimized_batches(df: pd.DataFrame) -> List[pd.DataFrame]:
    # Dynamic batch size based on token usage
    # API tier awareness
    # Rate limit compliance
    # Cost optimization
```

### 7. 🤖 **LLM Calls with Monitoring**
**Location**: `core/ai_engine/api_call.py` + `utils/rate_limiter.py`

```python
class LLMApiClient:
    def analyze_batch(self, comments: List[str]) -> List[Dict]:
        # RateLimiter check before each request
        # Dynamic batch sizing based on token usage
        # UsageMonitor tracking in real-time
        # Intelligent backoff with jitter
        # Production-ready error handling
```

#### 7.1 **Intelligent Rate Limiting (NEW)**
```python
# Features:
- Token counting with tiktoken
- API tier configuration support
- Proactive 429 error prevention
- Dynamic batch size adjustment
- Usage-based optimization
```

#### 7.2 **Usage Monitoring (NEW)**
**Location**: `utils/usage_monitor.py`

```python
class UsageMonitor:
    def log_batch_usage(self, batch_size, tokens_used, processing_time):
        # Real-time usage tracking
        # Cost analysis per batch
        # Performance metrics
        # Automated recommendations
```

### 8. 🎭 **Analysis Modules (ENHANCED)**

#### 8.1 Emotions Module (`emotion_module.py`)
```python
def analyze(llm_response: Dict) -> Dict[str, float]:
    # Extracts scores for 16 emotions
    # Validates range [0.0, 1.0]
    # Handles missing values
    # Usage context logging
```

#### 8.2 Pain Points Module (`pain_points_module.py`)
```python
def analyze(llm_response: Dict) -> List[str]:
    # Extracts pain points list
    # Categories by type
    # Filters duplicates
    # Cost tracking
```

#### 8.3 Churn Module (`churn_module.py`)
```python
def analyze(llm_response: Dict) -> float:
    # Calculates churn risk [0.0, 1.0]
    # Considers high-risk keywords
    # Weights with general sentiment
    # Performance monitoring
```

#### 8.4 NPS Module (`nps_module.py`)
```python
def analyze(llm_response: Dict, nps_score: int) -> str:
    # Categorizes NPS: detractor, passive, promoter
    # Validates consistency with sentiment
    # Handles missing values
    # Usage analytics
```

### 9. 🗂 **Enhanced Results Merge**
**Location**: `core/ai_engine/engine_controller.py`

```python
def _merge_results_with_analytics(original_df, results, usage_stats) -> pd.DataFrame:
    # Combines results with original DataFrame
    # Creates columns: emo_joy, emo_sadness, etc.
    # Adds: pain_points, churn_risk, nps_category
    # Includes: usage metrics, cost analysis
    # Maintains original indices
```

### 10. 📊 **Enhanced Visualization**
**Location**: `components/ui_components/chart_generator.py`

#### 10.1 Emotions Distribution with Usage Dashboard
```python
# Horizontal Bar Chart - 16 individual emotions
# Ordered by % (descending)
# Color-coded: green (positive), red (negative), blue (neutral)
# Usage metrics overlay: tokens used, cost estimate
```

#### 10.2 NPS Analysis with Cost Tracking
```python
# Pie Chart: Promoters, Passives, Detractors
# NPS Score calculation: (Promoters - Detractors) / Total * 100
# Automatic interpretation
# Cost per NPS category analysis
```

#### 10.3 Usage Analytics Dashboard (NEW)
```python
# Real-time usage metrics
# API rate limit utilization
# Cost tracking and projections
# Optimization recommendations
```

### 11. ⬇️ **Smart Export (ENHANCED)**
**Location**: `components/ui_components/report_exporter.py`

```python
# Formats: Excel (.xlsx), CSV (.csv), JSON (.json)
# Location: local-reports/
# Includes: raw data + analysis + usage metrics + cost analysis
# Usage Report: tokens used, estimated cost, efficiency metrics
# Recommendations: optimization suggestions for future analysis
# API Usage Summary: rate limit utilization, tier recommendations
```

### 12. 📈 **Usage Analytics (NEW)**
**Location**: `utils/usage_monitor.py`

```python
# Real-time usage tracking
# Cost analysis per pipeline run
# API efficiency metrics
# Automated optimization recommendations
# Usage trend analysis
# Rate limit compliance monitoring
```

## Performance Metrics v2.0

### SLA Targets with Cost Awareness
- **Complete pipeline**: ≤10 seconds (800-1200 rows) + cost tracking
- **File processing**: ≤2 seconds
- **LLM batch**: ≤8 seconds with rate limiting
- **Chart generation**: ≤2 seconds + usage dashboard
- **Data export**: ≤3 seconds + usage report
- **Rate limit compliance**: 0 429 errors
- **Cost efficiency**: Automatic batch size optimization

### Advanced Monitoring
```python
# utils/performance_monitor.py + rate_limiter.py + usage_monitor.py
@monitor.measure_time("pipeline_execution")
def run_pipeline_with_monitoring(file_path: str) -> pd.DataFrame:
    # Traditional performance tracking
    # Rate limit compliance monitoring
    # Cost tracking per batch
    # Usage recommendations generation
    # Proactive optimization alerts
```

### New Metrics v2.0
- **Token Usage Efficiency**: Tokens/comment vs. baseline
- **Rate Limit Utilization**: % of limits used
- **Cost per Analysis**: Estimated cost per pipeline run
- **Batch Size Optimization**: Efficiency vs. size
- **API Tier Recommendations**: Upgrade suggestions

## Error Handling v2.0

### Enhanced Fallback Levels
1. **Rate Limit Error (429)** → Intelligent backoff with jitter
2. **API Error** → Mock mode with simulated data
3. **Token Limit Error** → Dynamic batch size reduction
4. **Parsing Error** → Default values + usage logging
5. **File Error** → Clear message + robust validation
6. **Memory Error** → Automatic reduction + alerts

### Advanced Logging
```python
# Error tracking with usage context
logger.error(f"Failed batch {batch_id}: {error}, usage: {usage_stats}")
# Rate limit incident tracking
usage_monitor.log_rate_limit_incident(batch_id, retry_count)
# Cost impact analysis
cost_tracker.log_failed_batch_cost(batch_id, tokens_wasted)
# Automated recovery recommendations
recommendation_engine.suggest_optimization(error_pattern)
```

### Recovery Strategies (NEW)
- **Adaptive Batch Sizing**: Automatic reduction on errors
- **Smart Retry**: Backoff based on error type
- **Usage-based Fallback**: Mock mode when usage is high
- **Cost Protection**: Automatic spending limits

## Configuration Examples

### API Tier Configuration
```python
# .streamlit/secrets.toml
[API_CONFIG]
API_PROVIDER = "openai"          # or "azure"
API_TIER = "tier_2"              # tier_1, tier_2, tier_3, tier_4, tier_5
OPENAI_API_KEY = "your_api_key"
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS_PER_CALL = "12000"

[BATCH_CONFIG]
MAX_BATCH_SIZE = "100"
MAX_WORKERS = "4"
AVG_TOKENS_PER_COMMENT = "150"
```

### Rate Limiting Configuration
```python
# Automatic configuration based on API tier
OPENAI_RATE_LIMITS = {
    "tier_1": {"requests_per_minute": 500, "tokens_per_minute": 200000},
    "tier_2": {"requests_per_minute": 5000, "tokens_per_minute": 2000000},
    # ... other tiers
}
```

This v2.0 pipeline flow ensures production-ready performance with intelligent cost optimization and comprehensive usage monitoring.