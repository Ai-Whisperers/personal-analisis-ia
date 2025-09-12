# PROJECT_BLUEPRINT.md

Este documento empaqueta la **arquitectura**, **reglas anti-overengineering**, **estructura**, y **guía rápida** del proyecto.

## Reglas anti-colapso
1. UI solo en `pages/` + `static/` (sin lógica).
2. Lógica en `core/` (sin Streamlit).
3. ≤480 líneas/archivo; sin import cíclicos.
4. Concurrencia paralela en `core/ai_engine/api_call.py` (ThreadPoolExecutor).
5. Estado/caché: UI layer (session_state, cache_data/resource).
6. SLA: ≤10 s P50 (800–1200 filas). Medido en `utils/performance_monitor.py`.

## Estructura (resumen)
- `main.py` entrypoint (renombrable).
- `pages/` UI multipágina.
- `static/` CSS glassmorphism.
- `core/` parseo→batch→LLM→merge.
- `components/` integración UI.
- `utils/` helpers.
- `docs/` ES/EN.
- `local-reports/` (gitignore).

## Pipeline
Excel → parseo → validación/limpieza → batch (≤100) → LLM paralelo → merge → export/visualización.

## Emociones (16)
alegria, tristeza, enojo, miedo, confianza, desagrado, sorpresa, expectativa,
frustracion, gratitud, aprecio, indiferencia, decepcion, entusiasmo, verguenza, esperanza

## Cómo correr
```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...   # opcional (sin esto, usa mock)
streamlit run main.py
```
