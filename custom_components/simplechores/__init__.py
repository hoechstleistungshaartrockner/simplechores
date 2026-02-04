# __init__.py
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .storage_manager import SimpleChoresStorageManager
from .coordinator import SimpleChoresCoordinator

async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up integration via YAML (not used)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up SimpleChores from a config entry."""
    storage = SimpleChoresStorageManager(hass)
    await storage.async_load()

    coordinator = SimpleChoresCoordinator(hass, storage)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "storage": storage,
        "coordinator": coordinator,
    }

    # Forward platforms later (sensor, button, etc.)
    # await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
