from dataclasses import dataclass, field
from typing import Dict

@dataclass
class ProgressTracker:
    timings: Dict[str, float] = field(default_factory=dict)

    def set(self, key: str, ms: float):
        self.timings[key] = ms
