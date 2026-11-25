"""Failed sign-in counting and temporary locks, keyed by email and by client address.

Counts live in this process's memory (like the memory-cache module). With several API instances each one counts on
its own, so a shared store is needed before the API is scaled out (recorded as a risk in WI-030's plan).
"""

import time
from collections.abc import Callable


class LoginLockout:
    def __init__(self, max_failures: int, lock_seconds: int, clock: Callable[[], float] = time.monotonic) -> None:
        self._max_failures = max_failures
        self._lock_seconds = lock_seconds
        self._clock = clock
        self._failures: dict[str, int] = {}
        self._locked_until: dict[str, float] = {}

    def is_locked(self, key: str) -> bool:
        until = self._locked_until.get(key)
        if until is None:
            return False
        if self._clock() < until:
            return True
        self._locked_until.pop(key, None)
        self._failures.pop(key, None)
        return False

    def record_failure(self, key: str) -> None:
        self._failures[key] = self._failures.get(key, 0) + 1
        if self._failures[key] >= self._max_failures:
            self._locked_until[key] = self._clock() + self._lock_seconds
            self._failures.pop(key, None)

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)
        self._locked_until.pop(key, None)
