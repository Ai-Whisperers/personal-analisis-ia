import pandas as pd

def read_excel(file) -> pd.DataFrame:
    # Lee excel con columnas exactas: NPS | Nota | Comentario Final
    df = pd.read_excel(file)
    return df
