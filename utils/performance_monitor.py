import time
from functools import wraps

def measure_time(timings: dict, key: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            out = func(*args, **kwargs)
            timings[key] = round((time.perf_counter() - t0)*1000, 1)  # ms
            return out
        return wrapper
    return decorator
