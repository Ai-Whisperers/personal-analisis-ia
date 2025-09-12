"""
Personal Comment Analyzer - Streamlit App Entry Point
Production-ready Streamlit application following 2025 best practices
"""
import streamlit as st
import sys
import os
from pathlib import Path

# Configure Streamlit page FIRST (must be the first Streamlit command)
st.set_page_config(
    page_title="Personal Comment Analyzer",
    page_icon="[EMOTIONS]",
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

# Import configuration and utilities AFTER st.set_page_config
from config import APP_INFO, FEATURE_FLAGS, validate_config, get_secret
from utils.logging_helpers import setup_logging, get_logger
from utils.streamlit_helpers import get_state_manager

# Initialize logging with secrets support
log_level = get_secret("LOG_LEVEL", "INFO")
setup_logging(level=log_level, log_to_console=True, log_to_file=True)
logger = get_logger(__name__)

def main():
    """Main application entry point"""
    
    # Validate configuration
    if not validate_config():
        st.error("[ERROR] Configuration validation failed. Please check the logs.")
        st.stop()
    
    # Initialize state manager
    state_manager = get_state_manager()
    
    # Application header
    st.title(f"[EMOTIONS] {APP_INFO['name']}")
    st.markdown(f"*{APP_INFO['description']}*")
    st.markdown(f"**Versión:** {APP_INFO['version']}")
    
    # Show debug info if enabled
    if FEATURE_FLAGS.get('enable_debug_mode', False):
        with st.expander("[CONFIG] Debug Information"):
            st.json({
                "app_info": APP_INFO,
                "feature_flags": FEATURE_FLAGS,
                "state_summary": state_manager.get_state_summary()
            })
    
    # Navigation instructions
    st.markdown("---")
    st.markdown("""
    ## [CHECKLIST] Cómo usar la aplicación:
    
    1. **[FOLDER] Página Principal**: Ve a la página **1_Landing_Page** para comenzar
    2. **[UPLOAD] Subir Archivo**: Usa la página **2_Subir** para subir tu Excel y ejecutar el análisis
    3. **[DATA] Resultados**: Los resultados aparecerán automáticamente después del análisis
    
    ### [DOCUMENT] Formato de archivo requerido:
    Tu archivo Excel debe contener las siguientes columnas:
    - **NPS**: Puntuación NPS (0-10)
    - **Nota**: Calificación del cliente
    - **Comentario Final**: Texto del comentario a analizar
    """)
    
    # Quick access buttons
    st.markdown("---")
    st.markdown("### [LAUNCH] Acceso Rápido:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("[FOLDER] Ir a Landing Page", use_container_width=True):
            st.switch_page("pages/1_Landing_Page.py")
    
    with col2:
        if st.button("[UPLOAD] Subir y Analizar", use_container_width=True):
            st.switch_page("pages/2_Subir.py")
    
    with col3:
        if st.button("[DATA] Ver Documentación", use_container_width=True):
            with st.expander("[DOCS] Documentación del Sistema", expanded=True):
                st.markdown("""
                ### [EMOTIONS] Sistema de 16 Emociones
                
                El sistema analiza cada comentario para detectar 16 emociones específicas:
                
                **Emociones Positivas (7):**
                - alegría, confianza, expectativa, gratitud, aprecio, entusiasmo, esperanza
                
                **Emociones Negativas (7):**
                - tristeza, enojo, miedo, desagrado, frustración, decepción, vergüenza
                
                **Emociones Neutras (2):**
                - sorpresa, indiferencia
                
                ### [CHART] Análisis Incluido
                
                - **Distribución de emociones**: % de cada emoción en todos los comentarios
                - **Análisis NPS**: Categorización en Promotores, Pasivos, Detractores
                - **Riesgo de Churn**: Probabilidad de abandono del cliente
                - **Pain Points**: Identificación de problemas específicos
                - **Exportación**: Resultados en Excel, CSV o JSON
                
                ### [PERFORMANCE] Rendimiento
                
                - **Procesamiento paralelo**: Análisis optimizado por lotes
                - **SLA Target**: ≤10 segundos para 800-1200 comentarios
                - **Modo Mock**: Funciona sin API key para pruebas
                """)
    
    # System status
    st.markdown("---")
    st.markdown("### [SEARCH] Estado del Sistema:")
    
    # Check system readiness
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        # API key status
        from config import get_openai_api_key, is_mock_mode
        api_key = get_openai_api_key()
        
        if api_key:
            st.success("[KEY] API Key: Configurada")
        else:
            if FEATURE_FLAGS.get('enable_mock_mode', True):
                st.info("[KEY] API Key: Modo Mock Activo")
            else:
                st.error("[KEY] API Key: No Configurada")
    
    with status_col2:
        # File upload status
        uploaded_file = state_manager.get_uploaded_file()
        if uploaded_file:
            st.success("[DOCUMENT] Archivo: Cargado")
        else:
            st.info("[DOCUMENT] Archivo: Pendiente")
    
    with status_col3:
        # Analysis status
        if state_manager.is_analysis_complete():
            st.success("[TARGET] Análisis: Completado")
        elif state_manager.is_pipeline_running():
            st.warning("[TARGET] Análisis: En Proceso")
        else:
            st.info("[TARGET] Análisis: Pendiente")
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
        {APP_INFO['name']} v{APP_INFO['version']} | 
        <a href='{APP_INFO['repository']}' target='_blank'>GitHub Repository</a> | 
        Desarrollado por {APP_INFO['author']}
    </div>
    """, unsafe_allow_html=True)
    
    # Log application start
    logger.info(f"Application started - {APP_INFO['name']} v{APP_INFO['version']}")

if __name__ == "__main__":
    main()