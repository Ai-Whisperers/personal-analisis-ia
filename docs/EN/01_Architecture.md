# Architecture

- `pages/`: UI (no business logic)
- `static/`: CSS & assets
- `core/`: pure logic (parsing, batching, LLM, postprocess)
- `components/`: UI integration (uploader, charts, export)
- `utils/`: helpers (timings, logging)
- `docs/`: bilingual docs
- `local-reports/`: local artifacts (gitignored)

**Anti-overengineering**
- ≤480 lines per file, no import cycles.
- UI non-blocking; parallel via ThreadPoolExecutor.
- `@st.cache_*` only at UI layer (not in `core/`).

**Entry point**
- `main.py` (renameable). Run with `streamlit run main.py`.
