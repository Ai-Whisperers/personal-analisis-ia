# -*- coding: utf-8 -*-
"""
AI Engine Controller - Orchestrates the entire pipeline
parse → batch → LLM → merge
"""
import pandas as pd
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

# Default configuration - can be overridden via constructor
DEFAULT_CONFIG = {
    'batch_size': 100,
    'max_concurrent_batches': 4
}

class EngineController:
    """Main orchestrator for the analysis pipeline"""
    
    def __init__(self, api_client: LLMApiClient, config: Dict[str, Any] = None):
        self.api_client = api_client
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.emotion_analyzer = EmotionAnalyzer()
        self.pain_analyzer = PainPointsAnalyzer()
        self.churn_analyzer = ChurnAnalyzer()
        self.nps_analyzer = NPSAnalyzer()
        self.batch_size = self.config['batch_size']
    
    def run_pipeline(self, file_path: str) -> pd.DataFrame:
        """Main pipeline execution"""
        logger.info(f"Starting pipeline for file: {file_path}")
        
        # Step 1: Parse and clean
        df = reader.read_excel(file_path)
        df = cleaner.clean(df)
        df = validator.validate(df)
        df = normalizer.normalize(df)
        
        # Step 2: Create batches
        batches = self._create_batches(df)
        
        # Step 3: Process batches in parallel
        results = self._process_batches_parallel(batches)
        
        # Step 4: Merge results back to DataFrame
        final_df = self._merge_results(df, results)
        
        logger.info("Pipeline completed successfully")
        return final_df
    
    def _create_batches(self, df: pd.DataFrame) -> List[pd.DataFrame]:
        """Split DataFrame into batches for parallel processing"""
        batches = []
        for i in range(0, len(df), self.batch_size):
            batch = df.iloc[i:i + self.batch_size].copy()
            batches.append(batch)
        
        logger.info(f"Created {len(batches)} batches of max {self.batch_size} rows")
        return batches
    
    def _process_batches_parallel(self, batches: List[pd.DataFrame]) -> List[Dict[str, Any]]:
        """Process all batches in parallel using ThreadPoolExecutor"""
        results = []
        max_workers = self.config['max_concurrent_batches']
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {
                executor.submit(self._process_single_batch, batch): batch 
                for batch in batches
            }
            
            for future in as_completed(future_to_batch):
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                except Exception as e:
                    logger.error(f"Error processing batch: {e}")
                    raise
        
        return results
    
    def _process_single_batch(self, batch: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process a single batch through LLM and all analyzers"""
        comments = batch['Comentario Final'].tolist()
        
        # Get LLM responses for all comments in batch
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
        
        return batch_results
    
    def _merge_results(self, original_df: pd.DataFrame, results: List[Dict[str, Any]]) -> pd.DataFrame:
        """Merge analysis results back into the original DataFrame"""
        df = original_df.copy()
        
        # Create emotion columns
        emotion_cols = {}
        for emotion in self.emotion_analyzer.get_emotions():
            emotion_cols[f'emo_{emotion}'] = 0.0
        
        # Add analysis columns
        df = df.assign(**emotion_cols)
        df['pain_points'] = ''
        df['churn_risk'] = 0.0
        df['nps_category'] = ''
        
        # Fill with results
        for result in results:
            idx = result['index']
            if idx in df.index:
                # Update emotion scores
                for emotion, score in result['emotions'].items():
                    df.at[idx, f'emo_{emotion}'] = score
                
                # Update other analysis results
                df.at[idx, 'pain_points'] = ', '.join(result['pain_points'])
                df.at[idx, 'churn_risk'] = result['churn_risk']
                df.at[idx, 'nps_category'] = result['nps_category']
        
        return df