"""
Emotion Charts - Specialized charts for 16 emotions analysis
Shows % of each emotion individually (not categories)
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any

from .base_chart import BaseChartRenderer
from config import EMOTIONS_16, EMO_CATEGORIES

class EmotionChartRenderer(BaseChartRenderer):
    """Renders charts specific to emotion analysis"""
    
    def render_emotion_distribution(self, df: pd.DataFrame, chart_type: str = "bar") -> None:
        """Render main emotion distribution chart"""
        st.subheader("Distribución de Emociones")
        st.write("Porcentaje de cada emoción detectada en todos los comentarios")
        
        # Get emotion percentages
        emotion_data = self._calculate_emotion_percentages(df)
        
        if not emotion_data:
            st.warning("No se encontraron datos de emociones")
            return
        
        # Create chart based on type
        if chart_type == "bar":
            self._render_emotion_bar_chart(emotion_data)
        elif chart_type == "pie":
            self._render_emotion_pie_chart(emotion_data)
        elif chart_type == "heatmap":
            self._render_emotion_heatmap(df)
    
    def _calculate_emotion_percentages(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate percentage for each emotion"""
        emotion_cols = [col for col in df.columns if col.startswith('emo_')]
        
        emotion_percentages = {}
        for col in emotion_cols:
            emotion_name = col.replace('emo_', '')
            if emotion_name in EMOTIONS_16:
                percentage = (df[col].mean() * 100)
                emotion_percentages[emotion_name] = round(percentage, 2)
        
        return emotion_percentages
    
    def _render_emotion_bar_chart(self, emotion_data: Dict[str, float]) -> None:
        """Render horizontal bar chart of emotions"""
        # Sort emotions by percentage
        sorted_emotions = dict(sorted(emotion_data.items(), key=lambda x: x[1], reverse=True))
        
        emotions = list(sorted_emotions.keys())
        percentages = list(sorted_emotions.values())
        colors = [self.get_emotion_color(emotion) for emotion in emotions]
        
        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                y=emotions,
                x=percentages,
                orientation='h',
                marker_color=colors,
                text=[f"{p:.1f}%" for p in percentages],
                textposition='outside'
            )
        ])
        
        fig = self.apply_base_layout(fig, "Distribución de Emociones (%)")
        fig.update_layout(
            xaxis_title="Porcentaje",
            yaxis_title="Emociones",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_emotion_pie_chart(self, emotion_data: Dict[str, float]) -> None:
        """Render pie chart of top emotions"""
        # Get top 8 emotions to avoid cluttered pie
        sorted_emotions = dict(sorted(emotion_data.items(), key=lambda x: x[1], reverse=True))
        top_emotions = dict(list(sorted_emotions.items())[:8])
        
        # Sum remaining as "Others"
        remaining_sum = sum(list(sorted_emotions.values())[8:])
        if remaining_sum > 0:
            top_emotions["Otras"] = remaining_sum
        
        emotions = list(top_emotions.keys())
        percentages = list(top_emotions.values())
        colors = [self.get_emotion_color(emotion) if emotion != "Otras" else self.colors['neutral'] 
                 for emotion in emotions]
        
        fig = go.Figure(data=[
            go.Pie(
                labels=emotions,
                values=percentages,
                marker_colors=colors,
                textinfo='label+percent'
            )
        ])
        
        fig = self.apply_base_layout(fig, "Top 8 Emociones")
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_emotion_heatmap(self, df: pd.DataFrame) -> None:
        """Render emotion correlation heatmap (advanced view)"""
        emotion_cols = [col for col in df.columns if col.startswith('emo_')]
        
        if len(emotion_cols) < 2:
            st.warning("Se necesitan al menos 2 emociones para el heatmap")
            return
        
        # Calculate correlation matrix
        emotion_df = df[emotion_cols]
        correlation_matrix = emotion_df.corr()
        
        # Clean column names
        correlation_matrix.columns = [col.replace('emo_', '') for col in correlation_matrix.columns]
        correlation_matrix.index = [idx.replace('emo_', '') for idx in correlation_matrix.index]
        
        # Create heatmap
        fig = px.imshow(
            correlation_matrix,
            title="Correlación entre Emociones",
            color_continuous_scale='RdBu',
            aspect='auto'
        )
        
        fig = self.apply_base_layout(fig, "Correlación entre Emociones")
        fig.update_layout(height=600)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_emotion_categories_summary(self, df: pd.DataFrame) -> None:
        """Render summary by emotion categories (positive/negative/neutral)"""
        st.subheader("Resumen por Categorías")
        
        category_data = self._calculate_category_percentages(df)
        
        if not category_data:
            st.warning("No se pudieron calcular las categorías")
            return
        
        # Create simple bar chart for categories
        categories = list(category_data.keys())
        percentages = list(category_data.values())
        colors = [self.colors['positive'], self.colors['negative'], self.colors['neutral']]
        
        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=percentages,
                marker_color=colors,
                text=[f"{p:.1f}%" for p in percentages],
                textposition='outside'
            )
        ])
        
        fig = self.apply_base_layout(fig, "Distribución por Categorías")
        fig.update_layout(
            xaxis_title="Categorías",
            yaxis_title="Porcentaje",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _calculate_category_percentages(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate percentages for emotion categories"""
        category_totals = {'Positivas': 0, 'Negativas': 0, 'Neutras': 0}
        
        for category, emotions in EMO_CATEGORIES.items():
            total_pct = 0
            for emotion in emotions:
                col_name = f"emo_{emotion}"
                if col_name in df.columns:
                    total_pct += (df[col_name].mean() * 100)
            
            if category == 'positivas':
                category_totals['Positivas'] = round(total_pct, 2)
            elif category == 'negativas':
                category_totals['Negativas'] = round(total_pct, 2)
            elif category == 'neutras':
                category_totals['Neutras'] = round(total_pct, 2)
        
        return category_totals