import streamlit as st

st.set_page_config(page_title="Comment Insights", page_icon="🧭", layout="wide")

st.markdown('<link rel="stylesheet" href="static/css/glassmorphism_styles.css">', unsafe_allow_html=True)

st.title("🧭 Comment Insights — Landing")
st.write("Analiza comentarios (ES/GN/EN) → 16 emociones, NPS, pain points, churn risk.")

st.markdown('''
<div class="glass container">
  <div class="title">Flujo</div>
  <ol class="subtle">
    <li>Sube el Excel (formato: NPS | Nota | Comentario Final)</li>
    <li>Procesamos en paralelo (≤100 comentarios por lotes)</li>
    <li>Mostramos métricas y exportable</li>
  </ol>
</div>
''', unsafe_allow_html=True)

st.write("Navega a la página **2_Subir** desde la barra lateral.")
