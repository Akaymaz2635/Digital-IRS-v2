# utils/cache.py
from functools import lru_cache
from typing import Dict, Any


class DocumentCache:
    def __init__(self, max_size: int = 100):
        self._cache: Dict[str, Any] = {}
        self.max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        if len(self._cache) >= self.max_size:
            # LRU eviction logic
            pass
        self._cache[key] = value