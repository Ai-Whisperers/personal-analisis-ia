"""
Landing Page - Welcome and navigation page
Pure UI - no business logic
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import APP_INFO, EMOTIONS_16, EMO_CATEGORIES, FEATURE_FLAGS
from utils.streamlit_helpers import get_state_manager, create_metrics

def main():
    """Landing page main function"""
    
    # Page header
    st.title("  Bienvenido al Personal Comment Analyzer")
    st.markdown("### Tu herramienta de analisis de sentimientos basada en IA")
    
    # Hero section
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## = Qu puedes hacer?
        
        **Personal Comment Analyzer** te permite analizar comentarios de clientes de manera automtica e inteligente:
        
        ### = **Anlisis de 16 Emociones**
        Detecta emociones especficas en cada comentario con alta precisin
        
        ### = **Anlisis NPS Automtico**  
        Categoriza clientes en Promotores, Pasivos y Detractores
        
        ###  **Prediccin de Churn**
        Identifica clientes en riesgo de abandonar tu servicio
        
        ### < **Identificacin de Pain Points**
        Encuentra problemas especficos mencionados por tus clientes
        
        ### = **Exportacin Completa**
        Descarga resultados en Excel, CSV o JSON
        """)
    
    with col2:
        st.markdown("""
        ### < Sistema de Emociones
        
        **Positivas (7):**
        - Alegra, Confianza, Expectativa
        - Gratitud, Aprecio, Entusiasmo  
        - Esperanza
        
        **Negativas (7):**
        - Tristeza, Enojo, Miedo
        - Desagrado, Frustracin
        - Decepcin, Vergenza
        
        **Neutras (2):**
        - Sorpresa, Indiferencia
        """)
    
    # Quick stats
    st.markdown("---")
    st.markdown("## = Capacidades del Sistema")
    
    metrics = {
        "Emociones Detectadas": "16",
        "Procesamiento": "Paralelo",
        "Tiempo SLA": "d10s",
        "Formato Soporte": "Excel, CSV"
    }
    
    create_metrics(metrics)
    
    # How it works section
    st.markdown("---")
    st.markdown("## = Cmo Funciona?")
    
    step_col1, step_col2, step_col3, step_col4 = st.columns(4)
    
    with step_col1:
        st.markdown("""
        ### 1 Sube tu Excel
        
        Archivo con columnas:
        - **NPS**: Puntuacin 0-10
        - **Nota**: Calificacin  
        - **Comentario Final**: Texto
        """)
    
    with step_col2:
        st.markdown("""
        ### 2 Procesamiento IA
        
        - Anlisis paralelo por lotes
        - 16 emociones por comentario
        - Identificacin de patrones
        """)
    
    with step_col3:
        st.markdown("""
        ### 3 Anlisis Avanzado
        
        - Categorizacin NPS
        - Riesgo de Churn
        - Pain Points
        """)
    
    with step_col4:
        st.markdown("""
        ### 4 Resultados
        
        - Grficos interactivos
        - Insights automticos
        - Exportacin completa
        """)
    
    # Demo section
    st.markdown("---")
    st.markdown("## < Ejemplo de Resultados")
    
    # Create sample data visualization
    with st.expander("=@ Ver ejemplo de anlisis", expanded=False):
        demo_col1, demo_col2 = st.columns(2)
        
        with demo_col1:
            st.markdown("""
            **Comentario ejemplo:**  
            *"El servicio es terrible, muy lento y el soporte no me ayuda. Estoy muy frustrado."*
            
            **Emociones detectadas:**
            - Frustracin: 85%
            - Enojo: 70%
            - Decepcin: 60%
            - Desagrado: 45%
            """)
        
        with demo_col2:
            st.markdown("""
            **Anlisis adicional:**
            - **NPS Categora**: Detractor
            - **Churn Risk**: 0.85 (Alto)
            - **Pain Points**: servicio lento, soporte deficiente
            
            **Recomendacin**: Contacto prioritario para retencin
            """)
    
    # System status
    st.markdown("---")
    st.markdown("##  Estado del Sistema")
    
    state_manager = get_state_manager()
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        from config import get_openai_api_key
        api_key = get_openai_api_key()
        
        if api_key:
            st.success("= **API**: Configurada y lista")
        else:
            if FEATURE_FLAGS.get('enable_mock_mode', True):
                st.info("=5 **API**: Modo demo disponible")
            else:
                st.error("=4 **API**: Configuracin requerida")
    
    with status_col2:
        uploaded_file = state_manager.get_uploaded_file()
        if uploaded_file:
            st.success("= **Archivo**: Listo para analizar")
        else:
            st.info("=5 **Archivo**: Esperando subida")
    
    with status_col3:
        if state_manager.is_analysis_complete():
            st.success("= **Anlisis**: Resultados disponibles")
        elif state_manager.is_pipeline_running():
            st.warning("= **Anlisis**: Procesando...")
        else:
            st.info("=5 **Anlisis**: Listo para iniciar")
    
    # Action buttons
    st.markdown("---")
    st.markdown("## = Comienza Ahora!")
    
    action_col1, action_col2, action_col3 = st.columns([1, 1, 1])
    
    with action_col1:
        if st.button("= **Subir Archivo y Analizar**", use_container_width=True, type="primary"):
            st.switch_page("pages/2_Subir.py")
    
    with action_col2:
        if uploaded_file and not state_manager.is_pipeline_running():
            if st.button("< **Iniciar Anlisis**", use_container_width=True):
                st.switch_page("pages/2_Subir.py")
        else:
            st.button("< **Iniciar Anlisis**", use_container_width=True, disabled=True)
    
    with action_col3:
        if state_manager.is_analysis_complete():
            if st.button("= **Ver Resultados**", use_container_width=True):
                st.switch_page("pages/2_Subir.py")
        else:
            st.button("= **Ver Resultados**", use_container_width=True, disabled=True)
    
    # Tips section
    st.markdown("---")
    st.markdown("## = Consejos para mejores resultados")
    
    tip_col1, tip_col2 = st.columns(2)
    
    with tip_col1:
        st.markdown("""
        ### = **Preparacin del archivo**
        - Asegrate de que las columnas tengan los nombres exactos
        - Limpia comentarios muy cortos (menos de 5 caracteres)  
        - Verifica que los valores NPS estn entre 0-10
        - Formato recomendado: Excel (.xlsx)
        """)
    
    with tip_col2:
        st.markdown("""
        ###  **Optimizacin de rendimiento**
        - Archivos de hasta 50MB son procesados eficientemente
        - Lotes de 100 comentarios se procesan en paralelo
        - Tiempo esperado: ~8-10 segundos para 1000 comentarios
        - Los resultados se guardan automticamente
        """)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #666; font-size: 0.8em; padding: 20px;'>
        < {APP_INFO['name']} v{APP_INFO['version']} | 
        Desarrollado con d por {APP_INFO['author']} | 
        <a href='{APP_INFO['repository']}' target='_blank'>Ver en GitHub</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()