"""Small device capability checks based on Apple's product identifiers."""

_DYNAMIC_ISLAND_MODELS = frozenset({
    "iPhone15,2", "iPhone15,3", "iPhone15,4", "iPhone15,5",
    "iPhone16,1", "iPhone16,2",
    "iPhone17,1", "iPhone17,2", "iPhone17,3", "iPhone17,4",
    "iPhone18,1", "iPhone18,2", "iPhone18,3", "iPhone18,4",
})

_CAMERA_CONTROL_MODELS = frozenset({
    "iPhone17,1", "iPhone17,2", "iPhone17,3", "iPhone17,4",
    "iPhone18,1", "iPhone18,2", "iPhone18,3", "iPhone18,4",
})

_ACTION_BUTTON_MODELS = frozenset({
    "iPhone17,1", "iPhone17,2", "iPhone17,3", "iPhone17,4",
    "iPhone18,1", "iPhone18,2", "iPhone18,3", "iPhone18,4",
})

_HOME_BUTTON_MODELS = frozenset({
    "iPhone8,1", "iPhone8,2", "iPhone8,4", "iPhone9,1", "iPhone9,2",
    "iPhone9,3", "iPhone9,4", "iPhone10,1", "iPhone10,2",
    "iPhone10,3", "iPhone10,4", "iPhone10,5", "iPhone10,6",
    "iPhone11,8", "iPhone12,8", "iPhone13,1", "iPhone13,2",
    "iPhone13,3", "iPhone13,4", "iPhone14,1", "iPhone14,2",
    "iPhone14,3", "iPhone14,4", "iPhone14,5", "iPhone14,6",
    "iPhone14,7", "iPhone14,8",
})

_ALWAYS_ON_DISPLAY_MODELS = frozenset({
    "iPhone15,2", "iPhone15,3", "iPhone15,4", "iPhone15,5",
    "iPhone16,1", "iPhone16,2",
    "iPhone17,1", "iPhone17,2", "iPhone17,3", "iPhone17,4",
    "iPhone18,1", "iPhone18,2", "iPhone18,3", "iPhone18,4",
})


def has_dynamic_island(model: str) -> bool:
    """Return whether a known iPhone product type has Dynamic Island hardware."""
    return str(model or "").strip() in _DYNAMIC_ISLAND_MODELS


def has_camera_control(model: str) -> bool:
    """Return whether a known iPhone product type has Camera Control button."""
    return str(model or "").strip() in _CAMERA_CONTROL_MODELS


def has_action_button(model: str) -> bool:
    """Return whether a known iPhone product type has Action Button."""
    return str(model or "").strip() in _ACTION_BUTTON_MODELS


def has_home_button(model: str) -> bool:
    """Return whether a known iPhone product type has a physical Home button."""
    return str(model or "").strip() in _HOME_BUTTON_MODELS


def has_always_on_display(model: str) -> bool:
    """Return whether a known iPhone product type has Always-On Display."""
    return str(model or "").strip() in _ALWAYS_ON_DISPLAY_MODELS


def device_text(model: str) -> str:
    """Return a human-readable device name for a product identifier."""
    # Simplified mapping for common models
    model_map = {
        "iPhone15,2": "iPhone 15 Pro",
        "iPhone15,3": "iPhone 15 Pro Max",
        "iPhone15,4": "iPhone 15",
        "iPhone15,5": "iPhone 15 Plus",
        "iPhone16,1": "iPhone 16 Pro",
        "iPhone16,2": "iPhone 16 Pro Max",
        "iPhone16,3": "iPhone 16",
        "iPhone16,4": "iPhone 16 Plus",
        "iPhone17,1": "iPhone 17 Pro",
        "iPhone17,2": "iPhone 17 Pro Max",
        "iPhone17,3": "iPhone 17",
        "iPhone17,4": "iPhone 17 Plus",
        "iPhone18,1": "iPhone 18 Pro",
        "iPhone18,2": "iPhone 18 Pro Max",
        "iPhone18,3": "iPhone 18",
        "iPhone18,4": "iPhone 18 Plus",
    }
    return model_map.get(model, model)


def device_os_name(model: str) -> str:
    """Return the iOS version name for a product identifier."""
    # Simplified - would need actual iOS version detection
    return "iOS"
