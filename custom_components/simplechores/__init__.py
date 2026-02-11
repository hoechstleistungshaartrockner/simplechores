# __init__.py
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_time_change

from .const import (
    DOMAIN, 
    CONF_MEMBERS, 
    PLATFORMS,
    DEVICE_MANUFACTURER, 
    DEVICE_MODEL_MEMBER,
    DEVICE_MODEL_CHORE,
    DEVICE_SW_VERSION,
    )
from .storage_manager import SimpleChoresStorageManager
from .coordinator import SimpleChoresCoordinator
from .member import Member
from . import services

async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up integration via YAML (not used)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up SimpleChores from a config entry."""
    
    storage = SimpleChoresStorageManager(hass)
    await storage.async_load()

    # If this is the very first run (storage file didn't exist), create members from config entry
    # We check if storage.data is empty (not just members) to distinguish first run from "all members deleted"
    if not storage.data.get("members") and not storage.data.get("chores") and CONF_MEMBERS in entry.data:
        member_names = entry.data[CONF_MEMBERS]
        for member_name in member_names:
            member = Member(name=member_name)
            storage.add_member(member)
        await storage.async_save()
    
    coordinator = SimpleChoresCoordinator(hass, storage)
    await coordinator.async_config_entry_first_refresh()

    # Register devices for each household member in storage
    device_reg = dr.async_get(hass)
    all_members = storage.get_members()
    
    for member_name in all_members:
        device_reg.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, f"member_{member_name}")},
            name=member_name,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL_MEMBER,
            sw_version=DEVICE_SW_VERSION,
        )
    
    # Register devices for each chore in storage
    all_chores = storage.get_chores()
    
    for chore_id, chore in all_chores.items():
        device = device_reg.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, f"chore_{chore_id}")},
            name=chore.name,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL_CHORE,
            sw_version=DEVICE_SW_VERSION,
        )
        
        # Assign to area if specified
        if chore.area_id:
            device_reg.async_update_device(device.id, area_id=chore.area_id)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "storage": storage,
        "coordinator": coordinator,
    }

    # Set up midnight timer to check for period resets
    async def _handle_midnight(now):
        """Handle midnight event to check period resets."""
        await coordinator.async_refresh_data()
    
    # Trigger at midnight every day
    unsub = async_track_time_change(
        hass,
        _handle_midnight,
        hour=0,
        minute=0,
        second=0,
    )
    hass.data[DOMAIN][entry.entry_id]["unsub_midnight"] = unsub

    # Set up services (only once for the integration)
    if len(hass.data[DOMAIN]) == 1:
        await services.async_setup_services(hass)

    # Forward sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Unsubscribe from midnight timer
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        if "unsub_midnight" in entry_data:
            entry_data["unsub_midnight"]()
        
        # Unload services if this was the last entry
        if not hass.data[DOMAIN]:
            await services.async_unload_services(hass)
    
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove a config entry and clean up storage."""
    # Remove the storage file when the integration is deleted
    storage = SimpleChoresStorageManager(hass)
    await storage.store.async_remove()
