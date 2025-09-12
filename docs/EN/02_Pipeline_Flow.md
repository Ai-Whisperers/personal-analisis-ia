# Pipeline Flow

1) Excel → `core/file_processor/reader.py`
2) Validate/clean/normalize
3) Batch split (≤100)
4) Parallel to LLM → `core/ai_engine/api_call.py`
5) Merge results → DataFrame
6) UI visualization/export

**SLA:** ≤10 s P50 (800–1200 rows)
