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
    
    def get_batch_analysis_prompt(self, comments: list) -> str:
        """Generate optimized prompt for batch processing with clear separators"""
        # Create numbered list with clear separators
        comments_text = ""
        for i, comment in enumerate(comments, 1):
            comments_text += f"COMENTARIO_{i}: {comment}\n"
            if i < len(comments):
                comments_text += "---\n"
        
        return f"""Analiza TODOS los siguientes {len(comments)} comentarios de clientes y proporciona el análisis completo para cada uno.

{comments_text}

INSTRUCCIONES CRÍTICAS:
1. Analiza cada comentario individualmente
2. Proporciona exactamente {len(comments)} análisis en el JSON array
3. Mantén el orden exacto de los comentarios
4. Para cada comentario incluye TODAS las 16 emociones con valores 0-1

Formato de respuesta - JSON array con exactamente {len(comments)} elementos:
[
  {{
    "emotions": {{
      "alegria": 0.0, "tristeza": 0.0, "enojo": 0.0, "miedo": 0.0,
      "confianza": 0.0, "desagrado": 0.0, "sorpresa": 0.0, "expectativa": 0.0,
      "frustracion": 0.0, "gratitud": 0.0, "aprecio": 0.0, "indiferencia": 0.0,
      "decepcion": 0.0, "entusiasmo": 0.0, "verguenza": 0.0, "esperanza": 0.0
    }},
    "pain_points": ["punto1", "punto2"],
    "churn_risk": 0.5,
    "sentiment": "positive"
  }},
  ... ({len(comments)} elementos total)
]

Responde ÚNICAMENTE con el JSON array válido, sin texto adicional."""
    
    def get_batch_prompt(self, comments: list) -> str:
        """Legacy method - redirects to optimized batch analysis"""
        return self.get_batch_analysis_prompt(comments)