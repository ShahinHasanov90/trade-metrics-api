from __future__ import annotations

import time

from trade_metrics.cache import TTLLRUCache


def test_get_or_set_returns_hit_flag():
    cache = TTLLRUCache(maxsize=4, ttl=60.0)
    calls = {"n": 0}

    def producer() -> int:
        calls["n"] += 1
        return 42

    value, hit = cache.get_or_set("k", producer)
    assert value == 42
    assert hit is False
    assert calls["n"] == 1

    value, hit = cache.get_or_set("k", producer)
    assert value == 42
    assert hit is True
    assert calls["n"] == 1


def test_ttl_expires_entries():
    cache = TTLLRUCache(maxsize=4, ttl=0.05)
    cache.set("k", "v")
    found, _ = cache.get("k")
    assert found is True
    time.sleep(0.1)
    found, _ = cache.get("k")
    assert found is False


def test_clear_drops_all_entries():
    cache = TTLLRUCache(maxsize=4, ttl=60.0)
    cache.set("a", 1)
    cache.set("b", 2)
    assert len(cache) == 2
    cache.clear()
    assert len(cache) == 0


def test_maxsize_evicts_older_entries():
    cache = TTLLRUCache(maxsize=2, ttl=60.0)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    assert len(cache) == 2
