"""
Validador de seguridad y anti-hardcode.
Detecta valores hardcodeados, secrets expuestos y malas prácticas de seguridad.
"""

import os
import re
import ast
import logging
from typing import List, Dict, Set, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class SecuritySeverity(Enum):
    """Niveles de severidad de issues de seguridad."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityIssue:
    """Representa un issue de seguridad detectado."""
    severity: SecuritySeverity
    category: str
    message: str
    file_path: str
    line_number: int
    line_content: str
    suggestion: str = ""

# Patrones de detección de secrets y valores sensibles
SECRET_PATTERNS = [
    # API Keys
    (r'sk-[a-zA-Z0-9]{48,}', "OpenAI API Key", SecuritySeverity.CRITICAL),
    (r'[a-zA-Z0-9]{32,}', "Possible API Key", SecuritySeverity.HIGH),
    
    # Tokens y Passwords
    (r'token["\s]*[:=]["\s]*[a-zA-Z0-9]{20,}', "Hardcoded Token", SecuritySeverity.CRITICAL),
    (r'password["\s]*[:=]["\s]*[^\s"\']{6,}', "Hardcoded Password", SecuritySeverity.CRITICAL),
    (r'secret["\s]*[:=]["\s]*[a-zA-Z0-9]{10,}', "Hardcoded Secret", SecuritySeverity.CRITICAL),
    
    # Conexiones de DB
    (r'mongodb://[^"\s]+', "MongoDB Connection String", SecuritySeverity.HIGH),
    (r'postgres://[^"\s]+', "PostgreSQL Connection String", SecuritySeverity.HIGH),
    (r'mysql://[^"\s]+', "MySQL Connection String", SecuritySeverity.HIGH),
    
    # URLs con credenciales
    (r'https?://[^/\s:]+:[^/\s@]+@[^/\s]+', "URL with embedded credentials", SecuritySeverity.HIGH),
]

# Patrones de hardcoding detectables
HARDCODE_PATTERNS = [
    # Números mágicos comunes
    (r'\b(100|1000|10000|50|25|12|16)\b(?!\s*[+\-*/])', "Magic Number", SecuritySeverity.LOW),
    
    # Strings hardcodeados sospechosos
    (r'"[a-z]{2,}-[a-z0-9-]{10,}"', "Possible Hardcoded Identifier", SecuritySeverity.MEDIUM),
    (r"'[A-Z_]{5,}'", "Possible Hardcoded Constant", SecuritySeverity.LOW),
    
    # URLs hardcodeadas
    (r'https?://[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}[^\s"\']*', "Hardcoded URL", SecuritySeverity.MEDIUM),
    
    # Paths absolutos
    (r'["\']/?([a-zA-Z]:/|/[a-zA-Z])[^"\']*["\']', "Hardcoded Path", SecuritySeverity.MEDIUM),
]

# Archivos a excluir del análisis
EXCLUDED_FILES = {
    '.git', '__pycache__', '.pytest_cache', 'node_modules',
    '.env', '.env.template', 'requirements.txt', '.gitignore',
    'README.md', 'LICENSE', '.md', 'local-reports',
    'security_validator.py'  # Excluir el propio validador
}

# Patrones permitidos (no son hardcode problemático)
ALLOWED_PATTERNS = [
    # Configuraciones estándar
    r'utf-8', r'localhost', r'127\.0\.0\.1', r'0\.0\.0\.0',
    
    # Formatos estándar
    r'%Y-%m-%d', r'%H:%M:%S', r'application/json',
    
    # Constantes matemáticas/técnicas comunes
    r'\b(0|1|2|3|4|5|10|12|16|20|24|25|30|50|60|100|120|365|480|600|1000|1024|2000|3000|3600|10000|12000)\b',
    
    # Rangos y porcentajes comunes
    r'\b(0\.[0-9]+|[0-9]+\.[0-9]+)\b',
    
    # Extensiones de archivo
    r'\.(py|js|html|css|md|txt|json|yml|yaml|log)$',
    
    # Patterns de código común
    r'["\'][a-z_]{2,}["\']', r'[a-z]+_[a-z]+', r'[A-Z_]{2,}',
    
    # URLs de documentación y ejemplos
    r'https://docs\.|https://example\.|https://github\.com',
    
    # Emociones (específico de nuestro proyecto)
    r'alegria|tristeza|enojo|miedo|confianza|desagrado|sorpresa|expectativa|frustracion|gratitud|aprecio|indiferencia|decepcion|entusiasmo|verguenza|esperanza',
]

def is_allowed_pattern(content: str) -> bool:
    """
    Verifica si el contenido coincide con patrones permitidos.
    
    Args:
        content: Contenido a verificar
        
    Returns:
        True si es un patrón permitido
    """
    for pattern in ALLOWED_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False

def extract_strings_from_python(file_path: str) -> List[Tuple[str, int, str]]:
    """
    Extrae strings literales de archivos Python usando AST.
    
    Args:
        file_path: Ruta del archivo Python
        
    Returns:
        Lista de tuplas (string_value, line_number, context)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parsear AST
        tree = ast.parse(content)
        strings = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Str):  # Python < 3.8
                strings.append((node.s, node.lineno, content.split('\n')[node.lineno - 1].strip()))
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):  # Python >= 3.8
                strings.append((node.value, node.lineno, content.split('\n')[node.lineno - 1].strip()))
        
        return strings
        
    except Exception as e:
        logger.warning(f"Error parsing {file_path}: {e}")
        return []

def scan_file_for_secrets(file_path: str) -> List[SecurityIssue]:
    """
    Escanea un archivo en busca de secrets y valores hardcodeados.
    
    Args:
        file_path: Ruta del archivo a escanear
        
    Returns:
        Lista de issues encontrados
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line_clean = line.strip()
            
            # Skip comentarios y líneas vacías
            if not line_clean or line_clean.startswith('#'):
                continue
            
            # Buscar patterns de secrets
            for pattern, description, severity in SECRET_PATTERNS:
                if re.search(pattern, line_clean, re.IGNORECASE):
                    if not is_allowed_pattern(line_clean):
                        issues.append(SecurityIssue(
                            severity=severity,
                            category="secret_detection",
                            message=f"{description} detectada",
                            file_path=file_path,
                            line_number=line_num,
                            line_content=line_clean,
                            suggestion="Mover a variable de entorno (.env)"
                        ))
            
            # Buscar patterns de hardcode
            for pattern, description, severity in HARDCODE_PATTERNS:
                matches = re.finditer(pattern, line_clean)
                for match in matches:
                    matched_text = match.group()
                    if not is_allowed_pattern(matched_text):
                        issues.append(SecurityIssue(
                            severity=severity,
                            category="hardcode_detection",
                            message=f"{description}: {matched_text}",
                            file_path=file_path,
                            line_number=line_num,
                            line_content=line_clean,
                            suggestion="Considerar usar variable de configuración"
                        ))
        
    except Exception as e:
        logger.error(f"Error escaneando {file_path}: {e}")
    
    return issues

def scan_python_file_ast(file_path: str) -> List[SecurityIssue]:
    """
    Escanea archivo Python usando AST para detectar hardcode más sofisticado.
    
    Args:
        file_path: Ruta del archivo Python
        
    Returns:
        Lista de issues encontrados
    """
    issues = []
    
    # Extraer strings del AST
    strings = extract_strings_from_python(file_path)
    
    for string_value, line_num, context in strings:
        # Skip strings muy cortos o muy comunes
        if len(string_value) < 3 or string_value in ['', ' ', '\n', '\t']:
            continue
        
        # Detectar posibles configuraciones hardcodeadas
        if re.match(r'^[A-Z][A-Z0-9_]{3,}$', string_value):
            issues.append(SecurityIssue(
                severity=SecuritySeverity.LOW,
                category="config_hardcode",
                message=f"Posible configuración hardcodeada: {string_value}",
                file_path=file_path,
                line_number=line_num,
                line_content=context,
                suggestion="Considerar mover a config.py o .env"
            ))
        
        # Detectar URLs hardcodeadas
        if string_value.startswith(('http://', 'https://')):
            issues.append(SecurityIssue(
                severity=SecuritySeverity.MEDIUM,
                category="url_hardcode",
                message=f"URL hardcodeada: {string_value}",
                file_path=file_path,
                line_number=line_num,
                line_content=context,
                suggestion="Mover URL a variable de entorno"
            ))
        
        # Detectar paths absolutos
        if (string_value.startswith('/') or 
            (len(string_value) > 3 and string_value[1:3] == ':\\')):
            issues.append(SecurityIssue(
                severity=SecuritySeverity.MEDIUM,
                category="path_hardcode",
                message=f"Path absoluto hardcodeado: {string_value}",
                file_path=file_path,
                line_number=line_num,
                line_content=context,
                suggestion="Usar rutas relativas o variables de entorno"
            ))
    
    return issues

def should_skip_file(file_path: str) -> bool:
    """
    Determina si un archivo debe ser omitido del escaneo.
    
    Args:
        file_path: Ruta del archivo
        
    Returns:
        True si debe ser omitido
    """
    path_parts = Path(file_path).parts
    
    # Skip archivos en directorios excluidos
    for part in path_parts:
        if part in EXCLUDED_FILES:
            return True
    
    # Skip por extensión
    extension = Path(file_path).suffix
    if extension in ['.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin']:
        return True
    
    # Skip archivos muy grandes (> 1MB)
    try:
        if os.path.getsize(file_path) > 1024 * 1024:
            return True
    except OSError:
        return True
    
    return False

def scan_directory(directory: str) -> List[SecurityIssue]:
    """
    Escanea un directorio completo en busca de issues de seguridad.
    
    Args:
        directory: Directorio a escanear
        
    Returns:
        Lista de todos los issues encontrados
    """
    all_issues = []
    
    logger.info(f"Iniciando escaneo de seguridad en: {directory}")
    
    for root, dirs, files in os.walk(directory):
        # Skip directorios excluidos
        dirs[:] = [d for d in dirs if d not in EXCLUDED_FILES]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            if should_skip_file(file_path):
                continue
            
            # Escaneo básico para todos los archivos
            issues = scan_file_for_secrets(file_path)
            all_issues.extend(issues)
            
            # Escaneo AST para archivos Python
            if file.endswith('.py'):
                ast_issues = scan_python_file_ast(file_path)
                all_issues.extend(ast_issues)
    
    logger.info(f"Escaneo completado. {len(all_issues)} issues encontrados")
    return all_issues

def validate_env_file(env_path: str) -> List[SecurityIssue]:
    """
    Valida que el archivo .env tenga configuración segura.
    
    Args:
        env_path: Ruta al archivo .env
        
    Returns:
        Lista de issues de configuración
    """
    issues = []
    
    if not os.path.exists(env_path):
        issues.append(SecurityIssue(
            severity=SecuritySeverity.MEDIUM,
            category="configuration",
            message="Archivo .env no encontrado",
            file_path=env_path,
            line_number=0,
            line_content="",
            suggestion="Crear .env basado en .env.template"
        ))
        return issues
    
    try:
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        required_vars = ['MODEL_NAME', 'MAX_BATCH_SIZE', 'SUPPORTED_LANGS']
        found_vars = set()
        
        for line_num, line in enumerate(lines, 1):
            if '=' in line and not line.strip().startswith('#'):
                var_name = line.split('=')[0].strip()
                var_value = line.split('=', 1)[1].strip()
                found_vars.add(var_name)
                
                # Validar que no haya secrets en el valor
                if len(var_value) > 50 and re.match(r'^[a-zA-Z0-9+/=]+$', var_value):
                    issues.append(SecurityIssue(
                        severity=SecuritySeverity.HIGH,
                        category="env_validation",
                        message=f"Posible secret en variable {var_name}",
                        file_path=env_path,
                        line_number=line_num,
                        line_content=line.strip(),
                        suggestion="Verificar que sea el valor correcto"
                    ))
        
        # Verificar variables requeridas
        missing_vars = [var for var in required_vars if var not in found_vars]
        if missing_vars:
            issues.append(SecurityIssue(
                severity=SecuritySeverity.LOW,
                category="configuration",
                message=f"Variables de entorno faltantes: {missing_vars}",
                file_path=env_path,
                line_number=0,
                line_content="",
                suggestion="Agregar variables faltantes basándose en .env.template"
            ))
    
    except Exception as e:
        logger.error(f"Error validando .env: {e}")
    
    return issues

def generate_security_report(issues: List[SecurityIssue]) -> Dict[str, Any]:
    """
    Genera reporte de seguridad detallado.
    
    Args:
        issues: Lista de issues encontrados
        
    Returns:
        Diccionario con reporte completo
    """
    if not issues:
        return {
            "status": "PASS",
            "summary": "✅ No se encontraron issues de seguridad",
            "total_issues": 0,
            "by_severity": {},
            "by_category": {},
            "recommendations": ["Continuar con buenas prácticas de seguridad"]
        }
    
    # Agrupar por severidad y categoría
    by_severity = {}
    by_category = {}
    
    for issue in issues:
        severity = issue.severity.value
        category = issue.category
        
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1
    
    # Determinar status general
    status = "PASS"
    if by_severity.get("critical", 0) > 0:
        status = "CRITICAL"
    elif by_severity.get("high", 0) > 0:
        status = "HIGH"
    elif by_severity.get("medium", 0) > 0:
        status = "MEDIUM"
    
    # Generar recomendaciones
    recommendations = []
    if by_severity.get("critical", 0) > 0:
        recommendations.append("🚨 CRÍTICO: Remover secrets hardcodeados inmediatamente")
    if by_severity.get("high", 0) > 0:
        recommendations.append("⚠️ ALTO: Mover configuraciones sensibles a variables de entorno")
    if by_category.get("hardcode_detection", 0) > 5:
        recommendations.append("🔧 Considerar refactorizar para reducir hardcoding")
    if by_category.get("config_hardcode", 0) > 0:
        recommendations.append("⚙️ Centralizar configuración en config.py y .env")
    
    return {
        "status": status,
        "total_issues": len(issues),
        "by_severity": by_severity,
        "by_category": by_category,
        "recommendations": recommendations,
        "critical_files": list(set(issue.file_path for issue in issues 
                                  if issue.severity == SecuritySeverity.CRITICAL)),
        "summary": f"Encontrados {len(issues)} issues de seguridad. Status: {status}",
        "detailed_issues": [
            {
                "severity": issue.severity.value,
                "category": issue.category,
                "message": issue.message,
                "file": issue.file_path,
                "line": issue.line_number,
                "suggestion": issue.suggestion
            }
            for issue in sorted(issues, key=lambda x: (x.severity.value, x.file_path, x.line_number))[:20]
        ]
    }

def run_security_scan(project_root: str = ".") -> Dict[str, Any]:
    """
    Ejecuta escaneo completo de seguridad del proyecto.
    
    Args:
        project_root: Directorio raíz del proyecto
        
    Returns:
        Reporte completo de seguridad
    """
    logger.info("Iniciando escaneo completo de seguridad")
    
    # Escanear directorio completo
    all_issues = scan_directory(project_root)
    
    # Validar .env específicamente
    env_path = os.path.join(project_root, '.env')
    env_issues = validate_env_file(env_path)
    all_issues.extend(env_issues)
    
    # Generar reporte
    report = generate_security_report(all_issues)
    
    # Agregar información del escaneo
    report["scan_info"] = {
        "project_root": os.path.abspath(project_root),
        "files_scanned": len([f for root, dirs, files in os.walk(project_root) 
                             for f in files if not should_skip_file(os.path.join(root, f))]),
        "scan_timestamp": __import__('datetime').datetime.now().isoformat()
    }
    
    logger.info(f"Escaneo de seguridad completado: {report['status']}")
    return report