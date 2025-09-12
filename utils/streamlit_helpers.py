import streamlit as st
from contextlib import contextmanager

@contextmanager
def show_progress_bar(label: str="Procesando..."):
    progress = st.progress(0)
    def set_progress(pct: float):
        progress.progress(int(max(0, min(100, pct))))
    try:
        yield type("Prog", (), {"set_progress": set_progress})
    finally:
        progress.progress(100)
