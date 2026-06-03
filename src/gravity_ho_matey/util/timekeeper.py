from __future__ import annotations

from dataclasses import dataclass
import time

from gravity_ho_matey.settings import MAX_DT


@dataclass(slots=True)
class TimeKeeper:
    last: float = 0.0

    def reset(self) -> None:
        self.last = time.perf_counter()

    def tick(self) -> float:
        now = time.perf_counter()
        if self.last <= 0:
            self.last = now
            return 0.0
        dt = min(now - self.last, MAX_DT)
        self.last = now
        return dt
