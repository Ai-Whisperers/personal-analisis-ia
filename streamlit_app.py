# -*- coding: utf-8 -*-
"""
Personal Comment Analyzer - Streamlit App Entry Point
Minimal router following blueprint <150 lines requirement
"""
import streamlit as st
import sys
from pathlib import Path

# Configure Streamlit page FIRST
st.set_page_config(
    page_title="Personal Comment Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/Ai-Whisperers/personal-analisis-ia',
        'Report a bug': "https://github.com/Ai-Whisperers/personal-analisis-ia/issues",
        'About': "# Personal Comment Analyzer\nAnálisis de sentimientos con IA usando 16 emociones específicas."
    }
)

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import configuration and utilities
from config import APP_INFO, FEATURE_FLAGS, validate_config, get_secret
from utils.logging_helpers import setup_logging, get_logger
from utils.streamlit_helpers import inject_css

# Initialize logging
log_level = get_secret("LOG_LEVEL", "INFO")
setup_logging(level=log_level, log_to_console=True, log_to_file=True)
logger = get_logger(__name__)

# Apply CSS globally (must be after page config)
inject_css()

def main():
    """Main application entry point - minimal router"""
    
    # Validate configuration
    if not validate_config():
        st.error("⚠️ Configuration validation failed. Please check the logs.")
        st.stop()
    
    # Application header
    render_app_header()
    
    # Navigation section
    render_navigation_section()
    
    # System status
    render_system_status()
    
    # Footer
    render_footer()
    
    logger.info(f"Application started - {APP_INFO['name']} v{APP_INFO['version']}")

def render_app_header():
    """Render application header"""
    st.title(f"📊 {APP_INFO['name']}")
    st.markdown(f"*{APP_INFO['description']}*")
    st.markdown(f"**Versión:** {APP_INFO['version']}")

def render_navigation_section():
    """Render navigation instructions and quick access"""
    st.markdown("---")
    st.markdown("## 📋 Cómo usar la aplicación:")
    st.markdown("""
    1. **📂 Landing Page**: Ve a **1_Landing_Page** para información del sistema
    2. **📤 Subir Archivo**: Usa **2_Subir** para cargar Excel y ejecutar análisis  
    3. **📊 Resultados**: Los gráficos aparecen automáticamente después del análisis
    
    **📋 Formato requerido:** Excel con columnas `NPS`, `Nota`, `Comentario Final`
    """)
    
    # Quick access buttons
    st.markdown("### 🚀 Acceso Rápido:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📂 Landing Page", use_container_width=True):
            st.switch_page("pages/1_Landing_Page.py")
    
    with col2:
        if st.button("📤 Subir y Analizar", use_container_width=True, type="primary"):
            st.switch_page("pages/2_Subir.py")
    
    with col3:
        if st.button("📋 Documentación", use_container_width=True):
            show_documentation_modal()

def show_documentation_modal():
    """Show documentation in expandable section"""
    with st.expander("📚 Documentación", expanded=True):
        st.markdown("""
        ### 🎭 16 Emociones
        **Positivas:** alegría, confianza, expectativa, gratitud, aprecio, entusiasmo, esperanza
        **Negativas:** tristeza, enojo, miedo, desagrado, frustración, decepción, vergüenza  
        **Neutras:** sorpresa, indiferencia
        
        ### 📊 Análisis: NPS, Churn, Pain Points, Exportación
        ### ⚡ SLA: ≤10s para 800-1200 comentarios
        """)

def render_system_status():
    """Render system status indicators"""
    st.markdown("---")
    st.markdown("### 🔍 Estado del Sistema:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # API key status
        from config import get_openai_api_key
        api_key = get_openai_api_key()
        
        if api_key:
            st.success("🔑 API Key: Configurada")
        else:
            if FEATURE_FLAGS.get('enable_mock_mode', True):
                st.info("🔑 Modo Demo Activo")
            else:
                st.error("🔑 API Key: No configurada")
    
    with col2:
        # Controller status
        try:
            from controller import PipelineController
            st.success("🎛️ Controller: Disponible")
        except ImportError:
            st.error("🎛️ Controller: Error")
    
    with col3:
        # Configuration status
        if FEATURE_FLAGS:
            st.success("⚙️ Config: Válida")
        else:
            st.warning("⚙️ Config: Limitada")

def render_footer():
    """Render application footer"""
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
        {APP_INFO['name']} v{APP_INFO['version']} | 
        <a href='{APP_INFO['repository']}' target='_blank'>GitHub Repository</a> | 
        Desarrollado por {APP_INFO['author']}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()