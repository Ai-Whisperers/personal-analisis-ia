import pandas as pd

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    # Placeholder: normalizaciones ligeras
    df = df.copy()
    df["Comentario Final"] = df["Comentario Final"].astype(str)
    return df
