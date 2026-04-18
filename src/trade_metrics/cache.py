from __future__ import annotations

import threading
from typing import Any, Callable, Hashable

from cachetools import TTLCache


class TTLLRUCache:
    def __init__(self, maxsize: int = 256, ttl: float = 60.0) -> None:
        self._cache: TTLCache[Hashable, Any] = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = threading.RLock()

    def get(self, key: Hashable) -> tuple[bool, Any]:
        with self._lock:
            if key in self._cache:
                return True, self._cache[key]
            return False, None

    def set(self, key: Hashable, value: Any) -> None:
        with self._lock:
            self._cache[key] = value

    def get_or_set(self, key: Hashable, producer: Callable[[], Any]) -> tuple[Any, bool]:
        with self._lock:
            if key in self._cache:
                return self._cache[key], True
        value = producer()
        with self._lock:
            self._cache[key] = value
        return value, False

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)
