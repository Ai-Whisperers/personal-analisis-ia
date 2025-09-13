# -*- coding: utf-8 -*-
"""
Rate Limiter - Smart token and request rate limiting for API calls
Prevents 429 errors by tracking usage and applying intelligent backoff
"""
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from threading import Lock
import tiktoken

logger = logging.getLogger(__name__)

@dataclass
class UsageWindow:
    """Track API usage in a time window"""
    start_time: float = field(default_factory=time.time)
    requests_made: int = 0
    tokens_used: int = 0
    
    def is_expired(self, window_seconds: int = 60) -> bool:
        """Check if this window has expired"""
        return time.time() - self.start_time > window_seconds
    
    def reset(self) -> None:
        """Reset the window"""
        self.start_time = time.time()
        self.requests_made = 0
        self.tokens_used = 0

class RateLimiter:
    """Intelligent rate limiter with token counting and backoff"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.current_window = UsageWindow()
        self.lock = Lock()
        
        # Get rate limits from config
        self.requests_per_minute = config.get('requests_per_minute', 450)
        self.tokens_per_minute = config.get('tokens_per_minute', 200000)
        self.max_concurrent = config.get('max_concurrent_batches', 4)
        
        # Token estimation
        self.avg_tokens_per_comment = config.get('avg_tokens_per_comment', 150)
        self.prompt_tokens = config.get('prompt_tokens', 800)
        self.max_tokens_per_request = config.get('max_tokens_per_request', 12000)
        
        # Backoff settings
        self.base_backoff = 1.0
        self.max_backoff = 60.0
        self.backoff_multiplier = 2.0
        self.consecutive_429s = 0
        
        # Initialize tokenizer for accurate counting
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4o-mini")
        except Exception:
            logger.warning("Could not load tokenizer, using estimation")
            self.tokenizer = None
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        
        # Fallback estimation: ~4 characters per token
        return max(1, len(text) // 4)
    
    def calculate_batch_tokens(self, comments: list[str]) -> int:
        """Calculate total tokens for a batch of comments"""
        total_tokens = self.prompt_tokens  # Base prompt tokens
        
        for comment in comments:
            total_tokens += self.estimate_tokens(comment)
        
        # Add estimated response tokens (roughly 50% of input)
        total_tokens += int(total_tokens * 0.5)
        
        return total_tokens
    
    def can_make_request(self, comments: list[str]) -> tuple[bool, str]:
        """Check if a request can be made without exceeding limits"""
        with self.lock:
            # Reset window if expired
            if self.current_window.is_expired():
                self.current_window.reset()
            
            # Calculate tokens for this request
            request_tokens = self.calculate_batch_tokens(comments)
            
            # Check request limit
            if self.current_window.requests_made >= self.requests_per_minute:
                return False, f"Request limit exceeded: {self.current_window.requests_made}/{self.requests_per_minute} RPM"
            
            # Check token limit
            if self.current_window.tokens_used + request_tokens > self.tokens_per_minute:
                return False, f"Token limit would be exceeded: {self.current_window.tokens_used + request_tokens}/{self.tokens_per_minute} TPM"
            
            # Check if batch is too large for single request
            if request_tokens > self.max_tokens_per_request:
                return False, f"Batch too large: {request_tokens} > {self.max_tokens_per_request} tokens per request"
            
            return True, "OK"
    
    def record_request(self, comments: list[str], actual_tokens: Optional[int] = None) -> None:
        """Record a successful request"""
        with self.lock:
            if self.current_window.is_expired():
                self.current_window.reset()
            
            self.current_window.requests_made += 1
            
            if actual_tokens:
                self.current_window.tokens_used += actual_tokens
            else:
                estimated_tokens = self.calculate_batch_tokens(comments)
                self.current_window.tokens_used += estimated_tokens
            
            # Reset consecutive 429s on success
            self.consecutive_429s = 0
    
    def record_rate_limit_error(self) -> float:
        """Record a 429 error and return backoff time"""
        with self.lock:
            self.consecutive_429s += 1
            backoff_time = min(
                self.base_backoff * (self.backoff_multiplier ** self.consecutive_429s),
                self.max_backoff
            )
            
            logger.warning(f"Rate limit hit (#{self.consecutive_429s}), backing off for {backoff_time:.2f}s")
            return backoff_time
    
    def get_recommended_batch_size(self, comment_length_avg: int = None) -> int:
        """Get recommended batch size based on current usage and limits"""
        if comment_length_avg is None:
            comment_length_avg = self.avg_tokens_per_comment
        
        # Calculate max comments that fit in token limit
        available_tokens = self.max_tokens_per_request - self.prompt_tokens
        max_comments_by_tokens = available_tokens // comment_length_avg
        
        # Consider current usage
        with self.lock:
            if self.current_window.is_expired():
                remaining_tokens = self.tokens_per_minute
                remaining_requests = self.requests_per_minute
            else:
                remaining_tokens = self.tokens_per_minute - self.current_window.tokens_used
                remaining_requests = self.requests_per_minute - self.current_window.requests_made
        
        # If low on tokens, reduce batch size
        if remaining_tokens < self.tokens_per_minute * 0.2:  # Less than 20% remaining
            max_comments_by_tokens = min(max_comments_by_tokens, remaining_tokens // (comment_length_avg * 2))
        
        # Ensure we don't exceed request limits
        if remaining_requests < 5:  # Low on requests
            max_comments_by_tokens = min(max_comments_by_tokens, 10)
        
        return max(1, min(max_comments_by_tokens, self.config.get('batch_size', 100)))
    
    def wait_if_needed(self, comments: list[str]) -> None:
        """Wait if necessary before making a request"""
        can_proceed, reason = self.can_make_request(comments)
        
        if not can_proceed:
            if "Request limit exceeded" in reason:
                # Wait until next minute
                with self.lock:
                    time_to_wait = 60 - (time.time() - self.current_window.start_time)
                    if time_to_wait > 0:
                        logger.info(f"Waiting {time_to_wait:.2f}s for request limit reset")
                        time.sleep(time_to_wait)
            
            elif "Token limit" in reason:
                # Wait until next minute or reduce batch size
                with self.lock:
                    time_to_wait = 60 - (time.time() - self.current_window.start_time)
                    if time_to_wait > 0:
                        logger.info(f"Waiting {time_to_wait:.2f}s for token limit reset")
                        time.sleep(time_to_wait)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        with self.lock:
            if self.current_window.is_expired():
                return {
                    'requests_used': 0,
                    'requests_limit': self.requests_per_minute,
                    'requests_percentage': 0,
                    'tokens_used': 0,
                    'tokens_limit': self.tokens_per_minute,
                    'tokens_percentage': 0,
                    'window_remaining_seconds': 60,
                    'consecutive_rate_limits': self.consecutive_429s
                }
            
            window_remaining = 60 - (time.time() - self.current_window.start_time)
            
            return {
                'requests_used': self.current_window.requests_made,
                'requests_limit': self.requests_per_minute,
                'requests_percentage': (self.current_window.requests_made / self.requests_per_minute) * 100,
                'tokens_used': self.current_window.tokens_used,
                'tokens_limit': self.tokens_per_minute,
                'tokens_percentage': (self.current_window.tokens_used / self.tokens_per_minute) * 100,
                'window_remaining_seconds': max(0, window_remaining),
                'consecutive_rate_limits': self.consecutive_429s
            }