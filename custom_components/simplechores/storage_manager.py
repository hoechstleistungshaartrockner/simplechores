# storage_manager.py
from __future__ import annotations

from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_VERSION

class SimpleChoresStorageManager:
    """Handle persistent storage for SimpleChores."""

    def __init__(self, hass):
        self.hass = hass
        self.store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.storage")
        self.data = {
            "chores": {},
            "members": {},
        }

    async def async_load(self):
        """Load stored data from disk."""
        stored = await self.store.async_load()
        if stored:
            self.data = stored

    async def async_save(self):
        """Persist current data to disk."""
        await self.store.async_save(self.data)

    # convenience helpers for later
    def get_chores(self):
        return self.data.get("chores", {})

    def get_members(self):
        return self.data.get("members", {})
