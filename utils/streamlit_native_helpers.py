# -*- coding: utf-8 -*-
"""
Streamlit Native Helpers - 100% Streamlit Cloud Compatible
Implements native progress indicators, status containers, and UI feedback
Following Streamlit 2025 best practices for production deployment
"""
import streamlit as st
import time
from typing import Dict, Any, Optional, List, Callable
from contextlib import contextmanager
import pandas as pd

from utils.logging_helpers import get_logger

logger = get_logger(__name__)

class StreamlitNativeProgress:
    """
    Native Streamlit progress indicators and status management
    Replaces threading-based progress with UI-native feedback
    """

    def __init__(self):
        self.current_status = None
        self.current_progress = None
        self.toast_history = []

    @contextmanager
    def progress_container(self, title: str, total_steps: int = 100):
        """
        Create a progress container with native Streamlit components

        Usage:
            with progress.progress_container("Processing", 5) as progress:
                progress.update("Step 1", 0.2)
                progress.update("Step 2", 0.4)
        """
        # Create progress components
        status_container = st.status(title, expanded=True)
        progress_bar = st.progress(0.0, text="Inicializando...")

        class ProgressUpdater:
            def __init__(self, status_container, progress_bar):
                self.status = status_container
                self.progress = progress_bar
                self.steps_completed = 0

            def update(self, message: str, progress_value: float):
                """Update progress with message and value (0.0 to 1.0)"""
                try:
                    self.progress.progress(progress_value, text=message)
                    with self.status:
                        st.write(f"⚡ {message}")

                    # Allow UI to update
                    time.sleep(0.1)

                except Exception as e:
                    logger.error(f"Error updating progress: {e}")

            def complete(self, final_message: str = "Completado"):
                """Mark progress as complete"""
                self.progress.progress(1.0, text=final_message)
                self.status.update(label=f"✅ {final_message}", state="complete")
                st.balloons()

            def error(self, error_message: str):
                """Mark progress as error"""
                self.progress.progress(0.0, text="Error")
                self.status.update(label=f"❌ {error_message}", state="error")
                st.error(error_message)

        try:
            progress_updater = ProgressUpdater(status_container, progress_bar)
            yield progress_updater

        except Exception as e:
            progress_updater.error(f"Error: {str(e)}")
            raise
        finally:
            logger.debug(f"Progress container '{title}' completed")

    def show_realtime_feedback(self, message: str, icon: str = "ℹ️"):
        """Show real-time feedback using st.toast"""
        try:
            st.toast(f"{icon} {message}")
            self.toast_history.append((time.time(), message, icon))
            logger.debug(f"Toast shown: {message}")

        except Exception as e:
            logger.error(f"Error showing toast: {e}")

    def show_success(self, message: str):
        """Show success message with celebration"""
        st.success(message)
        st.balloons()
        self.show_realtime_feedback(message, "🎉")

    def show_warning(self, message: str):
        """Show warning message"""
        st.warning(message)
        self.show_realtime_feedback(message, "⚠️")

    def show_error(self, message: str):
        """Show error message"""
        st.error(message)
        self.show_realtime_feedback(message, "🚨")

class StreamlitNativeDataDisplay:
    """
    Native data display components optimized for large datasets
    Implements pagination and memory-efficient display
    """

    def __init__(self):
        self.default_page_size = 50

    def show_paginated_dataframe(self,
                                df: pd.DataFrame,
                                page_size: int = None,
                                title: str = "Datos Procesados") -> None:
        """Display DataFrame with native pagination"""
        if df is None or len(df) == 0:
            st.warning("No hay datos para mostrar")
            return

        page_size = page_size or self.default_page_size
        total_rows = len(df)
        total_pages = (total_rows + page_size - 1) // page_size

        st.subheader(title)

        if total_pages > 1:
            # Pagination controls
            col1, col2, col3 = st.columns([1, 2, 1])

            with col1:
                current_page = st.selectbox(
                    "Página",
                    range(1, total_pages + 1),
                    index=0,
                    key="dataframe_page_selector"
                )

            with col2:
                st.info(f"Mostrando página {current_page} de {total_pages} ({total_rows} filas totales)")

            with col3:
                rows_to_show = st.selectbox(
                    "Filas por página",
                    [25, 50, 100, 200],
                    index=1,
                    key="dataframe_page_size"
                )

            # Update page size if changed
            if rows_to_show != page_size:
                page_size = rows_to_show
                total_pages = (total_rows + page_size - 1) // page_size
                current_page = min(current_page, total_pages)

            # Calculate display range
            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, total_rows)
            display_df = df.iloc[start_idx:end_idx]

        else:
            display_df = df
            st.info(f"Mostrando {total_rows} filas")

        # Display the data
        st.dataframe(display_df, use_container_width=True)

        # Summary information
        if total_pages > 1:
            st.caption(f"Filas {start_idx + 1}-{end_idx} de {total_rows}")

    def show_metrics_summary(self, metrics: Dict[str, Any]) -> None:
        """Display metrics in native Streamlit format"""
        if not metrics:
            return

        st.subheader("📈 Métricas de Análisis")

        # Extract key metrics
        emotion_pcts = metrics.get('emotion_percentages', {})
        nps_dist = metrics.get('nps_distribution', {})
        churn_dist = metrics.get('churn_risk_distribution', {})

        if emotion_pcts:
            st.markdown("#### Top Emociones")
            # Sort emotions by percentage
            sorted_emotions = sorted(emotion_pcts.items(), key=lambda x: x[1], reverse=True)

            # Display top 5 emotions as metrics
            cols = st.columns(min(5, len(sorted_emotions)))
            for i, (emotion, pct) in enumerate(sorted_emotions[:5]):
                with cols[i]:
                    # Clean emotion name (remove 'emo_' prefix if present)
                    clean_name = emotion.replace('emo_', '').title()
                    st.metric(clean_name, f"{pct:.1f}%")

        if nps_dist:
            st.markdown("#### Distribución NPS")
            cols = st.columns(len(nps_dist))
            for i, (category, pct) in enumerate(nps_dist.items()):
                with cols[i]:
                    st.metric(category.title(), f"{pct:.1f}%")

        if churn_dist:
            st.markdown("#### Riesgo de Churn")
            cols = st.columns(len(churn_dist))
            for i, (risk_level, pct) in enumerate(churn_dist.items()):
                with cols[i]:
                    st.metric(f"Riesgo {risk_level}", f"{pct:.1f}%")

class StreamlitNativeNavigation:
    """
    Native navigation helpers for page transitions
    """

    @staticmethod
    def safe_page_switch(target_page: str, delay: float = 0.5) -> None:
        """Safely switch pages with optional delay"""
        try:
            if delay > 0:
                time.sleep(delay)
            st.switch_page(target_page)

        except Exception as e:
            logger.error(f"Error switching to page {target_page}: {e}")
            st.error(f"Error navegando a {target_page}")

    @staticmethod
    def show_navigation_buttons(pages: Dict[str, str]) -> None:
        """Show navigation buttons for multiple pages"""
        if not pages:
            return

        st.markdown("### 🧭 Navegación")
        cols = st.columns(len(pages))

        for i, (label, page_path) in enumerate(pages.items()):
            with cols[i]:
                if st.button(label, use_container_width=True, key=f"nav_{i}"):
                    StreamlitNativeNavigation.safe_page_switch(page_path)

class StreamlitNativeState:
    """
    Native state management helpers
    """

    @staticmethod
    def safe_state_update(key: str, value: Any) -> bool:
        """Safely update session state with error handling"""
        try:
            st.session_state[key] = value
            return True
        except Exception as e:
            logger.error(f"Error updating state key '{key}': {e}")
            return False

    @staticmethod
    def get_state_with_default(key: str, default: Any = None) -> Any:
        """Get session state value with default fallback"""
        try:
            return st.session_state.get(key, default)
        except Exception as e:
            logger.error(f"Error getting state key '{key}': {e}")
            return default

    @staticmethod
    def clear_state_keys(keys: List[str]) -> int:
        """Clear multiple state keys safely"""
        cleared = 0
        for key in keys:
            try:
                if key in st.session_state:
                    del st.session_state[key]
                    cleared += 1
            except Exception as e:
                logger.error(f"Error clearing state key '{key}': {e}")

        return cleared

# Global instances for easy import
native_progress = StreamlitNativeProgress()
native_data_display = StreamlitNativeDataDisplay()
native_navigation = StreamlitNativeNavigation()
native_state = StreamlitNativeState()

# Convenience functions
def show_progress(title: str, total_steps: int = 100):
    """Convenience function for progress container"""
    return native_progress.progress_container(title, total_steps)

def show_success(message: str):
    """Convenience function for success message"""
    native_progress.show_success(message)

def show_error(message: str):
    """Convenience function for error message"""
    native_progress.show_error(message)

def show_warning(message: str):
    """Convenience function for warning message"""
    native_progress.show_warning(message)

def display_dataframe_paginated(df: pd.DataFrame, title: str = "Datos"):
    """Convenience function for paginated dataframe display"""
    native_data_display.show_paginated_dataframe(df, title=title)

def display_metrics(metrics: Dict[str, Any]):
    """Convenience function for metrics display"""
    native_data_display.show_metrics_summary(metrics)