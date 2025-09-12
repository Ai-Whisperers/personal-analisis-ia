# Interfaz neutral de estado (placeholder). Mantener core libre de Streamlit.
class StateIface:
    def __init__(self):
        self._store = {}

    def set(self, k, v):
        self._store[k] = v

    def get(self, k, default=None):
        return self._store.get(k, default)
