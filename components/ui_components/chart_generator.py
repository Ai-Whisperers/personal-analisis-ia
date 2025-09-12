# -*- coding: utf-8 -*-
"""
Chart Generator - Refactored to use modular chart components
Main interface for rendering all analysis charts
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional

from .charts import EmotionChartRenderer, NPSChartRenderer, ChurnChartRenderer
from utils.logging_helpers import get_logger

logger = get_logger(__name__)

def render_analysis_charts(df: pd.DataFrame, chart_options: Optional[Dict[str, Any]] = None) -> None:
    """
    Main function to render all analysis charts
    Uses modular chart renderers to avoid god file
    """
    if df is None or df.empty:
        st.warning("No hay datos para mostrar gráficos")
        return
    
    try:
        st.header("Visualizaciones del Análisis")
        
        # Initialize chart renderers
        emotion_renderer = EmotionChartRenderer()
        nps_renderer = NPSChartRenderer()
        churn_renderer = ChurnChartRenderer()
        
        # Chart selection tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "Emociones", "NPS", "Riesgo Churn", "Análisis Avanzado"
        ])
        
        # Emotions tab
        with tab1:
            render_emotions_section(emotion_renderer, df, chart_options)
        
        # NPS tab
        with tab2:
            render_nps_section(nps_renderer, df)
        
        # Churn tab
        with tab3:
            render_churn_section(churn_renderer, df)
        
        # Advanced analysis tab
        with tab4:
            render_advanced_section(emotion_renderer, churn_renderer, df)
            
    except Exception as e:
        logger.error(f"Error rendering charts: {e}")
        st.error(f"Error al generar gráficos: {str(e)}")

def render_emotions_section(renderer: EmotionChartRenderer, df: pd.DataFrame, options: Optional[Dict] = None) -> None:
    """Render emotions analysis section"""
    
    # Chart type selector
    chart_type = st.selectbox(
        "Tipo de gráfico:",
        ["bar", "pie", "heatmap"],
        format_func=lambda x: {
            "bar": "Barras horizontales",
            "pie": "Circular (top 8)",
            "heatmap": "Mapa de correlación"
        }[x]
    )
    
    # Main emotion distribution
    renderer.render_emotion_distribution(df, chart_type)
    
    # Categories summary
    st.markdown("---")
    renderer.render_emotion_categories_summary(df)

def render_nps_section(renderer: NPSChartRenderer, df: pd.DataFrame) -> None:
    """Render NPS analysis section"""
    
    # Main NPS distribution
    renderer.render_nps_distribution(df)
    
    # NPS score histogram
    st.markdown("---")
    renderer.render_nps_score_histogram(df)

def render_churn_section(renderer: ChurnChartRenderer, df: pd.DataFrame) -> None:
    """Render churn risk analysis section"""
    
    # Main churn risk distribution
    renderer.render_churn_risk_distribution(df)
    
    # Detailed histogram
    st.markdown("---")
    renderer.render_churn_risk_histogram(df)

def render_advanced_section(
    emotion_renderer: EmotionChartRenderer,
    churn_renderer: ChurnChartRenderer, 
    df: pd.DataFrame
) -> None:
    """Render advanced analysis charts"""
    
    st.subheader("Análisis Avanzado")
    st.info("Correlaciones y análisis multivariable")
    
    # Emotion heatmap
    emotion_renderer.render_emotion_distribution(df, "heatmap")
    
    # Risk vs emotions correlation
    st.markdown("---")
    churn_renderer.render_risk_vs_emotion_correlation(df)

def generate_chart_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate summary statistics for charts"""
    try:
        summary = {
            'total_records': len(df),
            'has_emotions': any(col.startswith('emo_') for col in df.columns),
            'has_nps': 'nps_category' in df.columns or 'NPS' in df.columns,
            'has_churn': 'churn_risk' in df.columns,
            'emotion_count': len([col for col in df.columns if col.startswith('emo_')]),
        }
        
        if summary['has_emotions']:
            emotion_cols = [col for col in df.columns if col.startswith('emo_')]
            summary['top_emotion'] = df[emotion_cols].mean().idxmax().replace('emo_', '')
        
        if summary['has_nps'] and 'NPS' in df.columns:
            summary['avg_nps'] = df['NPS'].mean()
        
        if summary['has_churn']:
            summary['high_churn_risk'] = (df['churn_risk'] > 0.7).sum()
        
        return summary
        
    except Exception as e:
        logger.warning(f"Error generating chart summary: {e}")
        return {'total_records': len(df) if df is not None else 0}

# Backward compatibility functions (used by existing pages)
def render_emotion_distribution_chart(df: pd.DataFrame, chart_type: str = "bar") -> None:
    """Backward compatible emotion chart function"""
    renderer = EmotionChartRenderer()
    renderer.render_emotion_distribution(df, chart_type)

def render_nps_analysis_chart(df: pd.DataFrame) -> None:
    """Backward compatible NPS chart function"""
    renderer = NPSChartRenderer()
    renderer.render_nps_distribution(df)

def render_churn_risk_chart(df: pd.DataFrame) -> None:
    """Backward compatible churn chart function"""
    renderer = ChurnChartRenderer()
    renderer.render_churn_risk_distribution(df)