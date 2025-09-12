"""
File Uploader Component - Handles Excel file uploads with validation
"""
import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any
import tempfile
import os

from core.file_processor import reader, validator

class FileUploader:
    """Streamlit file upload component with validation"""
    
    def __init__(self):
        self.supported_types = ['xlsx', 'xls', 'csv']
        self.max_file_size_mb = 50
    
    def render(self, key: str = "file_uploader") -> Optional[Dict[str, Any]]:
        """Render file upload component and return file info if uploaded"""
        
        st.subheader("📂 Subir Archivo Excel")
        st.write("Sube tu archivo Excel con las columnas: **NPS**, **Nota**, **Comentario Final**")
        
        uploaded_file = st.file_uploader(
            "Selecciona tu archivo",
            type=self.supported_types,
            key=key,
            help="Formatos soportados: .xlsx, .xls, .csv"
        )
        
        if uploaded_file is None:
            return None
        
        # Display file info
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        st.info(f"📄 **{uploaded_file.name}** ({file_size_mb:.1f} MB)")
        
        # Check file size
        if file_size_mb > self.max_file_size_mb:
            st.error(f"❌ Archivo demasiado grande. Máximo: {self.max_file_size_mb} MB")
            return None
        
        # Process file
        with st.spinner("Procesando archivo..."):
            try:
                # Save to temporary file
                temp_path = self._save_temp_file(uploaded_file)
                
                # Validate file
                file_info = reader.reader.get_file_info(temp_path)
                
                if 'error' in file_info:
                    st.error(f"❌ Error al leer el archivo: {file_info['error']}")
                    self._cleanup_temp_file(temp_path)
                    return None
                
                # Display file information
                self._display_file_info(file_info)
                
                # Validate columns
                if not file_info['has_required_columns']:
                    st.error("❌ **Columnas faltantes:**")
                    for col in file_info['missing_columns']:
                        st.write(f"   • {col}")
                    st.write("**Columnas disponibles:**")
                    for col in file_info['column_names']:
                        st.write(f"   • {col}")
                    self._cleanup_temp_file(temp_path)
                    return None
                
                # Show preview
                if st.checkbox("Ver vista previa", key=f"{key}_preview"):
                    self._show_preview(temp_path)
                
                # Return file information
                return {
                    'temp_path': temp_path,
                    'filename': uploaded_file.name,
                    'size_mb': file_size_mb,
                    'info': file_info,
                    'validated': True
                }
                
            except Exception as e:
                st.error(f"❌ Error procesando archivo: {str(e)}")
                return None
    
    def _save_temp_file(self, uploaded_file) -> str:
        """Save uploaded file to temporary location"""
        suffix = os.path.splitext(uploaded_file.name)[1]
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(uploaded_file.getvalue())
        temp_file.close()
        return temp_file.name
    
    def _cleanup_temp_file(self, temp_path: str):
        """Clean up temporary file"""
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass  # Ignore cleanup errors
    
    def _display_file_info(self, file_info: Dict[str, Any]):
        """Display file information in nice format"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📊 Filas", file_info['rows'])
            st.metric("📋 Columnas", file_info['columns'])
        
        with col2:
            st.metric("💾 Tamaño", f"{file_info['size_mb']} MB")
            status = "✅ Válido" if file_info['has_required_columns'] else "❌ Inválido"
            st.metric("🔍 Estado", status)
    
    def _show_preview(self, temp_path: str):
        """Show data preview"""
        try:
            df_preview = reader.get_file_preview(temp_path, rows=5)
            st.subheader("Vista Previa")
            st.dataframe(df_preview, use_container_width=True)
            
            # Show basic stats
            st.subheader("Estadísticas Básicas")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'NPS' in df_preview.columns:
                    nps_valid = df_preview['NPS'].dropna()
                    if len(nps_valid) > 0:
                        st.metric("NPS Promedio", f"{nps_valid.mean():.1f}")
            
            with col2:
                if 'Comentario Final' in df_preview.columns:
                    comments = df_preview['Comentario Final'].dropna()
                    if len(comments) > 0:
                        avg_length = comments.str.len().mean()
                        st.metric("Long. Promedio", f"{avg_length:.0f} chars")
            
            with col3:
                if 'Nota' in df_preview.columns:
                    ratings = df_preview['Nota'].dropna()
                    if len(ratings) > 0:
                        st.metric("Nota Promedio", f"{ratings.mean():.1f}")
        
        except Exception as e:
            st.error(f"Error mostrando vista previa: {str(e)}")

def render_file_uploader(key: str = "main_uploader") -> Optional[Dict[str, Any]]:
    """Convenience function to render file uploader"""
    uploader = FileUploader()
    return uploader.render(key)