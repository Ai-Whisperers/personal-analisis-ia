# Despliegue

## Configuración para Streamlit Cloud

### 1. **Archivos de Configuración**

El proyecto está configurado para deployment en Streamlit Cloud con la estructura actual:

```
├── streamlit_app.py          # ✅ Entry point correcto
├── requirements.txt          # ✅ Dependencias
├── .streamlit/
│   ├── config.toml          # ✅ Configuración Streamlit
│   └── secrets.toml         # 🔒 Solo local (no versionar)
└── config.py                # ✅ Manejo de secrets
```

### 2. **Variables de Entorno / Secrets**

#### Para Desarrollo Local (`.streamlit/secrets.toml`):
```toml
OPENAI_API_KEY = "sk-..."
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS_PER_CALL = "12000"
MAX_BATCH_SIZE = "100"
MAX_WORKERS = "12"
LOG_LEVEL = "INFO"
```

#### Para Streamlit Cloud:
Configurar en **Settings → Secrets** del dashboard:
```toml
OPENAI_API_KEY = "sk-..."
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS_PER_CALL = "12000"
MAX_BATCH_SIZE = "100"
MAX_WORKERS = "12"
LOG_LEVEL = "INFO"
```

### 3. **Deployment en Streamlit Cloud**

1. **Push a GitHub**:
   ```bash
   git add .
   git commit -m "feat: prepare for deployment"
   git push origin main
   ```

2. **Conectar Repositorio**:
   - Ir a [share.streamlit.io](https://share.streamlit.io)
   - "New app" → GitHub repo: `Ai-Whisperers/personal-analisis-ia`
   - Main file path: `streamlit_app.py`

3. **Configurar Secrets**:
   - Settings → Secrets
   - Copiar contenido del `.streamlit/secrets.toml` local

4. **Deploy Automático**:
   - Streamlit Cloud detecta cambios en `main`
   - Redeploy automático en cada push

### 4. **Modo Mock (Sin API Key)**

El sistema puede funcionar sin API key usando datos simulados:

```python
# En config.py
def is_mock_mode() -> bool:
    api_key = get_openai_api_key()
    return not api_key or api_key in ["", "mock", "test"]

# Si no hay API key, usa responses simuladas
if is_mock_mode():
    return mock_llm_response()
```

### 5. **Verificación Post-Deploy**

#### Checklist de Funcionalidad:
- [ ] Landing page carga correctamente
- [ ] Upload de Excel funciona
- [ ] Análisis ejecuta sin errores
- [ ] Charts se generan (16 emociones)
- [ ] Export funciona
- [ ] Performance ≤10s para archivos test

#### URLs de Testing:
- **App URL**: `https://personal-analisis-ia.streamlit.app/`
- **Landing**: Página principal
- **Subir**: `/2_Subir` - Upload y análisis

## Configuración Local

### Setup Inicial:
```bash
# Clone
git clone https://github.com/Ai-Whisperers/personal-analisis-ia
cd Comment-Analizer-Personal

# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Dependencies
pip install -r requirements.txt

# Secrets (crear manualmente)
mkdir .streamlit
echo 'OPENAI_API_KEY = "tu_key_aqui"' > .streamlit/secrets.toml
```

### Ejecutar Localmente:
```bash
streamlit run streamlit_app.py
```

Abrir: `http://localhost:8501`

## Troubleshooting

### Errores Comunes

#### 1. **Import Error al Deploy**
```
ModuleNotFoundError: No module named 'X'
```
**Solución**: Verificar `requirements.txt` actualizado

#### 2. **Secrets No Detectados**
```
KeyError: 'OPENAI_API_KEY'
```  
**Solución**: Verificar secrets en Streamlit Cloud dashboard

#### 3. **Memory Errors**
```
ResourceError: App exceeded memory limit
```
**Solución**: Reducir `MAX_BATCH_SIZE` y `MAX_WORKERS` en secrets

#### 4. **Timeout en Pipeline**
```
Timeout after 30s
```
**Solución**: Verificar API key válida o usar modo mock

### Logs y Debugging

#### En Streamlit Cloud:
- **Manage app** → **Logs** para ver output
- **Settings** → **Secrets** para verificar configuración

#### Localmente:
```bash
# Ver logs completos
streamlit run streamlit_app.py --logger.level debug

# Verificar configuración
python -c "from config import validate_config; validate_config()"
```

## Performance en Producción

### Configuración Recomendada:
```toml
# Para datasets pequeños (<500 rows)
MAX_BATCH_SIZE = "50"
MAX_WORKERS = "6"

# Para datasets medianos (500-1200 rows)  
MAX_BATCH_SIZE = "100"
MAX_WORKERS = "12"

# Para datasets grandes (>1200 rows)
MAX_BATCH_SIZE = "150"
MAX_WORKERS = "8"
```

### Monitoring:
- Pipeline debe completar en ≤10s para 800-1200 filas
- Memory usage debe mantenerse <1GB
- API calls exitosos >95%

### Optimizaciones:
1. **Cache Results**: `st.cache_data` para resultados previos
2. **Lazy Loading**: Solo cargar componentes cuando necesario  
3. **Progress Bars**: Feedback visual para usuarios
4. **Error Handling**: Fallbacks graceful a modo mock