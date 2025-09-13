# -*- coding: utf-8 -*-
"""
LLM API Client - Optimized batch processing with single API calls
Handles rate limiting, retries, and performance optimization for 800-1200 comments in <10s
"""
import json
import time
import logging
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI

from .prompt_templates import PromptTemplates
from utils.rate_limiter import RateLimiter
from utils.usage_monitor import UsageMonitor

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
    """Optimized OpenAI API client for high-throughput batch processing"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, mock_mode: bool = False):
        self.api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.mock_mode = mock_mode
        self.client = OpenAI(api_key=api_key) if api_key and not mock_mode else None
        self.prompt_templates = PromptTemplates()
        self.max_retries = 5  # Increased for better reliability
        self.retry_delay = 1
        
        # Initialize intelligent rate limiter and usage monitor
        try:
            from config import BATCH_CONFIG
            self.config = BATCH_CONFIG
            self.rate_limiter = RateLimiter(BATCH_CONFIG)
            self.usage_monitor = UsageMonitor(BATCH_CONFIG)
            logger.info(f"API client initialized: {BATCH_CONFIG.get('requests_per_minute', 'unknown')} RPM, {BATCH_CONFIG.get('tokens_per_minute', 'unknown')} TPM")
        except ImportError:
            # Fallback configuration with conservative limits
            fallback_config = {
                'requests_per_minute': 400,  # 80% of 500 (Tier 1)
                'tokens_per_minute': 160000,  # 80% of 200k (Tier 1)
                'max_concurrent_batches': 3,
                'avg_tokens_per_comment': 150,
                'prompt_tokens': 800,
                'max_tokens_per_request': 12000,
                'batch_size': 50
            }
            self.config = fallback_config
            self.rate_limiter = RateLimiter(fallback_config)
            self.usage_monitor = UsageMonitor(fallback_config)
            logger.warning("Using fallback configuration for API client")
        
        # Performance tracking
        self.total_requests = 0
        self.total_tokens = 0
        self.session_start = time.time()
    
    def analyze_batch(self, comments: List[str]) -> List[Dict[str, Any]]:
        """Analyze batch of comments with single optimized API call"""
        if not comments:
            return []
        
        if not self.client or not self.api_key or self.mock_mode:
            logger.warning("No API key provided or mock mode enabled, using mock responses")
            return [self._get_mock_response(comment) for comment in comments]
        
        start_time = time.time()
        
        # Calculate optimal batch size based on current usage
        optimal_size = self._calculate_optimal_batch_size(comments)
        
        if len(comments) > optimal_size:
            logger.info(f"Splitting batch of {len(comments)} into optimal size of {optimal_size}")
            return self._split_and_analyze_batch(comments, optimal_size)
        
        # Check rate limits before proceeding
        can_proceed, reason = self.rate_limiter.can_make_request(comments)
        if not can_proceed:
            if "would be exceeded" in reason:
                # Wait for rate limit window to reset
                self.rate_limiter.wait_if_needed(comments)
            else:
                logger.warning(f"Rate limit check failed: {reason}")
                return [self._get_mock_response(comment) for comment in comments]
        
        # Log usage before request
        usage_before = self.rate_limiter.get_usage_stats()
        estimated_tokens = self.rate_limiter.calculate_batch_tokens(comments)
        logger.info(f"Processing batch: {len(comments)} comments, ~{estimated_tokens} tokens, {usage_before['requests_used']}/{usage_before['requests_limit']} RPM")
        
        try:
            # Make single API call for entire batch
            results = self._make_batch_api_call(comments)
            
            # Record metrics
            processing_time = time.time() - start_time
            self.rate_limiter.record_request(comments)
            self.usage_monitor.log_batch_usage(
                batch_size=len(comments),
                processing_time=processing_time,
                tokens_used=estimated_tokens,
                requests_made=1
            )
            
            # Log success
            usage_after = self.rate_limiter.get_usage_stats()
            logger.info(f"Batch completed in {processing_time:.2f}s: {usage_after['requests_used']}/{usage_after['requests_limit']} RPM ({usage_after['requests_percentage']:.1f}%), {usage_after['tokens_used']}/{usage_after['tokens_limit']} TPM ({usage_after['tokens_percentage']:.1f}%)")
            
            return results
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Batch processing failed after {processing_time:.2f}s: {e}")
            
            # Record failed batch for monitoring
            self.usage_monitor.log_batch_usage(
                batch_size=len(comments),
                processing_time=processing_time,
                tokens_used=estimated_tokens,
                requests_made=0,
                error_count=1
            )
            
            # Return mock responses as fallback
            return [self._get_mock_response(comment) for comment in comments]
    
    def _calculate_optimal_batch_size(self, comments: List[str]) -> int:
        """Calculate optimal batch size based on current usage and token limits"""
        # Get recommended size from rate limiter
        base_size = self.rate_limiter.get_recommended_batch_size()
        
        # Adjust based on current usage
        usage_stats = self.rate_limiter.get_usage_stats()
        tokens_used_percentage = usage_stats['tokens_percentage']
        requests_used_percentage = usage_stats['requests_percentage']
        
        # If we're close to limits, be more conservative
        if tokens_used_percentage > 70 or requests_used_percentage > 70:
            base_size = int(base_size * 0.7)  # 30% reduction
        elif tokens_used_percentage > 50 or requests_used_percentage > 50:
            base_size = int(base_size * 0.85)  # 15% reduction
        
        # Ensure minimum viable batch size
        return max(10, min(base_size, len(comments)))
    
    def _split_and_analyze_batch(self, comments: List[str], optimal_size: int) -> List[Dict[str, Any]]:
        """Split large batch into optimal chunks and process sequentially"""
        results = []
        
        for i in range(0, len(comments), optimal_size):
            chunk = comments[i:i + optimal_size]
            chunk_results = self.analyze_batch(chunk)
            results.extend(chunk_results)
            
            # Small delay between chunks to respect rate limits
            if i + optimal_size < len(comments):  # Not the last chunk
                time.sleep(0.1)
        
        return results
    
    def _make_batch_api_call(self, comments: List[str]) -> List[Dict[str, Any]]:
        """Make single API call for batch with exponential backoff retry"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Create batch prompt
                batch_prompt = self.prompt_templates.get_batch_analysis_prompt(comments)
                
                # Make API call
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.prompt_templates.get_system_prompt()},
                        {"role": "user", "content": batch_prompt}
                    ],
                    temperature=DEFAULT_TEMPERATURE,
                    max_tokens=DEFAULT_MAX_TOKENS
                )
                
                # Record actual token usage
                actual_tokens = None
                if hasattr(response, 'usage') and response.usage:
                    actual_tokens = response.usage.total_tokens
                    logger.debug(f"Actual token usage: {actual_tokens}")
                
                # Parse response
                content = response.choices[0].message.content
                results = self._parse_batch_response(content, len(comments))
                
                # Update tracking
                self.total_requests += 1
                if actual_tokens:
                    self.total_tokens += actual_tokens
                
                return results
                
            except openai.RateLimitError as e:
                # Record rate limit error and apply exponential backoff
                backoff_time = self.rate_limiter.record_rate_limit_error()
                logger.warning(f"Rate limit hit (attempt {attempt + 1}/{self.max_retries}), backing off for {backoff_time:.2f}s")
                
                # Log for monitoring
                self.usage_monitor.log_batch_usage(
                    batch_size=len(comments),
                    processing_time=0,
                    tokens_used=0,
                    requests_made=0,
                    rate_limited=True
                )
                
                if attempt < self.max_retries - 1:
                    time.sleep(backoff_time)
                last_exception = e
                
            except openai.APIError as e:
                if "insufficient_quota" in str(e).lower():
                    logger.error(f"API quota exhausted: {e}")
                    raise e  # Don't retry quota errors
                else:
                    logger.error(f"API error (attempt {attempt + 1}/{self.max_retries}): {e}")
                    if attempt < self.max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                        wait_time = min(2 ** attempt, 16)
                        time.sleep(wait_time)
                    last_exception = e
                    
            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                last_exception = e
        
        # All retries exhausted
        logger.error(f"All {self.max_retries} retries exhausted. Last error: {last_exception}")
        raise last_exception or Exception("Unknown error in batch processing")
    
    def _parse_batch_response(self, content: str, expected_count: int) -> List[Dict[str, Any]]:
        """Parse batch response JSON array with robust error handling"""
        try:
            # Extract JSON from response
            json_str = content.strip()
            if '```json' in content:
                json_start = content.find('```json') + 7
                json_end = content.find('```', json_start)
                json_str = content[json_start:json_end].strip()
            elif '```' in content:
                # Handle cases where JSON is in code blocks without 'json' label
                lines = content.split('\n')
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip() == '```':
                        in_code_block = not in_code_block
                    elif in_code_block or (line.strip().startswith('[') or line.strip().startswith('{')):
                        json_lines.append(line)
                json_str = '\n'.join(json_lines).strip()
            
            # Parse JSON
            parsed = json.loads(json_str)
            
            # Handle different response formats
            if isinstance(parsed, list):
                results = parsed
            elif isinstance(parsed, dict):
                # Single object response - wrap in list
                results = [parsed]
            else:
                logger.error(f"Unexpected response format: {type(parsed)}")
                return [self._get_default_response() for _ in range(expected_count)]
            
            # Validate and pad results
            validated_results = []
            for i, result in enumerate(results):
                if isinstance(result, dict) and self._validate_response_structure(result):
                    validated_results.append(result)
                else:
                    logger.warning(f"Invalid response structure for comment {i}, using default")
                    validated_results.append(self._get_default_response())
            
            # Ensure we have exactly the expected number of results
            while len(validated_results) < expected_count:
                validated_results.append(self._get_default_response())
            
            if len(validated_results) > expected_count:
                validated_results = validated_results[:expected_count]
            
            logger.info(f"Successfully parsed {len(validated_results)}/{expected_count} responses")
            return validated_results
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse batch JSON response: {e}")
            logger.error(f"Raw content preview: {content[:300]}...")
            return [self._get_default_response() for _ in range(expected_count)]
        except Exception as e:
            logger.error(f"Unexpected error parsing batch response: {e}")
            return [self._get_default_response() for _ in range(expected_count)]
    
    def _validate_response_structure(self, response: Dict[str, Any]) -> bool:
        """Validate that response has required structure"""
        required_fields = ['emotions', 'pain_points', 'churn_risk', 'sentiment']
        
        for field in required_fields:
            if field not in response:
                return False
        
        # Validate emotions is a dict
        if not isinstance(response['emotions'], dict):
            return False
        
        # Validate pain_points is a list
        if not isinstance(response['pain_points'], list):
            return False
        
        # Validate churn_risk is a number
        if not isinstance(response['churn_risk'], (int, float)):
            return False
        
        # Validate sentiment is a string
        if not isinstance(response['sentiment'], str):
            return False
        
        return True
    
    def _get_mock_response(self, comment: str) -> Dict[str, Any]:
        """Generate mock response for testing/fallback"""
        import random
        
        # Simple sentiment analysis
        positive_words = ['bueno', 'excelente', 'genial', 'perfecto', 'increíble', 'fantástico']
        negative_words = ['malo', 'terrible', 'horrible', 'pésimo', 'odio', 'problema']
        
        comment_lower = comment.lower()
        has_positive = any(word in comment_lower for word in positive_words)
        has_negative = any(word in comment_lower for word in negative_words)
        
        # Generate emotions based on sentiment
        try:
            from config import EMOTIONS_16
        except ImportError:
            EMOTIONS_16 = [
                "alegria", "tristeza", "enojo", "miedo", "confianza", "desagrado", 
                "sorpresa", "expectativa", "frustracion", "gratitud", "aprecio", 
                "indiferencia", "decepcion", "entusiasmo", "verguenza", "esperanza"
            ]
        
        emotions = {}
        if has_positive and not has_negative:
            primary_emotions = ['alegria', 'gratitud', 'entusiasmo', 'esperanza']
            sentiment = 'positive'
        elif has_negative and not has_positive:
            primary_emotions = ['frustracion', 'decepcion', 'enojo', 'tristeza']
            sentiment = 'negative'
        else:
            primary_emotions = ['indiferencia', 'sorpresa']
            sentiment = 'neutral'
        
        for emotion in EMOTIONS_16:
            if emotion in primary_emotions:
                emotions[emotion] = random.uniform(0.6, 1.0)
            else:
                emotions[emotion] = random.uniform(0.0, 0.3)
        
        return {
            'emotions': emotions,
            'pain_points': ['mock_pain_point'] if has_negative else [],
            'churn_risk': random.uniform(0.7, 1.0) if has_negative else random.uniform(0.0, 0.4),
            'sentiment': sentiment
        }
    
    def _get_default_response(self) -> Dict[str, Any]:
        """Default response when parsing fails"""
        try:
            from config import EMOTIONS_16
        except ImportError:
            EMOTIONS_16 = [
                "alegria", "tristeza", "enojo", "miedo", "confianza", "desagrado", 
                "sorpresa", "expectativa", "frustracion", "gratitud", "aprecio", 
                "indiferencia", "decepcion", "entusiasmo", "verguenza", "esperanza"
            ]
        
        return {
            'emotions': {emotion: 0.0 for emotion in EMOTIONS_16},
            'pain_points': [],
            'churn_risk': 0.5,
            'sentiment': 'neutral'
        }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics"""
        rate_stats = self.rate_limiter.get_usage_stats()
        session_stats = self.usage_monitor.get_session_summary()
        
        return {
            **rate_stats,
            'session_duration': time.time() - self.session_start,
            'total_api_requests': self.total_requests,
            'total_tokens_used': self.total_tokens,
            'session_summary': session_stats,
            'recommendations': self.usage_monitor.get_recommendations()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        stats = self.get_usage_stats()
        session_duration = stats['session_duration']
        
        return {
            'requests_per_second': self.total_requests / max(session_duration, 1),
            'tokens_per_second': self.total_tokens / max(session_duration, 1),
            'average_tokens_per_request': self.total_tokens / max(self.total_requests, 1),
            'session_duration': session_duration,
            'rate_limit_utilization': {
                'requests': stats['requests_percentage'],
                'tokens': stats['tokens_percentage']
            }
        }