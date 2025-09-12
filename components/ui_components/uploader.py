import streamlit as st

def upload_excel():
    return st.file_uploader("Subir Excel (NPS | Nota | Comentario Final)", type=["xlsx"])
