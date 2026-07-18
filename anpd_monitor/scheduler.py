from __future__ import annotations

import time
from collections.abc import Callable
from datetime import timedelta


def run_weekly(task: Callable[[], None], interval: timedelta = timedelta(days=7)) -> None:
    while True:
        task()
        time.sleep(interval.total_seconds())

