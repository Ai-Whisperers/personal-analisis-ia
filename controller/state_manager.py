# -*- coding: utf-8 -*-
"""
Streamlit State Manager - Handles session state without UI dependencies
Implements IStateManager interface for clean separation
"""
import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime
import json

from .interfaces import IStateManager
from utils.logging_helpers import get_logger

logger = get_logger(__name__)

class StreamlitStateManager(IStateManager):
    """
    Manages application state using Streamlit's session_state
    Provides abstraction layer to avoid direct st.session_state usage in core logic
    """
    
    def __init__(self):
        """Initialize state manager with default values"""
        self._init_default_state()
    
    def _init_default_state(self) -> None:
        """Initialize default session state values"""
        defaults = {
            'uploaded_file_info': None,
            'analysis_results': None,
            'pipeline_running': False,
            'analysis_complete': False,
            'pipeline_start_time': None,
            'current_stage': None,
            'error_message': None,
            'processing_config': {},
            'file_hash': None,
            'results_timestamp': None
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
                logger.debug(f"Initialized session state key: {key}")
    
    def set_uploaded_file(self, file_info: Dict[str, Any]) -> None:
        """Store uploaded file information"""
        st.session_state.uploaded_file_info = file_info
        st.session_state.file_hash = file_info.get('hash')
        
        # Clear previous results when new file is uploaded
        if st.session_state.analysis_results:
            logger.info("New file uploaded, clearing previous results")
            self.set_analysis_results(None)
        
        logger.info(f"Stored uploaded file: {file_info.get('name', 'unknown')}")
    
    def get_uploaded_file(self) -> Optional[Dict[str, Any]]:
        """Get uploaded file information"""
        return st.session_state.get('uploaded_file_info')
    
    def set_analysis_results(self, results: Optional[Dict[str, Any]]) -> None:
        """Store analysis results"""
        st.session_state.analysis_results = results
        
        if results:
            st.session_state.analysis_complete = True
            st.session_state.pipeline_running = False
            st.session_state.results_timestamp = datetime.now().isoformat()
            logger.info("Analysis results stored and marked complete")
        else:
            st.session_state.analysis_complete = False
            st.session_state.results_timestamp = None
            logger.info("Analysis results cleared")
    
    def get_analysis_results(self) -> Optional[Dict[str, Any]]:
        """Get analysis results"""
        return st.session_state.get('analysis_results')
    
    def is_pipeline_running(self) -> bool:
        """Check if pipeline is currently running"""
        return st.session_state.get('pipeline_running', False)
    
    def is_analysis_complete(self) -> bool:
        """Check if analysis is complete"""
        return st.session_state.get('analysis_complete', False)
    
    def set_pipeline_running(self, running: bool) -> None:
        """Set pipeline running state"""
        st.session_state.pipeline_running = running
        
        if running:
            st.session_state.pipeline_start_time = datetime.now().isoformat()
            st.session_state.analysis_complete = False
            st.session_state.error_message = None
            logger.info("Pipeline started")
        else:
            logger.info("Pipeline stopped")
    
    def set_current_stage(self, stage: Optional[str]) -> None:
        """Set current pipeline stage"""
        st.session_state.current_stage = stage
        if stage:
            logger.debug(f"Pipeline stage: {stage}")
    
    def get_current_stage(self) -> Optional[str]:
        """Get current pipeline stage"""
        return st.session_state.get('current_stage')
    
    def set_error_message(self, error: Optional[str]) -> None:
        """Set error message"""
        st.session_state.error_message = error
        if error:
            st.session_state.pipeline_running = False
            logger.error(f"Pipeline error: {error}")
    
    def get_error_message(self) -> Optional[str]:
        """Get error message"""
        return st.session_state.get('error_message')
    
    def clear_error(self) -> None:
        """Clear error message"""
        st.session_state.error_message = None
    
    def set_processing_config(self, config: Dict[str, Any]) -> None:
        """Set processing configuration"""
        st.session_state.processing_config = config
        logger.debug(f"Processing config updated: {list(config.keys())}")
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration"""
        return st.session_state.get('processing_config', {})
    
    def clear_state(self) -> None:
        """Clear all stored state"""
        keys_to_clear = [
            'uploaded_file_info', 'analysis_results', 'pipeline_running',
            'analysis_complete', 'pipeline_start_time', 'current_stage',
            'error_message', 'processing_config', 'file_hash', 'results_timestamp'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        self._init_default_state()
        logger.info("All session state cleared")
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current state for debugging"""
        summary = {
            'has_uploaded_file': self.get_uploaded_file() is not None,
            'pipeline_running': self.is_pipeline_running(),
            'analysis_complete': self.is_analysis_complete(),
            'current_stage': self.get_current_stage(),
            'has_error': self.get_error_message() is not None,
            'has_results': self.get_analysis_results() is not None,
            'file_hash': st.session_state.get('file_hash'),
            'results_timestamp': st.session_state.get('results_timestamp'),
            'pipeline_start_time': st.session_state.get('pipeline_start_time')
        }
        
        return summary
    
    def is_file_changed(self, new_file_hash: str) -> bool:
        """Check if uploaded file has changed"""
        current_hash = st.session_state.get('file_hash')
        return current_hash != new_file_hash
    
    def get_pipeline_duration(self) -> Optional[float]:
        """Get pipeline duration in seconds if running or completed"""
        start_time_str = st.session_state.get('pipeline_start_time')
        if not start_time_str:
            return None
        
        try:
            start_time = datetime.fromisoformat(start_time_str)
            duration = (datetime.now() - start_time).total_seconds()
            return duration
        except (ValueError, TypeError):
            return None