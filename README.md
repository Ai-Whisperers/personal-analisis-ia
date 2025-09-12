# Comment Insights — Streamlit

**Objetivo:** Analizar comentarios (Excel con columnas `NPS | Nota | Comentario Final`) y producir **analisis de emociones**, **pain points**, **churn risk** y **NPS** en **≤10s** (P50) con batch paralelo (≤100 comentarios/call) usando LLM (`gpt-4o-mini` por defecto).

- UI: `pages/` + estilos `static/` (glassmorphism).
- Lógica pura (sin Streamlit) en `core/`.
- Evitamos *overengineering*: módulos pequeños, ≤480 líneas por archivo, caché/estado claros.
- Documentación bilingüe en `docs/ES` y `docs/EN`.
- Carpeta `local-reports/` (gitignore) para artefactos sensibles locales.


## Documentacion detallada


> Para detalles completos, ver `docs/ES/01_Arquitectura.md` y `docs/ES/02_Flujo_Pipeline.md`.
