"""
NPS Charts - Net Promoter Score visualizations
Charts for promoter/passive/detractor analysis
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any

from .base_chart import BaseChartRenderer

class NPSChartRenderer(BaseChartRenderer):
    """Renders NPS-related charts"""
    
    def render_nps_distribution(self, df: pd.DataFrame) -> None:
        """Render NPS category distribution"""
        if 'nps_category' not in df.columns:
            st.warning("No se encontraron datos de categorías NPS")
            return
        
        st.subheader("Distribución NPS")
        
        # Calculate NPS distribution
        nps_counts = df['nps_category'].value_counts()
        nps_percentages = (nps_counts / len(df) * 100).round(2)
        
        # Define NPS colors
        nps_colors = {
            'promoter': self.colors['success'],
            'passive': self.colors['warning'], 
            'detractor': self.colors['danger']
        }
        
        categories = list(nps_percentages.index)
        percentages = list(nps_percentages.values)
        colors = [nps_colors.get(cat, self.colors['neutral']) for cat in categories]
        
        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=percentages,
                marker_color=colors,
                text=[f"{p:.1f}%" for p in percentages],
                textposition='outside'
            )
        ])
        
        fig = self.apply_base_layout(fig, "Distribución de Categorías NPS")
        fig.update_layout(
            xaxis_title="Categoría NPS",
            yaxis_title="Porcentaje",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show NPS score if available
        if 'NPS' in df.columns:
            avg_nps = df['NPS'].mean()
            st.metric("Puntuación NPS Promedio", f"{avg_nps:.1f}")
    
    def render_nps_score_histogram(self, df: pd.DataFrame) -> None:
        """Render histogram of NPS scores"""
        if 'NPS' not in df.columns:
            return
        
        st.subheader("Distribución de Puntuaciones NPS")
        
        fig = go.Figure(data=[
            go.Histogram(
                x=df['NPS'],
                nbinsx=11,  # 0-10 scores
                marker_color=self.colors['primary'],
                opacity=0.7
            )
        ])
        
        fig = self.apply_base_layout(fig, "Histograma de Puntuaciones NPS")
        fig.update_layout(
            xaxis_title="Puntuación NPS",
            yaxis_title="Frecuencia",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)