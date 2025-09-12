import streamlit as st
import pandas as pd
import io

def export_dataframe(df: pd.DataFrame):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Reporte")
    st.download_button(
        label="⬇️ Descargar Excel",
        data=buffer.getvalue(),
        file_name="reporte_comment_insights.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
