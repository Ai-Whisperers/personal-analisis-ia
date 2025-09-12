# -*- coding: utf-8 -*-
"""
Progress Tracker - UI-agnostic progress tracking and timing
"""
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskInfo:
    """Information about a single task"""
    name: str
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    progress_percent: float = 0.0
    message: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return None
    
    @property
    def is_running(self) -> bool:
        """Check if task is currently running"""
        return self.status == TaskStatus.RUNNING
    
    @property
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.status == TaskStatus.COMPLETED

class ProgressTracker:
    """Tracks progress of multiple tasks with timing information"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.pipeline_start_time: Optional[float] = None
        self.pipeline_end_time: Optional[float] = None
        self.total_steps = 0
        
    def start_pipeline(self, total_steps: int = 0):
        """Start tracking a complete pipeline"""
        self.pipeline_start_time = time.time()
        self.pipeline_end_time = None
        self.total_steps = total_steps
        self.tasks.clear()
        logger.info(f"Started pipeline tracking with {total_steps} steps")
    
    def end_pipeline(self):
        """End pipeline tracking"""
        self.pipeline_end_time = time.time()
        duration = self.get_pipeline_duration()
        logger.info(f"Pipeline completed in {duration:.2f} seconds")
    
    def add_task(self, task_name: str, message: str = "") -> TaskInfo:
        """Add a new task to track"""
        task = TaskInfo(name=task_name, message=message)
        self.tasks[task_name] = task
        logger.debug(f"Added task: {task_name}")
        return task
    
    def start_task(self, task_name: str, message: str = "") -> TaskInfo:
        """Start a task"""
        if task_name not in self.tasks:
            self.add_task(task_name, message)
        
        task = self.tasks[task_name]
        task.status = TaskStatus.RUNNING
        task.start_time = time.time()
        task.message = message or task.message
        task.progress_percent = 0.0
        
        logger.info(f"Started task: {task_name}")
        return task
    
    def update_task_progress(self, task_name: str, progress_percent: float, message: str = ""):
        """Update task progress"""
        if task_name not in self.tasks:
            logger.warning(f"Task {task_name} not found")
            return
        
        task = self.tasks[task_name]
        task.progress_percent = max(0.0, min(100.0, progress_percent))
        if message:
            task.message = message
        
        logger.debug(f"Updated {task_name}: {progress_percent:.1f}% - {message}")
    
    def complete_task(self, task_name: str, message: str = ""):
        """Mark task as completed"""
        if task_name not in self.tasks:
            logger.warning(f"Task {task_name} not found")
            return
        
        task = self.tasks[task_name]
        task.status = TaskStatus.COMPLETED
        task.end_time = time.time()
        task.progress_percent = 100.0
        if message:
            task.message = message
        
        duration = task.duration
        logger.info(f"Completed task: {task_name} in {duration:.2f}s")
    
    def fail_task(self, task_name: str, error: str, message: str = ""):
        """Mark task as failed"""
        if task_name not in self.tasks:
            logger.warning(f"Task {task_name} not found")
            return
        
        task = self.tasks[task_name]
        task.status = TaskStatus.FAILED
        task.end_time = time.time()
        task.error = error
        if message:
            task.message = message
        
        logger.error(f"Failed task: {task_name} - {error}")
    
    def cancel_task(self, task_name: str, message: str = ""):
        """Cancel a task"""
        if task_name not in self.tasks:
            logger.warning(f"Task {task_name} not found")
            return
        
        task = self.tasks[task_name]
        task.status = TaskStatus.CANCELLED
        task.end_time = time.time()
        if message:
            task.message = message
        
        logger.info(f"Cancelled task: {task_name}")
    
    def get_task(self, task_name: str) -> Optional[TaskInfo]:
        """Get task information"""
        return self.tasks.get(task_name)
    
    def get_all_tasks(self) -> Dict[str, TaskInfo]:
        """Get all tasks"""
        return self.tasks.copy()
    
    def get_running_tasks(self) -> List[TaskInfo]:
        """Get all currently running tasks"""
        return [task for task in self.tasks.values() if task.is_running]
    
    def get_completed_tasks(self) -> List[TaskInfo]:
        """Get all completed tasks"""
        return [task for task in self.tasks.values() if task.is_completed]
    
    def get_failed_tasks(self) -> List[TaskInfo]:
        """Get all failed tasks"""
        return [task for task in self.tasks.values() if task.status == TaskStatus.FAILED]
    
    def get_overall_progress(self) -> float:
        """Calculate overall progress percentage"""
        if not self.tasks:
            return 0.0
        
        if self.total_steps > 0:
            completed_steps = len(self.get_completed_tasks())
            return (completed_steps / self.total_steps) * 100.0
        else:
            # Calculate based on individual task progress
            total_progress = sum(task.progress_percent for task in self.tasks.values())
            return total_progress / len(self.tasks)
    
    def get_pipeline_duration(self) -> Optional[float]:
        """Get total pipeline duration"""
        if self.pipeline_start_time:
            end_time = self.pipeline_end_time or time.time()
            return end_time - self.pipeline_start_time
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive progress summary"""
        total_tasks = len(self.tasks)
        completed = len(self.get_completed_tasks())
        running = len(self.get_running_tasks())
        failed = len(self.get_failed_tasks())
        
        return {
            'total_tasks': total_tasks,
            'completed': completed,
            'running': running,
            'failed': failed,
            'pending': total_tasks - completed - running - failed,
            'overall_progress': self.get_overall_progress(),
            'pipeline_duration': self.get_pipeline_duration(),
            'pipeline_running': self.pipeline_start_time is not None and self.pipeline_end_time is None
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for completed tasks"""
        completed_tasks = self.get_completed_tasks()
        
        if not completed_tasks:
            return {'no_completed_tasks': True}
        
        durations = [task.duration for task in completed_tasks if task.duration]
        
        if not durations:
            return {'no_duration_data': True}
        
        return {
            'total_completed': len(completed_tasks),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'total_duration': sum(durations),
            'task_details': [
                {
                    'name': task.name,
                    'duration': task.duration,
                    'status': task.status.value
                }
                for task in completed_tasks
            ]
        }
    
    def reset(self):
        """Reset all tracking data"""
        self.tasks.clear()
        self.pipeline_start_time = None
        self.pipeline_end_time = None
        self.total_steps = 0
        logger.info("Reset progress tracker")

# Context manager for automatic task tracking
class TaskTracker:
    """Context manager for automatic task start/complete"""
    
    def __init__(self, tracker: ProgressTracker, task_name: str, message: str = ""):
        self.tracker = tracker
        self.task_name = task_name
        self.message = message
    
    def __enter__(self):
        self.tracker.start_task(self.task_name, self.message)
        return self.tracker.get_task(self.task_name)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.tracker.complete_task(self.task_name)
        else:
            error_msg = str(exc_val) if exc_val else "Unknown error"
            self.tracker.fail_task(self.task_name, error_msg)