# -*- coding: utf-8 -*-
"""
AI Engine Controller - Optimized pipeline orchestration
parse → smart_batch → single_LLM_call → merge
Optimized for 800-1200 comments in <10s with intelligent rate limiting
"""
import pandas as pd
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .api_call import LLMApiClient
from .emotion_module import EmotionAnalyzer
from .pain_points_module import PainPointsAnalyzer
from .churn_module import ChurnAnalyzer
from .nps_module import NPSAnalyzer
from ..file_processor import reader, cleaner, validator, normalizer

logger = logging.getLogger(__name__)

# Optimized configuration for high performance
DEFAULT_CONFIG = {
    'batch_size': 80,  # Optimized for token limits
    'max_concurrent_batches': 3  # Conservative for rate limits
}

class EngineController:
    """Optimized pipeline orchestrator for high-throughput processing"""
    
    def __init__(self, api_client: LLMApiClient, config: Dict[str, Any] = None):
        self.api_client = api_client
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.emotion_analyzer = EmotionAnalyzer()
        self.pain_analyzer = PainPointsAnalyzer()
        self.churn_analyzer = ChurnAnalyzer()
        self.nps_analyzer = NPSAnalyzer()
        
        # Dynamic batch sizing based on rate limits
        self.batch_size = self._calculate_optimal_batch_size()
        
        # Performance tracking
        self.total_comments_processed = 0
        self.total_processing_time = 0.0
        
        logger.info(f"Engine controller initialized with batch_size={self.batch_size}, max_concurrent={self.config['max_concurrent_batches']}")
    
    def run_pipeline(self, file_path: str) -> pd.DataFrame:
        """Optimized main pipeline execution for high performance"""
        start_time = time.time()
        logger.info(f"Starting optimized pipeline for file: {file_path}")
        
        # Step 1: Parse and clean with timing
        file_start = time.time()
        df = reader.read_excel(file_path)
        df = cleaner.clean(df)
        df = validator.validate(df)
        df = normalizer.normalize(df)
        file_time = time.time() - file_start
        
        comment_count = len(df)
        logger.info(f"File processing completed in {file_time:.2f}s. Processing {comment_count} comments with target <10s")
        
        # Step 2: Create optimized batches based on current API usage
        batch_start = time.time()
        batches = self._create_optimized_batches(df)
        batch_time = time.time() - batch_start
        
        # Step 3: Process batches with intelligent concurrency
        llm_start = time.time()
        results = self._process_batches_optimized(batches)
        llm_time = time.time() - llm_start
        
        # Step 4: Merge results back to DataFrame
        merge_start = time.time()
        final_df = self._merge_results(df, results)
        merge_time = time.time() - merge_start
        
        # Performance reporting
        total_time = time.time() - start_time
        self.total_processing_time += total_time
        self.total_comments_processed += comment_count
        
        avg_time_per_comment = total_time / comment_count if comment_count > 0 else 0
        logger.info(f"Pipeline completed in {total_time:.2f}s for {comment_count} comments ({avg_time_per_comment*1000:.1f}ms/comment)")
        logger.info(f"Timing breakdown: File={file_time:.2f}s, Batch={batch_time:.2f}s, LLM={llm_time:.2f}s, Merge={merge_time:.2f}s")
        
        # Log performance metrics
        if hasattr(self.api_client, 'get_performance_metrics'):
            metrics = self.api_client.get_performance_metrics()
            logger.info(f"API Performance: {metrics['requests_per_second']:.1f} req/s, {metrics['tokens_per_second']:.0f} tokens/s")
        
        return final_df
    
    def _calculate_optimal_batch_size(self) -> int:
        """Calculate optimal batch size based on API client configuration"""
        if hasattr(self.api_client, 'get_recommended_batch_size'):
            recommended = self.api_client.get_recommended_batch_size()
            optimal_size = min(recommended, self.config['batch_size'])
        else:
            optimal_size = self.config['batch_size']
        
        return max(10, optimal_size)  # Minimum 10 comments per batch
    
    def _create_optimized_batches(self, df: pd.DataFrame) -> List[pd.DataFrame]:
        """Create optimized batches based on current API usage and performance targets"""
        # Recalculate batch size based on current conditions
        current_batch_size = self._calculate_optimal_batch_size()
        
        batches = []
        for i in range(0, len(df), current_batch_size):
            batch = df.iloc[i:i + current_batch_size].copy()
            batches.append(batch)
        
        logger.info(f"Created {len(batches)} optimized batches of max {current_batch_size} rows")
        return batches
    
    def _process_batches_optimized(self, batches: List[pd.DataFrame]) -> List[Dict[str, Any]]:
        """Process batches with intelligent concurrency and rate limiting"""
        results = []
        
        # Calculate optimal concurrency based on rate limits
        max_workers = self._calculate_optimal_concurrency()
        
        if max_workers == 1 or len(batches) == 1:
            # Sequential processing for rate limit safety
            logger.info("Processing batches sequentially for rate limit safety")
            for i, batch in enumerate(batches):
                logger.info(f"Processing batch {i+1}/{len(batches)}")
                batch_results = self._process_single_batch(batch)
                results.extend(batch_results)
        else:
            # Parallel processing with controlled concurrency
            logger.info(f"Processing {len(batches)} batches with {max_workers} workers")
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_batch = {
                    executor.submit(self._process_single_batch, batch): i 
                    for i, batch in enumerate(batches)
                }
                
                for future in as_completed(future_to_batch):
                    try:
                        batch_idx = future_to_batch[future]
                        batch_results = future.result()
                        results.extend(batch_results)
                        logger.info(f"Completed batch {batch_idx + 1}/{len(batches)}")
                    except Exception as e:
                        batch_idx = future_to_batch[future]
                        logger.error(f"Error processing batch {batch_idx + 1}: {e}")
                        # Continue with other batches, don't fail entire pipeline
                        continue
        
        logger.info(f"Processed {len(results)} total comments across {len(batches)} batches")
        return results
    
    def _calculate_optimal_concurrency(self) -> int:
        """Calculate optimal concurrency based on current API usage"""
        # Get current usage statistics from API client
        if hasattr(self.api_client, 'get_usage_stats'):
            usage_stats = self.api_client.get_usage_stats()
            tokens_percentage = usage_stats.get('tokens_percentage', 0)
            requests_percentage = usage_stats.get('requests_percentage', 0)
            
            # Reduce concurrency if we're close to rate limits
            if tokens_percentage > 70 or requests_percentage > 70:
                return 1  # Sequential processing
            elif tokens_percentage > 50 or requests_percentage > 50:
                return min(2, self.config['max_concurrent_batches'])
        
        return self.config['max_concurrent_batches']
    
    def _process_single_batch(self, batch: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process single batch with optimized single API call"""
        start_time = time.time()
        comments = batch['Comentario Final'].tolist()
        
        logger.debug(f"Processing batch of {len(comments)} comments")
        
        # Single optimized API call for entire batch
        llm_responses = self.api_client.analyze_batch(comments)
        
        # Process each response through all analyzers
        batch_results = []
        for i, (_, row) in enumerate(batch.iterrows()):
            llm_response = llm_responses[i] if i < len(llm_responses) else {}
            
            # Run all analyzers on this single response
            emotions = self.emotion_analyzer.analyze(llm_response)
            pain_points = self.pain_analyzer.analyze(llm_response)
            churn_risk = self.churn_analyzer.analyze(llm_response)
            nps_category = self.nps_analyzer.analyze(llm_response, row.get('NPS', 0))
            
            result = {
                'index': row.name,  # Original DataFrame index
                'emotions': emotions,
                'pain_points': pain_points,
                'churn_risk': churn_risk,
                'nps_category': nps_category
            }
            batch_results.append(result)
        
        batch_time = time.time() - start_time
        logger.debug(f"Batch of {len(comments)} processed in {batch_time:.2f}s ({batch_time/len(comments)*1000:.1f}ms/comment)")
        
        return batch_results
    
    def _merge_results(self, original_df: pd.DataFrame, results: List[Dict[str, Any]]) -> pd.DataFrame:
        """Efficiently merge analysis results back into the original DataFrame"""
        df = original_df.copy()
        
        # Create emotion columns efficiently
        emotion_cols = {}
        for emotion in self.emotion_analyzer.get_emotions():
            emotion_cols[f'emo_{emotion}'] = 0.0
        
        # Add analysis columns
        df = df.assign(**emotion_cols)
        df['pain_points'] = ''
        df['churn_risk'] = 0.0
        df['nps_category'] = ''
        
        # Fill with results - optimized for performance
        results_processed = 0
        for result in results:
            idx = result['index']
            if idx in df.index:
                # Update emotion scores
                for emotion, score in result['emotions'].items():
                    col_name = f'emo_{emotion}'
                    if col_name in df.columns:
                        df.at[idx, col_name] = score
                
                # Update other analysis results
                df.at[idx, 'pain_points'] = ', '.join(result['pain_points']) if result['pain_points'] else ''
                df.at[idx, 'churn_risk'] = result['churn_risk']
                df.at[idx, 'nps_category'] = result['nps_category']
                results_processed += 1
        
        logger.info(f"Merged {results_processed}/{len(results)} analysis results into DataFrame")
        return df
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for the controller"""
        avg_time_per_comment = (self.total_processing_time / self.total_comments_processed 
                               if self.total_comments_processed > 0 else 0)
        
        return {
            'total_comments_processed': self.total_comments_processed,
            'total_processing_time': self.total_processing_time,
            'average_time_per_comment_ms': avg_time_per_comment * 1000,
            'estimated_time_for_1000_comments': avg_time_per_comment * 1000,
            'current_batch_size': self.batch_size,
            'api_client_stats': self.api_client.get_usage_stats() if hasattr(self.api_client, 'get_usage_stats') else {}
        }