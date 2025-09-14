# -*- coding: utf-8 -*-
"""
Core API Client - Streamlined OpenAI API client
Handles the core API communication without batch processing logic
"""
import json
import time
import logging
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI

from utils.rate_limiter import RateLimiter
from utils.usage_monitor import UsageMonitor
from .batch_processor import BatchProcessor

logger = logging.getLogger(__name__)

# Import configuration for dynamic settings
try:
    from config import BATCH_CONFIG, LLM_CONFIG
    DEFAULT_MODEL = LLM_CONFIG.get('model', 'gpt-4o-mini')
    DEFAULT_MAX_TOKENS = LLM_CONFIG.get('max_tokens', 12000)
    DEFAULT_TEMPERATURE = LLM_CONFIG.get('temperature', 0.3)
except ImportError:
    DEFAULT_MODEL = 'gpt-4o-mini'
    DEFAULT_MAX_TOKENS = 12000
    DEFAULT_TEMPERATURE = 0.3

class LLMApiClient:
    """Streamlined OpenAI API client for high-throughput processing"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        if not api_key:
            raise ValueError("OpenAI API key is required. Mock mode has been eliminated.")

        # Validate API key format
        if not self._validate_api_key_format(api_key):
            raise ValueError("Invalid OpenAI API key format. Must start with 'sk-' and be at least 40 characters.")

        self.api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.client = OpenAI(api_key=api_key)
        self.max_retries = 3
        self.retry_delay = 0.5

        # Initialize components
        try:
            from config import BATCH_CONFIG
            self.config = BATCH_CONFIG
            self.rate_limiter = RateLimiter(BATCH_CONFIG)
            self.usage_monitor = UsageMonitor(BATCH_CONFIG)
            self.batch_processor = BatchProcessor(
                self.rate_limiter,
                self.usage_monitor,
                BATCH_CONFIG
            )
            logger.info(f"API client initialized: {BATCH_CONFIG.get('requests_per_minute', 'unknown')} RPM, {BATCH_CONFIG.get('tokens_per_minute', 'unknown')} TPM")
        except Exception as e:
            logger.error(f"Failed to initialize rate limiting: {e}")
            # Fallback configuration
            self.config = {'batch_size': 30, 'max_tokens_per_request': 12000}
            self.rate_limiter = None
            self.usage_monitor = None
            self.batch_processor = None

    def analyze_batch(self, comments: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze a batch of comments using single API call
        This is the main interface used by EngineController
        """
        if not comments:
            logger.warning("Empty comments list provided to analyze_batch")
            return []

        try:
            # Use batch processor if available
            if self.batch_processor:
                return self._analyze_batch_with_processor(comments)
            else:
                # Fallback to simple processing
                return self._analyze_batch_simple(comments)

        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return self._create_fallback_results(len(comments))

    def _analyze_batch_with_processor(self, comments: List[str]) -> List[Dict[str, Any]]:
        """Analyze batch using the batch processor"""
        # Prepare request
        request_data = self.batch_processor.prepare_batch_request(comments)

        # Check rate limits
        if not self.batch_processor.check_rate_limits_before_request(
            request_data['estimated_tokens']
        ):
            logger.error("Rate limit exceeded, cannot process batch")
            return self._create_fallback_results(len(comments))

        # Make API call
        response = self._make_api_call(request_data['messages'])

        if response:
            # Process response
            results = self.batch_processor.process_batch_response(
                response, request_data['comment_count']
            )

            # Record usage
            actual_tokens = getattr(response, 'usage', {}).get('total_tokens')
            self.batch_processor.record_request_usage(
                request_data['estimated_tokens'], actual_tokens
            )

            logger.info(f"Successfully processed batch of {len(comments)} comments")
            return results
        else:
            logger.error("API call failed")
            return self._create_fallback_results(len(comments))

    def _analyze_batch_simple(self, comments: List[str]) -> List[Dict[str, Any]]:
        """Simple batch analysis without rate limiting"""
        logger.warning("Using simple batch processing (rate limiting unavailable)")

        # Create simple request
        messages = [
            {
                "role": "system",
                "content": "Analyze the sentiment and emotions of the following comments. Respond with JSON array."
            },
            {
                "role": "user",
                "content": f"Analyze these comments: {comments[:10]}"  # Limit for safety
            }
        ]

        response = self._make_api_call(messages)

        if response:
            try:
                # Simple parsing
                content = response.strip()
                if content.startswith('['):
                    parsed = json.loads(content)
                    return parsed[:len(comments)]  # Match comment count
            except:
                pass

        return self._create_fallback_results(len(comments))

    def _make_api_call(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Make the actual API call with retry logic"""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Making API call (attempt {attempt + 1}/{self.max_retries})")

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=DEFAULT_MAX_TOKENS,
                    temperature=DEFAULT_TEMPERATURE,
                    response_format={"type": "json_object"} if "json" in messages[0]["content"].lower() else None
                )

                content = response.choices[0].message.content
                logger.debug(f"API call successful, response length: {len(content) if content else 0}")
                return content

            except openai.RateLimitError as e:
                logger.warning(f"Rate limit error on attempt {attempt + 1}: {e}")
                last_error = e

                if attempt < self.max_retries - 1:
                    # Exponential backoff with jitter
                    wait_time = (self.retry_delay * (2 ** attempt)) + (0.1 * attempt)
                    logger.info(f"Waiting {wait_time:.2f}s before retry")
                    time.sleep(wait_time)

            except openai.APIError as e:
                logger.error(f"API error on attempt {attempt + 1}: {e}")
                last_error = e

                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                last_error = e
                break

        logger.error(f"All API call attempts failed. Last error: {last_error}")
        return None

    def _create_fallback_results(self, count: int) -> List[Dict[str, Any]]:
        """Create fallback results when API calls fail"""
        try:
            from config import EMOTIONS_16
            emotions = EMOTIONS_16
        except ImportError:
            emotions = ["alegria", "tristeza", "enojo", "miedo", "confianza", "desagrado"]

        results = []
        for i in range(count):
            result = {
                'emotions': {emotion: 0.0 for emotion in emotions},
                'pain_points': [],
                'churn_risk': 0.0,
                'sentiment': 'neutral',
                '_fallback': True,
                '_index': i
            }
            results.append(result)

        logger.warning(f"Created {count} fallback results due to API failure")
        return results

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        if self.usage_monitor:
            return self.usage_monitor.get_current_usage()
        else:
            return {
                'requests_percentage': 0,
                'tokens_percentage': 0,
                'status': 'monitoring_unavailable'
            }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        if self.batch_processor:
            return self.batch_processor.get_performance_stats()
        else:
            return {
                'batch_processor': 'unavailable',
                'model': self.model,
                'max_retries': self.max_retries
            }

    def get_recommended_batch_size(self) -> int:
        """Get recommended batch size based on current usage"""
        if self.batch_processor:
            return self.batch_processor.get_batch_size_recommendation()
        else:
            return 30  # Safe default

    def _validate_api_key_format(self, api_key: str) -> bool:
        """Validate OpenAI API key format"""
        if not api_key or not isinstance(api_key, str):
            return False

        # Basic format validation
        if not api_key.startswith('sk-'):
            return False

        # Length validation (OpenAI keys are typically 51+ characters)
        if len(api_key) < 40:
            return False

        # Check for placeholder values
        placeholder_patterns = [
            'your-openai-api-key-here',
            'your-api-key',
            'placeholder',
            'sk-test',
            'sk-fake'
        ]

        api_key_lower = api_key.lower()
        for pattern in placeholder_patterns:
            if pattern in api_key_lower:
                return False

        return True