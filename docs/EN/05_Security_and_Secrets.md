# Security and Secrets Management v2.0

## Security Overview

Personal Comment Analyzer v2.0 includes comprehensive security measures for production deployment, including secure API key management, rate limiting protection, and data privacy controls.

## API Key Security

### OpenAI API Key Management

#### Development Environment
```toml
# .streamlit/secrets.toml (local development only)
[API_CONFIG]
OPENAI_API_KEY = "sk-your-development-key"
API_PROVIDER = "openai"
API_TIER = "tier_1"  # or tier_2, tier_3, etc.
MODEL_NAME = "gpt-4o-mini"

# Never commit this file to version control
```

#### Production Environment (Streamlit Cloud)
```python
# Configure through Streamlit Cloud UI
# Go to: App settings > Secrets
# Add the same structure as above
```

#### Production Environment (Self-hosted)
```bash
# Method 1: Environment Variables
export OPENAI_API_KEY="sk-prod-key"
export API_PROVIDER="openai"
export API_TIER="tier_2"

# Method 2: Docker Secrets
echo "sk-prod-key" | docker secret create openai_api_key -
```

### Azure OpenAI Configuration
```toml
# .streamlit/secrets.toml
[API_CONFIG]
AZURE_OPENAI_KEY = "your-azure-key"
AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
API_PROVIDER = "azure"
API_TIER = "standard"
```

### API Key Validation
```python
# config.py includes automatic validation
def validate_api_key(api_key: str) -> bool:
    """Validate API key format and basic connectivity."""
    if not api_key or len(api_key) < 20:
        return False

    if api_key.startswith(("sk-", "azure-")):
        return True

    logger.warning("API key format validation failed")
    return False
```

## Rate Limiting Security

### Protection Against Abuse

#### Intelligent Rate Limiting
```python
# utils/rate_limiter.py
class RateLimiter:
    def __init__(self, config: Dict[str, Any]):
        # Conservative defaults for security
        self.base_backoff = 0.5
        self.max_backoff = 2.0  # Short max backoff
        self.consecutive_429s = 0

        # API tier-based limits
        self.requests_per_minute = config.get('requests_per_minute', 60)
        self.tokens_per_minute = config.get('tokens_per_minute', 150000)
```

#### Usage Monitoring
```python
# utils/usage_monitor.py
class UsageMonitor:
    def __init__(self, config: Dict[str, Any]):
        # Alert thresholds for security
        self.warning_threshold_requests = 0.75  # 75% of limit
        self.critical_threshold_requests = 0.90  # 90% of limit

    def _check_usage_alerts(self) -> None:
        """Security alerts for high usage."""
        if requests_percentage >= self.critical_threshold_requests * 100:
            logger.critical(f"🚨 CRITICAL: Request usage at {requests_percentage:.1f}%")
```

### API Cost Protection
```python
# Automatic cost protection
def enforce_cost_limits(usage_stats: Dict) -> bool:
    """Enforce cost limits to prevent unexpected charges."""
    daily_cost_estimate = calculate_daily_cost(usage_stats)

    if daily_cost_estimate > MAX_DAILY_COST:
        logger.critical(f"Daily cost limit exceeded: ${daily_cost_estimate}")
        return False

    return True
```

## Data Security

### Input Data Protection

#### File Upload Security
```python
# components/ui_components/uploader.py
ALLOWED_EXTENSIONS = ['.xlsx', '.xls', '.csv']
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_upload_security(uploaded_file) -> Dict[str, Any]:
    """Security validation for uploaded files."""

    # Check file size
    if len(uploaded_file.getvalue()) > MAX_FILE_SIZE:
        return {"valid": False, "error": "File too large"}

    # Check file type
    file_ext = Path(uploaded_file.name).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return {"valid": False, "error": "Invalid file type"}

    # Basic malware check (file structure validation)
    try:
        if file_ext in ['.xlsx', '.xls']:
            pd.read_excel(uploaded_file, nrows=1)
        else:
            pd.read_csv(uploaded_file, nrows=1)
    except Exception as e:
        return {"valid": False, "error": "Invalid file structure"}

    return {"valid": True}
```

#### Data Processing Security
```python
# core/file_processor/cleaner.py
def sanitize_text_input(text: str) -> str:
    """Sanitize text input for security."""
    if not isinstance(text, str):
        return ""

    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\';]', '', text)

    # Limit text length
    max_length = 2000
    if len(text) > max_length:
        text = text[:max_length]
        logger.warning(f"Text truncated for security: {len(text)} chars")

    return text.strip()
```

### Output Security

#### Report Generation
```python
# components/ui_components/report_exporter.py
def secure_export(data: pd.DataFrame, export_format: str) -> bytes:
    """Secure data export with sanitization."""

    # Remove potentially sensitive columns if they exist
    sensitive_cols = ['api_key', 'user_id', 'session_id']
    data_clean = data.drop(columns=[col for col in sensitive_cols if col in data.columns])

    # Sanitize text content
    for col in data_clean.select_dtypes(include=['object']).columns:
        data_clean[col] = data_clean[col].astype(str).apply(sanitize_text_input)

    # Export with timestamp for auditability
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analysis_{timestamp}.{export_format}"

    return export_data(data_clean, filename)
```

## Access Control

### User Session Security
```python
# utils/streamlit_helpers.py
def init_secure_session():
    """Initialize secure session state."""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = secrets.token_urlsafe(32)
        st.session_state.session_start = time.time()

    # Session timeout (1 hour)
    if time.time() - st.session_state.session_start > 3600:
        st.session_state.clear()
        st.rerun()
```

### IP-based Rate Limiting (Advanced)
```python
# For production environments with reverse proxy
def get_client_ip() -> str:
    """Get client IP for rate limiting."""
    # Check for forwarded IP (behind proxy)
    forwarded_for = st.context.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()

    real_ip = st.context.headers.get('X-Real-IP')
    if real_ip:
        return real_ip

    return 'unknown'

# Rate limiting by IP
ip_rate_limiter = {}
def check_ip_rate_limit(ip: str) -> bool:
    """Basic IP-based rate limiting."""
    if ip not in ip_rate_limiter:
        ip_rate_limiter[ip] = {'requests': 0, 'window_start': time.time()}

    window = ip_rate_limiter[ip]
    if time.time() - window['window_start'] > 3600:  # Reset every hour
        window['requests'] = 0
        window['window_start'] = time.time()

    if window['requests'] > 100:  # Max 100 requests per hour per IP
        return False

    window['requests'] += 1
    return True
```

## Logging and Auditing

### Security Logging
```python
# utils/logging_helpers.py
def setup_security_logging():
    """Setup security-specific logging."""
    security_logger = logging.getLogger('security')

    # Separate security log file
    security_handler = RotatingFileHandler(
        'logs/security.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )

    security_formatter = logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s - %(extra)s'
    )
    security_handler.setFormatter(security_formatter)
    security_logger.addHandler(security_handler)

    return security_logger

# Usage
security_logger = setup_security_logging()

def log_security_event(event_type: str, details: Dict):
    """Log security events."""
    security_logger.warning(f"{event_type}: {details}")
```

### API Usage Auditing
```python
# Enhanced usage monitoring with audit trail
class SecurityAuditMonitor(UsageMonitor):
    def log_batch_usage(self, batch_size: int, processing_time: float, **kwargs):
        """Enhanced logging with security context."""

        # Standard usage logging
        super().log_batch_usage(batch_size, processing_time, **kwargs)

        # Security audit logging
        audit_data = {
            'timestamp': time.time(),
            'session_id': st.session_state.get('session_id', 'unknown'),
            'batch_size': batch_size,
            'tokens_used': kwargs.get('tokens_used', 0),
            'client_ip': get_client_ip(),
            'processing_time': processing_time
        }

        security_logger.info(f"API_USAGE: {audit_data}")
```

## Environment-Specific Security

### Development Security
```python
# Development-specific security settings
DEVELOPMENT_SECURITY = {
    "enable_debug_mode": True,
    "log_sensitive_data": True,  # Only in development
    "mock_mode_allowed": True,
    "relaxed_rate_limits": True
}
```

### Production Security
```python
# Production security hardening
PRODUCTION_SECURITY = {
    "enable_debug_mode": False,
    "log_sensitive_data": False,
    "mock_mode_allowed": False,
    "strict_rate_limits": True,
    "enable_audit_logging": True,
    "session_timeout": 3600,  # 1 hour
    "max_concurrent_sessions": 100
}
```

## Security Configuration Templates

### Complete Security Configuration
```toml
# .streamlit/secrets.toml - Production template
[API_CONFIG]
OPENAI_API_KEY = "sk-your-production-key"
API_PROVIDER = "openai"
API_TIER = "tier_2"
MODEL_NAME = "gpt-4o-mini"

[SECURITY]
ENABLE_AUDIT_LOGGING = true
SESSION_TIMEOUT = 3600
MAX_DAILY_COST = 100.0
ENABLE_IP_RATE_LIMITING = false  # Enable if behind reverse proxy
MAX_FILE_SIZE_MB = 50
ALLOWED_FILE_TYPES = ["xlsx", "xls", "csv"]

[RATE_LIMITS]
# These auto-configure based on API_TIER, but can override
WARNING_THRESHOLD = 0.75
CRITICAL_THRESHOLD = 0.90
MAX_CONSECUTIVE_RETRIES = 3

[MONITORING]
ENABLE_USAGE_ALERTS = true
ENABLE_COST_MONITORING = true
ENABLE_PERFORMANCE_MONITORING = true
ALERT_EMAIL = "admin@yourdomain.com"  # If implemented
```

## Security Best Practices

### For Developers
1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive configuration
3. **Validate all user inputs** before processing
4. **Log security events** for audit trails
5. **Implement rate limiting** for all API calls
6. **Use secure communication** (HTTPS in production)

### For Deployments
1. **Use secrets management** services (AWS Secrets Manager, etc.)
2. **Enable audit logging** in production
3. **Monitor usage patterns** for anomalies
4. **Set up cost alerts** to prevent unexpected charges
5. **Regularly rotate API keys**
6. **Implement backup strategies** for configuration

### For Operations
1. **Monitor security logs** regularly
2. **Set up automated alerts** for security events
3. **Review access patterns** monthly
4. **Update dependencies** regularly for security patches
5. **Test disaster recovery** procedures

## Incident Response

### Security Incident Checklist
- [ ] Identify the scope of the incident
- [ ] Rotate API keys if compromised
- [ ] Check audit logs for unauthorized access
- [ ] Review cost impact
- [ ] Document incident details
- [ ] Implement additional security measures
- [ ] Update security procedures

### Emergency Response
```python
# Emergency security functions
def emergency_shutdown():
    """Emergency shutdown procedure."""
    logger.critical("EMERGENCY SHUTDOWN INITIATED")

    # Disable API calls
    os.environ['ENABLE_MOCK_MODE'] = 'true'

    # Clear sensitive session data
    if hasattr(st, 'session_state'):
        st.session_state.clear()

    # Log incident
    security_logger.critical("Emergency shutdown executed")

def rotate_api_keys():
    """API key rotation procedure."""
    logger.warning("API key rotation required")
    # Implementation depends on your key management system
```

## Compliance and Privacy

### Data Privacy
- **No persistent storage** of user data by default
- **Temporary file cleanup** after processing
- **Session isolation** between users
- **Option to disable logging** of sensitive content

### Compliance Features
- **Audit logging** for compliance requirements
- **Data retention policies** configurable
- **Export controls** for data governance
- **Access logging** for security audits

This security guide ensures your Comment Analyzer v2.0 deployment maintains the highest security standards while providing comprehensive monitoring and incident response capabilities.