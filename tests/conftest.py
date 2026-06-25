"""Pytest configuration for loading integration helper modules."""

from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]


def _ensure_module(name: str) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return module


homeassistant = _ensure_module("homeassistant")
ha_const = _ensure_module("homeassistant.const")
ha_const.__version__ = "test"
ha_helpers = _ensure_module("homeassistant.helpers")
ha_cv = _ensure_module("homeassistant.helpers.config_validation")


def ensure_list_csv(value):
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    return [item.strip() for item in str(value).split(",")]


ha_cv.ensure_list_csv = ensure_list_csv
ha_helpers.config_validation = ha_cv
homeassistant.const = ha_const
homeassistant.helpers = ha_helpers

custom_components = _ensure_module("custom_components")
custom_components.__path__ = [str(ROOT / "custom_components")]
telegram_client = _ensure_module("custom_components.telegram_client")
telegram_client.__path__ = [str(ROOT / "custom_components" / "telegram_client")]
