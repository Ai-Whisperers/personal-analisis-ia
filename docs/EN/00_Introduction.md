# Personal Comment Analyzer - Introduction v2.0

## Overview

Personal Comment Analyzer is an advanced AI-powered sentiment analysis system for customer comments, specifically designed to analyze customer feedback using 16 specific emotions. Version 2.0 includes intelligent rate limiting, usage monitoring, and production-ready architecture.

## Key Features

### 🎭 16-Emotion Analysis System
Analyzes each comment detecting 16 specific emotions:

**Positive (7):**
- joy, trust, anticipation, gratitude, appreciation, enthusiasm, hope

**Negative (7):**
- sadness, anger, fear, disgust, frustration, disappointment, shame

**Neutral (2):**
- surprise, indifference

### 📊 Multi-dimensional Analysis
- **NPS Score**: Automatic categorization (Promoters, Passives, Detractors)
- **Churn Risk**: Customer abandonment risk prediction (0-1 score)
- **Pain Points**: Automatic identification of specific problems
- **Sentiment Summary**: General sentiment overview

### ⚡ Optimized Performance v2.0
- **Intelligent Rate Limiting**: Proactive prevention of 429 errors
- **Dynamic Batch Sizing**: Automatic adjustment based on token usage
- **SLA Target**: ≤10 seconds for 800-1200 comments with monitoring
- **Background Processing**: Non-blocking UI with BackgroundRunner
- **Usage Monitoring**: Detailed API usage tracking
- **Production-Ready**: Robust configuration for deployment

## Technology Stack v2.0

- **Frontend**: Streamlit + Glassmorphism CSS
- **Backend**: Controller-based architecture + Core modules
- **AI**: OpenAI API with intelligent rate limiting
- **Data**: Excel/CSV processing with robust validation
- **Visualization**: Plotly charts + Usage dashboards
- **Concurrency**: ThreadPoolExecutor + BackgroundRunner
- **Monitoring**: RateLimiter + UsageMonitor in real-time

## Use Cases v2.0

1. **Feedback Analysis**: Process satisfaction surveys with cost optimization
2. **Churn Detection**: Identify at-risk customers with monitoring
3. **NPS Analysis**: Calculate NPS with usage analytics
4. **Pain Points**: Find problems with intelligent rate limiting
5. **Reporting**: Generate reports + API usage metrics
6. **Production Analysis**: Enterprise analysis with background processing

## System Requirements v2.0

- Python 3.8+
- Streamlit
- OpenAI API Key with configured tier for rate limits
- Excel file with columns: `NPS`, `Nota`, `Comentario Final`
- secrets.toml configuration for production
- Environment variables for API tier and limits

## New Features v2.0

### 🎛️ **Controller Architecture**
- `PipelineController`: Centralizes pipeline orchestration
- `BackgroundRunner`: Non-blocking processing
- `StateManager`: Advanced state management

### 📊 **Rate Limiting & Monitoring**
- `RateLimiter`: Intelligent prevention of 429 errors
- `UsageMonitor`: Detailed API cost tracking
- Dynamic batch sizing based on token usage
- Automatic usage alerts

### 🔧 **Production Features**
- Robust secrets management
- Configuration by API tier
- Improved error handling
- Background processing for UX
- Usage analytics and recommendations

## Competitive Advantages v2.0

1. **Speed**: Process 1000+ comments in <10 seconds with rate limiting
2. **Precision**: 16 specific emotions vs. basic sentiment
3. **Stability**: Intelligent rate limiting prevents 429 errors
4. **Scalability**: Dynamic batch sizing + usage monitoring
5. **Production-Ready**: Configuration management + background processing
6. **Observability**: Detailed usage metrics + performance tracking
7. **Robustness**: Enhanced error handling + fallback mechanisms

## Anti-Overengineering Architecture v2.0

The system follows **6 evolved critical rules** to avoid unnecessary complexity:

1. **UI only in `pages/` + `static/`** - No business logic
2. **Logic in `core/`** - Completely separated from Streamlit
3. **≤480 lines/file** - No circular imports
4. **Controller Pattern** - PipelineController + BackgroundRunner
5. **Intelligent Rate Limiting** - Prevention of 429 errors
6. **SLA: ≤10s P50** - With usage monitoring and dynamic batching

This v2.0 architecture ensures **production readiness**, **cost optimization**, and **observability** without sacrificing simplicity.

## Input Format

Requires Excel/CSV file with columns:
- **NPS**: Numeric score (0-10)
- **Nota**: Customer rating
- **Comentario Final**: Feedback text

## Output

- **Interactive Visualizations**: Charts with usage metrics
- **Enhanced Export**: Excel, CSV, JSON with performance metrics
- **Advanced Reports**: Analysis + usage statistics in local-reports/
- **Monitoring Dashboards**: Rate limits and token usage

## Next Steps

1. **Installation**: Follow the guide in `04_Deployment.md`
2. **Configuration**: Review `05_Security_and_Secrets.md` for API keys and rate limits setup
3. **Production Setup**: Configure API tier and monitoring
4. **Development**: Read `03_Dev_Guide.md` to contribute
5. **Troubleshooting**: Check `06_FAQ.md` for common issues

---

**Ready to start?** 🚀 Go to the installation and configuration section.

## Changelog v2.0

- ✅ **Controller Architecture**: Clear UI/Business Logic separation
- ✅ **Rate Limiting**: Intelligent prevention of 429 errors
- ✅ **Usage Monitoring**: Detailed API cost tracking
- ✅ **Background Processing**: Non-blocking UI
- ✅ **Dynamic Batching**: Optimization based on token usage
- ✅ **Production Config**: Robust secrets management
- ✅ **Error Handling**: Enhanced fallbacks and recovery

## Navigation

- [01_Architecture.md](01_Architecture.md) - Technical architecture details
- [02_Pipeline_Flow.md](02_Pipeline_Flow.md) - Step-by-step analysis process
- [03_Dev_Guide.md](03_Dev_Guide.md) - Developer guide
- [04_Deployment.md](04_Deployment.md) - Deployment instructions
- [05_Security_and_Secrets.md](05_Security_and_Secrets.md) - Secure configuration
- [06_FAQ.md](06_FAQ.md) - Frequently asked questions