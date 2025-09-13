# Development Guide v2.0

## Development Environment Setup

### Prerequisites
- Python 3.8+
- Git
- OpenAI API Key (or Azure OpenAI)
- Code editor (VS Code recommended)

### Quick Setup
```bash
# Clone repository
git clone https://github.com/Ai-Whisperers/personal-analisis-ia
cd personal-analisis-ia

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your API keys and configuration
```

## Architecture Guidelines v2.0

### Code Organization Rules

1. **≤480 lines per file** - Keep files focused and maintainable
2. **No circular imports** - Use dependency injection and interfaces
3. **Separation of concerns** - Follow the layer architecture
4. **Type hints required** - Use typing for all functions
5. **Docstrings mandatory** - Document all public functions
6. **Error handling** - Always handle exceptions gracefully

### Layer Guidelines

#### Core Layer (`core/`)
```python
# ✅ Good: Pure business logic
def analyze_emotions(text: str) -> Dict[str, float]:
    """Analyze emotions in text without UI dependencies."""
    pass

# ❌ Bad: UI dependencies in core
import streamlit as st  # Never import streamlit in core/
```

#### Controller Layer (`controller/`)
```python
# ✅ Good: Orchestration without UI
class PipelineController:
    def run_pipeline(self, file_path: str) -> Dict[str, Any]:
        """Orchestrate pipeline execution."""
        pass

# ✅ Good: Background processing
class BackgroundRunner:
    def run_async(self, func: callable, *args) -> None:
        """Run function in background."""
        pass
```

#### UI Layer (`pages/`, `components/`)
```python
# ✅ Good: UI logic only
import streamlit as st
from controller import PipelineController

controller = PipelineController()
if st.button("Analyze"):
    controller.run_pipeline(file_path)
```

## Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/rate-limiting-enhancement

# Make changes following architecture rules
# Test locally
streamlit run streamlit_app.py

# Commit with descriptive message
git commit -m "feat: enhance rate limiting with usage monitoring"

# Push and create PR
git push origin feature/rate-limiting-enhancement
```

### 2. Code Quality Standards

#### Type Hints
```python
# ✅ Required for all functions
def process_batch(comments: List[str], config: Dict[str, Any]) -> List[Dict[str, float]]:
    """Process batch of comments with configuration."""
    pass

# ❌ Avoid untyped functions
def process_batch(comments, config):
    pass
```

#### Error Handling
```python
# ✅ Proper error handling with logging
from utils.logging_helpers import get_logger
logger = get_logger(__name__)

def api_call(data: Dict) -> Dict:
    try:
        response = make_request(data)
        return response
    except RateLimitError as e:
        logger.warning(f"Rate limit hit: {e}")
        return fallback_response(data)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise ProcessingError(f"Failed to process: {e}")
```

#### Configuration Management
```python
# ✅ Use config.py for all settings
from config import get_rate_limits, get_batch_config

def initialize_client():
    limits = get_rate_limits()
    batch_config = get_batch_config()
    return LLMApiClient(limits=limits, batch_config=batch_config)

# ❌ Hard-coded values
def initialize_client():
    return LLMApiClient(max_requests=500)  # Don't hardcode
```

### 3. Testing Guidelines

#### Unit Tests
```python
# tests/test_rate_limiter.py
import pytest
from utils.rate_limiter import RateLimiter

def test_rate_limiter_prevents_overuse():
    config = {"requests_per_minute": 10, "tokens_per_minute": 1000}
    limiter = RateLimiter(config)

    # Test that rate limiter correctly blocks requests
    comments = ["test"] * 100  # Large batch
    can_proceed, reason = limiter.can_make_request(comments)

    assert not can_proceed
    assert "Token limit" in reason
```

#### Integration Tests
```python
# tests/test_pipeline_integration.py
def test_full_pipeline_with_mock_api():
    controller = PipelineController()
    # Test with mock data
    result = controller.run_pipeline("test_data.xlsx")

    assert result["success"] is True
    assert "emotion_analysis" in result
    assert len(result["usage_stats"]) > 0
```

## Adding New Features

### 1. New Analysis Module
```python
# core/ai_engine/new_module.py
from typing import Dict, Any
from utils.logging_helpers import get_logger

logger = get_logger(__name__)

class NewAnalysisModule:
    """New analysis module following architecture patterns."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def analyze(self, llm_response: Dict) -> Dict[str, Any]:
        """Analyze LLM response for new insights."""
        try:
            # Implementation
            result = self._process_response(llm_response)
            logger.info(f"New analysis completed: {len(result)} items")
            return result
        except Exception as e:
            logger.error(f"New analysis failed: {e}")
            return {}

    def _process_response(self, response: Dict) -> Dict[str, Any]:
        """Private method for processing."""
        pass
```

### 2. New UI Component
```python
# components/ui_components/new_component.py
import streamlit as st
from typing import Dict, Any

def render_new_component(data: Dict[str, Any]) -> None:
    """Render new UI component with data."""
    st.subheader("New Feature")

    if not data:
        st.warning("No data available")
        return

    # Render component
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Metric 1", data.get("metric1", 0))
        with col2:
            st.metric("Metric 2", data.get("metric2", 0))
```

### 3. New Utility Function
```python
# utils/new_utility.py
from typing import List, Dict, Any
from utils.logging_helpers import get_logger

logger = get_logger(__name__)

def new_utility_function(input_data: List[Dict]) -> Dict[str, Any]:
    """New utility function with proper typing and logging."""
    logger.debug(f"Processing {len(input_data)} items")

    try:
        result = _process_data(input_data)
        logger.info(f"Utility function completed successfully")
        return result
    except Exception as e:
        logger.error(f"Utility function failed: {e}")
        raise

def _process_data(data: List[Dict]) -> Dict[str, Any]:
    """Private helper function."""
    pass
```

## Performance Optimization

### 1. Rate Limiting Optimization
```python
# When adding new API calls, always use rate limiter
from utils.rate_limiter import RateLimiter
from utils.usage_monitor import UsageMonitor

def new_api_feature(comments: List[str]):
    limiter = RateLimiter(config)
    monitor = UsageMonitor(config)

    # Check before making request
    can_proceed, reason = limiter.can_make_request(comments)
    if not can_proceed:
        logger.warning(f"Rate limit check failed: {reason}")
        return fallback_result()

    # Make request and track usage
    start_time = time.time()
    result = make_api_call(comments)
    processing_time = time.time() - start_time

    # Log usage
    monitor.log_batch_usage(
        batch_size=len(comments),
        processing_time=processing_time,
        tokens_used=result.get("tokens_used", 0)
    )

    return result
```

### 2. Memory Optimization
```python
# Use generators for large datasets
def process_large_dataset(df: pd.DataFrame) -> Iterator[Dict]:
    """Process large dataset in chunks to save memory."""
    chunk_size = 1000
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i + chunk_size]
        yield process_chunk(chunk)

# Clear large objects when done
def process_and_cleanup(data: pd.DataFrame) -> Dict:
    result = heavy_processing(data)
    del data  # Explicit cleanup
    return result
```

## Debugging

### 1. Logging Setup
```python
# Use consistent logging throughout
from utils.logging_helpers import get_logger

logger = get_logger(__name__)

def your_function():
    logger.debug("Starting function")  # Development info
    logger.info("Processing started")   # General info
    logger.warning("Non-critical issue") # Warnings
    logger.error("Error occurred", exc_info=True)  # Errors
```

### 2. Development Mode
```python
# config.py - Enable debug mode for development
FEATURE_FLAGS = {
    "enable_debug_mode": True,  # Set to True for development
    "enable_mock_mode": True,   # Use mock API for testing
    "enable_detailed_logging": True
}
```

### 3. Performance Debugging
```python
# Use performance monitor for debugging slow operations
from utils.performance_monitor import monitor

@monitor.measure_time("custom_operation")
def slow_operation():
    # Your code here
    pass

# Check performance logs
# Logs will show execution time and help identify bottlenecks
```

## Configuration for Development

### Local Development secrets.toml
```toml
# .streamlit/secrets.toml
[API_CONFIG]
OPENAI_API_KEY = "your_development_api_key"
API_PROVIDER = "openai"
API_TIER = "tier_1"
MODEL_NAME = "gpt-4o-mini"

[DEVELOPMENT]
LOG_LEVEL = "DEBUG"
ENABLE_MOCK_MODE = true
ENABLE_DEBUG_MODE = true

[BATCH_CONFIG]
MAX_BATCH_SIZE = "50"  # Smaller for development
MAX_WORKERS = "2"      # Fewer workers for development
```

## Code Review Checklist

### Before Submitting PR
- [ ] Follows ≤480 lines per file rule
- [ ] No circular imports
- [ ] Proper type hints
- [ ] Error handling implemented
- [ ] Logging added
- [ ] Tests written
- [ ] Documentation updated
- [ ] Rate limiting considered (if API calls)
- [ ] Memory usage optimized
- [ ] Configuration externalized

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Performance improvement
- [ ] Documentation update

## Architecture Compliance
- [ ] Follows layer separation rules
- [ ] No UI dependencies in core/
- [ ] Proper error handling
- [ ] Rate limiting implemented (if applicable)

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Performance Impact
- [ ] No performance regression
- [ ] Memory usage optimized
- [ ] Rate limiting considered
```

## Common Patterns

### 1. Error Handling Pattern
```python
def safe_operation(data: Any) -> Dict[str, Any]:
    try:
        result = risky_operation(data)
        return {"success": True, "data": result}
    except SpecificError as e:
        logger.warning(f"Expected error: {e}")
        return {"success": False, "error": str(e), "fallback": True}
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {"success": False, "error": "Internal error"}
```

### 2. Configuration Pattern
```python
def feature_function(custom_config: Optional[Dict] = None):
    # Merge with default config
    config = {**DEFAULT_CONFIG}
    if custom_config:
        config.update(custom_config)

    # Use configuration
    return process_with_config(config)
```

### 3. Resource Management Pattern
```python
def process_with_resources():
    resource = None
    try:
        resource = acquire_resource()
        return process_data(resource)
    finally:
        if resource:
            release_resource(resource)
```

This development guide ensures consistent, maintainable, and high-quality code that follows the project's v2.0 architecture principles.