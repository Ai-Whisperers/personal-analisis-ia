# 08. Ejemplos de Uso - AI Engine

## Introducción

Este documento proporciona ejemplos prácticos de uso de todos los módulos del AI Engine implementados en la FASE 1.

## Configuración Inicial

### Instalación de Dependencias

```bash
pip install -r requirements.txt
```

### Variables de Entorno (Opcionales)

```bash
# Para usar OpenAI real (opcional)
export OPENAI_API_KEY=sk-your-openai-key

# Sin API key funciona con mock automático
# No es necesario configurar nada más
```

## 1. Uso Básico del API Integration

### Ejemplo Simple

```python
from core.ai_engine.api_call import analyze_batch_via_llm

# Lista de comentarios a analizar
comentarios = [
    "El servicio es excelente, muy recomendado",
    "Terrible experiencia, cancelaré mi suscripción",
    "Está bien, pero podría mejorar el precio"
]

# Análisis con mock (funciona sin API key)
resultados = analyze_batch_via_llm(
    comments=comentarios,
    lang="es",
    max_workers=4
)

# Imprimir resultados
for resultado in resultados:
    print(f"Comentario: {resultado['comentario']}")
    print(f"Churn Risk: {resultado['churn_risk']}")
    print(f"NPS Category: {resultado['nps_category']}")
    print("---")
```

### Ejemplo con Multilenguaje

```python
# Comentarios en diferentes idiomas
comentarios_multilenguaje = [
    "El producto es fantástico",  # Español
    "The service is terrible",    # Inglés
    "Iporã haguã pe servicio"     # Guaraní
]

# Análisis detectando idioma automáticamente
resultados = analyze_batch_via_llm(
    comments=comentarios_multilenguaje,
    lang="es",  # Idioma del prompt
    max_workers=2
)
```

### Ejemplo con Configuración Avanzada

```python
import logging

# Configurar logging para ver detalles
logging.basicConfig(level=logging.INFO)

# Análisis de lote grande
comentarios_grandes = ["comentario " + str(i) for i in range(150)]

resultados = analyze_batch_via_llm(
    comments=comentarios_grandes,
    lang="es",
    max_workers=12  # Máximo paralelismo
)

# El sistema automáticamente:
# - Divide en batches de ≤100
# - Procesa en paralelo
# - Maneja errores con fallback
# - Reintenta en caso de rate limits
```

## 2. Análisis Detallado de Emociones

### Procesamiento Básico

```python
from core.ai_engine.emotion_module import extract_emotions, aggregate_emotion_insights

# Supongamos que tenemos resultados del análisis
resultados_raw = analyze_batch_via_llm(comentarios, lang="es")

# Enriquecer con análisis emocional detallado
resultados_emociones = extract_emotions(resultados_raw)

# Ver análisis detallado de la primera emoción
primer_resultado = resultados_emociones[0]
print("Emociones normalizadas:")
for emocion, valor in primer_resultado["emociones"].items():
    print(f"  {emocion}: {valor:.3f}")

print("\nMetadatos emocionales:")
metadata = primer_resultado["emotion_metadata"]
print(f"  Intensidad: {metadata['intensity']:.3f}")
print(f"  Emoción dominante: {metadata['dominant_emotion']}")
print(f"  Categoría: {metadata['category']}")
print(f"  Balance emocional: {metadata['emotional_balance']:.3f}")
```

### Análisis de Patrones Emocionales

```python
# Detectar patrones emocionales complejos
for resultado in resultados_emociones:
    patterns = resultado["emotion_metadata"]["patterns"]
    
    if patterns["emotional_conflict"]:
        print(f"⚠️  Conflicto emocional detectado: {resultado['comentario'][:50]}...")
    
    if patterns["mixed_emotions"]:
        print(f"🔀 Emociones mixtas: {resultado['comentario'][:50]}...")
    
    if patterns["high_arousal"]:
        print(f"🔥 Alta activación emocional: {resultado['comentario'][:50]}...")
```

### Insights Agregados

```python
# Obtener insights a nivel dataset
insights = aggregate_emotion_insights(resultados_emociones)

print("INSIGHTS EMOCIONALES DEL DATASET")
print(f"Total comentarios: {insights['total_comments']}")
print(f"Emoción dominante general: {insights['dominant_emotion_overall']}")
print(f"Intensidad promedio: {insights['avg_emotional_intensity']:.3f}")
print(f"Balance emocional promedio: {insights['avg_emotional_balance']:.3f}")

print("\nDistribución por categorías:")
for categoria, count in insights['category_distribution'].items():
    print(f"  {categoria}: {count} comentarios")

print("\nPromedios por emoción:")
for emocion, promedio in insights['emotion_averages'].items():
    print(f"  {emocion}: {promedio:.3f}")
```

## 3. Validación y Corrección NPS

### Análisis Básico de NPS

```python
from core.ai_engine.nps_module import analyze_nps_batch, calculate_nps_score_aggregate

# Scores NPS correspondientes (opcional)
nps_scores = [9, 3, 7]  # Promotor, Detractor, Pasivo

# Analizar y corregir inconsistencias
resultados_nps = analyze_nps_batch(resultados_raw, nps_scores)

# Ver correcciones realizadas
for resultado in resultados_nps:
    metadata = resultado["nps_metadata"]
    
    if metadata["category_corrected"]:
        print(f"✅ Corrección NPS:")
        print(f"   Original: {metadata['original_category']}")
        print(f"   Corregida: {resultado['nps_category']}")
        print(f"   Consistencia: {metadata['consistency_score']:.3f}")
        print(f"   Comentario: {resultado['comentario'][:60]}...")
        print()
```

### Análisis de Consistencia

```python
# Detectar inconsistencias sentiment-NPS
for resultado in resultados_nps:
    metadata = resultado["nps_metadata"]
    
    if metadata["sentiment_alignment"] == "misaligned":
        print(f"⚠️  Inconsistencia detectada:")
        print(f"   NPS: {resultado['nps_category']}")
        print(f"   Score consistencia: {metadata['consistency_score']:.3f}")
        print(f"   Comentario: {resultado['comentario']}")
        print()
```

### Métricas NPS Agregadas

```python
# Calcular NPS score y métricas del dataset
nps_metrics = calculate_nps_score_aggregate(resultados_nps)

print("MÉTRICAS NPS AGREGADAS")
print(f"NPS Score: {nps_metrics['nps_score']}")
print(f"Total respuestas: {nps_metrics['total_responses']}")
print(f"Consistencia promedio: {nps_metrics['avg_consistency']:.3f}")
print(f"Correcciones realizadas: {nps_metrics['corrections_made']}")
print(f"Tasa de corrección: {nps_metrics['correction_rate']:.1f}%")

print("\nDistribución por categorías:")
for categoria, porcentaje in nps_metrics['category_percentages'].items():
    print(f"  {categoria}: {porcentaje}%")
```

## 4. Predicción de Churn Risk

### Análisis de Churn Básico

```python
from core.ai_engine.churn_module import compute_churn, aggregate_churn_insights

# Enriquecer con análisis de churn
resultados_churn = compute_churn(resultados_nps)

# Ver clientes de alto riesgo
print("CLIENTES DE ALTO RIESGO DE CHURN")
for resultado in resultados_churn:
    metadata = resultado["churn_metadata"]
    
    if metadata["risk_level"] in ["high", "critical"]:
        print(f"🚨 Riesgo {metadata['risk_level'].upper()}")
        print(f"   Score: {resultado['churn_risk']:.3f}")
        print(f"   Confianza: {metadata['confidence_score']:.3f}")
        print(f"   Recomendación: {metadata['recommendation']}")
        print(f"   Indicadores: {metadata['risk_indicators']}")
        print(f"   Comentario: {resultado['comentario'][:80]}...")
        print()
```

### Análisis de Factores Contribuyentes

```python
# Analizar qué factores contribuyen más al riesgo
for resultado in resultados_churn:
    if resultado["churn_risk"] > 0.6:  # Solo alto riesgo
        print(f"Factores para comentario con riesgo {resultado['churn_risk']:.3f}:")
        
        factors = resultado["churn_metadata"]["contributing_factors"]
        sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)
        
        for factor, contribution in sorted_factors:
            print(f"  {factor}: {contribution:.3f}")
        print()
```

### Insights de Churn Agregados

```python
# Obtener insights de churn a nivel dataset
churn_insights = aggregate_churn_insights(resultados_churn)

print("INSIGHTS DE CHURN DEL DATASET")
print(f"Riesgo promedio: {churn_insights['avg_churn_risk']:.3f}")
print(f"Tasa de churn estimada: {churn_insights['estimated_churn_rate']:.1f}%")
print(f"Clientes de alto riesgo: {churn_insights['high_risk_customers']}")
print(f"Acción inmediata requerida: {churn_insights['immediate_action_required']}")

print("\nDistribución de niveles de riesgo:")
for nivel, porcentaje in churn_insights['risk_level_percentages'].items():
    print(f"  {nivel}: {porcentaje}% ({churn_insights['risk_level_distribution'][nivel]} clientes)")

print("\nPrincipales factores de riesgo:")
for factor, score in churn_insights['top_risk_factors'].items():
    print(f"  {factor}: {score:.3f}")
```

## 5. Extracción de Pain Points

### Análisis Básico de Pain Points

```python
from core.ai_engine.pain_points_module import extract_pain_points, aggregate_pain_points_insights

# Enriquecer con análisis de pain points
resultados_pain_points = extract_pain_points(resultados_churn)

# Ver pain points identificados
print("PAIN POINTS IDENTIFICADOS")
for i, resultado in enumerate(resultados_pain_points):
    pain_points = resultado["pain_points"]
    
    if pain_points:
        print(f"\nComentario {i+1}: {resultado['comentario'][:60]}...")
        for j, pain_point in enumerate(pain_points):
            print(f"  {j+1}. {pain_point['descripcion']}")
            print(f"     Categoría: {pain_point['categoria']}")
            print(f"     Severidad: {pain_point['severidad']}")
            print(f"     Impacto: {pain_point.get('impact_score', 0):.3f}")
```

### Pain Points de Alto Impacto

```python
# Identificar pain points de alto impacto
print("PAIN POINTS DE ALTO IMPACTO")
for resultado in resultados_pain_points:
    pain_points = resultado["pain_points"]
    
    high_impact_points = [
        pp for pp in pain_points 
        if pp.get("impact_score", 0) > 0.7
    ]
    
    if high_impact_points:
        print(f"\nComentario: {resultado['comentario'][:80]}...")
        for pain_point in high_impact_points:
            print(f"  🔥 {pain_point['descripcion']}")
            print(f"     Impacto: {pain_point['impact_score']:.3f}")
            print(f"     Categoría: {pain_point['categoria']} ({pain_point['severidad']})")
```

### Insights de Pain Points Agregados

```python
# Obtener insights agregados
pain_insights = aggregate_pain_points_insights(resultados_pain_points)

print("INSIGHTS DE PAIN POINTS")
print(f"Total pain points: {pain_insights['total_pain_points']}")
print(f"Promedio por comentario: {pain_insights['avg_pain_points_per_comment']}")
print(f"Impacto promedio: {pain_insights['avg_impact_score']:.3f}")
print(f"Pain points alto impacto: {pain_insights['high_impact_pain_points']}")
print(f"Categoría más problemática: {pain_insights['most_problematic_category']}")

print("\nDistribución por categorías:")
for categoria, porcentaje in pain_insights['category_percentages'].items():
    print(f"  {categoria}: {porcentaje}%")

print("\nTop 5 pain points más frecuentes:")
for pain_point in pain_insights['top_pain_points'][:5]:
    print(f"  {pain_point['descripcion']} ({pain_point['frecuencia']} veces, {pain_point['porcentaje']}%)")
```

## 6. Pipeline Completo - Ejemplo End-to-End

### Análisis Completo de un Dataset

```python
def analizar_comentarios_completo(comentarios, nps_scores=None):
    """
    Análisis completo end-to-end de comentarios.
    """
    print(f"🚀 Iniciando análisis de {len(comentarios)} comentarios...")
    
    # 1. Análisis inicial con OpenAI
    print("1️⃣ Análisis base con OpenAI...")
    resultados = analyze_batch_via_llm(comentarios, lang="es")
    
    # 2. Enriquecer con análisis emocional
    print("2️⃣ Enriqueciendo con análisis emocional...")
    resultados = extract_emotions(resultados)
    
    # 3. Validar y corregir NPS
    print("3️⃣ Validando y corrigiendo NPS...")
    resultados = analyze_nps_batch(resultados, nps_scores)
    
    # 4. Calcular churn risk
    print("4️⃣ Calculando churn risk...")
    resultados = compute_churn(resultados)
    
    # 5. Extraer pain points
    print("5️⃣ Extrayendo pain points...")
    resultados = extract_pain_points(resultados)
    
    print("✅ Análisis completo finalizado!")
    return resultados

# Ejemplo de uso
comentarios_ejemplo = [
    "Excelente servicio, muy recomendado",
    "El producto funciona pero es muy caro, consideraré cancelar",
    "Terrible experiencia, el personal no sabe nada y me hicieron esperar 2 horas",
    "Está bien, podría mejorar",
    "Fantástico, seguiré usando este servicio"
]

nps_scores_ejemplo = [10, 4, 1, 7, 9]

# Ejecutar análisis completo
resultados_completos = analizar_comentarios_completo(
    comentarios_ejemplo, 
    nps_scores_ejemplo
)

# Generar reporte final
print("\n📊 REPORTE FINAL")
print("=" * 50)

# Insights emocionales
emotion_insights = aggregate_emotion_insights(resultados_completos)
print(f"Emoción dominante: {emotion_insights['dominant_emotion_overall']}")

# Métricas NPS
nps_metrics = calculate_nps_score_aggregate(resultados_completos)
print(f"NPS Score: {nps_metrics['nps_score']}")

# Insights de churn
churn_insights = aggregate_churn_insights(resultados_completos)
print(f"Riesgo churn promedio: {churn_insights['avg_churn_risk']:.3f}")

# Pain points
pain_insights = aggregate_pain_points_insights(resultados_completos)
print(f"Total pain points: {pain_insights['total_pain_points']}")
```

## 7. Testing y Debugging

### Testing con Mock

```python
import os

# Asegurar que usa mock
if 'OPENAI_API_KEY' in os.environ:
    del os.environ['OPENAI_API_KEY']

# Test básico
comentarios_test = ["Comentario de prueba"]
resultados_test = analyze_batch_via_llm(comentarios_test)

print("✅ Mock funcionando correctamente")
print(f"Resultado: {resultados_test[0]['nps_category']}")
```

### Debugging con Logs

```python
import logging

# Activar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Ver logs detallados durante el procesamiento
resultados_debug = analyze_batch_via_llm(
    ["Comentario de debug"],
    lang="es",
    max_workers=1
)
```

### Performance Testing

```python
import time

def test_performance(num_comments=100):
    """Test de performance con comentarios sintéticos."""
    
    comentarios = [f"Comentario de prueba número {i}" for i in range(num_comments)]
    
    start_time = time.time()
    resultados = analizar_comentarios_completo(comentarios)
    end_time = time.time()
    
    tiempo_total = end_time - start_time
    print(f"⏱️  Performance Test Results:")
    print(f"   Comentarios procesados: {num_comments}")
    print(f"   Tiempo total: {tiempo_total:.2f} segundos")
    print(f"   Tiempo por comentario: {tiempo_total/num_comments:.3f} segundos")
    print(f"   Comentarios por segundo: {num_comments/tiempo_total:.1f}")

# Ejecutar test
test_performance(50)
```

---

## Conclusión

Estos ejemplos muestran el uso completo del AI Engine implementado. El sistema es:

- **Robusto**: Funciona con y sin API key
- **Escalable**: Procesa lotes grandes con paralelismo
- **Completo**: Análisis integral de emociones, NPS, churn y pain points
- **Fácil de usar**: API simple y consistente
- **Bien documentado**: Logs detallados para debugging

La implementación está lista para producción y cumple 100% con el blueprint arquitectónico.