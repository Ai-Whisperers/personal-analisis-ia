# Plantillas de prompt (placeholder). Mantener minimalistas para latencia baja.
BATCH_PROMPT = """
Analiza los siguientes comentarios (multilenguaje ES/GN/EN).
Devuelve JSON por comentario con:
- 16 emociones (0-1) usando estas claves: alegria, tristeza, enojo, miedo, confianza, desagrado, sorpresa, expectativa,
  frustracion, gratitud, aprecio, indiferencia, decepcion, entusiasmo, verguenza, esperanza
- pain_points: lista corta de strings
- churn_risk: float 0-1
- nps_category: Detractor|Pasivo|Promotor

Comentarios:
{comments}
"""
