"""
Chart Generator Component - Creates visualizations using Plotly
Shows 16 emotions as individual percentages, not categories
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, Any, List, Optional

from config import EMOTIONS_16, EMO_CATEGORIES

class ChartGenerator:
    """Generates charts for emotion analysis and other metrics"""
    
    def __init__(self):
        self.color_palette = {
            'positive': '#2E8B57',    # Sea Green
            'negative': '#DC143C',    # Crimson  
            'neutral': '#4682B4',     # Steel Blue
            'primary': '#1f77b4',
            'secondary': '#ff7f0e'
        }
    
    def render_emotion_distribution_chart(self, df: pd.DataFrame, chart_type: str = "bar") -> None:
        """Render emotion distribution chart showing % of each of the 16 emotions"""
        st.subheader("[DATA] Distribución de Emociones")
        st.write("Porcentaje de cada emoción detectada en todos los comentarios")
        
        # Get emotion columns
        emotion_cols = [col for col in df.columns if col.startswith('emo_')]
        
        if not emotion_cols:
            st.warning("No se encontraron datos de emociones en el análisis")
            return
        
        # Calculate percentages (mean of each emotion column * 100)
        emotion_percentages = {}
        for col in emotion_cols:
            emotion_name = col.replace('emo_', '')
            if emotion_name in EMOTIONS_16:
                percentage = (df[col].mean() * 100)
                emotion_percentages[emotion_name] = percentage
        
        if not emotion_percentages:
            st.warning("No se pudieron calcular los porcentajes de emociones")
            return
        
        # Sort by percentage (descending)
        sorted_emotions = dict(sorted(emotion_percentages.items(), key=lambda x: x[1], reverse=True))
        
        if chart_type == "bar":
            self._render_emotion_bar_chart(sorted_emotions)
        elif chart_type == "pie":
            self._render_emotion_pie_chart(sorted_emotions)
        elif chart_type == "heatmap":
            self._render_emotion_heatmap(df, emotion_cols)
        
        # Show top emotions summary
        self._render_emotion_summary(sorted_emotions)
    
    def _render_emotion_bar_chart(self, emotion_data: Dict[str, float]) -> None:
        """Render horizontal bar chart of emotions"""
        emotions = list(emotion_data.keys())
        percentages = list(emotion_data.values())
        
        # Color code by emotion category
        colors = []
        for emotion in emotions:
            if emotion in EMO_CATEGORIES['positivas']:
                colors.append(self.color_palette['positive'])
            elif emotion in EMO_CATEGORIES['negativas']:
                colors.append(self.color_palette['negative'])
            else:
                colors.append(self.color_palette['neutral'])
        
        fig = go.Figure(data=[
            go.Bar(
                y=emotions,
                x=percentages,
                orientation='h',
                marker_color=colors,
                text=[f"{p:.1f}%" for p in percentages],
                textposition="outside",
                hovertemplate='<b>%{y}</b><br>Porcentaje: %{x:.1f}%<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title="Distribución de las 16 Emociones",
            xaxis_title="Porcentaje (%)",
            yaxis_title="Emociones",
            height=600,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        fig.update_xaxis(range=[0, max(percentages) * 1.1])
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_emotion_pie_chart(self, emotion_data: Dict[str, float]) -> None:
        """Render pie chart of emotions (only top emotions to avoid clutter)"""
        # Show only top 8 emotions to keep pie chart readable
        top_emotions = dict(list(emotion_data.items())[:8])
        others_sum = sum(list(emotion_data.values())[8:])
        
        if others_sum > 0:
            top_emotions['Otras'] = others_sum
        
        emotions = list(top_emotions.keys())
        percentages = list(top_emotions.values())
        
        # Color mapping
        colors = []
        for emotion in emotions:
            if emotion == 'Otras':
                colors.append('#CCCCCC')
            elif emotion in EMO_CATEGORIES['positivas']:
                colors.append(self.color_palette['positive'])
            elif emotion in EMO_CATEGORIES['negativas']:
                colors.append(self.color_palette['negative'])
            else:
                colors.append(self.color_palette['neutral'])
        
        fig = go.Figure(data=[go.Pie(
            labels=emotions,
            values=percentages,
            marker_colors=colors,
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Porcentaje: %{percent}<br>Valor: %{value:.1f}%<extra></extra>'
        )])
        
        fig.update_layout(
            title="Top 8 Emociones - Distribución",
            height=500,
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        if others_sum > 0:
            st.info(f"💡 'Otras' incluye las {len(emotion_data) - 8} emociones restantes ({others_sum:.1f}%)")
    
    def _render_emotion_heatmap(self, df: pd.DataFrame, emotion_cols: List[str]) -> None:
        """Render heatmap showing emotion patterns"""
        # Sample data for heatmap (first 20 rows)
        sample_size = min(20, len(df))
        df_sample = df.head(sample_size)
        
        # Prepare data for heatmap
        emotion_names = [col.replace('emo_', '') for col in emotion_cols if col.replace('emo_', '') in EMOTIONS_16]
        heatmap_data = []
        
        for _, row in df_sample.iterrows():
            emotion_values = [row[f'emo_{emotion}'] for emotion in emotion_names]
            heatmap_data.append(emotion_values)
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=emotion_names,
            y=[f"Comentario {i+1}" for i in range(sample_size)],
            colorscale='RdYlGn',
            colorbar=dict(title="Intensidad"),
            hovertemplate='<b>%{y}</b><br>Emoción: %{x}<br>Intensidad: %{z:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f"Mapa de Calor - Emociones por Comentario (Muestra de {sample_size})",
            xaxis_title="Emociones",
            yaxis_title="Comentarios",
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_emotion_summary(self, emotion_data: Dict[str, float]) -> None:
        """Render emotion summary statistics"""
        st.subheader("[CHART] Resumen de Emociones")
        
        # Calculate category percentages
        category_percentages = {}
        for category, emotions in EMO_CATEGORIES.items():
            total = sum(emotion_data.get(emotion, 0) for emotion in emotions)
            avg_percentage = total / len(emotions) if emotions else 0
            category_percentages[category] = avg_percentage
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "[POSITIVE] Emociones Positivas", 
                f"{category_percentages['positivas']:.1f}%",
                help="Promedio de: " + ", ".join(EMO_CATEGORIES['positivas'])
            )
        
        with col2:
            st.metric(
                "[NEGATIVE] Emociones Negativas", 
                f"{category_percentages['negativas']:.1f}%",
                help="Promedio de: " + ", ".join(EMO_CATEGORIES['negativas'])
            )
        
        with col3:
            st.metric(
                "[NEUTRAL] Emociones Neutras", 
                f"{category_percentages['neutras']:.1f}%",
                help="Promedio de: " + ", ".join(EMO_CATEGORIES['neutras'])
            )
        
        # Top emotions
        top_3_emotions = list(emotion_data.items())[:3]
        st.write("**[TOP] Top 3 Emociones:**")
        for i, (emotion, percentage) in enumerate(top_3_emotions, 1):
            st.write(f"{i}. **{emotion.capitalize()}**: {percentage:.1f}%")
    
    def render_nps_distribution_chart(self, df: pd.DataFrame) -> None:
        """Render NPS distribution chart"""
        st.subheader("[DATA] Distribución NPS")
        
        if 'nps_category' not in df.columns:
            st.warning("No se encontraron datos de categorías NPS")
            return
        
        # Count NPS categories
        nps_counts = df['nps_category'].value_counts()
        
        # Calculate percentages
        total = len(df)
        nps_percentages = (nps_counts / total * 100).round(1)
        
        # Create pie chart
        colors = {
            'promoter': self.color_palette['positive'],
            'passive': self.color_palette['neutral'], 
            'detractor': self.color_palette['negative'],
            'unknown': '#CCCCCC'
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=[label.capitalize() for label in nps_counts.index],
            values=nps_counts.values,
            marker_colors=[colors.get(label, '#CCCCCC') for label in nps_counts.index],
            textinfo='label+percent+value',
            hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Distribución de Categorías NPS",
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Calculate NPS score
        promoters = nps_counts.get('promoter', 0)
        detractors = nps_counts.get('detractor', 0)
        valid_total = promoters + nps_counts.get('passive', 0) + detractors
        
        if valid_total > 0:
            nps_score = ((promoters - detractors) / valid_total) * 100
            
            # Display NPS score with interpretation
            col1, col2 = st.columns(2)
            with col1:
                st.metric("[TARGET] Puntuación NPS", f"{nps_score:.1f}")
            
            with col2:
                if nps_score >= 50:
                    interpretation = "[EXCELLENT] Excelente"
                elif nps_score >= 0:
                    interpretation = "[GOOD] Bueno"
                elif nps_score >= -50:
                    interpretation = "[WARNING] Mejorar"
                else:
                    interpretation = "[CRITICAL] Crítico"
                
                st.metric("[CHART] Interpretación", interpretation)
    
    def render_churn_risk_chart(self, df: pd.DataFrame) -> None:
        """Render churn risk distribution"""
        st.subheader("[WARNING] Distribución de Riesgo de Churn")
        
        if 'churn_risk' not in df.columns:
            st.warning("No se encontraron datos de riesgo de churn")
            return
        
        churn_risks = df['churn_risk'].dropna()
        
        if len(churn_risks) == 0:
            st.warning("No hay datos válidos de riesgo de churn")
            return
        
        # Create risk categories
        risk_categories = pd.cut(
            churn_risks, 
            bins=[0, 0.3, 0.7, 1.0], 
            labels=['Bajo', 'Medio', 'Alto'],
            include_lowest=True
        )
        
        risk_counts = risk_categories.value_counts()
        
        # Create bar chart
        colors = ['#2E8B57', '#FFD700', '#DC143C']  # Green, Yellow, Red
        
        fig = go.Figure(data=[go.Bar(
            x=risk_counts.index,
            y=risk_counts.values,
            marker_color=colors,
            text=risk_counts.values,
            textposition='outside',
            hovertemplate='<b>Riesgo %{x}</b><br>Cantidad: %{y}<br>Porcentaje: %{customdata:.1f}%<extra></extra>',
            customdata=(risk_counts / len(churn_risks) * 100).round(1)
        )])
        
        fig.update_layout(
            title="Distribución de Riesgo de Churn",
            xaxis_title="Nivel de Riesgo",
            yaxis_title="Cantidad de Clientes",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("[DATA] Riesgo Promedio", f"{churn_risks.mean():.2f}")
        
        with col2:
            high_risk_pct = (risk_counts.get('Alto', 0) / len(churn_risks) * 100)
            st.metric("[CRITICAL] Alto Riesgo", f"{high_risk_pct:.1f}%")
        
        with col3:
            low_risk_pct = (risk_counts.get('Bajo', 0) / len(churn_risks) * 100)
            st.metric("[VALID] Bajo Riesgo", f"{low_risk_pct:.1f}%")

def render_emotion_charts(df: pd.DataFrame, chart_type: str = "bar") -> None:
    """Convenience function to render emotion charts"""
    generator = ChartGenerator()
    generator.render_emotion_distribution_chart(df, chart_type)

def render_analysis_charts(df: pd.DataFrame) -> None:
    """Render all analysis charts"""
    generator = ChartGenerator()
    
    # Emotion charts
    st.header("[EMOTIONS] Análisis de Emociones")
    
    chart_type = st.selectbox(
        "Tipo de gráfico para emociones:",
        ["bar", "pie", "heatmap"],
        format_func=lambda x: {"bar": "Barras", "pie": "Pastel", "heatmap": "Mapa de Calor"}[x]
    )
    
    generator.render_emotion_distribution_chart(df, chart_type)
    
    # Other charts
    col1, col2 = st.columns(2)
    
    with col1:
        generator.render_nps_distribution_chart(df)
    
    with col2:
        generator.render_churn_risk_chart(df)