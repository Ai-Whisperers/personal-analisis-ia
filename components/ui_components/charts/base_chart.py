# -*- coding: utf-8 -*-
"""
Base Chart Renderer - Common functionality for all charts
Provides color palettes and base methods
"""
import plotly.graph_objects as go
from typing import Dict, Any

class BaseChartRenderer:
    """Base class for all chart renderers"""
    
    def __init__(self):
        """Initialize with common color palette"""
        self.colors = {
            'positive': '#2E8B57',    # Sea Green
            'negative': '#DC143C',    # Crimson  
            'neutral': '#4682B4',     # Steel Blue
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545'
        }
        
        self.layout_config = {
            'font': {'family': 'Arial, sans-serif', 'size': 12},
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'margin': dict(l=40, r=40, t=60, b=40)
        }
    
    def apply_base_layout(self, fig: go.Figure, title: str = "") -> go.Figure:
        """Apply base layout configuration to figure"""
        fig.update_layout(
            title=title,
            **self.layout_config
        )
        return fig
    
    def get_emotion_color(self, emotion: str) -> str:
        """Get color for emotion based on category"""
        from config import EMO_CATEGORIES
        
        if emotion in EMO_CATEGORIES.get('positivas', []):
            return self.colors['positive']
        elif emotion in EMO_CATEGORIES.get('negativas', []):
            return self.colors['negative']
        else:
            return self.colors['neutral']