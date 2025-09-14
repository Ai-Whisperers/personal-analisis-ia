# -*- coding: utf-8 -*-
"""
Synchronous Pipeline Controller - Streamlit-Native Implementation
Replaces background threading with synchronous processing + real-time UI updates
Following Streamlit 2025 best practices and blueprint guidelines
"""
import streamlit as st
import time
import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path
import tempfile
import os

from .interfaces import IPipelineRunner, IStateManager, IProgressTracker
from .optimized_state_manager import OptimizedStateManager as StreamlitStateManager

# Import core modules (existing logic)
from core.ai_engine.engine_controller import EngineController
from core.ai_engine.api_client_core import LLMApiClient
from core.progress.tracker import ProgressTracker

# Import utilities
from utils.logging_helpers import get_logger
from utils.performance_monitor import monitor
from utils.streamlit_native_helpers import show_progress, show_success, show_error
from config import get_openai_api_key

logger = get_logger(__name__)

class SynchronousPipelineController(IPipelineRunner):
    """
    Streamlit-native pipeline controller with synchronous processing
    Eliminates threading issues while providing real-time UI feedback
    """

    def __init__(self, state_manager: Optional[IStateManager] = None):
        """Initialize synchronous pipeline controller"""
        self.state_manager = state_manager or StreamlitStateManager()
        self.progress_tracker = ProgressTracker()

        # Initialize core components
        api_key = get_openai_api_key()
        self.api_client = LLMApiClient(api_key=api_key)

        # Get batch configuration from config
        try:
            from config import BATCH_CONFIG
            batch_config = BATCH_CONFIG
        except ImportError:
            batch_config = {}

        self.engine_controller = EngineController(self.api_client, batch_config)

        logger.info("Synchronous pipeline controller initialized")

    def run_pipeline(self, file_path: str) -> Dict[str, Any]:
        """
        Execute complete pipeline synchronously with real-time UI updates
        Uses Streamlit-native progress indicators and status containers
        """
        # Initialize progress tracking
        progress_placeholder = st.empty()
        status_container = st.status("Iniciando análisis...", expanded=True)
        progress_bar = st.progress(0.0, text="Preparando pipeline...")

        try:
            self.state_manager.set_pipeline_running(True)
            self.state_manager.set_current_stage("initializing")

            with status_container:
                st.write("🔧 Configurando pipeline de análisis...")
                progress_bar.progress(0.1, text="Pipeline configurado")
                time.sleep(0.5)  # Allow UI to update

                # Stage 1: File Processing
                st.write("📂 Procesando archivo de comentarios...")
                progress_bar.progress(0.2, text="Leyendo archivo Excel...")

                self.state_manager.set_current_stage("file_processing")
                results_df = self._execute_pipeline_with_progress(
                    file_path, progress_bar, status_container
                )

                # Stage 2: Results Processing
                st.write("🎯 Procesando resultados...")
                progress_bar.progress(0.9, text="Formateando resultados...")

                # Convert DataFrame to serializable format
                results = {
                    'dataframe': results_df,
                    'summary': self._generate_summary(results_df),
                    'metrics': self._extract_metrics(results_df),
                    'file_path': file_path,
                    'processing_complete': True
                }

                # Final stage
                progress_bar.progress(1.0, text="¡Análisis completado!")
                st.write("✅ Análisis completado exitosamente")

                # Store results in session state
                self.state_manager.set_analysis_results(results)
                self.state_manager.set_pipeline_running(False)

                logger.info("Synchronous pipeline completed successfully")

                # Success feedback
                st.balloons()
                st.toast("✅ Análisis completado - Resultados disponibles", icon="🎉")

                return results

        except Exception as e:
            error_msg = f"Error en pipeline: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Error handling with UI feedback
            status_container.error(f"❌ Error: {error_msg}")
            st.error(error_msg)
            st.toast(f"❌ Error: {error_msg}", icon="🚨")

            self.state_manager.set_error_message(error_msg)
            self.state_manager.set_pipeline_running(False)

            raise

    def _execute_pipeline_with_progress(
        self,
        file_path: str,
        progress_bar: st.progress,
        status_container: st.status
    ) -> pd.DataFrame:
        """Execute engine controller pipeline with real-time progress updates"""

        # Create a custom progress callback
        def update_progress(stage: str, progress: float, message: str = ""):
            """Update UI with current progress without rerunning"""
            progress_bar.progress(progress, text=message or stage)
            status_container.write(f"⚡ {stage}: {message}")
            # Removed st.rerun() to prevent infinite loops and UI instability
            time.sleep(0.1)  # Brief pause to allow UI to render naturally

        # Override engine controller progress tracking
        original_run = self.engine_controller.run_pipeline

        def run_with_progress(file_path: str) -> pd.DataFrame:
            """Wrapper to inject progress updates"""

            # Set up progress callback in engine controller
            self.engine_controller.set_progress_callback(update_progress)

            # Use performance monitor (should work in sync context)
            with monitor("sync_pipeline_execution"):
                start_time = time.time()

                # Execute the actual pipeline with integrated progress callbacks
                results_df = original_run(file_path)

                # Final processing stage
                update_progress("Post-procesamiento", 0.9, "Finalizando resultados")

                total_time = time.time() - start_time
                logger.info(f"Synchronous pipeline completed in {total_time:.2f}s")

                return results_df

        return run_with_progress(file_path)

    def validate_file(self, uploaded_file) -> Dict[str, Any]:
        """
        Validate uploaded file with real-time feedback
        """
        # Show validation progress
        with st.status("Validando archivo...", expanded=False) as status:
            try:
                st.write("📝 Verificando formato de archivo...")

                # Save uploaded file to temp location
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                st.write("🔍 Validando estructura de datos...")

                # Use existing file validation from reader module
                from core.file_processor.reader import validate_file

                is_valid = validate_file(tmp_path)
                validation_result = {
                    'success': is_valid,
                    'message': 'Estructura válida' if is_valid else 'Formato inválido'
                }

                if validation_result['success']:
                    st.write("✅ Validación completada")

                    file_info = {
                        'name': uploaded_file.name,
                        'size': len(uploaded_file.getvalue()),
                        'temp_path': tmp_path,
                        'hash': str(hash(uploaded_file.getvalue())),
                        'validation': validation_result
                    }

                    self.state_manager.set_uploaded_file(file_info)
                    logger.info(f"File validated successfully: {uploaded_file.name}")

                    status.update(label="✅ Archivo validado", state="complete")
                    st.toast(f"✅ Archivo validado: {uploaded_file.name}", icon="📋")

                    return {
                        'success': True,
                        'file_info': file_info,
                        'message': 'Validación exitosa'
                    }
                else:
                    # Clean up temp file on validation failure
                    try:
                        os.unlink(tmp_path)
                        logger.debug(f"Cleaned up temp file after validation failure: {tmp_path}")
                    except Exception as cleanup_error:
                        logger.warning(f"Could not cleanup temp file {tmp_path}: {cleanup_error}")

                    status.update(label="❌ Validación fallida", state="error")
                    st.toast("❌ Archivo inválido", icon="⚠️")

                    return {
                        'success': False,
                        'errors': validation_result.get('errors', []),
                        'message': 'Validación fallida'
                    }

            except Exception as e:
                error_msg = f"Error en validación: {str(e)}"
                logger.error(error_msg, exc_info=True)

                status.update(label="❌ Error de validación", state="error")
                st.toast(f"❌ {error_msg}", icon="🚨")

                return {
                    'success': False,
                    'error': error_msg,
                    'message': 'Proceso de validación falló'
                }

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline execution status"""
        return {
            'is_running': self.state_manager.is_pipeline_running(),
            'is_complete': self.state_manager.is_analysis_complete(),
            'current_stage': self.state_manager.get_current_stage(),
            'error_message': self.state_manager.get_error_message(),
            'has_results': self.state_manager.get_analysis_results() is not None,
            'duration_seconds': self.state_manager.get_pipeline_duration() or 0
        }

    def _generate_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate analysis summary from results DataFrame"""
        try:
            emotion_cols = [col for col in df.columns if col.startswith('emo_')]

            summary = {
                'total_comments': len(df),
                'emotions_detected': len(emotion_cols),
                'avg_nps_score': df.get('NPS', pd.Series()).mean() if 'NPS' in df.columns else None,
                'churn_risk_high': len(df[df.get('churn_risk', 0) > 0.7]) if 'churn_risk' in df.columns else 0,
                'processing_method': 'synchronous_streamlit_native'
            }

            # Top emotions
            if emotion_cols:
                emotion_means = df[emotion_cols].mean().sort_values(ascending=False)
                summary['top_emotions'] = emotion_means.head(5).to_dict()

            return summary

        except Exception as e:
            logger.warning(f"Error generating summary: {e}")
            return {
                'total_comments': len(df) if df is not None else 0,
                'processing_method': 'synchronous_streamlit_native'
            }

    def _extract_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract key metrics from results"""
        try:
            metrics = {}

            # Emotion distribution
            emotion_cols = [col for col in df.columns if col.startswith('emo_')]
            if emotion_cols:
                emotion_pcts = (df[emotion_cols].mean() * 100).round(2)
                metrics['emotion_percentages'] = emotion_pcts.to_dict()

            # NPS distribution
            if 'nps_category' in df.columns:
                nps_dist = df['nps_category'].value_counts(normalize=True) * 100
                metrics['nps_distribution'] = nps_dist.to_dict()

            # Churn risk levels
            if 'churn_risk' in df.columns:
                risk_levels = pd.cut(df['churn_risk'],
                                   bins=[0, 0.3, 0.7, 1.0],
                                   labels=['Low', 'Medium', 'High'])
                risk_dist = risk_levels.value_counts(normalize=True) * 100
                metrics['churn_risk_distribution'] = risk_dist.to_dict()

            return metrics

        except Exception as e:
            logger.warning(f"Error extracting metrics: {e}")
            return {}

    def cleanup(self) -> None:
        """Clean up resources and temporary files with explicit error handling"""
        try:
            # Clean up temp files
            file_info = self.state_manager.get_uploaded_file()
            if file_info and 'temp_path' in file_info:
                temp_path = file_info['temp_path']
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                        logger.debug(f"Cleaned up temp file: {temp_path}")

                        # Clear file info from state after successful cleanup
                        self.state_manager.set_uploaded_file(None)

                    except PermissionError as e:
                        logger.warning(f"Permission denied cleaning up temp file {temp_path}: {e}")
                    except FileNotFoundError:
                        logger.debug(f"Temp file already cleaned up: {temp_path}")
                    except Exception as e:
                        logger.warning(f"Unexpected error cleaning up temp file {temp_path}: {e}")

            # Also trigger memory optimization
            if hasattr(self.state_manager, 'optimize_memory'):
                self.state_manager.optimize_memory()

            logger.info("Synchronous pipeline controller cleanup complete")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except Exception:
            # Silent cleanup in destructor
            pass