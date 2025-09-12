"""
Streamlit Helpers - Wrappers and utilities for Streamlit UI components
"""
import streamlit as st
import time
from typing import Any, Dict, Optional, Callable, List
from contextlib import contextmanager
import logging

from core.progress.state_iface import StateManager, StateInterface

logger = logging.getLogger(__name__)

class StreamlitStateInterface(StateInterface):
    """Streamlit session state implementation of StateInterface"""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from Streamlit session state"""
        return st.session_state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in Streamlit session state"""
        st.session_state[key] = value
    
    def delete(self, key: str) -> None:
        """Delete key from Streamlit session state"""
        if key in st.session_state:
            del st.session_state[key]
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Streamlit session state"""
        return key in st.session_state
    
    def clear(self) -> None:
        """Clear all Streamlit session state"""
        st.session_state.clear()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all session state as dictionary"""
        return dict(st.session_state)

class StreamlitHelpers:
    """Helper functions for Streamlit UI operations"""
    
    def __init__(self):
        self.state_manager = StateManager(StreamlitStateInterface())
    
    @contextmanager
    def status_container(self, message: str, expanded: bool = False):
        """Context manager for Streamlit status container"""
        with st.status(message, expanded=expanded) as status:
            yield status
    
    @contextmanager
    def spinner_with_messages(self, initial_message: str):
        """Context manager for spinner with changeable messages"""
        placeholder = st.empty()
        
        class SpinnerManager:
            def __init__(self, placeholder):
                self.placeholder = placeholder
                self.current_spinner = None
                self.start_spinner(initial_message)
            
            def start_spinner(self, message):
                if self.current_spinner:
                    self.current_spinner.__exit__(None, None, None)
                self.current_spinner = self.placeholder.empty()
                with self.current_spinner:
                    st.spinner(message)
            
            def update_message(self, message):
                self.start_spinner(message)
            
            def __enter__(self):
                return self
            
            def __exit__(self, *args):
                if self.current_spinner:
                    self.current_spinner.empty()
        
        try:
            yield SpinnerManager(placeholder)
        finally:
            placeholder.empty()
    
    def show_progress_bar(
        self, 
        current: int, 
        total: int, 
        message: str = "",
        key: str = "progress_bar"
    ) -> None:
        """Show progress bar with message"""
        progress = current / total if total > 0 else 0
        
        progress_placeholder = st.empty()
        message_placeholder = st.empty()
        
        with progress_placeholder:
            st.progress(progress)
        
        if message:
            with message_placeholder:
                st.text(f"{message} ({current}/{total})")
    
    def show_animated_progress(
        self,
        progress_data: Dict[str, Any],
        key: str = "animated_progress"
    ) -> None:
        """Show animated progress with task details"""
        
        if not progress_data:
            return
        
        # Main progress
        overall_progress = progress_data.get('overall_progress', 0) / 100
        st.progress(overall_progress)
        
        # Current task info
        current_task = progress_data.get('current_task', 'Procesando...')
        st.text(f"📋 {current_task}")
        
        # Task breakdown
        tasks = progress_data.get('tasks', {})
        if tasks:
            with st.expander("Ver detalles de progreso", expanded=False):
                for task_name, task_info in tasks.items():
                    status = task_info.get('status', 'pending')
                    message = task_info.get('message', '')
                    
                    status_icon = {
                        'pending': '⏳',
                        'running': '🔄',
                        'completed': '✅',
                        'failed': '❌',
                        'cancelled': '⭕'
                    }.get(status, '❓')
                    
                    st.text(f"{status_icon} {task_name}: {message}")
    
    def create_metric_cards(self, metrics: Dict[str, Any]) -> None:
        """Create metric cards in columns"""
        if not metrics:
            return
        
        num_cols = min(len(metrics), 4)  # Max 4 columns
        cols = st.columns(num_cols)
        
        for i, (label, value) in enumerate(metrics.items()):
            with cols[i % num_cols]:
                if isinstance(value, dict):
                    st.metric(
                        label=value.get('label', label),
                        value=value.get('value', ''),
                        delta=value.get('delta')
                    )
                else:
                    st.metric(label=label, value=value)
    
    def show_error_with_details(
        self, 
        error_message: str, 
        details: Optional[str] = None,
        show_trace: bool = False
    ) -> None:
        """Show error message with optional details"""
        st.error(f"❌ {error_message}")
        
        if details:
            with st.expander("Ver detalles del error"):
                st.text(details)
        
        if show_trace and details:
            with st.expander("Stack trace completo"):
                st.code(details)
    
    def create_info_box(
        self,
        title: str,
        content: str,
        box_type: str = "info",
        icon: Optional[str] = None
    ) -> None:
        """Create styled info box"""
        
        icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'success': '✅',
            'error': '❌'
        }
        
        display_icon = icon or icons.get(box_type, 'ℹ️')
        
        if box_type == "info":
            st.info(f"{display_icon} **{title}**\n\n{content}")
        elif box_type == "warning":
            st.warning(f"{display_icon} **{title}**\n\n{content}")
        elif box_type == "success":
            st.success(f"{display_icon} **{title}**\n\n{content}")
        elif box_type == "error":
            st.error(f"{display_icon} **{title}**\n\n{content}")
    
    def create_expandable_section(
        self,
        title: str,
        content_func: Callable,
        expanded: bool = False,
        key: Optional[str] = None
    ) -> None:
        """Create expandable section with dynamic content"""
        with st.expander(title, expanded=expanded):
            content_func()
    
    def show_data_preview(
        self,
        data: Any,
        title: str = "Vista Previa de Datos",
        max_rows: int = 5,
        max_cols: int = 10
    ) -> None:
        """Show data preview with limits"""
        st.subheader(title)
        
        try:
            import pandas as pd
            
            if isinstance(data, pd.DataFrame):
                # Limit rows and columns for preview
                preview_data = data.head(max_rows)
                if len(data.columns) > max_cols:
                    preview_data = preview_data.iloc[:, :max_cols]
                    st.warning(f"Mostrando solo las primeras {max_cols} columnas")
                
                st.dataframe(preview_data, use_container_width=True)
                
                # Show data info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Filas", len(data))
                with col2:
                    st.metric("Columnas", len(data.columns))
                with col3:
                    st.metric("Memoria", f"{data.memory_usage(deep=True).sum() / 1024:.1f} KB")
            
            elif isinstance(data, dict):
                st.json(data)
            
            elif isinstance(data, (list, tuple)):
                st.json(data[:max_rows] if len(data) > max_rows else data)
                if len(data) > max_rows:
                    st.info(f"Mostrando solo los primeros {max_rows} elementos de {len(data)}")
            
            else:
                st.text(str(data)[:1000])  # Limit text output
        
        except Exception as e:
            st.error(f"Error mostrando vista previa: {str(e)}")
    
    def cache_data_with_ttl(
        self,
        func: Callable,
        ttl_seconds: int = 3600,
        key_suffix: str = ""
    ) -> Any:
        """Cache data with TTL using Streamlit's caching"""
        cache_key = f"{func.__name__}{key_suffix}"
        
        @st.cache_data(ttl=ttl_seconds)
        def cached_func(*args, **kwargs):
            return func(*args, **kwargs)
        
        return cached_func
    
    def safe_file_upload(
        self,
        label: str,
        accepted_types: List[str],
        max_size_mb: int = 50,
        key: Optional[str] = None
    ) -> Optional[Any]:
        """Safe file upload with validation"""
        
        uploaded_file = st.file_uploader(
            label,
            type=accepted_types,
            key=key,
            help=f"Tipos aceptados: {', '.join(accepted_types)}. Tamaño máximo: {max_size_mb}MB"
        )
        
        if uploaded_file is None:
            return None
        
        # Check file size
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            st.error(f"Archivo demasiado grande: {file_size_mb:.1f}MB. Máximo permitido: {max_size_mb}MB")
            return None
        
        # Validate file type
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension not in [ext.lower() for ext in accepted_types]:
            st.error(f"Tipo de archivo no válido: .{file_extension}")
            return None
        
        return uploaded_file
    
    def create_download_link(
        self,
        data: bytes,
        filename: str,
        mime_type: str,
        button_text: str = "Descargar"
    ) -> None:
        """Create download button"""
        st.download_button(
            label=button_text,
            data=data,
            file_name=filename,
            mime=mime_type
        )
    
    def get_state_manager(self) -> StateManager:
        """Get the state manager instance"""
        return self.state_manager

# Global instance for easy import
helpers = StreamlitHelpers()

# Convenience functions
def get_state_manager() -> StateManager:
    """Get Streamlit-backed state manager"""
    return helpers.get_state_manager()

def show_progress(current: int, total: int, message: str = "") -> None:
    """Show progress bar"""
    helpers.show_progress_bar(current, total, message)

def show_error(message: str, details: Optional[str] = None) -> None:
    """Show error message"""
    helpers.show_error_with_details(message, details)

def create_metrics(metrics: Dict[str, Any]) -> None:
    """Create metric cards"""
    helpers.create_metric_cards(metrics)