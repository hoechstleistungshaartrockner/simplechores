# __init__.py
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, CONF_MEMBERS, PLATFORMS
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

    # Register devices for each household member
    device_reg = dr.async_get(hass)
    member_names = entry.data.get(CONF_MEMBERS, [])
    
    for member_name in member_names:
        device_reg.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, f"member_{member_name}")},
            name=member_name,
            manufacturer="SimpleChores",
            model="Household Member",
            sw_version="1.0.0",
        )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "storage": storage,
        "coordinator": coordinator,
    }

    # Forward sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
