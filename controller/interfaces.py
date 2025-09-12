# -*- coding: utf-8 -*-
"""
Interface definitions for controller layer
Provides clear contracts between UI and core logic
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
import pandas as pd

class IPipelineRunner(ABC):
    """Interface for running the complete analysis pipeline"""
    
    @abstractmethod
    def run_pipeline(self, file_path: str) -> Dict[str, Any]:
        """
        Execute complete pipeline: Excel -> parse -> batch -> LLM -> merge
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Dict with results, metrics, and status
        """
        pass
    
    @abstractmethod 
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline execution status"""
        pass
    
    @abstractmethod
    def cancel_pipeline(self) -> bool:
        """Cancel running pipeline if possible"""
        pass

class IStateManager(ABC):
    """Interface for managing application state"""
    
    @abstractmethod
    def set_uploaded_file(self, file_info: Dict[str, Any]) -> None:
        """Store uploaded file information"""
        pass
    
    @abstractmethod
    def get_uploaded_file(self) -> Optional[Dict[str, Any]]:
        """Get uploaded file information"""
        pass
    
    @abstractmethod
    def set_analysis_results(self, results: Dict[str, Any]) -> None:
        """Store analysis results"""
        pass
    
    @abstractmethod
    def get_analysis_results(self) -> Optional[Dict[str, Any]]:
        """Get analysis results"""
        pass
    
    @abstractmethod
    def is_pipeline_running(self) -> bool:
        """Check if pipeline is currently running"""
        pass
    
    @abstractmethod
    def is_analysis_complete(self) -> bool:
        """Check if analysis is complete"""
        pass
    
    @abstractmethod
    def clear_state(self) -> None:
        """Clear all stored state"""
        pass
    
    @abstractmethod
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current state for debugging"""
        pass

class IProgressTracker(ABC):
    """Interface for tracking pipeline progress"""
    
    @abstractmethod
    def start_stage(self, stage_name: str) -> None:
        """Mark start of pipeline stage"""
        pass
    
    @abstractmethod
    def complete_stage(self, stage_name: str) -> None:
        """Mark completion of pipeline stage"""
        pass
    
    @abstractmethod
    def update_progress(self, stage_name: str, progress: float) -> None:
        """Update progress within a stage (0.0 to 1.0)"""
        pass
    
    @abstractmethod
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary"""
        pass
    
    @abstractmethod
    def reset_progress(self) -> None:
        """Reset all progress tracking"""
        pass

class IFileProcessor(ABC):
    """Interface for file processing operations"""
    
    @abstractmethod
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate uploaded file format and structure"""
        pass
    
    @abstractmethod
    def parse_file(self, file_path: str) -> pd.DataFrame:
        """Parse Excel file to DataFrame"""
        pass
    
    @abstractmethod
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize data"""
        pass

class IAnalysisEngine(ABC):
    """Interface for AI analysis operations"""
    
    @abstractmethod
    def analyze_comments(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run complete AI analysis on comments"""
        pass
    
    @abstractmethod
    def get_analysis_config(self) -> Dict[str, Any]:
        """Get current analysis configuration"""
        pass