# Arquitectura

- `pages/`: UI (sin lógica de negocio)
- `static/`: CSS y assets
- `core/`: lógica pura (parseo, batching, LLM, postproceso)
- `components/`: integración UI (uploader, charts, export)
- `utils/`: helpers (tiempos, logging)
- `docs/`: documentación bilingüe
- `local-reports/`: artefactos locales (gitignore)

**Reglas anti-overengineering**
- ≤480 líneas por archivo, sin ciclos de import.
- UI no bloquea; paralelo con `ThreadPoolExecutor`.
- `@st.cache_*` solo en UI-layer (no en `core/`).

**Entry point**
- `main.py` (renombrable). Ejecutar con `streamlit run main.py`.
