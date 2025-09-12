from typing import Dict, Tuple
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.file_processor.reader import read_excel
from core.file_processor.cleaner import clean
from core.file_processor.validator import validate
from core.file_processor.normalizer import normalize

from core.ai_engine.api_call import analyze_batch_via_llm
from core.ai_engine.nps_module import map_nps_category

from utils.performance_monitor import measure_time

from config import EMOTIONS_16, MAX_BATCH_SIZE

def chunk(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]

def _make_empty_emotion_cols(df: pd.DataFrame) -> pd.DataFrame:
    for e in EMOTIONS_16:
        df[f"emo_{e}"] = 0.0
    return df

def _apply_results(df: pd.DataFrame, results: list) -> pd.DataFrame:
    # results: list of dicts aligned to comments order
    emo_keys = EMOTIONS_16
    out_rows = []
    for i, row in df.iterrows():
        res = results[i]
        emo = res.get("emociones", {})
        new_row = row.to_dict()
        for e in emo_keys:
            new_row[f"emo_{e}"] = float(emo.get(e, 0.0))
        new_row["pain_points"] = ", ".join(res.get("pain_points", [])[:5])
        new_row["churn_risk"] = float(res.get("churn_risk", 0.0))
        # Validar/combinar NPS
        new_row["NPS_category"] = new_row.get("NPS_category") or map_nps_category(new_row.get("Nota", 0))
        out_rows.append(new_row)
    return pd.DataFrame(out_rows)

def run_analysis(file, progress_cb=None) -> Tuple[pd.DataFrame, Dict]:
    timings: Dict = {}

    @measure_time(timings, "01_read_ms")
    def _read():
        return read_excel(file)

    @measure_time(timings, "02_validate_ms")
    def _validate(df):
        validate(df)
        return df

    @measure_time(timings, "03_clean_norm_ms")
    def _clean_norm(df):
        return normalize(clean(df))

    @measure_time(timings, "04_batch_ms")
    def _batch(df):
        comments = df["Comentario Final"].astype(str).tolist()
        batches = list(chunk(comments, MAX_BATCH_SIZE))
        return df, batches

    @measure_time(timings, "05_llm_parallel_ms")
    def _llm(batches):
        results_all = []
        with ThreadPoolExecutor(max_workers=min(12, max(1, len(batches)))) as ex:
            futs = {ex.submit(analyze_batch_via_llm, b): idx for idx, b in enumerate(batches)}
            total = len(futs)
            done_ct = 0
            for fut in as_completed(futs):
                res = fut.result()
                results_all.extend(res)
                done_ct += 1
                if progress_cb:
                    progress_cb(int(done_ct/total*90))  # 90% hasta aquí
        return results_all

    @measure_time(timings, "06_merge_ms")
    def _merge(df, results):
        if progress_cb: progress_cb(95)
        # preparar columnas
        df = _make_empty_emotion_cols(df)
        df["pain_points"] = ""
        df["churn_risk"] = 0.0
        df["NPS_category"] = df["Nota"].apply(map_nps_category)
        merged = _apply_results(df, results)
        if progress_cb: progress_cb(100)
        return merged

    df = _read()
    df = _validate(df)
    df = _clean_norm(df)
    df, batches = _batch(df)
    results = _llm(batches)
    final_df = _merge(df, results)

    return final_df, timings
