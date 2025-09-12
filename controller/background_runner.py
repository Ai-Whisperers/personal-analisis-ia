"""
Background Pipeline Runner - Handles threading and async execution
Prevents UI blocking during heavy processing operations
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum

from .interfaces import IProgressTracker
from utils.logging_helpers import get_logger
from utils.performance_monitor import monitor

logger = get_logger(__name__)

class PipelineStatus(Enum):
    """Pipeline execution status"""
    IDLE = "idle"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class PipelineResult:
    """Container for pipeline execution results"""
    status: PipelineStatus
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    stage_timings: Optional[Dict[str, float]] = None

class BackgroundPipelineRunner:
    """
    Manages background execution of pipeline operations
    Provides thread-safe execution with timeout and cancellation
    """
    
    def __init__(self, progress_tracker: Optional[IProgressTracker] = None):
        """Initialize background runner"""
        self.progress_tracker = progress_tracker
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pipeline")
        self._current_future: Optional[Future] = None
        self._current_status = PipelineStatus.IDLE
        self._status_lock = threading.Lock()
        self._cancel_event = threading.Event()
        
        logger.info("Background pipeline runner initialized")
    
    def get_status(self) -> PipelineStatus:
        """Get current pipeline status (thread-safe)"""
        with self._status_lock:
            return self._current_status
    
    def _set_status(self, status: PipelineStatus) -> None:
        """Set pipeline status (thread-safe)"""
        with self._status_lock:
            self._current_status = status
            logger.debug(f"Pipeline status changed to: {status.value}")
    
    def is_running(self) -> bool:
        """Check if pipeline is currently running"""
        return self.get_status() == PipelineStatus.RUNNING
    
    def run_pipeline_async(
        self,
        pipeline_func: Callable[[str], Dict[str, Any]],
        file_path: str,
        timeout_seconds: int = 300,  # 5 minutes default
        on_complete: Optional[Callable[[PipelineResult], None]] = None,
        on_progress: Optional[Callable[[str, float], None]] = None
    ) -> Future[PipelineResult]:
        """
        Run pipeline function asynchronously with timeout and progress tracking
        
        Args:
            pipeline_func: Function to execute (should take file_path as argument)
            file_path: Path to input file
            timeout_seconds: Maximum execution time
            on_complete: Callback when pipeline completes
            on_progress: Callback for progress updates
            
        Returns:
            Future object for result tracking
        """
        if self.is_running():
            raise RuntimeError("Pipeline is already running")
        
        self._cancel_event.clear()
        self._set_status(PipelineStatus.RUNNING)
        
        def _pipeline_wrapper() -> PipelineResult:
            """Wrapper function for safe pipeline execution"""
            start_time = time.time()
            
            try:
                logger.info(f"Starting pipeline execution for: {file_path}")
                
                # Track progress if callback provided
                if on_progress and self.progress_tracker:
                    self.progress_tracker.reset_progress()
                
                # Execute pipeline with monitoring
                with monitor("complete_pipeline"):
                    results = pipeline_func(file_path)
                
                execution_time = time.time() - start_time
                
                # Check if cancelled during execution
                if self._cancel_event.is_set():
                    self._set_status(PipelineStatus.CANCELLED)
                    return PipelineResult(
                        status=PipelineStatus.CANCELLED,
                        error_message="Pipeline was cancelled",
                        execution_time=execution_time
                    )
                
                # Success
                self._set_status(PipelineStatus.COMPLETED)
                result = PipelineResult(
                    status=PipelineStatus.COMPLETED,
                    results=results,
                    execution_time=execution_time
                )
                
                logger.info(f"Pipeline completed successfully in {execution_time:.2f}s")
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = f"Pipeline failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                
                self._set_status(PipelineStatus.FAILED)
                return PipelineResult(
                    status=PipelineStatus.FAILED,
                    error_message=error_msg,
                    execution_time=execution_time
                )
        
        # Submit to thread pool with timeout
        self._current_future = self._executor.submit(_pipeline_wrapper)
        
        def _handle_completion(future: Future) -> None:
            """Handle pipeline completion"""
            try:
                result = future.result(timeout=timeout_seconds)
                if on_complete:
                    on_complete(result)
            except TimeoutError:
                logger.error(f"Pipeline timed out after {timeout_seconds}s")
                self._set_status(PipelineStatus.TIMEOUT)
                self.cancel_pipeline()
                if on_complete:
                    on_complete(PipelineResult(
                        status=PipelineStatus.TIMEOUT,
                        error_message=f"Pipeline timed out after {timeout_seconds}s"
                    ))
            except Exception as e:
                logger.error(f"Pipeline completion handler error: {e}")
        
        # Set up completion callback
        if on_complete:
            threading.Thread(
                target=_handle_completion,
                args=(self._current_future,),
                daemon=True
            ).start()
        
        return self._current_future
    
    def cancel_pipeline(self) -> bool:
        """Cancel running pipeline"""
        if not self.is_running():
            logger.warning("No pipeline running to cancel")
            return False
        
        try:
            # Signal cancellation
            self._cancel_event.set()
            
            # Cancel future if possible
            if self._current_future and not self._current_future.done():
                cancelled = self._current_future.cancel()
                if cancelled:
                    self._set_status(PipelineStatus.CANCELLED)
                    logger.info("Pipeline cancelled successfully")
                    return True
                else:
                    logger.warning("Could not cancel running pipeline")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling pipeline: {e}")
            return False
    
    def wait_for_completion(
        self,
        timeout_seconds: Optional[int] = None
    ) -> Optional[PipelineResult]:
        """
        Wait for pipeline completion (blocking)
        
        Args:
            timeout_seconds: Maximum time to wait
            
        Returns:
            PipelineResult if completed, None if timeout
        """
        if not self._current_future:
            return None
        
        try:
            return self._current_future.result(timeout=timeout_seconds)
        except TimeoutError:
            logger.warning(f"Timeout waiting for pipeline completion")
            return None
        except Exception as e:
            logger.error(f"Error waiting for pipeline: {e}")
            return None
    
    def get_progress_info(self) -> Dict[str, Any]:
        """Get current progress information"""
        info = {
            'status': self.get_status().value,
            'is_running': self.is_running(),
            'can_cancel': self._current_future and not self._current_future.done()
        }
        
        if self.progress_tracker:
            info.update(self.progress_tracker.get_progress_summary())
        
        return info
    
    def shutdown(self, wait: bool = True, timeout: float = 30.0) -> None:
        """Shutdown the background runner"""
        logger.info("Shutting down background pipeline runner")
        
        # Cancel any running pipeline
        if self.is_running():
            self.cancel_pipeline()
        
        # Shutdown executor
        self._executor.shutdown(wait=wait, timeout=timeout)
        logger.info("Background runner shutdown complete")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()