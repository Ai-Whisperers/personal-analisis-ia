from typing import List, Dict

def map_nps_category(nota: float) -> str:
    try:
        n = float(nota)
    except Exception:
        return "Desconocido"
    if n <= 6:
        return "Detractor"
    if 7 <= n <= 8:
        return "Pasivo"
    if n >= 9:
        return "Promotor"
    return "Desconocido"
