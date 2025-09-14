# -*- coding: utf-8 -*-
"""
Optimized State Manager - Memory Efficient Session State Management
Implements pagination, versioning, and atomic updates for Streamlit Cloud compatibility
"""
import streamlit as st
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import pandas as pd
import threading

from .interfaces import IStateManager
from utils.logging_helpers import get_logger

logger = get_logger(__name__)

@dataclass
class PaginatedResults:
    """Container for paginated analysis results"""
    current_page: int = 0
    page_size: int = 100
    total_rows: int = 0
    total_pages: int = 0
    current_data: Optional[pd.DataFrame] = None
    summary: Dict[str, Any] = None
    metrics: Dict[str, Any] = None

class OptimizedStateManager(IStateManager):
    """
    Memory-efficient state manager with pagination and atomic updates
    Follows Streamlit Cloud best practices for large datasets
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.state_version = 0
        self._init_session_state()
        logger.info("Optimized state manager initialized")

    def _init_session_state(self):
        """Initialize session state with optimized structure"""
        # Core pipeline state
        if 'pipeline_running' not in st.session_state:
            st.session_state.pipeline_running = False

        if 'current_stage' not in st.session_state:
            st.session_state.current_stage = 'idle'

        if 'error_message' not in st.session_state:
            st.session_state.error_message = None

        if 'pipeline_start_time' not in st.session_state:
            st.session_state.pipeline_start_time = None

        # Optimized results storage
        if 'paginated_results' not in st.session_state:
            st.session_state.paginated_results = None

        if 'uploaded_file' not in st.session_state:
            st.session_state.uploaded_file = None

        # State versioning for race condition prevention
        if 'state_version' not in st.session_state:
            st.session_state.state_version = 0

    def _atomic_update(self, updates: Dict[str, Any]) -> bool:
        """Perform atomic updates to session state"""
        try:
            with self._lock:
                # Increment version for race condition detection
                current_version = st.session_state.get('state_version', 0)
                st.session_state.state_version = current_version + 1

                # Apply all updates atomically
                for key, value in updates.items():
                    st.session_state[key] = value

                logger.debug(f"Atomic update completed: {list(updates.keys())}")
                return True

        except Exception as e:
            logger.error(f"Atomic update failed: {e}")
            return False

    def set_pipeline_running(self, running: bool) -> None:
        """Set pipeline running state with timing"""
        updates = {'pipeline_running': running}

        if running:
            updates['pipeline_start_time'] = time.time()
            updates['current_stage'] = 'starting'
        else:
            updates['pipeline_start_time'] = None
            updates['current_stage'] = 'idle'

        self._atomic_update(updates)
        logger.info(f"Pipeline running state set to: {running}")

    def is_pipeline_running(self) -> bool:
        """Check if pipeline is currently running"""
        return st.session_state.get('pipeline_running', False)

    def set_current_stage(self, stage: str) -> None:
        """Set current processing stage"""
        self._atomic_update({'current_stage': stage})
        logger.debug(f"Stage updated to: {stage}")

    def get_current_stage(self) -> str:
        """Get current processing stage"""
        return st.session_state.get('current_stage', 'idle')

    def set_error_message(self, message: str) -> None:
        """Set error message"""
        self._atomic_update({
            'error_message': message,
            'pipeline_running': False,
            'current_stage': 'error'
        })
        logger.warning(f"Error message set: {message}")

    def get_error_message(self) -> Optional[str]:
        """Get current error message"""
        return st.session_state.get('error_message')

    def clear_error(self) -> None:
        """Clear error state"""
        self._atomic_update({
            'error_message': None,
            'current_stage': 'idle'
        })
        logger.info("Error state cleared")

    def set_uploaded_file(self, file_info: Dict[str, Any]) -> None:
        """Set uploaded file information"""
        self._atomic_update({'uploaded_file': file_info})
        logger.info(f"Uploaded file set: {file_info.get('name', 'unknown')}")

    def get_uploaded_file(self) -> Optional[Dict[str, Any]]:
        """Get uploaded file information"""
        return st.session_state.get('uploaded_file')

    def set_analysis_results(self, results: Dict[str, Any]) -> None:
        """Set analysis results with pagination for memory efficiency"""
        try:
            df = results.get('dataframe')
            if df is None or len(df) == 0:
                logger.warning("No dataframe found in results")
                return

            # Create paginated results container
            page_size = 100  # Reasonable page size for UI performance
            total_rows = len(df)
            total_pages = (total_rows + page_size - 1) // page_size

            # Store only first page initially
            current_page_data = df.head(page_size)

            paginated_results = PaginatedResults(
                current_page=0,
                page_size=page_size,
                total_rows=total_rows,
                total_pages=total_pages,
                current_data=current_page_data,
                summary=results.get('summary', {}),
                metrics=results.get('metrics', {})
            )

            # Store full dataframe temporarily for processing (will be cleaned up)
            full_data_key = f"full_results_{int(time.time())}"

            updates = {
                'paginated_results': asdict(paginated_results),
                full_data_key: df,  # Temporary storage
                'analysis_complete': True,
                'pipeline_running': False,
                'current_stage': 'completed'
            }

            if self._atomic_update(updates):
                logger.info(f"Analysis results stored with pagination: {total_rows} rows, {total_pages} pages")

                # Schedule cleanup of full dataframe after brief delay
                self._schedule_cleanup(full_data_key)
            else:
                logger.error("Failed to store analysis results")

        except Exception as e:
            logger.error(f"Error storing analysis results: {e}")
            self.set_error_message(f"Error storing results: {str(e)}")

    def _schedule_cleanup(self, data_key: str) -> None:
        """Schedule cleanup of temporary data"""
        # Note: In production, this would be handled by a background task
        # For now, we rely on session expiration
        logger.debug(f"Scheduled cleanup for: {data_key}")

    def get_analysis_results(self) -> Optional[Dict[str, Any]]:
        """Get analysis results (paginated)"""
        paginated_data = st.session_state.get('paginated_results')
        if not paginated_data:
            return None

        try:
            # Reconstruct PaginatedResults from dict
            results = PaginatedResults(**paginated_data)

            return {
                'dataframe': results.current_data,
                'summary': results.summary or {},
                'metrics': results.metrics or {},
                'pagination_info': {
                    'current_page': results.current_page,
                    'page_size': results.page_size,
                    'total_rows': results.total_rows,
                    'total_pages': results.total_pages
                }
            }

        except Exception as e:
            logger.error(f"Error retrieving analysis results: {e}")
            return None

    def get_results_page(self, page_number: int) -> Optional[pd.DataFrame]:
        """Get specific page of results"""
        try:
            paginated_data = st.session_state.get('paginated_results')
            if not paginated_data:
                return None

            # For now, return current page data
            # In a full implementation, this would load the requested page
            results = PaginatedResults(**paginated_data)

            if page_number == results.current_page:
                return results.current_data

            # TODO: Implement dynamic page loading from stored data
            logger.warning(f"Dynamic page loading not implemented for page {page_number}")
            return results.current_data

        except Exception as e:
            logger.error(f"Error getting results page {page_number}: {e}")
            return None

    def is_analysis_complete(self) -> bool:
        """Check if analysis is complete"""
        return st.session_state.get('analysis_complete', False)

    def get_pipeline_duration(self) -> Optional[float]:
        """Get pipeline execution duration"""
        start_time = st.session_state.get('pipeline_start_time')
        if start_time and not self.is_pipeline_running():
            # Pipeline completed
            return time.time() - start_time
        elif start_time and self.is_pipeline_running():
            # Pipeline still running
            return time.time() - start_time
        return None

    def clear_all_state(self) -> None:
        """Clear all state for new analysis"""
        try:
            keys_to_clear = [
                'pipeline_running', 'current_stage', 'error_message',
                'pipeline_start_time', 'paginated_results', 'uploaded_file',
                'analysis_complete'
            ]

            # Also clear any temporary data keys
            temp_keys = [key for key in st.session_state.keys() if key.startswith('full_results_')]
            keys_to_clear.extend(temp_keys)

            updates = {key: None for key in keys_to_clear}
            updates['state_version'] = st.session_state.get('state_version', 0) + 1

            self._atomic_update(updates)
            logger.info("All state cleared for new analysis")

        except Exception as e:
            logger.error(f"Error clearing state: {e}")

    def get_memory_usage_info(self) -> Dict[str, Any]:
        """Get information about current memory usage"""
        try:
            import sys

            memory_info = {
                'session_state_keys': len(st.session_state.keys()),
                'has_paginated_results': 'paginated_results' in st.session_state,
                'state_version': st.session_state.get('state_version', 0)
            }

            # Estimate memory usage of key components
            if 'paginated_results' in st.session_state:
                paginated_data = st.session_state['paginated_results']
                if paginated_data and isinstance(paginated_data, dict):
                    memory_info['paginated_results_size'] = sys.getsizeof(paginated_data)
                    memory_info['total_rows'] = paginated_data.get('total_rows', 0)
                    memory_info['current_page'] = paginated_data.get('current_page', 0)

            return memory_info

        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return {'error': str(e)}

    def optimize_memory(self) -> bool:
        """Perform memory optimization"""
        try:
            # Clear temporary data
            temp_keys = [key for key in st.session_state.keys() if key.startswith('full_results_')]

            if temp_keys:
                updates = {key: None for key in temp_keys}
                self._atomic_update(updates)
                logger.info(f"Cleaned up {len(temp_keys)} temporary data keys")
                return True

            return False

        except Exception as e:
            logger.error(f"Error optimizing memory: {e}")
            return False