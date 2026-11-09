"""Oddiy metrikalar: hisoblagichlar va javob vaqti (L14)."""
import threading
import time
from collections import defaultdict
from contextlib import contextmanager


class Metrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.started = time.time()
        self.counters = defaultdict(int)
        self._timings = defaultdict(lambda: [0, 0.0, 0.0])  # soni, jami, max

    def incr(self, name: str, value: int = 1) -> None:
        with self._lock:
            self.counters[name] += value

    def observe(self, name: str, seconds: float) -> None:
        with self._lock:
            t = self._timings[name]
            t[0] += 1
            t[1] += seconds
            t[2] = max(t[2], seconds)

    @contextmanager
    def timer(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            self.observe(name, time.perf_counter() - start)

    def report(self) -> str:
        with self._lock:
            up = int(time.time() - self.started)
            lines = [f"⏱ Ishlash vaqti: {up // 3600} soat {up % 3600 // 60} daq {up % 60} son"]
            lines.append("\nSanagichlar:")
            for k in sorted(self.counters):
                lines.append(f"  {k}: {self.counters[k]}")
            lines.append("\nJavob vaqti (ms):")
            for k in sorted(self._timings):
                c, total, mx = self._timings[k]
                lines.append(f"  {k}: o'rtacha {total / c * 1000:.1f}, max {mx * 1000:.1f}, soni {c}")
        return "\n".join(lines)
