# -*- coding: utf-8 -*-
"""
Chart Generator - Consolidated all chart functionality
Main interface for rendering all analysis charts
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from typing import Dict, Any, Optional

from config import EMOTIONS_16, EMO_CATEGORIES
from utils.logging_helpers import get_logger

logger = get_logger(__name__)

class ChartGenerator:
    """Consolidated chart generator for all analysis visualizations"""
    
    def __init__(self):
        self.colors = {
            'primary': '#3B82F6',
            'success': '#10B981',
            'warning': '#F59E0B', 
            'error': '#EF4444',
            'positive': '#22C55E',
            'negative': '#EF4444',
            'neutral': '#6B7280'
        }
        self.emotion_colors = self._get_emotion_colors()
    
    def _get_emotion_colors(self) -> Dict[str, str]:
        """Get colors for each emotion based on category"""
        colors = {}
        for emotion in EMOTIONS_16:
            if emotion in EMO_CATEGORIES.get('positivas', []):
                colors[emotion] = self.colors['positive']
            elif emotion in EMO_CATEGORIES.get('negativas', []):
                colors[emotion] = self.colors['negative']
            else:
                colors[emotion] = self.colors['neutral']
        return colors
    
    def render_emotion_distribution(self, df: pd.DataFrame, chart_type: str = "bar") -> None:
        """Render emotion distribution chart with flexible column detection"""
        st.subheader("Distribución de Emociones")

        emotion_data = {}

        # Strategy 1: Direct emotion columns (post-AI processing format)
        for emotion in EMOTIONS_16:
            if emotion in df.columns:
                avg_score = df[emotion].mean()
                emotion_data[emotion.title()] = avg_score * 100

        # Strategy 2: Legacy emo_ prefixed columns (backward compatibility)
        if not emotion_data:
            emotion_cols = [col for col in df.columns if col.startswith('emo_')]
            for col in emotion_cols:
                emotion_name = col.replace('emo_', '')
                if emotion_name in EMOTIONS_16:
                    avg_score = df[col].mean()
                    emotion_data[emotion_name.title()] = avg_score * 100

        # Strategy 3: Parse from serialized emotion data
        if not emotion_data and 'emotions_json' in df.columns:
            import json
            for idx, emotion_json in df['emotions_json'].items():
                try:
                    emotions = json.loads(emotion_json) if isinstance(emotion_json, str) else emotion_json
                    for emotion, score in emotions.items():
                        if emotion in EMOTIONS_16:
                            if emotion not in emotion_data:
                                emotion_data[emotion] = 0
                            emotion_data[emotion] += score
                except Exception as e:
                    logger.warning(f"Error parsing emotions at row {idx}: {e}")

            # Average the accumulated scores
            if emotion_data:
                total_rows = len(df)
                emotion_data = {k.title(): (v/total_rows)*100 for k, v in emotion_data.items()}

        # Final validation
        if not emotion_data:
            st.error("❌ No se encontraron datos de emociones válidos")
            st.info("Columnas disponibles: " + ", ".join(df.columns.tolist()))
            logger.error(f"No emotion data found. Available columns: {list(df.columns)}")
            return
        
        # Sort by percentage
        emotion_data = dict(sorted(emotion_data.items(), key=lambda x: x[1], reverse=True))
        
        if chart_type == "bar":
            fig = go.Figure(data=[
                go.Bar(
                    x=list(emotion_data.values()),
                    y=list(emotion_data.keys()),
                    orientation='h',
                    marker_color=[self.emotion_colors.get(k.lower(), self.colors['primary']) 
                                for k in emotion_data.keys()],
                    text=[f"{v:.1f}%" for v in emotion_data.values()],
                    textposition='auto'
                )
            ])
            fig.update_layout(
                title="Distribución de Emociones (%)",
                xaxis_title="Porcentaje",
                yaxis_title="Emoción",
                height=600
            )
        else:  # pie chart
            fig = go.Figure(data=[
                go.Pie(
                    labels=list(emotion_data.keys()),
                    values=list(emotion_data.values()),
                    marker_colors=[self.emotion_colors.get(k.lower(), self.colors['primary']) 
                                 for k in emotion_data.keys()]
                )
            ])
            fig.update_layout(title="Distribución de Emociones")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show top emotions summary
        col1, col2, col3 = st.columns(3)
        emotions_list = list(emotion_data.items())
        
        if len(emotions_list) >= 1:
            with col1:
                st.metric("Emoción Principal", emotions_list[0][0], f"{emotions_list[0][1]:.1f}%")
        if len(emotions_list) >= 2:
            with col2:
                st.metric("Segunda Emoción", emotions_list[1][0], f"{emotions_list[1][1]:.1f}%")
        if len(emotions_list) >= 3:
            with col3:
                st.metric("Tercera Emoción", emotions_list[2][0], f"{emotions_list[2][1]:.1f}%")
    
    def render_nps_distribution(self, df: pd.DataFrame) -> None:
        """Render NPS category distribution"""
        st.subheader("Distribución NPS")
        
        if 'nps_category' not in df.columns:
            st.warning("No se encontraron datos de categorías NPS")
            return
        
        # Calculate NPS distribution
        nps_counts = df['nps_category'].value_counts()
        nps_percentages = (nps_counts / len(df) * 100).round(1)
        
        # Colors for NPS categories
        nps_colors = {
            'promoter': self.colors['success'],
            'detractor': self.colors['error'], 
            'passive': self.colors['warning']
        }
        
        # Create pie chart
        fig = go.Figure(data=[
            go.Pie(
                labels=[k.title() for k in nps_counts.index],
                values=nps_counts.values,
                marker_colors=[nps_colors.get(k.lower(), self.colors['neutral']) 
                             for k in nps_counts.index],
                textinfo='label+percent',
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title=f"Distribución NPS (Total: {len(df)} respuestas)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Calculate NPS Score
        if 'NPS' in df.columns:
            promoters = len(df[df['NPS'] >= 9])
            detractors = len(df[df['NPS'] <= 6])
            total = len(df)
            nps_score = ((promoters - detractors) / total) * 100 if total > 0 else 0
            
            # Show NPS metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Promotores", f"{promoters} ({promoters/total*100:.1f}%)")
            with col2:
                st.metric("Pasivos", f"{total - promoters - detractors} ({(total-promoters-detractors)/total*100:.1f}%)")
            with col3:
                st.metric("Detractores", f"{detractors} ({detractors/total*100:.1f}%)")
            with col4:
                st.metric("NPS Score", f"{nps_score:.0f}", delta=f"{'Excelente' if nps_score > 50 else 'Bueno' if nps_score > 0 else 'Crítico'}")
    
    def render_churn_risk_distribution(self, df: pd.DataFrame) -> None:
        """Render churn risk distribution"""
        st.subheader("Distribución de Riesgo de Churn")
        
        if 'churn_risk' not in df.columns:
            st.warning("No se encontraron datos de riesgo de churn")
            return
        
        # Create risk level bins
        risk_levels = pd.cut(
            df['churn_risk'],
            bins=[0, 0.3, 0.7, 1.0],
            labels=['Bajo', 'Medio', 'Alto']
        )
        
        risk_counts = risk_levels.value_counts()
        risk_percentages = (risk_counts / len(df) * 100).round(1)
        
        # Risk colors
        risk_colors = {
            'Bajo': self.colors['success'],
            'Medio': self.colors['warning'],
            'Alto': self.colors['error']
        }
        
        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=risk_counts.index,
                y=risk_counts.values,
                marker_color=[risk_colors.get(level, self.colors['neutral']) 
                            for level in risk_counts.index],
                text=[f"{count}\n({risk_percentages[level]:.1f}%)" 
                     for level, count in zip(risk_counts.index, risk_counts.values)],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Distribución por Nivel de Riesgo de Churn",
            xaxis_title="Nivel de Riesgo",
            yaxis_title="Número de Clientes",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show risk metrics
        avg_risk = df['churn_risk'].mean()
        high_risk_count = len(df[df['churn_risk'] > 0.7])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Riesgo Promedio", f"{avg_risk:.2f}")
        with col2:
            st.metric("Alto Riesgo", f"{high_risk_count} clientes")
        with col3:
            st.metric("% Alto Riesgo", f"{high_risk_count/len(df)*100:.1f}%")
    
    def render_correlation_matrix(self, df: pd.DataFrame) -> None:
        """Render correlation matrix for emotions and metrics"""
        st.subheader("Matriz de Correlación")
        
        # Get numeric columns for correlation
        numeric_cols = []
        
        # Add emotion columns
        emotion_cols = [col for col in df.columns if col.startswith('emo_')]
        numeric_cols.extend(emotion_cols)
        
        # Add other numeric columns
        other_numeric = ['NPS', 'Nota', 'churn_risk']
        for col in other_numeric:
            if col in df.columns:
                numeric_cols.append(col)
        
        if len(numeric_cols) < 2:
            st.warning("No hay suficientes variables numéricas para mostrar correlación")
            return
        
        # Calculate correlation matrix
        corr_matrix = df[numeric_cols].corr()
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=[col.replace('emo_', '').title() if col.startswith('emo_') else col 
               for col in corr_matrix.columns],
            y=[col.replace('emo_', '').title() if col.startswith('emo_') else col 
               for col in corr_matrix.index],
            colorscale='RdBu',
            zmid=0,
            text=corr_matrix.round(2).values,
            texttemplate="%{text}",
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title="Matriz de Correlación - Emociones y Métricas",
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Main render function
def render_analysis_charts(df: pd.DataFrame, chart_options: Optional[Dict[str, Any]] = None) -> None:
    """
    Main function to render all analysis charts
    """
    if df is None or df.empty:
        st.warning("No hay datos para mostrar gráficos")
        return
    
    try:
        st.header("Visualizaciones del Análisis")
        
        # Initialize chart generator
        chart_gen = ChartGenerator()
        
        # Chart selection tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "Emociones", "NPS", "Riesgo Churn", "Correlaciones"
        ])
        
        with tab1:
            chart_type = st.selectbox("Tipo de gráfico", ["bar", "pie"], key="emotion_chart_type")
            chart_gen.render_emotion_distribution(df, chart_type)
        
        with tab2:
            chart_gen.render_nps_distribution(df)
        
        with tab3:
            chart_gen.render_churn_risk_distribution(df)
        
        with tab4:
            chart_gen.render_correlation_matrix(df)
        
        logger.info("Charts rendered successfully")
        
    except Exception as e:
        st.error(f"Error renderizando gráficos: {str(e)}")
        logger.error(f"Chart rendering error: {e}", exc_info=True)