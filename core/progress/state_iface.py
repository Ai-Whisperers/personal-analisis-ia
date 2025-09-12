# -*- coding: utf-8 -*-
"""
State Interface - UI-agnostic state management interface
Provides abstraction between core logic and UI state management
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from enum import Enum

class StateKey(Enum):
    """Standard state keys for the application"""
    # Pipeline state
    PIPELINE_RUNNING = "pipeline_running"
    PIPELINE_RESULTS = "pipeline_results"
    PIPELINE_ERROR = "pipeline_error"
    CURRENT_TASK = "current_task"
    
    # File state
    UPLOADED_FILE = "uploaded_file"
    FILE_DATA = "file_data"
    FILE_VALIDATED = "file_validated"
    
    # Analysis state
    ANALYSIS_COMPLETE = "analysis_complete"
    ANALYSIS_RESULTS = "analysis_results"
    PROGRESS_DATA = "progress_data"
    
    # UI state
    SHOW_RESULTS = "show_results"
    SELECTED_CHART_TYPE = "selected_chart_type"
    EXPORT_FORMAT = "export_format"
    
    # Cache keys
    PROCESSED_DATA = "processed_data"
    CHART_DATA = "chart_data"

class StateInterface(ABC):
    """Abstract interface for state management"""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from state"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set value in state"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete key from state"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in state"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all state"""
        pass
    
    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """Get all state as dictionary"""
        pass

class MemoryStateManager(StateInterface):
    """Simple in-memory state manager for testing/non-UI contexts"""
    
    def __init__(self):
        self._state: Dict[str, Any] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from state"""
        return self._state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in state"""
        self._state[key] = value
    
    def delete(self, key: str) -> None:
        """Delete key from state"""
        self._state.pop(key, None)
    
    def exists(self, key: str) -> bool:
        """Check if key exists in state"""
        return key in self._state
    
    def clear(self) -> None:
        """Clear all state"""
        self._state.clear()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all state as dictionary"""
        return self._state.copy()

class StateManager:
    """State manager that works with different state backends"""
    
    def __init__(self, state_interface: StateInterface):
        self.state = state_interface
    
    def is_pipeline_running(self) -> bool:
        """Check if pipeline is currently running"""
        return self.state.get(StateKey.PIPELINE_RUNNING.value, False)
    
    def set_pipeline_running(self, running: bool) -> None:
        """Set pipeline running state"""
        self.state.set(StateKey.PIPELINE_RUNNING.value, running)
    
    def get_pipeline_results(self) -> Optional[Any]:
        """Get pipeline results"""
        return self.state.get(StateKey.PIPELINE_RESULTS.value)
    
    def set_pipeline_results(self, results: Any) -> None:
        """Set pipeline results"""
        self.state.set(StateKey.PIPELINE_RESULTS.value, results)
        self.state.set(StateKey.ANALYSIS_COMPLETE.value, True)
    
    def get_pipeline_error(self) -> Optional[str]:
        """Get pipeline error"""
        return self.state.get(StateKey.PIPELINE_ERROR.value)
    
    def set_pipeline_error(self, error: str) -> None:
        """Set pipeline error"""
        self.state.set(StateKey.PIPELINE_ERROR.value, error)
        self.set_pipeline_running(False)
    
    def clear_pipeline_error(self) -> None:
        """Clear pipeline error"""
        self.state.delete(StateKey.PIPELINE_ERROR.value)
    
    def get_current_task(self) -> Optional[str]:
        """Get current task name"""
        return self.state.get(StateKey.CURRENT_TASK.value)
    
    def set_current_task(self, task: str) -> None:
        """Set current task name"""
        self.state.set(StateKey.CURRENT_TASK.value, task)
    
    def get_uploaded_file(self) -> Optional[Any]:
        """Get uploaded file data"""
        return self.state.get(StateKey.UPLOADED_FILE.value)
    
    def set_uploaded_file(self, file_data: Any) -> None:
        """Set uploaded file data"""
        self.state.set(StateKey.UPLOADED_FILE.value, file_data)
        # Reset dependent state
        self.state.delete(StateKey.FILE_VALIDATED.value)
        self.state.delete(StateKey.ANALYSIS_COMPLETE.value)
        self.state.delete(StateKey.PIPELINE_RESULTS.value)
    
    def is_file_validated(self) -> bool:
        """Check if uploaded file has been validated"""
        return self.state.get(StateKey.FILE_VALIDATED.value, False)
    
    def set_file_validated(self, validated: bool) -> None:
        """Set file validation status"""
        self.state.set(StateKey.FILE_VALIDATED.value, validated)
    
    def is_analysis_complete(self) -> bool:
        """Check if analysis is complete"""
        return self.state.get(StateKey.ANALYSIS_COMPLETE.value, False)
    
    def get_progress_data(self) -> Optional[Dict[str, Any]]:
        """Get progress tracking data"""
        return self.state.get(StateKey.PROGRESS_DATA.value)
    
    def set_progress_data(self, progress: Dict[str, Any]) -> None:
        """Set progress tracking data"""
        self.state.set(StateKey.PROGRESS_DATA.value, progress)
    
    def should_show_results(self) -> bool:
        """Check if results should be displayed"""
        return self.state.get(StateKey.SHOW_RESULTS.value, False)
    
    def set_show_results(self, show: bool) -> None:
        """Set whether to show results"""
        self.state.set(StateKey.SHOW_RESULTS.value, show)
    
    def get_selected_chart_type(self) -> str:
        """Get selected chart type"""
        return self.state.get(StateKey.SELECTED_CHART_TYPE.value, "bar")
    
    def set_selected_chart_type(self, chart_type: str) -> None:
        """Set selected chart type"""
        self.state.set(StateKey.SELECTED_CHART_TYPE.value, chart_type)
    
    def get_export_format(self) -> str:
        """Get selected export format"""
        return self.state.get(StateKey.EXPORT_FORMAT.value, "xlsx")
    
    def set_export_format(self, format_type: str) -> None:
        """Set export format"""
        self.state.set(StateKey.EXPORT_FORMAT.value, format_type)
    
    def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get cached data"""
        return self.state.get(f"cache_{cache_key}")
    
    def set_cached_data(self, cache_key: str, data: Any) -> None:
        """Set cached data"""
        self.state.set(f"cache_{cache_key}", data)
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        all_state = self.state.get_all()
        for key in list(all_state.keys()):
            if key.startswith("cache_"):
                self.state.delete(key)
    
    def reset_pipeline_state(self) -> None:
        """Reset all pipeline-related state"""
        pipeline_keys = [
            StateKey.PIPELINE_RUNNING.value,
            StateKey.PIPELINE_RESULTS.value,
            StateKey.PIPELINE_ERROR.value,
            StateKey.CURRENT_TASK.value,
            StateKey.ANALYSIS_COMPLETE.value,
            StateKey.PROGRESS_DATA.value,
            StateKey.SHOW_RESULTS.value
        ]
        
        for key in pipeline_keys:
            self.state.delete(key)
        
        self.clear_cache()
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current state"""
        return {
            'pipeline_running': self.is_pipeline_running(),
            'file_uploaded': self.get_uploaded_file() is not None,
            'file_validated': self.is_file_validated(),
            'analysis_complete': self.is_analysis_complete(),
            'has_results': self.get_pipeline_results() is not None,
            'has_error': self.get_pipeline_error() is not None,
            'current_task': self.get_current_task(),
            'show_results': self.should_show_results()
        }

# Factory function for easy instantiation
def create_memory_state_manager() -> StateManager:
    """Create a state manager with in-memory backend"""
    return StateManager(MemoryStateManager())

# Global state manager instance for testing
_global_state_manager = None

def get_global_state_manager() -> StateManager:
    """Get global state manager instance"""
    global _global_state_manager
    if _global_state_manager is None:
        _global_state_manager = create_memory_state_manager()
    return _global_state_manager