import os
import time
from typing import List, Dict

# Placeholder de llamada paralela a LLM. Aquí podrías integrar openai SDK real.
# Mantener este módulo SIN dependencias de Streamlit.

def analyze_batch_via_llm(comments: List[str]) -> List[Dict]:
    # Si no hay API key, devolvemos un mock determinista (para demo/offline)
    if os.getenv("OPENAI_API_KEY") is None:
        out = []
        for c in comments:
            base = 0.1 + min(0.8, len(c)/2000.0)
            out.append({
                "comentario": c,
                "emociones": {
                    "alegria": 0.05,
                    "tristeza": 0.10,
                    "enojo": 0.10,
                    "miedo": 0.05,
                    "confianza": 0.10,
                    "desagrado": 0.05,
                    "sorpresa": 0.05,
                    "expectativa": 0.10,
                    "frustracion": 0.10,
                    "gratitud": 0.05,
                    "aprecio": 0.05,
                    "indiferencia": 0.05,
                    "decepcion": 0.10,
                    "entusiasmo": 0.05,
                    "verguenza": 0.05,
                    "esperanza": 0.05
                },
                "pain_points": [],
                "churn_risk": min(1.0, base),
                "nps_category": "Pasivo"
            })
        # Simula latencia de red
        time.sleep(0.6)
        return out

    # TODO: implementar integración real con OpenAI (chat.completions o responses)
    # Este return es por ahora mock para estructura.
    return analyze_batch_via_llm.__wrapped__(comments)  # type: ignore
