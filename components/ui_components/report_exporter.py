"""
Report Exporter Component - Exports analysis results to various formats
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from typing import Dict, Any, Optional
import tempfile
from pathlib import Path

class ReportExporter:
    """Handles exporting analysis results to different formats"""
    
    def __init__(self):
        self.export_formats = {
            'xlsx': 'Excel (.xlsx)',
            'csv': 'CSV (.csv)', 
            'json': 'JSON (.json)'
        }
        self.reports_dir = Path("local-reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    def render_export_section(self, df: pd.DataFrame, analysis_summary: Optional[Dict[str, Any]] = None) -> None:
        """Render export options and buttons"""
        st.subheader("📥 Exportar Resultados")
        st.write("Descarga los resultados del análisis en diferentes formatos")
        
        if df.empty:
            st.warning("No hay datos para exportar")
            return
        
        # Export format selection
        col1, col2 = st.columns([2, 1])
        
        with col1:
            export_format = st.selectbox(
                "Formato de exportación:",
                options=list(self.export_formats.keys()),
                format_func=lambda x: self.export_formats[x],
                key="export_format_selector"
            )
        
        with col2:
            include_summary = st.checkbox(
                "Incluir resumen", 
                value=True,
                help="Incluir hoja de resumen con estadísticas"
            )
        
        # Export options
        st.write("**Opciones de exportación:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            include_emotions = st.checkbox("🎭 Datos de emociones", value=True)
        
        with col2:
            include_analysis = st.checkbox("📊 Análisis completo", value=True)
        
        with col3:
            include_raw = st.checkbox("📄 Datos originales", value=False)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analisis_comentarios_{timestamp}"
        
        # Export button
        if st.button("⬇️ Exportar Resultados", key="export_button"):
            try:
                with st.spinner("Generando reporte..."):
                    export_data = self._prepare_export_data(
                        df, 
                        analysis_summary,
                        include_emotions=include_emotions,
                        include_analysis=include_analysis,
                        include_raw=include_raw,
                        include_summary=include_summary
                    )
                    
                    if export_format == 'xlsx':
                        file_path = self._export_to_excel(export_data, filename)
                    elif export_format == 'csv':
                        file_path = self._export_to_csv(export_data, filename)
                    elif export_format == 'json':
                        file_path = self._export_to_json(export_data, filename)
                    
                    st.success(f"✅ Reporte exportado: {file_path.name}")
                    
                    # Provide download link
                    self._create_download_link(file_path, export_format)
                    
            except Exception as e:
                st.error(f"❌ Error al exportar: {str(e)}")
        
        # Show export preview
        if st.checkbox("Ver vista previa de exportación", key="preview_export"):
            self._show_export_preview(df)
    
    def _prepare_export_data(
        self, 
        df: pd.DataFrame, 
        analysis_summary: Optional[Dict[str, Any]],
        include_emotions: bool = True,
        include_analysis: bool = True,
        include_raw: bool = False,
        include_summary: bool = True
    ) -> Dict[str, Any]:
        """Prepare data for export based on selected options"""
        
        export_data = {}
        
        # Main analysis data
        if include_analysis:
            # Create clean version of the dataframe
            analysis_df = df.copy()
            
            # Remove internal columns if not including raw data
            if not include_raw:
                cols_to_remove = []
                for col in analysis_df.columns:
                    if col.startswith('_') or col in ['index', 'temp_path']:
                        cols_to_remove.append(col)
                analysis_df = analysis_df.drop(columns=cols_to_remove, errors='ignore')
            
            # Include/exclude emotion columns
            if not include_emotions:
                emotion_cols = [col for col in analysis_df.columns if col.startswith('emo_')]
                analysis_df = analysis_df.drop(columns=emotion_cols, errors='ignore')
            
            export_data['Analisis_Completo'] = analysis_df
        
        # Emotions summary
        if include_emotions and include_summary:
            emotion_cols = [col for col in df.columns if col.startswith('emo_')]
            if emotion_cols:
                emotion_summary = []
                for col in emotion_cols:
                    emotion_name = col.replace('emo_', '')
                    avg_score = df[col].mean()
                    max_score = df[col].max()
                    count_high = (df[col] > 0.5).sum()
                    
                    emotion_summary.append({
                        'Emocion': emotion_name.capitalize(),
                        'Promedio': round(avg_score, 3),
                        'Maximo': round(max_score, 3),
                        'Casos_Altos': count_high,
                        'Porcentaje': round(avg_score * 100, 1)
                    })
                
                export_data['Resumen_Emociones'] = pd.DataFrame(emotion_summary)
        
        # Analysis summary
        if include_summary and analysis_summary:
            summary_data = []
            for key, value in analysis_summary.items():
                if isinstance(value, (int, float, str)):
                    summary_data.append({'Metrica': key, 'Valor': value})
            
            if summary_data:
                export_data['Resumen_Analisis'] = pd.DataFrame(summary_data)
        
        # NPS summary
        if 'nps_category' in df.columns and include_summary:
            nps_summary = df['nps_category'].value_counts().reset_index()
            nps_summary.columns = ['Categoria_NPS', 'Cantidad']
            nps_summary['Porcentaje'] = (nps_summary['Cantidad'] / len(df) * 100).round(1)
            export_data['Resumen_NPS'] = nps_summary
        
        # Churn risk summary
        if 'churn_risk' in df.columns and include_summary:
            churn_data = df['churn_risk'].dropna()
            if len(churn_data) > 0:
                risk_categories = pd.cut(
                    churn_data, 
                    bins=[0, 0.3, 0.7, 1.0], 
                    labels=['Bajo', 'Medio', 'Alto']
                )
                churn_summary = risk_categories.value_counts().reset_index()
                churn_summary.columns = ['Nivel_Riesgo', 'Cantidad']
                churn_summary['Porcentaje'] = (churn_summary['Cantidad'] / len(churn_data) * 100).round(1)
                export_data['Resumen_Churn'] = churn_summary
        
        return export_data
    
    def _export_to_excel(self, export_data: Dict[str, Any], filename: str) -> Path:
        """Export to Excel format with multiple sheets"""
        file_path = self.reports_dir / f"{filename}.xlsx"
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for sheet_name, data in export_data.items():
                if isinstance(data, pd.DataFrame):
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Auto-adjust column widths
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return file_path
    
    def _export_to_csv(self, export_data: Dict[str, Any], filename: str) -> Path:
        """Export to CSV format (main data only)"""
        file_path = self.reports_dir / f"{filename}.csv"
        
        # Export the main analysis data
        main_data_key = 'Analisis_Completo'
        if main_data_key in export_data:
            export_data[main_data_key].to_csv(file_path, index=False, encoding='utf-8')
        elif export_data:
            # Export the first available dataset
            first_key = list(export_data.keys())[0]
            export_data[first_key].to_csv(file_path, index=False, encoding='utf-8')
        
        return file_path
    
    def _export_to_json(self, export_data: Dict[str, Any], filename: str) -> Path:
        """Export to JSON format"""
        file_path = self.reports_dir / f"{filename}.json"
        
        # Convert DataFrames to dictionaries
        json_data = {}
        for key, data in export_data.items():
            if isinstance(data, pd.DataFrame):
                json_data[key] = data.to_dict(orient='records')
            else:
                json_data[key] = data
        
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        return file_path
    
    def _create_download_link(self, file_path: Path, export_format: str):
        """Create download link for the exported file"""
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            mime_types = {
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'csv': 'text/csv',
                'json': 'application/json'
            }
            
            st.download_button(
                label=f"💾 Descargar {file_path.name}",
                data=file_data,
                file_name=file_path.name,
                mime=mime_types.get(export_format, 'application/octet-stream'),
                key=f"download_{file_path.name}"
            )
            
        except Exception as e:
            st.error(f"Error creando enlace de descarga: {str(e)}")
    
    def _show_export_preview(self, df: pd.DataFrame):
        """Show preview of what will be exported"""
        st.write("**Vista previa de datos a exportar:**")
        
        # Show basic info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Total Filas", len(df))
        
        with col2:
            st.metric("📋 Total Columnas", len(df.columns))
        
        with col3:
            emotion_cols = [col for col in df.columns if col.startswith('emo_')]
            st.metric("🎭 Columnas Emociones", len(emotion_cols))
        
        # Show sample data
        st.write("**Muestra de datos (primeras 3 filas):**")
        
        # Select relevant columns for preview
        preview_cols = []
        
        # Always include these if they exist
        important_cols = ['NPS', 'Nota', 'Comentario Final', 'nps_category', 'churn_risk', 'pain_points']
        for col in important_cols:
            if col in df.columns:
                preview_cols.append(col)
        
        # Add a few emotion columns
        emotion_cols = [col for col in df.columns if col.startswith('emo_')][:5]
        preview_cols.extend(emotion_cols)
        
        if preview_cols:
            st.dataframe(df[preview_cols].head(3), use_container_width=True)
        else:
            st.dataframe(df.head(3), use_container_width=True)

def render_export_section(df: pd.DataFrame, analysis_summary: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function to render export section"""
    exporter = ReportExporter()
    exporter.render_export_section(df, analysis_summary)