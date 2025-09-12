# Flujo del Pipeline

1) Excel → `core/file_processor/reader.py`
2) Validación/limpieza/normalización
3) División por lotes (≤100)
4) Paralelo al LLM → `core/ai_engine/api_call.py`
5) Ensamblado de resultados → DataFrame
6) Visualización/Export en UI

**SLA:** ≤10 s P50 (800–1200 filas)
