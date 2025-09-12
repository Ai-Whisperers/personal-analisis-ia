"""
Módulo de validación de datos de entrada.
Valida estructura Excel, tipos de datos, rangos y consistencia de inputs.
"""

import re
import pandas as pd
import logging
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum
from config import MAX_COMMENT_LENGTH, VALIDATE_INPUT, SUPPORTED_LANGS

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Niveles de severidad de validaciones."""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationIssue:
    """Representa un problema de validación."""
    severity: ValidationSeverity
    category: str
    message: str
    row_index: Optional[int] = None
    column: Optional[str] = None
    value: Optional[Any] = None

@dataclass
class ValidationStats:
    """Estadísticas del proceso de validación."""
    total_rows: int
    valid_rows: int
    total_issues: int
    critical_issues: int
    error_issues: int
    warning_issues: int
    info_issues: int
    
# Configuración de columnas esperadas
EXPECTED_COLUMNS = {
    "required": ["comentario", "nps"],
    "optional": ["nota", "fecha", "cliente_id", "categoria", "canal"],
    "alias_mapping": {
        # Mapeo de nombres alternativos a nombres estándar
        "comment": "comentario",
        "comments": "comentario", 
        "comentarios": "comentario",
        "feedback": "comentario",
        "texto": "comentario",
        
        "nps_score": "nps",
        "score": "nps",
        "rating": "nps",
        "puntuacion": "nps",
        "calificacion": "nps",
        
        "note": "nota",
        "notes": "nota", 
        "observaciones": "nota",
        
        "date": "fecha",
        "timestamp": "fecha",
        "created_at": "fecha",
        
        "customer": "cliente_id",
        "user": "cliente_id",
        "client": "cliente_id",
        "usuario": "cliente_id",
        
        "category": "categoria",
        "type": "categoria",
        "tipo": "categoria",
        
        "channel": "canal",
        "source": "canal",
        "origen": "canal"
    }
}

# Validaciones de tipos de datos
DATA_TYPE_VALIDATIONS = {
    "comentario": {
        "type": str,
        "min_length": 1,
        "max_length": MAX_COMMENT_LENGTH,
        "allow_empty": False
    },
    "nps": {
        "type": [int, float],
        "min_value": 0,
        "max_value": 10,
        "allow_null": True
    },
    "nota": {
        "type": str,
        "min_length": 0,
        "max_length": 1000,
        "allow_empty": True
    },
    "fecha": {
        "type": [str, pd.Timestamp],
        "allow_null": True
    },
    "cliente_id": {
        "type": [str, int],
        "allow_null": True
    },
    "categoria": {
        "type": str,
        "allowed_values": ["producto", "servicio", "soporte", "ventas", "otros"],
        "allow_null": True
    },
    "canal": {
        "type": str,
        "allowed_values": ["web", "email", "telefono", "chat", "redes_sociales", "presencial"],
        "allow_null": True
    }
}

def normalize_column_names(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[ValidationIssue]]:
    """
    Normaliza nombres de columnas usando alias mapping.
    
    Args:
        df: DataFrame con columnas a normalizar
        
    Returns:
        Tupla (DataFrame normalizado, lista de issues)
    """
    issues = []
    df_normalized = df.copy()
    
    # Convertir nombres de columnas a lowercase para matching
    column_mapping = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        
        # Buscar en alias mapping
        if col_lower in EXPECTED_COLUMNS["alias_mapping"]:
            standard_name = EXPECTED_COLUMNS["alias_mapping"][col_lower]
            column_mapping[col] = standard_name
            
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="column_normalization",
                message=f"Columna '{col}' normalizada a '{standard_name}'",
                column=col
            ))
        elif col_lower in EXPECTED_COLUMNS["required"] + EXPECTED_COLUMNS["optional"]:
            # Ya está en formato estándar, pero puede tener diferente case
            if col != col_lower:
                column_mapping[col] = col_lower
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="column_case",
                    message=f"Columna '{col}' normalizada a lowercase: '{col_lower}'",
                    column=col
                ))
    
    # Aplicar renombrado
    if column_mapping:
        df_normalized = df_normalized.rename(columns=column_mapping)
    
    return df_normalized, issues

def validate_excel_structure(df: pd.DataFrame) -> List[ValidationIssue]:
    """
    Valida la estructura básica del DataFrame de Excel.
    
    Args:
        df: DataFrame a validar
        
    Returns:
        Lista de issues encontrados
    """
    issues = []
    
    # Validar que no esté vacío
    if df.empty:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.CRITICAL,
            category="structure",
            message="El archivo Excel está vacío"
        ))
        return issues
    
    # Validar columnas requeridas
    missing_required = []
    for col in EXPECTED_COLUMNS["required"]:
        if col not in df.columns:
            missing_required.append(col)
    
    if missing_required:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.CRITICAL,
            category="missing_columns",
            message=f"Columnas requeridas faltantes: {missing_required}"
        ))
    
    # Validar número de filas
    if len(df) > 10000:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            category="size",
            message=f"Archivo muy grande ({len(df)} filas). Puede afectar performance."
        ))
    elif len(df) < 5:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            category="size", 
            message=f"Archivo muy pequeño ({len(df)} filas). Resultados pueden no ser representativos."
        ))
    
    # Validar columnas desconocidas
    known_columns = EXPECTED_COLUMNS["required"] + EXPECTED_COLUMNS["optional"]
    unknown_columns = [col for col in df.columns if col not in known_columns]
    
    if unknown_columns:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.INFO,
            category="unknown_columns",
            message=f"Columnas no reconocidas (serán ignoradas): {unknown_columns}"
        ))
    
    return issues

def validate_single_value(value: Any, column: str, row_index: int, 
                         validation_config: Dict) -> List[ValidationIssue]:
    """
    Valida un valor individual según su configuración.
    
    Args:
        value: Valor a validar
        column: Nombre de la columna
        row_index: Índice de la fila
        validation_config: Configuración de validación
        
    Returns:
        Lista de issues encontrados
    """
    issues = []
    
    # Verificar nulos
    is_null = pd.isna(value) or value is None or (isinstance(value, str) and not value.strip())
    
    if is_null:
        if not validation_config.get("allow_null", False) and not validation_config.get("allow_empty", False):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="null_value",
                message=f"Valor nulo/vacío en columna requerida '{column}'",
                row_index=row_index,
                column=column,
                value=value
            ))
        return issues
    
    # Validar tipo
    expected_types = validation_config.get("type", [])
    if not isinstance(expected_types, list):
        expected_types = [expected_types]
    
    if expected_types and not any(isinstance(value, t) for t in expected_types):
        issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            category="data_type",
            message=f"Tipo incorrecto en '{column}': esperado {expected_types}, obtenido {type(value)}",
            row_index=row_index,
            column=column,
            value=value
        ))
        return issues  # No continuar validaciones si el tipo es incorrecto
    
    # Validaciones específicas por tipo
    if isinstance(value, str):
        # Longitud de string
        if "min_length" in validation_config and len(value) < validation_config["min_length"]:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="string_length",
                message=f"Texto muy corto en '{column}' (mín: {validation_config['min_length']})",
                row_index=row_index,
                column=column,
                value=f"'{value[:50]}...'" if len(str(value)) > 50 else value
            ))
        
        if "max_length" in validation_config and len(value) > validation_config["max_length"]:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="string_length",
                message=f"Texto muy largo en '{column}' (máx: {validation_config['max_length']})",
                row_index=row_index,
                column=column,
                value=f"'{value[:50]}...'" if len(str(value)) > 50 else value
            ))
        
        # Valores permitidos
        if "allowed_values" in validation_config:
            allowed = validation_config["allowed_values"]
            if value.lower() not in [v.lower() for v in allowed]:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="invalid_value",
                    message=f"Valor no reconocido en '{column}': '{value}'. Valores válidos: {allowed}",
                    row_index=row_index,
                    column=column,
                    value=value
                ))
    
    elif isinstance(value, (int, float)):
        # Rangos numéricos
        if "min_value" in validation_config and value < validation_config["min_value"]:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="numeric_range",
                message=f"Valor muy bajo en '{column}': {value} < {validation_config['min_value']}",
                row_index=row_index,
                column=column,
                value=value
            ))
        
        if "max_value" in validation_config and value > validation_config["max_value"]:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="numeric_range",
                message=f"Valor muy alto en '{column}': {value} > {validation_config['max_value']}",
                row_index=row_index,
                column=column,
                value=value
            ))
    
    return issues

def validate_business_rules(df: pd.DataFrame) -> List[ValidationIssue]:
    """
    Valida reglas de negocio específicas.
    
    Args:
        df: DataFrame a validar
        
    Returns:
        Lista de issues de reglas de negocio
    """
    issues = []
    
    if "comentario" not in df.columns or "nps" not in df.columns:
        return issues  # Ya validado en estructura
    
    # Regla: Comentarios muy negativos deberían tener NPS bajo
    for idx, row in df.iterrows():
        comment = str(row.get("comentario", "")).lower()
        nps = row.get("nps")
        
        if pd.notna(nps) and comment:
            # Detectar palabras muy negativas
            very_negative_words = [
                "terrible", "horrible", "pésimo", "desastroso", "inaceptable",
                "nunca más", "cancelar", "estafa", "fraude", "engaño"
            ]
            
            negative_count = sum(1 for word in very_negative_words if word in comment)
            
            # Si tiene palabras muy negativas pero NPS alto, es sospechoso
            if negative_count >= 2 and float(nps) >= 8:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="business_logic",
                    message=f"Inconsistencia: comentario muy negativo pero NPS alto ({nps})",
                    row_index=idx,
                    column="nps",
                    value=nps
                ))
            
            # Viceversa: comentarios muy positivos con NPS bajo
            very_positive_words = [
                "excelente", "fantástico", "perfecto", "increíble", "maravilloso",
                "recomiendo totalmente", "lo mejor", "cinco estrellas"
            ]
            
            positive_count = sum(1 for word in very_positive_words if word in comment)
            
            if positive_count >= 2 and float(nps) <= 3:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="business_logic",
                    message=f"Inconsistencia: comentario muy positivo pero NPS bajo ({nps})",
                    row_index=idx,
                    column="nps", 
                    value=nps
                ))
    
    # Regla: Detectar posibles duplicados de comentarios
    if "comentario" in df.columns:
        comments = df["comentario"].astype(str).str.lower().str.strip()
        duplicates = comments[comments.duplicated(keep=False)]
        
        if not duplicates.empty:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="duplicates",
                message=f"Se detectaron {len(duplicates)} comentarios posiblemente duplicados"
            ))
    
    return issues

def validate_data_quality(df: pd.DataFrame) -> List[ValidationIssue]:
    """
    Evalúa la calidad general de los datos.
    
    Args:
        df: DataFrame a analizar
        
    Returns:
        Lista de issues de calidad
    """
    issues = []
    
    # Calcular estadísticas de completitud
    for col in df.columns:
        if col in DATA_TYPE_VALIDATIONS:
            null_count = df[col].isna().sum()
            null_percentage = (null_count / len(df)) * 100
            
            if null_percentage > 50:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="data_quality",
                    message=f"Columna '{col}' tiene muchos valores nulos ({null_percentage:.1f}%)",
                    column=col
                ))
            elif null_percentage > 20:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="data_quality",
                    message=f"Columna '{col}' tiene algunos valores nulos ({null_percentage:.1f}%)",
                    column=col
                ))
    
    # Evaluar variabilidad de comentarios
    if "comentario" in df.columns:
        comments = df["comentario"].astype(str)
        avg_length = comments.str.len().mean()
        
        if avg_length < 10:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="data_quality",
                message=f"Comentarios muy cortos en promedio ({avg_length:.1f} caracteres)"
            ))
        elif avg_length > 1000:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="data_quality", 
                message=f"Comentarios muy largos en promedio ({avg_length:.1f} caracteres)"
            ))
    
    return issues

def validate_comments_batch(df: pd.DataFrame, strict_mode: bool = None) -> Tuple[pd.DataFrame, ValidationStats, List[ValidationIssue]]:
    """
    Valida un lote completo de comentarios en DataFrame.
    
    Args:
        df: DataFrame a validar
        strict_mode: Si usar modo estricto (None = usar config)
        
    Returns:
        Tupla (DataFrame limpio, estadísticas, lista de issues)
    """
    if strict_mode is None:
        strict_mode = VALIDATE_INPUT
    
    logger.info(f"Iniciando validación de DataFrame con {len(df) if not df.empty else 0} filas")
    
    all_issues = []
    
    # 1. Normalizar nombres de columnas
    df_clean, column_issues = normalize_column_names(df)
    all_issues.extend(column_issues)
    
    # 2. Validar estructura Excel
    structure_issues = validate_excel_structure(df_clean)
    all_issues.extend(structure_issues)
    
    # Si hay issues críticos, no continuar
    critical_issues = [i for i in all_issues if i.severity == ValidationSeverity.CRITICAL]
    if critical_issues:
        stats = ValidationStats(
            total_rows=len(df) if not df.empty else 0,
            valid_rows=0,
            total_issues=len(all_issues),
            critical_issues=len(critical_issues),
            error_issues=0,
            warning_issues=0,
            info_issues=0
        )
        return df_clean, stats, all_issues
    
    # 3. Validar cada celda individualmente
    valid_row_indices = []
    
    for idx, row in df_clean.iterrows():
        row_issues = []
        
        for col, validation_config in DATA_TYPE_VALIDATIONS.items():
            if col in df_clean.columns:
                cell_issues = validate_single_value(
                    row[col], col, idx, validation_config
                )
                row_issues.extend(cell_issues)
                all_issues.extend(cell_issues)
        
        # Decidir si la fila es válida
        row_errors = [i for i in row_issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]
        
        if not row_errors or not strict_mode:
            valid_row_indices.append(idx)
    
    # 4. Validar reglas de negocio
    business_issues = validate_business_rules(df_clean)
    all_issues.extend(business_issues)
    
    # 5. Evaluar calidad de datos
    quality_issues = validate_data_quality(df_clean)
    all_issues.extend(quality_issues)
    
    # Filtrar DataFrame solo con filas válidas en modo estricto
    if strict_mode and valid_row_indices:
        df_clean = df_clean.loc[valid_row_indices].reset_index(drop=True)
    
    # Calcular estadísticas
    stats = ValidationStats(
        total_rows=len(df),
        valid_rows=len(df_clean),
        total_issues=len(all_issues),
        critical_issues=len([i for i in all_issues if i.severity == ValidationSeverity.CRITICAL]),
        error_issues=len([i for i in all_issues if i.severity == ValidationSeverity.ERROR]),
        warning_issues=len([i for i in all_issues if i.severity == ValidationSeverity.WARNING]),
        info_issues=len([i for i in all_issues if i.severity == ValidationSeverity.INFO])
    )
    
    logger.info(f"Validación completada: {stats.valid_rows}/{stats.total_rows} filas válidas, "
               f"{stats.total_issues} issues encontrados")
    
    return df_clean, stats, all_issues

def get_validation_report(stats: ValidationStats, issues: List[ValidationIssue]) -> Dict[str, Any]:
    """
    Genera reporte detallado de validación.
    
    Args:
        stats: Estadísticas de validación
        issues: Lista de issues encontrados
        
    Returns:
        Diccionario con reporte completo
    """
    if stats.total_rows == 0:
        return {"error": "No data to validate"}
    
    # Agrupar issues por categoría
    issues_by_category = {}
    issues_by_severity = {}
    
    for issue in issues:
        category = issue.category
        severity = issue.severity.value
        
        if category not in issues_by_category:
            issues_by_category[category] = []
        issues_by_category[category].append(issue)
        
        if severity not in issues_by_severity:
            issues_by_severity[severity] = []
        issues_by_severity[severity].append(issue)
    
    return {
        "summary": {
            "total_rows": stats.total_rows,
            "valid_rows": stats.valid_rows,
            "validation_rate": round((stats.valid_rows / stats.total_rows) * 100, 2),
            "total_issues": stats.total_issues
        },
        "issues_by_severity": {
            "critical": stats.critical_issues,
            "error": stats.error_issues,
            "warning": stats.warning_issues,
            "info": stats.info_issues
        },
        "issues_by_category": {
            category: len(issue_list) 
            for category, issue_list in issues_by_category.items()
        },
        "data_quality_score": max(0, min(100, 
            100 - (stats.critical_issues * 25) - (stats.error_issues * 10) - (stats.warning_issues * 2)
        )),
        "recommendations": _generate_recommendations(stats, issues_by_category),
        "detailed_issues": [
            {
                "severity": issue.severity.value,
                "category": issue.category,
                "message": issue.message,
                "row": issue.row_index,
                "column": issue.column
            }
            for issue in issues[:50]  # Limitar a primeros 50 para no sobrecargar
        ]
    }

def _generate_recommendations(stats: ValidationStats, issues_by_category: Dict) -> List[str]:
    """Genera recomendaciones basadas en los issues encontrados."""
    recommendations = []
    
    if stats.critical_issues > 0:
        recommendations.append("❌ Corregir issues críticos antes de proceder con el análisis")
    
    if stats.error_issues > stats.total_rows * 0.1:
        recommendations.append("⚠️ Revisar y limpiar datos - muchos errores de validación")
    
    if "missing_columns" in issues_by_category:
        recommendations.append("📋 Verificar que el Excel tenga las columnas requeridas: comentario, nps")
    
    if "business_logic" in issues_by_category:
        recommendations.append("🔍 Revisar inconsistencias entre comentarios y puntuaciones NPS")
    
    if "data_quality" in issues_by_category:
        recommendations.append("💫 Considerar mejorar la calidad de datos para obtener mejores insights")
    
    if len(recommendations) == 0:
        recommendations.append("✅ Los datos están en buena condición para el análisis")
    
    return recommendations