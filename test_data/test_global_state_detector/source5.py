_in_memory_cache = {}


def target(key: str, value: any):
    print(f"CACHE: Adding item '{key}' to cache.")
    _in_memory_cache[key] = value
