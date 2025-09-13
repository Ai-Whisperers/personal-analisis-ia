# -*- coding: utf-8 -*-
"""
Pipeline Controller - Main orchestration point
Uses core/ modules without duplicating logic, provides UI isolation
"""
from typing import Dict, Any, Optional
import tempfile
import os
from pathlib import Path
import pandas as pd

from .interfaces import IPipelineRunner, IStateManager, IProgressTracker
from .state_manager import StreamlitStateManager 
from .background_runner import BackgroundPipelineRunner, PipelineResult, PipelineStatus

# Import core modules (existing logic)
from core.ai_engine.engine_controller import EngineController
from core.ai_engine.api_call import LLMApiClient
from core.progress.tracker import ProgressTracker

# Import utilities
from utils.logging_helpers import get_logger
from utils.performance_monitor import monitor
from config import get_openai_api_key, is_mock_mode

logger = get_logger(__name__)

class PipelineController(IPipelineRunner):
    """
    Main controller that orchestrates pipeline execution
    Bridges UI layer with core business logic
    """
    
    def __init__(self, state_manager: Optional[IStateManager] = None):
        """Initialize pipeline controller"""
        self.state_manager = state_manager or StreamlitStateManager()
        self.progress_tracker = ProgressTracker()
        self.background_runner = BackgroundPipelineRunner(self.progress_tracker)
        
        # Initialize core components
        api_key = get_openai_api_key()
        self.api_client = LLMApiClient(
            api_key=api_key,
            mock_mode=is_mock_mode()
        )
        
        # Get batch configuration from config
        try:
            from config import BATCH_CONFIG
            batch_config = BATCH_CONFIG
        except ImportError:
            batch_config = {}
        
        self.engine_controller = EngineController(self.api_client, batch_config)
        
        logger.info("Pipeline controller initialized")
    
    def run_pipeline(self, file_path: str) -> Dict[str, Any]:
        """
        Execute complete pipeline synchronously
        Uses existing EngineController from core/
        """
        try:
            self.state_manager.set_pipeline_running(True)
            self.state_manager.set_current_stage("initializing")
            
            with monitor("pipeline_execution"):
                # Use existing engine controller
                results_df = self.engine_controller.run_pipeline(file_path)
                
                # Convert DataFrame to serializable format
                results = {
                    'dataframe': results_df,
                    'summary': self._generate_summary(results_df),
                    'metrics': self._extract_metrics(results_df),
                    'file_path': file_path
                }
                
                self.state_manager.set_analysis_results(results)
                self.state_manager.set_pipeline_running(False)
                
                logger.info("Pipeline completed successfully")
                return results
                
        except Exception as e:
            error_msg = f"Pipeline execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            self.state_manager.set_error_message(error_msg)
            self.state_manager.set_pipeline_running(False)
            
            raise
    
    def run_pipeline_async(
        self,
        file_path: str,
        on_complete: Optional[callable] = None
    ) -> None:
        """
        Execute pipeline in background to prevent UI blocking
        """
        if self.background_runner.is_running():
            raise RuntimeError("Pipeline is already running")
        
        def pipeline_func(path: str) -> Dict[str, Any]:
            """Wrapper for async execution"""
            return self.run_pipeline(path)
        
        def completion_handler(result: PipelineResult) -> None:
            """Handle async completion"""
            if result.status == PipelineStatus.COMPLETED:
                # Results already stored by run_pipeline
                logger.info(f"Async pipeline completed in {result.execution_time:.2f}s")
            else:
                error_msg = result.error_message or f"Pipeline failed with status: {result.status.value}"
                self.state_manager.set_error_message(error_msg)
                self.state_manager.set_pipeline_running(False)
            
            if on_complete:
                on_complete(result)
        
        # Start async execution
        self.background_runner.run_pipeline_async(
            pipeline_func=pipeline_func,
            file_path=file_path,
            timeout_seconds=600,  # 10 minutes
            on_complete=completion_handler
        )
        
        logger.info(f"Started async pipeline for: {file_path}")
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline execution status"""
        base_status = {
            'is_running': self.state_manager.is_pipeline_running(),
            'is_complete': self.state_manager.is_analysis_complete(),
            'current_stage': self.state_manager.get_current_stage(),
            'error_message': self.state_manager.get_error_message(),
            'has_results': self.state_manager.get_analysis_results() is not None
        }
        
        # Add background runner status
        if self.background_runner.is_running():
            base_status.update(self.background_runner.get_progress_info())
        
        # Add timing info
        duration = self.state_manager.get_pipeline_duration()
        if duration:
            base_status['duration_seconds'] = duration
        
        return base_status
    
    def cancel_pipeline(self) -> bool:
        """Cancel running pipeline if possible"""
        if self.background_runner.is_running():
            success = self.background_runner.cancel_pipeline()
            if success:
                self.state_manager.set_pipeline_running(False)
                self.state_manager.set_error_message("Pipeline cancelled by user")
            return success
        
        # If running synchronously, can't cancel
        return False
    
    def validate_file(self, uploaded_file) -> Dict[str, Any]:
        """
        Validate uploaded file and prepare for processing
        Returns validation results and temp file path
        """
        try:
            # Save uploaded file to temp location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Use existing file validation from reader module
            from core.file_processor.reader import validate_file
            
            is_valid = validate_file(tmp_path)
            validation_result = {
                'is_valid': is_valid,
                'message': 'File structure validated' if is_valid else 'Invalid file structure or format'
            }
            
            if validation_result['is_valid']:
                file_info = {
                    'name': uploaded_file.name,
                    'size': len(uploaded_file.getvalue()),
                    'temp_path': tmp_path,
                    'hash': str(hash(uploaded_file.getvalue())),
                    'validation': validation_result
                }
                
                self.state_manager.set_uploaded_file(file_info)
                logger.info(f"File validated successfully: {uploaded_file.name}")
                
                return {
                    'success': True,
                    'file_info': file_info,
                    'message': 'File validated successfully'
                }
            else:
                # Clean up temp file on validation failure
                os.unlink(tmp_path)
                return {
                    'success': False,
                    'errors': validation_result.get('errors', []),
                    'message': 'File validation failed'
                }
                
        except Exception as e:
            error_msg = f"File validation error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'error': error_msg,
                'message': 'Validation process failed'
            }
    
    def _generate_summary(self, df) -> Dict[str, Any]:
        """Generate analysis summary from results DataFrame"""
        try:
            emotion_cols = [col for col in df.columns if col.startswith('emo_')]
            
            summary = {
                'total_comments': len(df),
                'emotions_detected': len(emotion_cols),
                'avg_nps_score': df.get('NPS', pd.Series()).mean() if 'NPS' in df.columns else None,
                'churn_risk_high': len(df[df.get('churn_risk', 0) > 0.7]) if 'churn_risk' in df.columns else 0
            }
            
            # Top emotions
            if emotion_cols:
                emotion_means = df[emotion_cols].mean().sort_values(ascending=False)
                summary['top_emotions'] = emotion_means.head(5).to_dict()
            
            return summary
            
        except Exception as e:
            logger.warning(f"Error generating summary: {e}")
            return {'total_comments': len(df) if df is not None else 0}
    
    def _extract_metrics(self, df) -> Dict[str, Any]:
        """Extract key metrics from results"""
        try:
            metrics = {}
            
            # Emotion distribution
            emotion_cols = [col for col in df.columns if col.startswith('emo_')]
            if emotion_cols:
                emotion_pcts = (df[emotion_cols].mean() * 100).round(2)
                metrics['emotion_percentages'] = emotion_pcts.to_dict()
            
            # NPS distribution
            if 'nps_category' in df.columns:
                nps_dist = df['nps_category'].value_counts(normalize=True) * 100
                metrics['nps_distribution'] = nps_dist.to_dict()
            
            # Churn risk levels
            if 'churn_risk' in df.columns:
                risk_levels = pd.cut(df['churn_risk'], 
                                   bins=[0, 0.3, 0.7, 1.0], 
                                   labels=['Low', 'Medium', 'High'])
                risk_dist = risk_levels.value_counts(normalize=True) * 100
                metrics['churn_risk_distribution'] = risk_dist.to_dict()
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Error extracting metrics: {e}")
            return {}
    
    def cleanup(self) -> None:
        """Clean up resources"""
        # Clean up temp files
        file_info = self.state_manager.get_uploaded_file()
        if file_info and 'temp_path' in file_info:
            temp_path = file_info['temp_path']
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    logger.debug(f"Cleaned up temp file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Could not clean up temp file: {e}")
        
        # Shutdown background runner
        self.background_runner.shutdown()
        logger.info("Pipeline controller cleanup complete")