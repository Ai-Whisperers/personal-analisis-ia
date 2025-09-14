# -*- coding: utf-8 -*-
"""
Results Display Page - Pure UI Layer with Controller Pattern
Handles all chart display and export functionality using existing controller logic
"""
import streamlit as st
import sys
import time
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import controller layer only (no direct core imports) - USE SYNC VERSION
from controller.sync_controller import SynchronousPipelineController as PipelineController
from config import APP_INFO, FEATURE_FLAGS
from utils.logging_helpers import get_logger

# Import UI components only
from components.ui_components.chart_generator import ChartGenerator
from components.ui_components.report_exporter import ReportExporter

# Import glassmorphism theme
from utils.streamlit_helpers import apply_glassmorphism_theme

logger = get_logger(__name__)

def main():
    """Main results display page with pure UI logic"""

    # Configure page
    st.set_page_config(
        page_title="Resultados del Análisis",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Apply glassmorphism theme
    apply_glassmorphism_theme()

    st.title("📊 Resultados del Análisis")
    st.markdown("Visualización de resultados y exportación de datos")

    # Initialize controller for state management only
    controller = PipelineController()

    # Check analysis state and render appropriate content
    render_analysis_state(controller)

def render_analysis_state(controller: PipelineController):
    """Render content based on current analysis state"""

    # Check if analysis results exist
    if not controller.state_manager.get_analysis_results():
        render_no_results()
        return

    # Check if analysis is still running
    if controller.state_manager.is_pipeline_running():
        render_analysis_progress(controller)
        return

    # Analysis is complete - display results
    results = controller.state_manager.get_analysis_results()
    render_complete_results(results)

def render_no_results():
    """Render state when no analysis results are available"""
    st.info("⏳ No hay resultados disponibles.")
    st.markdown("""
    Para ver los resultados:
    1. Ve a **Subir y Analizar Comentarios**
    2. Carga tu archivo Excel
    3. Ejecuta el análisis
    4. Los resultados aparecerán automáticamente aquí
    """)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔙 Ir a Subir Archivo", use_container_width=True, type="primary"):
            st.switch_page("pages/2_Subir.py")

def render_analysis_progress(controller: PipelineController):
    """Render progress - not needed with synchronous processing"""
    # With synchronous processing, this should rarely be called
    # Analysis happens in real-time on page 2 before redirect

    st.info("🔄 Preparando resultados...")

    # Simple check if pipeline just finished
    if controller.state_manager.is_analysis_complete():
        st.success("✅ Análisis completado - Cargando resultados...")
        time.sleep(1)
        st.rerun()
    else:
        # Redirect back to upload page if no analysis is running
        st.warning("No se encontró análisis en progreso")

        if st.button("🔙 Volver a Subir", type="primary"):
            st.switch_page("pages/2_Subir.py")

def render_complete_results(results: Dict[str, Any]):
    """Render complete analysis results using existing UI components"""

    try:
        df = results['dataframe']
        summary = results.get('summary', {})
        metrics = results.get('metrics', {})

        # Summary metrics section
        render_summary_metrics(df, summary, metrics)

        # Charts section
        st.markdown("---")
        render_analysis_charts(df, metrics)

        # Data table section
        st.markdown("---")
        render_data_table(df)

        # Export section
        st.markdown("---")
        render_export_section(df, results)

        # Actions section
        st.markdown("---")
        render_action_buttons()

    except Exception as e:
        logger.error(f"Error rendering results: {e}")
        st.error(f"Error al mostrar resultados: {str(e)}")

        # Fallback option
        if st.button("🔄 Reintentar"):
            st.rerun()

def render_summary_metrics(df: pd.DataFrame, summary: Dict, metrics: Dict):
    """Render summary metrics using pure UI logic"""

    st.subheader("📈 Resumen del Análisis")

    # Main metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Comentarios", len(df))

    with col2:
        nps_avg = df.get('NPS', pd.Series()).mean() if 'NPS' in df.columns else 0
        st.metric("NPS Promedio", f"{nps_avg:.1f}" if not pd.isna(nps_avg) else "N/A")

    with col3:
        emotion_cols = [col for col in df.columns if col.startswith('emo_')]
        st.metric("Emociones detectadas", len(emotion_cols))

    with col4:
        high_churn = len(df[df.get('churn_risk', 0) > 0.7]) if 'churn_risk' in df.columns else 0
        st.metric("Alto riesgo churn", high_churn)

    with col5:
        pain_points = len([p for p in df.get('pain_points', []) if p]) if 'pain_points' in df.columns else 0
        st.metric("Pain points", pain_points)

    # Additional insights
    if summary or metrics:
        with st.expander("📊 Insights detallados"):
            if summary:
                st.json(summary)
            if metrics:
                st.markdown("**Distribución de métricas:**")
                st.json(metrics)

def render_analysis_charts(df: pd.DataFrame, metrics: Dict):
    """Render analysis charts using existing chart component"""

    st.subheader("📊 Visualizaciones")

    try:
        # Use existing chart generator component
        chart_generator = ChartGenerator()

        # Emotions chart
        emotion_cols = [col for col in df.columns if col.startswith('emo_')]
        if emotion_cols:
            st.markdown("#### Análisis de Emociones (16 emociones)")

            # Calculate emotion percentages
            emotion_data = df[emotion_cols].mean() * 100

            # Create chart using existing component logic
            fig_emotions = chart_generator.create_emotion_chart(emotion_data)
            if fig_emotions:
                st.plotly_chart(fig_emotions, use_container_width=True)

        # NPS distribution chart
        if 'nps_category' in df.columns:
            st.markdown("#### Distribución NPS")

            nps_data = df['nps_category'].value_counts()
            fig_nps = chart_generator.create_nps_distribution_chart(nps_data)
            if fig_nps:
                st.plotly_chart(fig_nps, use_container_width=True)

        # Churn risk chart
        if 'churn_risk' in df.columns:
            st.markdown("#### Riesgo de Churn")

            # Create risk categories
            risk_categories = pd.cut(df['churn_risk'],
                                   bins=[0, 0.3, 0.7, 1.0],
                                   labels=['Bajo', 'Medio', 'Alto'])
            risk_data = risk_categories.value_counts()

            fig_churn = chart_generator.create_churn_risk_chart(risk_data)
            if fig_churn:
                st.plotly_chart(fig_churn, use_container_width=True)

    except Exception as e:
        logger.error(f"Error creating charts: {e}")
        st.error("Error al generar gráficos. Los datos están disponibles en la tabla.")

def render_data_table(df: pd.DataFrame):
    """Render data table with filtering options"""

    st.subheader("📋 Datos Procesados")

    # Table controls
    col1, col2, col3 = st.columns(3)

    with col1:
        show_emotions = st.checkbox("Mostrar columnas de emociones", True)

    with col2:
        show_analysis = st.checkbox("Mostrar análisis (NPS, churn)", True)

    with col3:
        max_rows = st.selectbox("Filas a mostrar", [10, 25, 50, 100], index=1)

    # Filter columns based on selection
    display_cols = ['Comentario Final']  # Always show comments

    if 'NPS' in df.columns:
        display_cols.append('NPS')

    if 'Nota' in df.columns:
        display_cols.append('Nota')

    if show_emotions:
        emotion_cols = [col for col in df.columns if col.startswith('emo_')]
        display_cols.extend(emotion_cols[:5])  # Show top 5 emotions

    if show_analysis:
        analysis_cols = [col for col in df.columns if col in ['nps_category', 'churn_risk', 'pain_points']]
        display_cols.extend(analysis_cols)

    # Display filtered dataframe
    display_df = df[display_cols].head(max_rows)
    st.dataframe(display_df, use_container_width=True)

    # Show total rows info
    st.caption(f"Mostrando {len(display_df)} de {len(df)} filas totales")

def render_export_section(df: pd.DataFrame, results: Dict[str, Any]):
    """Render export options using existing export component"""

    st.subheader("💾 Exportar Resultados")
    st.markdown("Descarga los resultados en diferentes formatos:")

    try:
        # Use existing report exporter component
        exporter = ReportExporter()

        col1, col2, col3 = st.columns(3)

        with col1:
            # Excel export
            if st.button("📊 Exportar a Excel", use_container_width=True):
                try:
                    excel_data = exporter.export_to_excel(df)
                    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')

                    st.download_button(
                        label="📥 Descargar Excel",
                        data=excel_data,
                        file_name=f"analisis_comentarios_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    st.success("✅ Excel preparado para descarga")
                except Exception as e:
                    st.error(f"Error generando Excel: {str(e)}")

        with col2:
            # CSV export
            if st.button("📄 Exportar a CSV", use_container_width=True):
                try:
                    csv_data = exporter.export_to_csv(df)
                    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')

                    st.download_button(
                        label="📥 Descargar CSV",
                        data=csv_data,
                        file_name=f"analisis_comentarios_{timestamp}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    st.success("✅ CSV preparado para descarga")
                except Exception as e:
                    st.error(f"Error generando CSV: {str(e)}")

        with col3:
            # JSON export
            if st.button("🔗 Exportar a JSON", use_container_width=True):
                try:
                    json_data = exporter.export_to_json(df)
                    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')

                    st.download_button(
                        label="📥 Descargar JSON",
                        data=json_data,
                        file_name=f"analisis_comentarios_{timestamp}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                    st.success("✅ JSON preparado para descarga")
                except Exception as e:
                    st.error(f"Error generando JSON: {str(e)}")

        # Export summary
        st.markdown("---")
        with st.expander("ℹ️ Información de exportación"):
            st.markdown(f"""
            **Datos incluidos en la exportación:**
            - Total de comentarios: {len(df)}
            - Columnas disponibles: {len(df.columns)}
            - Emociones analizadas: {len([c for c in df.columns if c.startswith('emo_')])}
            - Análisis adicional: NPS, Churn Risk, Pain Points

            **Formatos disponibles:**
            - **Excel (.xlsx)**: Formato completo con formateo
            - **CSV (.csv)**: Datos tabulares para análisis posterior
            - **JSON (.json)**: Datos estructurados para integración
            """)

    except Exception as e:
        logger.error(f"Error in export section: {e}")
        st.error("Error al preparar opciones de exportación")

def render_action_buttons():
    """Render action buttons for navigation and new analysis"""

    st.subheader("🎯 Próximos pasos")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Nuevo Análisis", use_container_width=True, type="primary"):
            # Clear session state using controller
            controller = PipelineController()
            controller.cleanup()

            # Clear specific session state keys
            keys_to_clear = ['analysis_results', 'pipeline_running', 'uploaded_file', 'current_stage']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]

            st.success("✅ Estado limpiado")
            st.switch_page("pages/2_Subir.py")

    with col2:
        if st.button("🏠 Inicio", use_container_width=True):
            st.switch_page("pages/1_Landing_Page.py")

    with col3:
        if st.button("📚 Documentación", use_container_width=True):
            st.markdown("""
            **Recursos útiles:**
            - [Arquitectura del sistema](docs/ES/01_Arquitectura.md)
            - [Guía de desarrollo](docs/ES/03_Guia_Desarrollo.md)
            - [FAQ](docs/ES/06_FAQ.md)
            """)

if __name__ == "__main__":
    main()