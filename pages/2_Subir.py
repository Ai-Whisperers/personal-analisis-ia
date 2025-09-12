"""
Upload and Analysis Page - Main workflow page
Handles file upload, analysis execution, and results display
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import tempfile
import os
import time
from typing import Optional, Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import modules following new architecture
from config import APP_INFO, FEATURE_FLAGS, get_openai_api_key
from utils.streamlit_helpers import get_state_manager, show_error, create_metrics
from utils.logging_helpers import get_logger
from utils.performance_monitor import monitor

# Import UI components
from components.ui_components.uploader import render_file_uploader
from components.ui_components.chart_generator import render_analysis_charts
from components.ui_components.report_exporter import render_export_section

# Import core modules
from core.ai_engine.engine_controller import EngineController
from core.ai_engine.api_call import LLMApiClient

# Initialize logger
logger = get_logger(__name__)

def main():
    """Main upload and analysis page"""
    
    st.title("=Â Subir y Analizar Comentarios")
    st.markdown("Sube tu archivo Excel y ejecuta el análisis de sentimientos")
    
    # Initialize state manager
    state_manager = get_state_manager()
    
    # Show current status
    show_current_status(state_manager)
    
    # File upload section
    st.markdown("---")
    uploaded_file_info = render_file_uploader("main_file_uploader")
    
    if uploaded_file_info:
        # Store file info in state
        state_manager.set_uploaded_file(uploaded_file_info)
        state_manager.set_file_validated(uploaded_file_info.get('validated', False))
        
        st.success(f" Archivo cargado: **{uploaded_file_info['filename']}**")
        
        # Analysis section
        st.markdown("---")
        render_analysis_section(state_manager, uploaded_file_info)
    
    # Results section (if analysis is complete)
    if state_manager.is_analysis_complete():
        st.markdown("---")
        render_results_section(state_manager)

def show_current_status(state_manager):
    """Show current pipeline status"""
    
    st.markdown("### =Ê Estado Actual")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        file_uploaded = state_manager.get_uploaded_file() is not None
        if file_uploaded:
            st.metric("=Ä Archivo", " Cargado")
        else:
            st.metric("=Ä Archivo", "ó Pendiente")
    
    with col2:
        if state_manager.is_file_validated():
            st.metric("= Validación", " OK")
        else:
            st.metric("= Validación", "ó Pendiente")
    
    with col3:
        if state_manager.is_pipeline_running():
            st.metric("™ Procesando", "= En curso")
        elif state_manager.is_analysis_complete():
            st.metric("™ Procesando", " Completo")
        else:
            st.metric("™ Procesando", "ó Listo")
    
    with col4:
        if state_manager.is_analysis_complete():
            st.metric("=È Resultados", " Disponible")
        else:
            st.metric("=È Resultados", "ó Pendiente")
    
    # Show progress if pipeline is running
    if state_manager.is_pipeline_running():
        progress_data = state_manager.get_progress_data()
        if progress_data:
            st.progress(progress_data.get('overall_progress', 0) / 100)
            current_task = progress_data.get('current_task', 'Procesando...')
            st.text(f"=Ë {current_task}")

def render_analysis_section(state_manager, uploaded_file_info: Dict[str, Any]):
    """Render analysis controls and execution"""
    
    st.subheader("<¯ Ejecutar Análisis")
    
    # Check prerequisites
    can_run_analysis = (
        uploaded_file_info.get('validated', False) and 
        not state_manager.is_pipeline_running()
    )
    
    if not can_run_analysis:
        if not uploaded_file_info.get('validated', False):
            st.warning("  Archivo no válido. Por favor, sube un archivo con las columnas requeridas.")
        elif state_manager.is_pipeline_running():
            st.info("ó Análisis en progreso...")
        return
    
    # Analysis options
    st.markdown("### ™ Opciones de Análisis")
    
    opt_col1, opt_col2 = st.columns(2)
    
    with opt_col1:
        use_mock = st.checkbox(
            ">ê Usar modo demo (sin API)", 
            value=not bool(get_openai_api_key()),
            help="Utiliza respuestas simuladas para pruebas"
        )
    
    with opt_col2:
        show_progress = st.checkbox(
            "=Ê Mostrar progreso detallado", 
            value=FEATURE_FLAGS.get('enable_batch_progress', True),
            help="Muestra el progreso de cada etapa del análisis"
        )
    
    # Run analysis button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("=€ **Iniciar Análisis**", use_container_width=True, type="primary"):
            run_analysis(state_manager, uploaded_file_info, use_mock, show_progress)

def run_analysis(
    state_manager, 
    uploaded_file_info: Dict[str, Any], 
    use_mock: bool, 
    show_progress: bool
):
    """Execute the analysis pipeline"""
    
    try:
        # Mark pipeline as running
        state_manager.set_pipeline_running(True)
        state_manager.clear_pipeline_error()
        
        # Setup progress tracking
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        # Initialize engine controller
        api_key = None if use_mock else get_openai_api_key()
        api_client = LLMApiClient(api_key=api_key)
        controller = EngineController(api_client)
        
        temp_file_path = uploaded_file_info['temp_path']
        
        # Execute pipeline with progress tracking
        with status_placeholder.container():
            st.info("=€ Iniciando análisis...")
        
        if show_progress:
            with progress_placeholder.container():
                progress_bar = st.progress(0)
                progress_text = st.empty()
                
                # Mock progress updates (in real implementation, this would come from the pipeline)
                stages = [
                    "=Ä Cargando archivo...",
                    ">ù Limpiando datos...",
                    " Validando estructura...",
                    "> Procesando con IA...",
                    "<­ Analizando emociones...", 
                    "=Ê Generando métricas...",
                    "( Finalizando..."
                ]
                
                for i, stage in enumerate(stages):
                    progress = (i + 1) / len(stages)
                    progress_bar.progress(progress)
                    progress_text.text(stage)
                    
                    if i == 3:  # AI processing stage - takes longer
                        time.sleep(1)
                    else:
                        time.sleep(0.3)
        
        # Run actual pipeline
        start_time = time.time()
        
        with monitor.measure_time("pipeline_execution", "pipeline_execution"):
            results_df = controller.run_pipeline(temp_file_path)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Store results
        state_manager.set_pipeline_results(results_df)
        state_manager.set_pipeline_running(False)
        
        # Clear progress displays
        progress_placeholder.empty()
        
        # Show success message
        with status_placeholder.container():
            st.success(f" **¡Análisis completado!** Procesado en {duration:.1f} segundos")
            
            # Show basic stats
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            
            with stats_col1:
                st.metric("=Ê Comentarios", len(results_df))
            
            with stats_col2:
                emotion_cols = [col for col in results_df.columns if col.startswith('emo_')]
                st.metric("<­ Emociones", len(emotion_cols))
            
            with stats_col3:
                st.metric("ñ Tiempo", f"{duration:.1f}s")
        
        # Cleanup temp file
        cleanup_temp_file(uploaded_file_info.get('temp_path'))
        
        logger.info(f"Analysis completed successfully in {duration:.1f}s for {len(results_df)} rows")
        
        # Auto-refresh to show results
        st.rerun()
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Analysis failed: {error_msg}")
        
        # Update state
        state_manager.set_pipeline_error(error_msg)
        state_manager.set_pipeline_running(False)
        
        # Show error
        progress_placeholder.empty()
        with status_placeholder.container():
            show_error("Error en el análisis", error_msg)
        
        # Cleanup temp file
        cleanup_temp_file(uploaded_file_info.get('temp_path'))

def render_results_section(state_manager):
    """Render analysis results and charts"""
    
    st.subheader("=È Resultados del Análisis")
    
    results_df = state_manager.get_pipeline_results()
    
    if results_df is None or results_df.empty:
        st.warning("No hay resultados disponibles")
        return
    
    # Results overview
    st.markdown("### =Ê Resumen General")
    
    overview_col1, overview_col2, overview_col3, overview_col4 = st.columns(4)
    
    with overview_col1:
        st.metric("=Ý Total Comentarios", len(results_df))
    
    with overview_col2:
        if 'nps_category' in results_df.columns:
            promoters = (results_df['nps_category'] == 'promoter').sum()
            st.metric("< Promotores", promoters)
    
    with overview_col3:
        if 'churn_risk' in results_df.columns:
            high_risk = (results_df['churn_risk'] > 0.7).sum()
            st.metric("  Alto Riesgo", high_risk)
    
    with overview_col4:
        emotion_cols = [col for col in results_df.columns if col.startswith('emo_')]
        if emotion_cols:
            # Find most common emotion
            emotion_means = results_df[emotion_cols].mean()
            top_emotion = emotion_means.idxmax().replace('emo_', '')
            st.metric("<­ Emoción Top", top_emotion.capitalize())
    
    # Charts section
    st.markdown("---")
    render_analysis_charts(results_df)
    
    # Export section
    st.markdown("---")
    
    # Generate analysis summary for export
    analysis_summary = generate_analysis_summary(results_df)
    render_export_section(results_df, analysis_summary)
    
    # Raw data preview
    with st.expander("= Ver datos procesados (preview)", expanded=False):
        st.dataframe(results_df.head(10), use_container_width=True)
        st.info(f"Mostrando 10 de {len(results_df)} filas totales")

def generate_analysis_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate summary statistics for the analysis"""
    
    summary = {
        "total_comments": len(df),
        "processing_timestamp": pd.Timestamp.now().isoformat()
    }
    
    # NPS analysis
    if 'nps_category' in df.columns:
        nps_counts = df['nps_category'].value_counts()
        summary.update({
            "promoters": nps_counts.get('promoter', 0),
            "passives": nps_counts.get('passive', 0), 
            "detractors": nps_counts.get('detractor', 0)
        })
        
        # Calculate NPS score
        total_valid = summary["promoters"] + summary["passives"] + summary["detractors"]
        if total_valid > 0:
            nps_score = ((summary["promoters"] - summary["detractors"]) / total_valid) * 100
            summary["nps_score"] = round(nps_score, 1)
    
    # Emotion analysis
    emotion_cols = [col for col in df.columns if col.startswith('emo_')]
    if emotion_cols:
        emotion_means = df[emotion_cols].mean()
        top_emotion = emotion_means.idxmax().replace('emo_', '')
        summary.update({
            "top_emotion": top_emotion,
            "top_emotion_score": round(emotion_means.max() * 100, 1)
        })
    
    # Churn analysis
    if 'churn_risk' in df.columns:
        churn_data = df['churn_risk'].dropna()
        if len(churn_data) > 0:
            summary.update({
                "avg_churn_risk": round(churn_data.mean(), 3),
                "high_churn_risk_count": (churn_data > 0.7).sum()
            })
    
    return summary

def cleanup_temp_file(temp_path: Optional[str]):
    """Clean up temporary file"""
    if temp_path and os.path.exists(temp_path):
        try:
            os.unlink(temp_path)
        except Exception:
            pass  # Ignore cleanup errors

if __name__ == "__main__":
    main()