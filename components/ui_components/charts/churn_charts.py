# -*- coding: utf-8 -*-
"""
Churn Risk Charts - Customer churn risk visualizations
Charts for analyzing probability of customer abandonment
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from typing import Dict, Any

from .base_chart import BaseChartRenderer

class ChurnChartRenderer(BaseChartRenderer):
    """Renders churn risk charts"""
    
    def render_churn_risk_distribution(self, df: pd.DataFrame) -> None:
        """Render churn risk level distribution"""
        if 'churn_risk' not in df.columns:
            st.warning("No se encontraron datos de riesgo de churn")
            return
        
        st.subheader("Distribución de Riesgo de Churn")
        
        # Create risk level bins
        risk_levels = pd.cut(
            df['churn_risk'], 
            bins=[0, 0.3, 0.7, 1.0], 
            labels=['Bajo', 'Medio', 'Alto']
        )
        
        risk_counts = risk_levels.value_counts()
        risk_percentages = (risk_counts / len(df) * 100).round(2)
        
        # Define colors for risk levels
        risk_colors = {
            'Bajo': self.colors['success'],
            'Medio': self.colors['warning'],
            'Alto': self.colors['danger']
        }
        
        levels = list(risk_percentages.index)
        percentages = list(risk_percentages.values)
        colors = [risk_colors.get(level, self.colors['neutral']) for level in levels]
        
        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=levels,
                y=percentages,
                marker_color=colors,
                text=[f"{p:.1f}%" for p in percentages],
                textposition='outside'
            )
        ])
        
        fig = self.apply_base_layout(fig, "Distribución de Riesgo de Churn")
        fig.update_layout(
            xaxis_title="Nivel de Riesgo",
            yaxis_title="Porcentaje de Clientes",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            high_risk = (df['churn_risk'] > 0.7).sum()
            st.metric("Clientes Alto Riesgo", high_risk)
        
        with col2:
            avg_risk = df['churn_risk'].mean()
            st.metric("Riesgo Promedio", f"{avg_risk:.2%}")
        
        with col3:
            max_risk = df['churn_risk'].max()
            st.metric("Riesgo Máximo", f"{max_risk:.2%}")
    
    def render_churn_risk_histogram(self, df: pd.DataFrame) -> None:
        """Render detailed histogram of churn risk scores"""
        if 'churn_risk' not in df.columns:
            return
        
        st.subheader("Distribución Detallada de Riesgo")
        
        fig = go.Figure(data=[
            go.Histogram(
                x=df['churn_risk'],
                nbinsx=20,
                marker_color=self.colors['warning'],
                opacity=0.7
            )
        ])
        
        fig = self.apply_base_layout(fig, "Histograma de Riesgo de Churn")
        fig.update_layout(
            xaxis_title="Probabilidad de Churn",
            yaxis_title="Número de Clientes",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_risk_vs_emotion_correlation(self, df: pd.DataFrame) -> None:
        """Show correlation between churn risk and emotions (if available)"""
        if 'churn_risk' not in df.columns:
            return
        
        emotion_cols = [col for col in df.columns if col.startswith('emo_')]
        
        if not emotion_cols:
            return
        
        st.subheader("Correlación Riesgo vs Emociones")
        
        # Calculate correlations
        correlations = {}
        for col in emotion_cols:
            emotion_name = col.replace('emo_', '')
            correlation = df['churn_risk'].corr(df[col])
            correlations[emotion_name] = correlation
        
        # Sort by absolute correlation
        sorted_corr = dict(sorted(correlations.items(), 
                                key=lambda x: abs(x[1]), reverse=True))
        
        # Take top 10 correlations
        top_correlations = dict(list(sorted_corr.items())[:10])
        
        emotions = list(top_correlations.keys())
        corr_values = list(top_correlations.values())
        colors = [self.colors['danger'] if corr > 0 else self.colors['success'] 
                 for corr in corr_values]
        
        # Create horizontal bar chart
        fig = go.Figure(data=[
            go.Bar(
                y=emotions,
                x=corr_values,
                orientation='h',
                marker_color=colors,
                text=[f"{c:.3f}" for c in corr_values],
                textposition='outside'
            )
        ])
        
        fig = self.apply_base_layout(fig, "Top 10 Correlaciones Churn-Emociones")
        fig.update_layout(
            xaxis_title="Correlación",
            yaxis_title="Emociones",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("Correlación positiva = mayor emoción aumenta riesgo de churn")
        st.info("Correlación negativa = mayor emoción reduce riesgo de churn")