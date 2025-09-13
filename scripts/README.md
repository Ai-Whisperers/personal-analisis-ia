# Scripts de Deployment y Mantenimiento

Scripts para manejo de caché, reinicio y deploy del Personal Comment Analyzer.

## Scripts Disponibles

### 🧹 `clean.sh` / `clean.bat`
**Limpia TODO el caché Python de TODOS los niveles**

```bash
# Linux/Mac
./scripts/clean.sh

# Windows  
scripts\clean.bat
```

**Elimina:**
- Todos los directorios `__pycache__/` 
- Todos los archivos `.pyc`
- Todos los archivos `.pyo` 
- Todos los archivos `.pyd`
- Cache de pytest (`.pytest_cache/`)
- Cache de mypy (`.mypy_cache/`)
- Coverage files (`.coverage`, `htmlcov/`)
- Cache de Streamlit relacionado

### 🔄 `restart.sh`
**Reinicio completo de la aplicación**

```bash
./scripts/restart.sh
```

**Proceso:**
1. Mata procesos Streamlit activos
2. Ejecuta limpieza completa de caché
3. Espera que procesos terminen
4. Testa imports críticos
5. Inicia Streamlit en http://localhost:8501

## Cuándo Usar

### Usar `clean.sh` cuando:
- Aparece "PerformanceMonitor object is not callable"
- Cambios en código no se reflejan
- Imports fallan después de refactoring
- Deploy muestra errores de caché

### Usar `restart.sh` cuando:
- Necesitas reinicio completo
- Después de cambios importantes al código
- Para deploy desde cero
- Cuando Streamlit se comporta raro

## Resolución de Problemas

### Error: "Permission denied"
```bash
chmod +x scripts/*.sh
```

### Error: Scripts no ejecutan en Windows
Usa las versiones `.bat` o ejecuta desde Git Bash.

### Error: "pkill command not found" 
En Windows usar Git Bash o WSL.

## Verificación Post-Limpieza

Después de ejecutar limpieza, verifica:

```bash
# Test crítico para PerformanceMonitor
python -c "
from utils.performance_monitor import monitor
with monitor('test'):
    print('✅ Monitor working')
"

# Test imports principales  
python -c "
from controller import PipelineController
print('✅ Controller working')
"
```

Si estos tests pasan, el deployment debería funcionar correctamente.