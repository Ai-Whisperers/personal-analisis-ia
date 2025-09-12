"""
Personal Comment Analyzer - Streamlit Application Entry Point
Punto de entrada principal de la aplicación con configuración y navegación.
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Personal Comment Analyzer",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Personal Comment Analyzer - Sistema de análisis de sentimientos con IA"
    }
)

# Load glassmorphism styles
st.markdown('<link rel="stylesheet" href="static/css/glassmorphism_styles.css">', unsafe_allow_html=True)

# Custom CSS for better Streamlit styling
st.markdown('''
<style>
/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Custom sidebar styling */
.css-1d391kg {
    background: rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(10px);
}

/* Main content area */
.stApp > div:first-child {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

/* Sidebar navigation styling */
.css-17eq0hr {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 1rem;
    margin: 0.5rem 0;
    backdrop-filter: blur(5px);
}
</style>
''', unsafe_allow_html=True)

# Welcome message
st.markdown('''
<div class="glass-card fade-in">
    <div class="title">🧭 Personal Comment Analyzer</div>
    <div class="subtitle">Bienvenido al sistema de análisis de sentimientos con IA</div>
    <div class="subtle">
        Utiliza la barra lateral para navegar entre las diferentes funcionalidades
    </div>
</div>
''', unsafe_allow_html=True)

# Navigation guide
st.markdown('''
<div class="glass container">
    <div class="title">📍 Navegación</div>
    <div class="grid-2">
        <div class="glass-metric">
            <div class="metric-value">🏠</div>
            <div class="metric-label">Landing Page</div>
            <div class="subtle">Información general y características del sistema</div>
        </div>
        <div class="glass-metric glass-success">
            <div class="metric-value">📈</div>
            <div class="metric-label">Subir y Analizar</div>
            <div class="subtle">Cargar archivos Excel y ejecutar análisis con IA</div>
        </div>
    </div>
</div>
''', unsafe_allow_html=True)

# Quick start guide
st.markdown('''
<div class="glass-card glass-warning">
    <div class="title">🚀 Inicio Rápido</div>
    <ol class="subtle">
        <li><strong>Preparar datos:</strong> Excel con columnas NPS | Nota | Comentario Final</li>
        <li><strong>Navegar:</strong> Ir a página "Subir" en la barra lateral</li>
        <li><strong>Cargar:</strong> Subir archivo Excel (.xlsx)</li>
        <li><strong>Analizar:</strong> Ejecutar análisis automático con IA</li>
        <li><strong>Visualizar:</strong> Explorar dashboards y descargar reportes</li>
    </ol>
</div>
''', unsafe_allow_html=True)

# System status
st.markdown('''
<div class="glass container">
    <div class="title">⚡ Estado del Sistema</div>
    <div class="grid-4">
        <div class="glass-metric glass-success">
            <div class="metric-value">✅</div>
            <div class="metric-label">Core Engine</div>
        </div>
        <div class="glass-metric glass-success">
            <div class="metric-value">✅</div>
            <div class="metric-label">Data Pipeline</div>
        </div>
        <div class="glass-metric glass-success">
            <div class="metric-value">✅</div>
            <div class="metric-label">Glassmorphism UI</div>
        </div>
        <div class="glass-metric glass-warning">
            <div class="metric-value">🔄</div>
            <div class="metric-label">Mock/API Ready</div>
        </div>
    </div>
</div>
''', unsafe_allow_html=True)
