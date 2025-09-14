# -*- coding: utf-8 -*-
"""
Controller Package - Pipeline Orchestration Layer
Isolates UI from core logic following blueprint architecture
"""

# Import existing implementations
from .sync_controller import SynchronousPipelineController as PipelineController
from .optimized_state_manager import OptimizedStateManager as StreamlitStateManager
from .interfaces import IPipelineRunner, IStateManager, IProgressTracker

# Legacy alias for backward compatibility
BackgroundPipelineRunner = PipelineController

__all__ = [
    'PipelineController',
    'IPipelineRunner',
    'IStateManager',
    'IProgressTracker',
    'StreamlitStateManager',
    'BackgroundPipelineRunner'
]