import streamlit as st
import pandas as pd

def basic_overview(df: pd.DataFrame):
    # Muestra conteos por NPS y promedios simples de emociones si existen columnas correspondientes
    cols = df.columns
    if "NPS_category" in cols:
        st.write("Distribución por NPS_category")
        st.bar_chart(df["NPS_category"].value_counts())

    emo_cols = [c for c in cols if c.startswith("emo_")]
    if emo_cols:
        st.write("Promedios de emociones (0-1)")
        st.bar_chart(df[emo_cols].mean())
