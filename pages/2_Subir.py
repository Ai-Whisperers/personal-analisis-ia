import streamlit as st
import pandas as pd
from components.ui_components import uploader, report_exporter, chart_generator
from core.ai_engine.engine_controller import run_analysis
from utils.streamlit_helpers import show_progress_bar

st.set_page_config(page_title="Subir y Analizar", page_icon="📈", layout="wide")

st.title("📈 Subir Comentarios y Analizar")

uploaded = uploader.upload_excel()

if uploaded is not None:
    st.success("Archivo recibido.")

    # Vista previa
    try:
        df_preview = pd.read_excel(uploaded)
        st.write("Vista previa (5 primeras filas):")
        st.dataframe(df_preview.head())
    except Exception as e:
        st.error(f"Error leyendo el Excel: {e}")

    if st.button("🚀 Analizar ahora", type="primary"):
        with show_progress_bar("Analizando en paralelo...") as p:
            try:
                results_df, timings = run_analysis(uploaded, progress_cb=p.set_progress)
                st.success("Listo.")
                st.subheader("Resultados (primeras 10 filas)")
                st.dataframe(results_df.head(10))

                st.subheader("Descargar reporte")
                report_exporter.export_dataframe(results_df)

                st.subheader("Vistas")
                chart_generator.basic_overview(results_df)

                with st.expander("Tiempos de cada etapa"):
                    st.json(timings)
            except Exception as e:
                st.error(f"Falló el análisis: {e}")
else:
    st.info("Sube un Excel con columnas: NPS | Nota | Comentario Final")
