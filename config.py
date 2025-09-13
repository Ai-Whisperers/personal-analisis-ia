# -*- coding: utf-8 -*-
"""
Configuration file for Personal Comment Analyzer
Contains all constants, settings, and configuration parameters
"""
import os
from typing import Dict, List, Any

# ============================================================================
# 16 EMOTIONS SYSTEM (CORE CONFIGURATION)
# ============================================================================

# The complete list of 16 emotions as defined in the blueprint
EMOTIONS_16 = [
    "alegria", "tristeza", "enojo", "miedo", "confianza", "desagrado", 
    "sorpresa", "expectativa", "frustracion", "gratitud", "aprecio", 
    "indiferencia", "decepcion", "entusiasmo", "verguenza", "esperanza"
]

# Emotion categorization for analysis and visualization
EMO_CATEGORIES = {
    "positivas": [
        "alegria", "confianza", "expectativa", "gratitud", 
        "aprecio", "entusiasmo", "esperanza"
    ],
    "negativas": [
        "tristeza", "enojo", "miedo", "desagrado", 
        "frustracion", "decepcion", "verguenza"
    ],
    "neutras": [
        "sorpresa", "indiferencia"
    ]
}

# ============================================================================
# API CONFIGURATION & RATE LIMITS
# ============================================================================

# OpenAI API Rate Limits by Tier
OPENAI_RATE_LIMITS = {
    "tier_1": {
        "requests_per_minute": 500,
        "tokens_per_minute": 200000,
        "description": "Default tier for new accounts"
    },
    "tier_2": {
        "requests_per_minute": 5000,
        "tokens_per_minute": 2000000,
        "description": "After $50 spent"
    },
    "tier_3": {
        "requests_per_minute": 5000,
        "tokens_per_minute": 4000000,
        "description": "After $100 spent"
    },
    "tier_4": {
        "requests_per_minute": 10000,
        "tokens_per_minute": 10000000,
        "description": "After $1000 spent"
    },
    "tier_5": {
        "requests_per_minute": 30000,
        "tokens_per_minute": 150000000,
        "description": "After $5000 spent"
    }
}

# Azure OpenAI Rate Limits by Tier
AZURE_RATE_LIMITS = {
    "standard": {
        "requests_per_minute": 2700,
        "tokens_per_minute": 450000,
        "description": "Default Azure OpenAI tier"
    },
    "data_zone_standard": {
        "requests_per_minute": 6000,
        "tokens_per_minute": 1000000,
        "description": "Data Zone Standard tier"
    },
    "global_standard": {
        "requests_per_minute": 12000,
        "tokens_per_minute": 2000000,
        "description": "Global Standard tier"
    }
}

# Default conservative limits (lowest tier) - optimized for SLA compliance
DEFAULT_RATE_LIMITS = {
    "requests_per_minute": 60,  # Conservative to avoid 429s
    "tokens_per_minute": 150000,  # Balanced for throughput
    "max_concurrent_requests": 4,  # Reduced to prevent throttling
    "safety_margin": 0.9  # Higher margin for production stability
}

# OpenAI API Configuration (from Streamlit secrets)
def get_openai_api_key() -> str:
    """Get OpenAI API key from Streamlit secrets or environment variables"""
    try:
        # Try Streamlit secrets first (recommended for Streamlit Cloud)
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and "OPENAI_API_KEY" in st.secrets:
                return st.secrets["OPENAI_API_KEY"]
            return st.secrets.get("OPENAI_API_KEY", "")
        except ImportError:
            pass
    except Exception:
        pass
    # Fallback to environment variable for local development
    return os.environ.get("OPENAI_API_KEY", "")

def get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit secrets with fallback to environment"""
    try:
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
            return st.secrets.get(key, os.environ.get(key, default))
        except ImportError:
            pass
    except Exception:
        pass
    return os.environ.get(key, default)


# LLM Model Configuration (with secrets support)
def get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration from secrets with defaults"""
    return {
        "model": get_secret("MODEL_NAME", "gpt-4o-mini"),
        "temperature": 0.3,
        "max_tokens": int(get_secret("MAX_TOKENS_PER_CALL", "12000")),
        "timeout": 30
    }

# Dynamic LLM config
try:
    LLM_CONFIG = get_llm_config()
except Exception:
    LLM_CONFIG = {
        "model": "gpt-3.5-turbo",
        "temperature": 0.3,
        "max_tokens": 500,
        "timeout": 30
    }

# ============================================================================
# PROCESSING CONFIGURATION
# ============================================================================

def get_rate_limits() -> Dict[str, Any]:
    """Get API rate limits based on provider and tier"""
    provider = get_secret("API_PROVIDER", "openai").lower()
    tier = get_secret("API_TIER", "tier_1").lower()
    
    if provider == "azure":
        tier_data = AZURE_RATE_LIMITS.get(tier, AZURE_RATE_LIMITS["standard"])
    else:
        tier_data = OPENAI_RATE_LIMITS.get(tier, OPENAI_RATE_LIMITS["tier_1"])
    
    # Apply safety margin (use 0.9 for production stability)
    safety_margin = DEFAULT_RATE_LIMITS["safety_margin"]
    return {
        "requests_per_minute": int(tier_data["requests_per_minute"] * safety_margin),
        "tokens_per_minute": int(tier_data["tokens_per_minute"] * safety_margin),
        "max_concurrent_requests": min(
            int(get_secret("MAX_WORKERS", "4")),
            int(tier_data["requests_per_minute"] * safety_margin / 5)  # Conservative estimate
        )
    }

# Batch processing settings for optimal performance (with secrets support)
def get_batch_config() -> Dict[str, Any]:
    """Get batch configuration from secrets with rate limit awareness"""
    rate_limits = get_rate_limits()
    
    # Calculate safe batch size based on token limits
    avg_tokens_per_comment = int(get_secret("AVG_TOKENS_PER_COMMENT", "150"))
    prompt_tokens = int(get_secret("PROMPT_TOKENS", "800"))
    max_tokens_per_request = int(get_secret("MAX_TOKENS_PER_REQUEST", "12000"))
    
    # Calculate max comments per batch to stay within token limits
    available_tokens = max_tokens_per_request - prompt_tokens
    safe_batch_size = min(
        int(get_secret("MAX_BATCH_SIZE", "100")),
        max(1, available_tokens // avg_tokens_per_comment)
    )
    
    return {
        "batch_size": safe_batch_size,
        "max_concurrent_batches": rate_limits["max_concurrent_requests"],
        "retry_attempts": 3,
        "retry_delay": 1,
        "rate_limit_delay": max(0.1, 60.0 / rate_limits["requests_per_minute"]),
        "requests_per_minute": rate_limits["requests_per_minute"],
        "tokens_per_minute": rate_limits["tokens_per_minute"],
        "avg_tokens_per_comment": avg_tokens_per_comment,
        "prompt_tokens": prompt_tokens,
        "max_tokens_per_request": max_tokens_per_request
    }

# Dynamic batch config with rate limit awareness
try:
    BATCH_CONFIG = get_batch_config()
except Exception:
    BATCH_CONFIG = {
        "batch_size": 50,  # Conservative fallback
        "max_concurrent_batches": 4,
        "retry_attempts": 3,
        "retry_delay": 1,
        "rate_limit_delay": 2.0,  # Conservative fallback
        "requests_per_minute": 30,  # Conservative fallback
        "tokens_per_minute": 150000,
        "avg_tokens_per_comment": 150,
        "prompt_tokens": 800,
        "max_tokens_per_request": 12000
    }

# File processing limits
FILE_CONFIG = {
    "max_file_size_mb": 50,
    "supported_formats": [".xlsx", ".xls", ".csv"],
    "required_columns": ["NPS", "Nota", "Comentario Final"],
    "max_comment_length": 2000,
    "min_comment_length": 5
}

# ============================================================================
# PERFORMANCE TARGETS (SLA)
# ============================================================================

# Performance SLA targets in seconds
SLA_TARGETS = {
    "pipeline_execution": 10.0,  # Full pipeline d10s for 800-1200 rows
    "file_processing": 2.0,      # File read/validation
    "llm_batch": 8.0,            # LLM batch processing
    "data_export": 3.0,          # Export to Excel/CSV
    "chart_generation": 2.0      # Chart rendering
}

# ============================================================================
# UI CONFIGURATION
# ============================================================================

# Streamlit page configuration
PAGE_CONFIG = {
    "page_title": "Personal Comment Analyzer",
    "page_icon": "🎭",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Chart styling
CHART_CONFIG = {
    "color_palette": {
        "positive": "#2E8B57",    # Sea Green
        "negative": "#DC143C",    # Crimson  
        "neutral": "#4682B4",     # Steel Blue
        "primary": "#1f77b4",
        "secondary": "#ff7f0e"
    },
    "default_height": 500,
    "use_container_width": True
}

# ============================================================================
# NPS CONFIGURATION
# ============================================================================

# NPS score categorization (standard)
NPS_CATEGORIES = {
    "detractor": (0, 6),    # 0-6: Detractors
    "passive": (7, 8),      # 7-8: Passives  
    "promoter": (9, 10)     # 9-10: Promoters
}

# ============================================================================
# CHURN RISK CONFIGURATION
# ============================================================================

# Churn risk thresholds
CHURN_THRESHOLDS = {
    "low": (0.0, 0.3),
    "medium": (0.3, 0.7),
    "high": (0.7, 1.0)
}

# High-risk keywords for churn analysis
CHURN_KEYWORDS = {
    "high_risk": [
        "cancelar", "cerrar cuenta", "dar de baja", "nunca más", "no vuelvo",
        "pésimo servicio", "horrible", "terrible", "odio", "detesto",
        "cambiar de proveedor", "buscar alternativa", "competencia",
        "no recomiendo", "perdieron cliente", "última vez"
    ],
    "medium_risk": [
        "decepcionado", "frustrado", "molesto", "insatisfecho",
        "problema", "queja", "reclamo", "mal servicio",
        "no cumple", "esperaba más", "no vale la pena"
    ]
}

# ============================================================================
# EXPORT CONFIGURATION
# ============================================================================

# Export settings
EXPORT_CONFIG = {
    "formats": {
        "xlsx": "Excel (.xlsx)",
        "csv": "CSV (.csv)", 
        "json": "JSON (.json)"
    },
    "output_dir": "local-reports",
    "filename_template": "analisis_comentarios_{timestamp}",
    "include_timestamp": True
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Logging settings
LOGGING_CONFIG = {
    "level": "INFO",
    "log_to_file": True,
    "log_to_console": True,
    "log_dir": "local-reports/logs",
    "max_file_size_mb": 10,
    "backup_count": 5
}

# ============================================================================
# VALIDATION CONFIGURATION
# ============================================================================

# Data validation rules
VALIDATION_CONFIG = {
    "min_rows": 1,
    "max_rows": 50000,
    "max_missing_percentage": {
        "comments": 10,     # Max 10% missing comments
        "nps": 50,          # Max 50% missing NPS
        "ratings": 30       # Max 30% missing ratings
    },
    "nps_range": (0, 10),
    "min_unique_nps_values": 3
}

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================

# Application metadata
APP_INFO = {
    "name": "Personal Comment Analyzer",
    "version": "2.0.0",
    "description": "Sistema de análisis de sentimientos de comentarios usando IA",
    "author": "AI Whisperers",
    "repository": "https://github.com/Ai-Whisperers/personal-analisis-ia"
}

# Feature flags
FEATURE_FLAGS = {
    "enable_mock_mode": True,           # Allow running without API key
    "enable_advanced_charts": True,    # Heatmaps, advanced visualizations
    "enable_export": True,             # File export functionality
    "enable_performance_monitoring": True,  # Performance tracking
    "enable_debug_mode": False,        # Debug information display
    "enable_batch_progress": True,     # Show batch processing progress
    "enable_rate_limit_monitoring": True,  # Track API usage
    "enable_dynamic_batch_sizing": True,   # Adjust batch size based on usage
    "enable_token_usage_logging": True     # Log token consumption
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_mock_mode() -> bool:
    """Check if running in mock mode (no API key or mock key)"""
    api_key = get_openai_api_key()
    return (not api_key or 
            api_key in ["", "your_openai_api_key_here", "mock", "test"] or 
            not FEATURE_FLAGS.get("enable_mock_mode", True))

def get_app_config() -> Dict[str, Any]:
    """Get complete application configuration"""
    return {
        "emotions": EMOTIONS_16,
        "emotion_categories": EMO_CATEGORIES,
        "batch_config": BATCH_CONFIG,
        "rate_limits": get_rate_limits(),
        "file_config": FILE_CONFIG,
        "sla_targets": SLA_TARGETS,
        "chart_config": CHART_CONFIG,
        "nps_categories": NPS_CATEGORIES,
        "churn_config": {
            "thresholds": CHURN_THRESHOLDS,
            "keywords": CHURN_KEYWORDS
        },
        "export_config": EXPORT_CONFIG,
        "validation_config": VALIDATION_CONFIG,
        "feature_flags": FEATURE_FLAGS,
        "app_info": APP_INFO
    }

def validate_config() -> tuple[bool, str]:
    """Validate configuration consistency
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    try:
        # Validate emotions configuration
        assert len(EMOTIONS_16) == 16, f"Expected 16 emotions, got {len(EMOTIONS_16)}"
        
        # Validate emotion categories
        all_categorized = sum(len(emotions) for emotions in EMO_CATEGORIES.values())
        assert all_categorized == 16, f"Not all emotions categorized: {all_categorized}/16"
        
        # Validate no duplicates in categories
        all_emotions_in_categories = []
        for emotions in EMO_CATEGORIES.values():
            all_emotions_in_categories.extend(emotions)
        assert len(all_emotions_in_categories) == len(set(all_emotions_in_categories)), "Duplicate emotions in categories"
        
        # Validate all emotions are categorized
        for emotion in EMOTIONS_16:
            found = False
            for category_emotions in EMO_CATEGORIES.values():
                if emotion in category_emotions:
                    found = True
                    break
            assert found, f"Emotion '{emotion}' not found in any category"
        
        return True, ""
    
    except AssertionError as e:
        return False, f"Configuration validation error: {e}"
    except Exception as e:
        return False, f"Unexpected configuration error: {e}"

# Validate configuration on import
if __name__ != "__main__":
    validate_config()