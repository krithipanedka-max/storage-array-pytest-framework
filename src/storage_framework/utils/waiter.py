from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from storage_framework.core.exceptions import OperationTimeout

T = TypeVar("T")


def wait_until(fetch: Callable[[], T], predicate: Callable[[T], bool], timeout: float = 30, interval: float = 1) -> T:
    deadline = time.monotonic() + timeout
    last = fetch()
    while time.monotonic() < deadline:
        if predicate(last):
            return last
        time.sleep(interval)
        last = fetch()
    raise OperationTimeout(f"Condition not met within {timeout}s; last value={last!r}")
