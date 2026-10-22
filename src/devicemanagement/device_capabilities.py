"""Small device capability checks based on Apple's product identifiers."""

_DYNAMIC_ISLAND_MODELS = frozenset({
    "iPhone15,2", "iPhone15,3", "iPhone15,4", "iPhone15,5",
    "iPhone16,1", "iPhone16,2",
    "iPhone17,1", "iPhone17,2", "iPhone17,3", "iPhone17,4",
    "iPhone18,1", "iPhone18,2", "iPhone18,3", "iPhone18,4",
})


def has_dynamic_island(model: str) -> bool:
    """Return whether a known iPhone product type has Dynamic Island hardware."""
    return str(model or "").strip() in _DYNAMIC_ISLAND_MODELS
