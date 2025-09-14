# -*- coding: utf-8 -*-
"""
Streamlit Native Logger - Uses Streamlit's native capabilities for pipeline validation
Replaces external file logging with st.session_state + st.status + st.toast
No threading issues, no external files, fully compatible with Streamlit Cloud
"""
import streamlit as st
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class StreamlitNativeLogger:
    """Pipeline validation using Streamlit's native capabilities"""

    def __init__(self):
        self.session_key = "pipeline_validation"
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize session state for pipeline validation"""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "start_time": time.time(),
                "levels": {},
                "current_stage": "idle",
                "errors": [],
                "warnings": [],
                "success_count": 0,
                "total_stages": 10
            }

    def _update_session_state(self, level: str, data: Dict[str, Any], status: str = "success"):
        """Update session state with validation data"""
        try:
            session_data = st.session_state[self.session_key]
            session_data["levels"][level] = {
                "timestamp": datetime.now().isoformat(),
                "data": data,
                "status": status
            }

            if status == "success":
                session_data["success_count"] += 1
            elif status == "error":
                session_data["errors"].append(f"{level}: {data.get('error', 'Unknown error')}")
            elif status == "warning":
                session_data["warnings"].append(f"{level}: {data.get('warning', 'Warning')}")

            session_data["current_stage"] = level
            st.session_state[self.session_key] = session_data

        except Exception as e:
            # Fail silently to not break pipeline
            logger.warning(f"Could not update session state: {e}")

    # LEVEL 1: API Validation with Streamlit UI
    def log_api_validation(self, api_key_present: bool, api_key_valid: bool):
        """Log API validation with native Streamlit feedback"""
        if api_key_present and api_key_valid:
            st.toast("✅ API Key válida - Mock mode eliminado", icon="✅")
            self._update_session_state("L1_API", {
                "api_key_present": True,
                "mock_eliminated": True,
                "production_ready": True
            }, "success")
        else:
            st.toast("❌ API Key requerida - Sin fallback mock", icon="❌")
            self._update_session_state("L1_API", {
                "api_key_present": api_key_present,
                "error": "API key missing or invalid"
            }, "error")

    # LEVEL 2: Data Ingestion with Progress
    def log_data_ingestion(self, file_info: Dict[str, Any]):
        """Log data ingestion with Streamlit progress indicators"""
        rows = file_info.get("rows", 0)
        has_required = file_info.get("has_required_columns", False)

        if has_required and rows > 0:
            st.toast(f"📊 Datos cargados: {rows} filas", icon="📊")
            self._update_session_state("L2_DATA", {
                "rows_loaded": rows,
                "quality": "good" if rows > 100 else "minimal"
            }, "success")
        else:
            st.toast("⚠️ Problemas en estructura de datos", icon="⚠️")
            self._update_session_state("L2_DATA", {
                "error": "Invalid data structure or empty file"
            }, "error")

    # LEVEL 3: Smart Preprocessing with Status Container
    def log_preprocessing_with_status(self, initial_rows: int, cleaned_rows: int, nps_parsed: int):
        """Log preprocessing with detailed status container"""
        retention_rate = (cleaned_rows / initial_rows * 100) if initial_rows > 0 else 0

        with st.status(f"🧹 Procesando datos: {cleaned_rows}/{initial_rows} filas", expanded=False) as status:
            st.write(f"**Retención**: {retention_rate:.1f}%")
            st.write(f"**NPS parseados**: {nps_parsed}")

            if retention_rate > 80:
                st.write("✅ Calidad de datos excelente")
                status.update(label="✅ Datos procesados exitosamente", state="complete")
                toast_msg = f"✅ Datos limpios: {retention_rate:.1f}% retenidos"
            elif retention_rate > 60:
                st.write("⚠️ Calidad de datos aceptable")
                status.update(label="⚠️ Datos procesados con advertencias", state="running")
                toast_msg = f"⚠️ Calidad aceptable: {retention_rate:.1f}% retenidos"
            else:
                st.write("❌ Calidad de datos baja")
                status.update(label="❌ Problemas en calidad de datos", state="error")
                toast_msg = f"❌ Calidad baja: {retention_rate:.1f}% retenidos"

        st.toast(toast_msg, icon="🧹")
        self._update_session_state("L3_PREPROCESS", {
            "retention_rate": retention_rate,
            "nps_parsed": nps_parsed
        }, "success" if retention_rate > 60 else "warning")

    # LEVEL 4: API Execution Progress
    def log_api_execution_progress(self, batch_num: int, total_batches: int, success: bool):
        """Log API execution progress with native Streamlit progress"""
        progress = batch_num / total_batches

        # Update progress bar in session state
        if "api_progress" not in st.session_state:
            st.session_state.api_progress = st.progress(0)
            st.session_state.api_status = st.empty()

        st.session_state.api_progress.progress(progress)

        if success:
            st.session_state.api_status.success(f"✅ Batch {batch_num}/{total_batches} completado")
            if batch_num == total_batches:
                st.toast("🚀 Todas las llamadas API exitosas", icon="🚀")
        else:
            st.session_state.api_status.error(f"❌ Error en batch {batch_num}/{total_batches}")
            st.toast(f"❌ Error en API - Batch {batch_num}", icon="❌")

        self._update_session_state("L4_API", {
            "current_batch": batch_num,
            "total_batches": total_batches,
            "progress": progress,
            "last_success": success
        }, "success" if success else "error")

    # LEVEL 5: Response Processing
    def log_response_processing(self, parsed_count: int, expected_count: int, repairs_applied: int):
        """Log response processing with Streamlit feedback"""
        success_rate = (parsed_count / expected_count * 100) if expected_count > 0 else 0

        if success_rate > 95:
            st.toast(f"✅ Respuestas procesadas: {success_rate:.1f}%", icon="✅")
            status = "success"
        elif success_rate > 80:
            st.toast(f"⚠️ Respuestas con reparaciones: {repairs_applied}", icon="⚠️")
            status = "warning"
        else:
            st.toast(f"❌ Problemas en respuestas: {success_rate:.1f}%", icon="❌")
            status = "error"

        self._update_session_state("L5_RESPONSE", {
            "success_rate": success_rate,
            "repairs_applied": repairs_applied
        }, status)

    # LEVEL 6: NPS Inference Progress
    def log_nps_inference_with_status(self, missing_count: int, inferred_count: int, avg_confidence: float):
        """Log NPS inference with detailed status"""
        with st.status(f"🧠 Inferencia NPS: {inferred_count}/{missing_count} valores", expanded=False) as status:
            st.write(f"**Valores faltantes**: {missing_count}")
            st.write(f"**Inferidos exitosamente**: {inferred_count}")
            st.write(f"**Confianza promedio**: {avg_confidence:.2f}")

            if avg_confidence > 0.7:
                st.write("✅ Inferencia de alta calidad")
                status.update(label="✅ NPS inference completado", state="complete")
                toast_msg = f"✅ NPS inferido: {inferred_count} valores (alta calidad)"
            elif avg_confidence > 0.5:
                st.write("⚠️ Inferencia de calidad media")
                status.update(label="⚠️ NPS inference con advertencias", state="running")
                toast_msg = f"⚠️ NPS inferido: {inferred_count} valores (calidad media)"
            else:
                st.write("❌ Inferencia de baja calidad")
                status.update(label="❌ NPS inference con problemas", state="error")
                toast_msg = f"❌ NPS inferido: {inferred_count} valores (baja calidad)"

        st.toast(toast_msg, icon="🧠")
        self._update_session_state("L6_NPS", {
            "inferred_count": inferred_count,
            "confidence": avg_confidence
        }, "success")

    # LEVEL 7-10: Consolidated Final Status
    def log_pipeline_completion(self, total_time: float, comments_processed: int,
                              charts_ready: bool, export_ready: bool, sla_met: bool):
        """Log complete pipeline execution with comprehensive Streamlit feedback"""

        # Main completion status
        with st.status(f"✅ Pipeline completado en {total_time:.1f}s", expanded=True) as status:
            st.write(f"**Comentarios procesados**: {comments_processed}")
            st.write(f"**Tiempo total**: {total_time:.1f}s")
            st.write(f"**SLA cumplido**: {'✅' if sla_met else '❌'}")
            st.write(f"**Charts listos**: {'✅' if charts_ready else '❌'}")
            st.write(f"**Export listo**: {'✅' if export_ready else '❌'}")

            if sla_met and charts_ready and export_ready:
                status.update(label="🎉 Pipeline completado exitosamente", state="complete")
                overall_status = "success"
                st.balloons()  # Celebration for full success
            elif charts_ready or export_ready:
                status.update(label="⚠️ Pipeline completado con limitaciones", state="running")
                overall_status = "warning"
            else:
                status.update(label="❌ Pipeline completado con errores", state="error")
                overall_status = "error"

        # Summary toast
        if overall_status == "success":
            st.toast(f"🎉 Análisis completo: {comments_processed} comentarios en {total_time:.1f}s", icon="🎉")
        elif overall_status == "warning":
            st.toast(f"⚠️ Análisis parcial: revisar resultados", icon="⚠️")
        else:
            st.toast(f"❌ Análisis con errores: revisar configuración", icon="❌")

        # Update final session state
        self._update_session_state("L10_SUMMARY", {
            "total_time": total_time,
            "comments_processed": comments_processed,
            "sla_met": sla_met,
            "charts_ready": charts_ready,
            "export_ready": export_ready,
            "overall_status": overall_status
        }, overall_status)

    def get_session_summary(self) -> Dict[str, Any]:
        """Get current session validation summary"""
        try:
            return st.session_state.get(self.session_key, {})
        except Exception:
            return {}

    def display_validation_dashboard(self):
        """Display real-time validation dashboard using Streamlit components"""
        session_data = self.get_session_summary()

        if not session_data:
            st.info("🔄 Validación de pipeline pendiente")
            return

        st.subheader("📊 Dashboard de Validación")

        # Progress overview
        levels_completed = len(session_data.get("levels", {}))
        total_levels = session_data.get("total_stages", 10)
        progress = levels_completed / total_levels

        st.progress(progress)
        st.write(f"**Progreso**: {levels_completed}/{total_levels} niveles completados")

        # Success/Error summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Éxitos", session_data.get("success_count", 0))
        with col2:
            st.metric("⚠️ Advertencias", len(session_data.get("warnings", [])))
        with col3:
            st.metric("❌ Errores", len(session_data.get("errors", [])))

        # Show errors if any
        if session_data.get("errors"):
            with st.expander("❌ Errores Detectados", expanded=False):
                for error in session_data["errors"]:
                    st.error(error)

        # Show warnings if any
        if session_data.get("warnings"):
            with st.expander("⚠️ Advertencias", expanded=False):
                for warning in session_data["warnings"]:
                    st.warning(warning)

    def clear_validation_data(self):
        """Clear current session validation data"""
        try:
            if self.session_key in st.session_state:
                del st.session_state[self.session_key]
            st.toast("🗑️ Datos de validación limpiados", icon="🗑️")
        except Exception as e:
            logger.warning(f"Could not clear validation data: {e}")

# Global instance
streamlit_logger = StreamlitNativeLogger()

# Decorator for automatic Streamlit-native logging
def log_with_streamlit(step_name: str, show_toast: bool = True):
    """Decorator for Streamlit-native pipeline step logging"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                if show_toast:
                    st.toast(f"✅ {step_name} completado ({execution_time:.1f}s)", icon="✅")

                streamlit_logger._update_session_state(f"STEP_{step_name.upper()}", {
                    "execution_time": execution_time,
                    "status": "completed"
                }, "success")

                return result

            except Exception as e:
                execution_time = time.time() - start_time

                if show_toast:
                    st.toast(f"❌ Error en {step_name}", icon="❌")

                streamlit_logger._update_session_state(f"STEP_{step_name.upper()}", {
                    "execution_time": execution_time,
                    "error": str(e)[:100]
                }, "error")

                raise

        return wrapper
    return decorator

# Convenience functions for common UI patterns
def show_pipeline_status(stage: str, message: str, progress: float = None):
    """Show pipeline status using Streamlit native components"""
    try:
        session_data = st.session_state.get("pipeline_validation", {})
        session_data["current_stage"] = stage
        session_data["current_message"] = message

        if progress is not None:
            session_data["current_progress"] = progress

        st.session_state["pipeline_validation"] = session_data

        # Update UI
        if progress is not None:
            st.progress(progress)

        st.info(f"🔄 {stage}: {message}")

    except Exception as e:
        logger.warning(f"Could not update pipeline status: {e}")

def show_validation_metrics(metrics: Dict[str, Any]):
    """Display validation metrics using Streamlit metrics"""
    try:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("API Calls", metrics.get("api_calls", 0))

        with col2:
            st.metric("NPS Inferred", metrics.get("nps_inferred", 0))

        with col3:
            success_rate = metrics.get("success_rate", 0)
            st.metric("Success Rate", f"{success_rate:.1f}%")

        with col4:
            processing_time = metrics.get("processing_time", 0)
            st.metric("Time", f"{processing_time:.1f}s")

    except Exception as e:
        logger.warning(f"Could not display validation metrics: {e}")

def log_critical_error(error_msg: str, component: str):
    """Log critical errors with prominent Streamlit display"""
    try:
        st.error(f"🚨 **Error Crítico en {component}**: {error_msg}")
        st.toast(f"🚨 Error crítico: {component}", icon="🚨")

        # Store in session for debugging
        session_data = st.session_state.get("pipeline_validation", {})
        if "critical_errors" not in session_data:
            session_data["critical_errors"] = []

        session_data["critical_errors"].append({
            "component": component,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        })

        st.session_state["pipeline_validation"] = session_data

    except Exception as e:
        logger.error(f"Could not log critical error: {e}")

def show_success_summary(comments_processed: int, total_time: float, features_working: List[str]):
    """Show success summary with Streamlit celebration components"""
    try:
        st.success(f"🎉 **Análisis Completado Exitosamente**")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Comentarios Procesados", comments_processed)
        with col2:
            st.metric("Tiempo Total", f"{total_time:.1f}s")

        st.write("**Características Funcionales**:")
        for feature in features_working:
            st.write(f"✅ {feature}")

        if len(features_working) >= 3:  # Most features working
            st.balloons()

        st.toast(f"🎉 {comments_processed} comentarios analizados exitosamente", icon="🎉")

    except Exception as e:
        logger.warning(f"Could not show success summary: {e}")