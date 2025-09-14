# -*- coding: utf-8 -*-
"""
Batch Processor - Handles batch operations for LLM API calls
Extracted from api_call.py to comply with 480-line blueprint limit
"""
import json
import time
import logging
from typing import List, Dict, Any, Optional

from .prompt_templates import PromptTemplates
from utils.rate_limiter import RateLimiter
from utils.usage_monitor import UsageMonitor

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Handles batch processing logic for LLM API calls"""

    def __init__(self, rate_limiter: RateLimiter, usage_monitor: UsageMonitor, config: Dict[str, Any]):
        self.rate_limiter = rate_limiter
        self.usage_monitor = usage_monitor
        self.config = config
        self.prompt_templates = PromptTemplates()

        # Batch configuration
        self.max_batch_size = config.get('batch_size', 30)
        self.max_tokens_per_request = config.get('max_tokens_per_request', 12000)

        logger.info(f"Batch processor initialized with max_batch_size={self.max_batch_size}")

    def prepare_batch_request(self, comments: List[str]) -> Dict[str, Any]:
        """Prepare a batch of comments for API processing"""
        if not comments:
            raise ValueError("Comments list cannot be empty")

        if len(comments) > self.max_batch_size:
            logger.warning(f"Batch size {len(comments)} exceeds maximum {self.max_batch_size}, truncating")
            comments = comments[:self.max_batch_size]

        # Create the system prompt for batch processing
        system_prompt = self.prompt_templates.get_system_prompt()

        # Create user prompt with all comments
        user_prompt = self.prompt_templates.create_batch_user_prompt(comments)

        # Estimate token usage
        estimated_tokens = self._estimate_tokens(system_prompt, user_prompt)

        if estimated_tokens > self.max_tokens_per_request:
            logger.warning(f"Estimated tokens {estimated_tokens} exceeds limit {self.max_tokens_per_request}")
            # Reduce batch size proportionally
            reduction_factor = self.max_tokens_per_request / estimated_tokens
            new_size = int(len(comments) * reduction_factor * 0.9)  # 10% safety margin
            comments = comments[:max(1, new_size)]
            user_prompt = self.prompt_templates.create_batch_user_prompt(comments)
            estimated_tokens = self._estimate_tokens(system_prompt, user_prompt)
            logger.info(f"Reduced batch to {len(comments)} comments, estimated tokens: {estimated_tokens}")

        return {
            'messages': [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            'estimated_tokens': estimated_tokens,
            'comment_count': len(comments)
        }

    def _estimate_tokens(self, system_prompt: str, user_prompt: str) -> int:
        """Estimate token usage for the request"""
        # Simple estimation: ~4 characters per token
        total_chars = len(system_prompt) + len(user_prompt)
        estimated_tokens = int(total_chars / 4)

        # Add output tokens estimation (generous estimate for JSON responses)
        output_tokens = len(self._get_comments_from_prompt(user_prompt)) * 50  # ~50 tokens per comment response

        return estimated_tokens + output_tokens

    def _get_comments_from_prompt(self, user_prompt: str) -> List[str]:
        """Extract comment count from user prompt for token estimation"""
        # This is a simple estimation based on the prompt structure
        # Count the number of "COMENTARIO" markers in the prompt
        return user_prompt.count("COMENTARIO")

    def process_batch_response(self, response_content: str, comment_count: int) -> List[Dict[str, Any]]:
        """Process the API response and extract structured data"""
        try:
            # Parse the JSON response
            if response_content.strip().startswith('['):
                # Direct JSON array
                parsed_data = json.loads(response_content.strip())
            else:
                # Try to extract JSON from markdown or other formatting
                parsed_data = self._extract_json_from_response(response_content)

            if not isinstance(parsed_data, list):
                logger.error(f"Expected list, got {type(parsed_data)}")
                return self._create_fallback_responses(comment_count)

            if len(parsed_data) != comment_count:
                logger.warning(f"Response count mismatch: expected {comment_count}, got {len(parsed_data)}")
                # Adjust the response list
                parsed_data = self._adjust_response_count(parsed_data, comment_count)

            # Validate and clean each response
            cleaned_responses = []
            for i, response in enumerate(parsed_data):
                cleaned_response = self._validate_and_clean_response(response, i)
                cleaned_responses.append(cleaned_response)

            return cleaned_responses

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return self._create_fallback_responses(comment_count)
        except Exception as e:
            logger.error(f"Unexpected error processing response: {e}")
            return self._create_fallback_responses(comment_count)

    def _extract_json_from_response(self, content: str) -> List[Dict[str, Any]]:
        """Extract JSON from response that might be wrapped in markdown or other formatting"""
        # Remove markdown code blocks
        content = content.replace('```json', '').replace('```', '')

        # Find JSON array markers
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1

        if start_idx == -1 or end_idx == 0:
            raise json.JSONDecodeError("No JSON array found", content, 0)

        json_str = content[start_idx:end_idx]
        return json.loads(json_str)

    def _adjust_response_count(self, responses: List[Dict], expected_count: int) -> List[Dict]:
        """Adjust response list to match expected count"""
        if len(responses) > expected_count:
            # Truncate to expected count
            return responses[:expected_count]
        elif len(responses) < expected_count:
            # Pad with fallback responses
            padding_needed = expected_count - len(responses)
            for i in range(padding_needed):
                responses.append(self._create_fallback_response(len(responses) + i))
            return responses
        else:
            return responses

    def _validate_and_clean_response(self, response: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Validate and clean individual response"""
        try:
            # Ensure required structure
            cleaned = {
                'emotions': response.get('emotions', {}),
                'pain_points': response.get('pain_points', []),
                'churn_risk': response.get('churn_risk', 0.0),
                'sentiment': response.get('sentiment', 'neutral')
            }

            # Validate emotions
            if not isinstance(cleaned['emotions'], dict):
                logger.warning(f"Invalid emotions format in response {index}, using defaults")
                cleaned['emotions'] = {}

            # Ensure all 16 emotions are present
            from config import EMOTIONS_16
            for emotion in EMOTIONS_16:
                if emotion not in cleaned['emotions']:
                    cleaned['emotions'][emotion] = 0.0
                else:
                    # Ensure numeric value
                    try:
                        cleaned['emotions'][emotion] = float(cleaned['emotions'][emotion])
                    except (ValueError, TypeError):
                        cleaned['emotions'][emotion] = 0.0

            # Validate pain points
            if not isinstance(cleaned['pain_points'], list):
                cleaned['pain_points'] = []

            # Validate churn risk
            try:
                cleaned['churn_risk'] = max(0.0, min(1.0, float(cleaned['churn_risk'])))
            except (ValueError, TypeError):
                cleaned['churn_risk'] = 0.0

            return cleaned

        except Exception as e:
            logger.error(f"Error validating response {index}: {e}")
            return self._create_fallback_response(index)

    def _create_fallback_responses(self, count: int) -> List[Dict[str, Any]]:
        """Create fallback responses when parsing fails"""
        return [self._create_fallback_response(i) for i in range(count)]

    def _create_fallback_response(self, index: int) -> Dict[str, Any]:
        """Create a single fallback response with default values"""
        from config import EMOTIONS_16

        return {
            'emotions': {emotion: 0.0 for emotion in EMOTIONS_16},
            'pain_points': [],
            'churn_risk': 0.0,
            'sentiment': 'neutral',
            '_fallback': True,
            '_index': index
        }

    def check_rate_limits_before_request(self, estimated_tokens: int) -> bool:
        """Check if we can make a request without hitting rate limits"""
        try:
            # Check current usage
            can_proceed = self.rate_limiter.can_make_request(tokens=estimated_tokens)

            if not can_proceed:
                current_usage = self.usage_monitor.get_current_usage()
                logger.warning(f"Rate limit would be exceeded. Current usage: {current_usage}")

                # Calculate wait time
                wait_time = self.rate_limiter.get_wait_time()
                if wait_time > 0:
                    logger.info(f"Waiting {wait_time:.2f}s before making request")
                    time.sleep(wait_time)
                    return True  # Try again after waiting

                return False

            return True

        except Exception as e:
            logger.error(f"Error checking rate limits: {e}")
            return True  # Proceed cautiously if rate limit check fails

    def record_request_usage(self, estimated_tokens: int, actual_tokens: Optional[int] = None):
        """Record usage after making a request"""
        try:
            tokens_used = actual_tokens if actual_tokens is not None else estimated_tokens

            self.rate_limiter.record_request(tokens=tokens_used)
            self.usage_monitor.record_request(tokens=tokens_used)

            # Log usage statistics
            current_usage = self.usage_monitor.get_current_usage()
            logger.debug(f"Request recorded: {tokens_used} tokens. Current usage: {current_usage}")

            # Check for usage warnings
            if current_usage.get('tokens_percentage', 0) > 80:
                logger.warning(f"High token usage: {current_usage['tokens_percentage']:.1f}%")

            if current_usage.get('requests_percentage', 0) > 80:
                logger.warning(f"High request usage: {current_usage['requests_percentage']:.1f}%")

        except Exception as e:
            logger.error(f"Error recording usage: {e}")

    def get_batch_size_recommendation(self) -> int:
        """Get recommended batch size based on current usage"""
        try:
            current_usage = self.usage_monitor.get_current_usage()
            tokens_percentage = current_usage.get('tokens_percentage', 0)
            requests_percentage = current_usage.get('requests_percentage', 0)

            # Reduce batch size if usage is high
            if tokens_percentage > 80 or requests_percentage > 80:
                return max(10, self.max_batch_size // 2)
            elif tokens_percentage > 60 or requests_percentage > 60:
                return max(15, int(self.max_batch_size * 0.75))
            else:
                return self.max_batch_size

        except Exception as e:
            logger.error(f"Error getting batch size recommendation: {e}")
            return self.max_batch_size

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        try:
            usage_stats = self.usage_monitor.get_current_usage()
            return {
                'max_batch_size': self.max_batch_size,
                'recommended_batch_size': self.get_batch_size_recommendation(),
                'current_usage': usage_stats,
                'max_tokens_per_request': self.max_tokens_per_request
            }
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return {
                'max_batch_size': self.max_batch_size,
                'error': str(e)
            }