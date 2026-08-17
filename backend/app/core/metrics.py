"""In-process request metrics for observability."""

from __future__ import annotations

import threading
from collections import defaultdict


class MetricsStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.requests_total = 0
        self.rate_limited_total = 0
        self.status_counts: dict[int, int] = defaultdict(int)

    def record_request(self, status_code: int) -> None:
        with self._lock:
            self.requests_total += 1
            self.status_counts[status_code] += 1

    def record_rate_limited(self) -> None:
        with self._lock:
            self.rate_limited_total += 1

    def prometheus_lines(self) -> list[str]:
        with self._lock:
            lines = [
                "# HELP commerce_requests_total Total HTTP requests handled",
                "# TYPE commerce_requests_total counter",
                f"commerce_requests_total {self.requests_total}",
                "# HELP commerce_rate_limited_total Total rate-limited requests",
                "# TYPE commerce_rate_limited_total counter",
                f"commerce_rate_limited_total {self.rate_limited_total}",
            ]
            for status, count in sorted(self.status_counts.items()):
                lines.append(f"commerce_http_responses_total{{status=\"{status}\"}} {count}")
            return lines


metrics_store = MetricsStore()
