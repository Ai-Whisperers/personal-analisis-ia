"""
LLM API Client - Parallel calls with ThreadPoolExecutor
Handles retries, JSON parsing, and mock fallback
"""
import json
import time
import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import openai
from openai import OpenAI

from .prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)

# Import configuration for dynamic settings
try:
    from config import BATCH_CONFIG, LLM_CONFIG
    MAX_WORKERS = BATCH_CONFIG.get('max_concurrent_batches', 4)
    DEFAULT_MODEL = LLM_CONFIG.get('model', 'gpt-4o-mini')
    DEFAULT_MAX_TOKENS = LLM_CONFIG.get('max_tokens', 12000)
    DEFAULT_TEMPERATURE = LLM_CONFIG.get('temperature', 0.3)
except ImportError:
    MAX_WORKERS = 4  # Fallback
    DEFAULT_MODEL = 'gpt-4o-mini'  # Blueprint default
    DEFAULT_MAX_TOKENS = 12000  # Blueprint default
    DEFAULT_TEMPERATURE = 0.3

class LLMApiClient:
    """OpenAI API client with parallel processing and fallback"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or DEFAULT_MODEL  # Use configuration default
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.prompt_templates = PromptTemplates()
        self.max_retries = 3
        self.retry_delay = 1
    
    def analyze_batch(self, comments: List[str]) -> List[Dict[str, Any]]:
        """Analyze a batch of comments in parallel"""
        if not comments:
            return []
        
        if not self.client or not self.api_key:
            logger.warning("No API key provided, using mock responses")
            return [self._get_mock_response(comment) for comment in comments]
        
        results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_comment = {
                executor.submit(self._analyze_single_comment, comment): comment
                for comment in comments
            }
            
            for future in as_completed(future_to_comment):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    comment = future_to_comment[future]
                    logger.error(f"Error analyzing comment '{comment[:50]}...': {e}")
                    results.append(self._get_mock_response(comment))
        
        return results
    
    def _analyze_single_comment(self, comment: str) -> Dict[str, Any]:
        """Analyze a single comment with retries"""
        for attempt in range(self.max_retries):
            try:
                prompt = self.prompt_templates.get_analysis_prompt(comment)
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.prompt_templates.get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=DEFAULT_TEMPERATURE,
                    max_tokens=DEFAULT_MAX_TOKENS
                )
                
                content = response.choices[0].message.content
                return self._parse_response(content)
                
            except openai.RateLimitError:
                wait_time = (2 ** attempt) * self.retry_delay
                logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}")
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    logger.error("All retries exhausted, using mock response")
                    return self._get_mock_response(comment)
                time.sleep(self.retry_delay)
        
        return self._get_mock_response(comment)
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response JSON"""
        try:
            # Try to extract JSON from response
            if '```json' in content:
                json_start = content.find('```json') + 7
                json_end = content.find('```', json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content.strip()
            
            parsed = json.loads(json_str)
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw content: {content}")
            return self._get_default_response()
    
    def _get_mock_response(self, comment: str) -> Dict[str, Any]:
        """Generate a mock response for testing"""
        import random
        
        # Simple sentiment analysis based on keywords
        positive_words = ['bueno', 'excelente', 'genial', 'perfecto', 'increíble', 'fantástico']
        negative_words = ['malo', 'terrible', 'horrible', 'pésimo', 'odio', 'problema']
        
        comment_lower = comment.lower()
        has_positive = any(word in comment_lower for word in positive_words)
        has_negative = any(word in comment_lower for word in negative_words)
        
        # Generate mock emotions based on sentiment
        if has_positive and not has_negative:
            primary_emotions = ['alegria', 'gratitud', 'entusiasmo', 'esperanza']
        elif has_negative and not has_positive:
            primary_emotions = ['frustracion', 'decepcion', 'enojo', 'tristeza']
        else:
            primary_emotions = ['indiferencia', 'sorpresa']
        
        # Create mock emotion scores
        emotions = {}
        from config import EMOTIONS_16
        for emotion in EMOTIONS_16:
            if emotion in primary_emotions:
                emotions[emotion] = random.uniform(0.6, 1.0)
            else:
                emotions[emotion] = random.uniform(0.0, 0.3)
        
        return {
            'emotions': emotions,
            'pain_points': ['mock_pain_point'] if has_negative else [],
            'churn_risk': random.uniform(0.7, 1.0) if has_negative else random.uniform(0.0, 0.4),
            'sentiment': 'negative' if has_negative else ('positive' if has_positive else 'neutral')
        }
    
    def _get_default_response(self) -> Dict[str, Any]:
        """Default response when parsing fails"""
        from config import EMOTIONS_16
        return {
            'emotions': {emotion: 0.0 for emotion in EMOTIONS_16},
            'pain_points': [],
            'churn_risk': 0.5,
            'sentiment': 'neutral'
        }