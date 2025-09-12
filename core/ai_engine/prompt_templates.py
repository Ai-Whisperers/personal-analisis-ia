# -*- coding: utf-8 -*-
"""
Prompt Templates for LLM analysis
Contains system and user prompts for emotion and analysis tasks
"""

class PromptTemplates:
    """Centralized prompt management for LLM calls"""
    
    def get_system_prompt(self) -> str:
        """System prompt defining the AI assistant's role and output format"""
        return """Eres un experto analista de sentimientos y emociones en español. 
Tu tarea es analizar comentarios de clientes y proporcionar:

1. EMOCIONES: Puntaje 0-1 para cada una de estas 16 emociones específicas:
   - Positivas: alegria, confianza, expectativa, gratitud, aprecio, entusiasmo, esperanza
   - Negativas: tristeza, enojo, miedo, desagrado, frustracion, decepcion, verguenza
   - Neutras: sorpresa, indiferencia

2. PAIN POINTS: Lista de problemas o puntos de dolor identificados

3. CHURN RISK: Probabilidad 0-1 de que el cliente abandone el servicio

4. SENTIMENT: Clasificación general (positive/negative/neutral)

IMPORTANTE: Responde SIEMPRE en formato JSON válido. Ejemplo:

{
  "emotions": {
    "alegria": 0.8,
    "tristeza": 0.1,
    "enojo": 0.2,
    ... (incluir las 16 emociones)
  },
  "pain_points": ["problema1", "problema2"],
  "churn_risk": 0.3,
  "sentiment": "positive"
}"""
    
    def get_analysis_prompt(self, comment: str) -> str:
        """Generate analysis prompt for a specific comment"""
        return f"""Analiza el siguiente comentario de cliente:

"{comment}"

Proporciona tu análisis en formato JSON con:
1. Puntuación 0-1 para cada una de las 16 emociones
2. Lista de pain points identificados
3. Riesgo de churn (0-1)
4. Sentiment general

Responde únicamente con el JSON, sin explicaciones adicionales."""
    
    def get_batch_prompt(self, comments: list) -> str:
        """Generate prompt for batch processing (if needed)"""
        comments_text = "\n".join([f"{i+1}. {comment}" for i, comment in enumerate(comments)])
        
        return f"""Analiza los siguientes comentarios de clientes:

{comments_text}

Para cada comentario, proporciona el análisis en formato JSON array:
[
  {{"comment_id": 1, "emotions": {{"alegria": 0.8, ...}}, "pain_points": [...], "churn_risk": 0.3, "sentiment": "positive"}},
  {{"comment_id": 2, ...}},
  ...
]

Responde únicamente con el JSON array, sin explicaciones adicionales."""