# Deployment Guide v2.0

## Production Deployment Options

### Option 1: Streamlit Cloud (Recommended)
Best for quick deployment with managed infrastructure.

### Option 2: Self-Hosted (Docker)
Best for enterprise environments with custom requirements.

### Option 3: Cloud Platforms
Deploy on AWS, GCP, or Azure with container services.

## Pre-Deployment Checklist

### API Configuration
- [ ] OpenAI API key obtained
- [ ] API tier confirmed (tier_1, tier_2, etc.)
- [ ] Rate limits documented
- [ ] Billing alerts configured
- [ ] Usage monitoring enabled

### Security
- [ ] Secrets properly configured
- [ ] No API keys in code
- [ ] Environment variables set
- [ ] Access controls defined

### Performance
- [ ] SLA targets tested (≤10s for 800-1200 comments)
- [ ] Rate limiting configured
- [ ] Batch sizes optimized
- [ ] Memory limits set

## Streamlit Cloud Deployment

### 1. Repository Setup
```bash
# Ensure your repository is ready
git add .
git commit -m "feat: prepare for production deployment"
git push origin main
```

### 2. Streamlit Cloud Configuration
```toml
# .streamlit/config.toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
base = "light"
```

### 3. Production Secrets
```toml
# .streamlit/secrets.toml (configure in Streamlit Cloud UI)
[API_CONFIG]
OPENAI_API_KEY = "sk-..."
API_PROVIDER = "openai"
API_TIER = "tier_2"  # Adjust based on your OpenAI tier
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS_PER_CALL = "12000"

[PRODUCTION]
LOG_LEVEL = "INFO"
ENABLE_MOCK_MODE = false
ENABLE_DEBUG_MODE = false
ENABLE_PERFORMANCE_MONITORING = true

[RATE_LIMITS]
# These will be auto-detected from API_TIER, but can override
REQUESTS_PER_MINUTE = "5000"
TOKENS_PER_MINUTE = "2000000"
MAX_CONCURRENT_REQUESTS = "8"

[BATCH_CONFIG]
MAX_BATCH_SIZE = "100"
MAX_WORKERS = "6"
AVG_TOKENS_PER_COMMENT = "150"
PROMPT_TOKENS = "800"
```

### 4. Deploy Steps
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Select `streamlit_app.py` as main file
4. Configure secrets in the Streamlit Cloud UI
5. Deploy and test

## Self-Hosted Docker Deployment

### 1. Create Dockerfile
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 streamlit && chown -R streamlit:streamlit /app
USER streamlit

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run application
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  comment-analyzer:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - API_PROVIDER=openai
      - API_TIER=tier_2
      - LOG_LEVEL=INFO
      - ENABLE_MOCK_MODE=false
    volumes:
      - ./local-reports:/app/local-reports
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

### 3. Environment File
```bash
# .env (for docker-compose)
OPENAI_API_KEY=sk-your-actual-api-key
API_PROVIDER=openai
API_TIER=tier_2
MODEL_NAME=gpt-4o-mini
LOG_LEVEL=INFO
ENABLE_MOCK_MODE=false
MAX_BATCH_SIZE=100
MAX_WORKERS=6
```

### 4. Deploy with Docker
```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f comment-analyzer

# Scale if needed
docker-compose up -d --scale comment-analyzer=2
```

## Cloud Platform Deployment

### AWS ECS Deployment
```yaml
# ecs-task-definition.json
{
  "family": "comment-analyzer",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "comment-analyzer",
      "image": "your-ecr-repo/comment-analyzer:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "API_PROVIDER", "value": "openai"},
        {"name": "API_TIER", "value": "tier_2"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/comment-analyzer",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## Production Configuration

### Rate Limiting Configuration by API Tier

#### OpenAI Tier Configuration
```python
# config.py - Production rate limits
OPENAI_RATE_LIMITS = {
    "tier_1": {
        "requests_per_minute": 500,
        "tokens_per_minute": 200000,
        "recommended_batch_size": 50,
        "max_concurrent": 4
    },
    "tier_2": {
        "requests_per_minute": 5000,
        "tokens_per_minute": 2000000,
        "recommended_batch_size": 100,
        "max_concurrent": 8
    },
    "tier_3": {
        "requests_per_minute": 5000,
        "tokens_per_minute": 4000000,
        "recommended_batch_size": 100,
        "max_concurrent": 10
    }
    # ... additional tiers
}
```

#### Azure OpenAI Configuration
```python
AZURE_RATE_LIMITS = {
    "standard": {
        "requests_per_minute": 2700,
        "tokens_per_minute": 450000,
        "recommended_batch_size": 75,
        "max_concurrent": 6
    }
}
```

### Production Secrets Management

#### Option 1: Environment Variables
```bash
# Production environment
export OPENAI_API_KEY="sk-..."
export API_PROVIDER="openai"
export API_TIER="tier_2"
export LOG_LEVEL="INFO"
export ENABLE_MONITORING="true"
```

#### Option 2: Secret Management Service
```python
# For AWS Secrets Manager
import boto3

def get_secret(secret_name: str) -> str:
    client = boto3.client('secretsmanager', region_name='us-west-2')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']
```

## Monitoring & Observability

### Application Logging
```python
# Production logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "log_to_file": True,
    "log_to_console": True,
    "log_dir": "/app/logs",
    "max_file_size_mb": 50,
    "backup_count": 10,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}
```

### Health Checks
```python
# Add to streamlit_app.py for production monitoring
def health_check():
    """Health check endpoint for load balancers."""
    try:
        # Check API connectivity
        api_client = LLMApiClient()
        if api_client.health_check():
            return {"status": "healthy", "timestamp": time.time()}
        else:
            return {"status": "unhealthy", "reason": "API unavailable"}
    except Exception as e:
        return {"status": "unhealthy", "reason": str(e)}
```

### Usage Monitoring Dashboard
```python
# Production usage monitoring
def create_monitoring_dashboard():
    """Create usage monitoring dashboard for production."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "API Usage",
            f"{usage_stats['requests_used']}/{usage_stats['requests_limit']}",
            delta=f"{usage_stats['requests_percentage']:.1f}%"
        )

    with col2:
        st.metric(
            "Token Usage",
            f"{usage_stats['tokens_used']:,}/{usage_stats['tokens_limit']:,}",
            delta=f"{usage_stats['tokens_percentage']:.1f}%"
        )

    with col3:
        st.metric(
            "Cost Estimate",
            f"${cost_estimate:.2f}",
            delta=f"+${daily_cost:.2f}/day"
        )

    with col4:
        st.metric(
            "Performance",
            f"{avg_processing_time:.1f}s",
            delta="✅ Within SLA" if avg_processing_time < 10 else "⚠️ Above SLA"
        )
```

## Performance Optimization

### Production Tuning
```python
# config.py - Production optimizations
PRODUCTION_CONFIG = {
    "streamlit": {
        "server.maxUploadSize": 200,  # 200MB max upload
        "server.maxMessageSize": 200,
        "server.enableXsrfProtection": True,
        "browser.gatherUsageStats": False
    },
    "performance": {
        "enable_caching": True,
        "cache_ttl": 3600,  # 1 hour
        "max_concurrent_users": 10,
        "request_timeout": 300  # 5 minutes
    }
}
```

### Memory Management
```python
# Memory optimization for production
import gc

def optimize_memory():
    """Optimize memory usage in production."""
    # Force garbage collection
    gc.collect()

    # Clear large objects from cache
    if hasattr(st, 'cache'):
        st.cache.clear()

    # Log memory usage
    import psutil
    memory_usage = psutil.virtual_memory().percent
    logger.info(f"Memory usage: {memory_usage}%")
```

## Scaling Considerations

### Horizontal Scaling
```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - comment-analyzer

  comment-analyzer:
    build: .
    expose:
      - "8501"
    deploy:
      replicas: 3
    environment:
      - INSTANCE_ID=${HOSTNAME}
```

### Load Balancing (Nginx)
```nginx
# nginx.conf
upstream comment_analyzer {
    least_conn;
    server comment-analyzer_1:8501;
    server comment-analyzer_2:8501;
    server comment-analyzer_3:8501;
}

server {
    listen 80;
    location / {
        proxy_pass http://comment_analyzer;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security Hardening

### Application Security
```python
# Security configuration
SECURITY_CONFIG = {
    "enable_xsrf_protection": True,
    "enable_cors": False,
    "max_request_size": "200MB",
    "session_timeout": 3600,
    "rate_limiting": True,
    "input_validation": True
}
```

### Network Security
```dockerfile
# Security-hardened Dockerfile
FROM python:3.9-slim

# Create non-root user early
RUN groupadd -r streamlit && useradd -r -g streamlit streamlit

# Install security updates
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy and set permissions
COPY --chown=streamlit:streamlit . /app
WORKDIR /app
USER streamlit

# Remove sensitive files
RUN rm -rf tests/ docs/ .git/ .env*
```

## Backup & Recovery

### Data Backup Strategy
```bash
#!/bin/bash
# backup-script.sh
DATE=$(date +%Y%m%d_%H%M%S)

# Backup local reports
tar -czf "backup/reports_$DATE.tar.gz" local-reports/

# Backup configuration
cp .streamlit/secrets.toml "backup/secrets_$DATE.toml.bak"

# Backup logs
tar -czf "backup/logs_$DATE.tar.gz" logs/

# Retain only last 30 days of backups
find backup/ -name "*.tar.gz" -mtime +30 -delete
```

## Post-Deployment Verification

### Testing Checklist
- [ ] Application loads successfully
- [ ] API connectivity works
- [ ] File upload works
- [ ] Analysis completes within SLA
- [ ] Rate limiting works correctly
- [ ] Usage monitoring displays data
- [ ] Export functionality works
- [ ] Error handling works
- [ ] Health checks pass

### Performance Testing
```bash
# Simple performance test
curl -f http://your-app-url/_stcore/health

# Load testing (if applicable)
# Use tools like Apache Bench or wrk for load testing
```

This deployment guide ensures your Comment Analyzer v2.0 is production-ready with proper rate limiting, monitoring, and scalability configurations.