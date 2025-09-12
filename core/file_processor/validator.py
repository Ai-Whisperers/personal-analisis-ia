import pandas as pd

REQUIRED_COLS = ["NPS", "Nota", "Comentario Final"]

def validate(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}. Se esperaba {REQUIRED_COLS}")
