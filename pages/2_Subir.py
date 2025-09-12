# -*- coding: utf-8 -*-
"""
Upload and Analysis Page - Refactored using Controller Pattern
Clean UI layer that delegates all logic to controller/
"""
import streamlit as st
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import controller layer (no direct core imports)
from controller import PipelineController
from config import FEATURE_FLAGS, get_openai_api_key
from utils.logging_helpers import get_logger

# Import UI components only
from components.ui_components.uploader import render_file_uploader
from components.ui_components.chart_generator import render_analysis_charts
from components.ui_components.report_exporter import render_export_section

logger = get_logger(__name__)

def main():
    """Main upload and analysis page"""
    st.title("Subir y Analizar Comentarios")
    st.markdown("Sube tu archivo Excel y ejecuta el análisis de sentimientos")
    
    # Initialize controller (handles all state management)
    controller = PipelineController()
    
    # Show current status
    render_status_section(controller)
    
    # File upload section
    st.markdown("---")
    uploaded_file = st.file_uploader(
        "Selecciona tu archivo Excel",
        type=['xlsx', 'xls'],
        help="Archivo debe contener columnas: NPS, Nota, Comentario Final"
    )
    
    if uploaded_file:
        handle_file_upload(controller, uploaded_file)
    
    # Analysis section
    if controller.state_manager.get_uploaded_file():
        st.markdown("---")
        render_analysis_section(controller)
    
    # Results section
    if controller.state_manager.is_analysis_complete():
        st.markdown("---")
        render_results_section(controller)

def render_status_section(controller: PipelineController):
    """Show current pipeline status"""
    st.markdown("### Estado del Sistema")
    
    status = controller.get_pipeline_status()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        file_status = "Cargado" if status['has_results'] else "Pendiente"
        st.metric("Archivo", file_status)
    
    with col2:
        analysis_status = "Completado" if status['is_complete'] else "Pendiente"
        st.metric("Análisis", analysis_status)
    
    with col3:
        running_status = "Procesando" if status['is_running'] else "Listo"
        st.metric("Estado", running_status)
    
    with col4:
        if 'duration_seconds' in status:
            st.metric("Tiempo", f"{status['duration_seconds']:.1f}s")
        else:
            st.metric("Tiempo", "-")
    
    # Show progress if running
    if status['is_running']:
        st.progress(0.5)  # Mock progress, real implementation would use controller progress
        st.info(f"Estado: {status.get('current_stage', 'Procesando...')}")
    
    # Show errors if any
    if status.get('error_message'):
        st.error(f"Error: {status['error_message']}")
        if st.button("Limpiar Error"):
            controller.state_manager.clear_error()
            st.rerun()

def handle_file_upload(controller: PipelineController, uploaded_file):
    """Handle file upload and validation"""
    try:
        # Validate using controller
        validation_result = controller.validate_file(uploaded_file)
        
        if validation_result['success']:
            st.success(f"Archivo validado: **{uploaded_file.name}**")
            
            # Show file info
            file_info = validation_result['file_info']
            with st.expander("Información del archivo"):
                st.json({
                    'nombre': file_info['name'],
                    'tamaño': f"{file_info['size'] / 1024:.1f} KB",
                    'validación': file_info['validation']
                })
        else:
            st.error("Archivo no válido")
            for error in validation_result.get('errors', []):
                st.error(f"• {error}")
                
    except Exception as e:
        st.error(f"Error al procesar archivo: {str(e)}")
        logger.error(f"File upload error: {e}")

def render_analysis_section(controller: PipelineController):
    """Render analysis controls"""
    st.subheader("Ejecutar Análisis")
    
    # Check if can run analysis
    status = controller.get_pipeline_status()
    
    if status['is_running']:
        st.info("Análisis en progreso...")
        if st.button("Cancelar Análisis"):
            if controller.cancel_pipeline():
                st.success("Análisis cancelado")
                st.rerun()
        return
    
    # Analysis options
    col1, col2 = st.columns(2)
    
    with col1:
        use_mock = st.checkbox(
            "Modo demo (sin API)",
            value=not bool(get_openai_api_key()),
            help="Utiliza respuestas simuladas"
        )
    
    with col2:
        show_progress = st.checkbox(
            "Mostrar progreso detallado",
            value=FEATURE_FLAGS.get('enable_batch_progress', True)
        )
    
    # Run analysis button
    if st.button("🚀 Iniciar Análisis", use_container_width=True, type="primary"):
        run_analysis_async(controller, use_mock, show_progress)

def run_analysis_async(controller: PipelineController, use_mock: bool, show_progress: bool):
    """Execute analysis using controller async pattern"""
    try:
        file_info = controller.state_manager.get_uploaded_file()
        if not file_info:
            st.error("No hay archivo cargado")
            return
        
        # Start async analysis
        controller.run_pipeline_async(
            file_path=file_info['temp_path']
        )
        
        st.success("Análisis iniciado en segundo plano")
        st.info("La página se actualizará automáticamente cuando termine")
        
        # Auto-refresh to show progress
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"Error al iniciar análisis: {str(e)}")
        logger.error(f"Analysis start error: {e}")

def render_results_section(controller: PipelineController):
    """Render analysis results using UI components"""
    st.subheader("Resultados del Análisis")
    
    results = controller.state_manager.get_analysis_results()
    if not results:
        st.warning("No hay resultados disponibles")
        return
    
    results_df = results['dataframe']
    summary = results.get('summary', {})
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Comentarios", summary.get('total_comments', 0))
    
    with col2:
        st.metric("Emociones", summary.get('emotions_detected', 0))
    
    with col3:
        avg_nps = summary.get('avg_nps_score')
        if avg_nps:
            st.metric("NPS Promedio", f"{avg_nps:.1f}")
    
    with col4:
        st.metric("Riesgo Alto", summary.get('churn_risk_high', 0))
    
    # Charts
    st.markdown("---")
    render_analysis_charts(results_df)
    
    # Export
    st.markdown("---")
    render_export_section(results_df, summary)
    
    # Raw data preview
    with st.expander("Ver datos procesados", expanded=False):
        st.dataframe(results_df.head(100))

if __name__ == "__main__":
    main()