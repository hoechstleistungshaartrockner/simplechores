# coordinator.py
from __future__ import annotations

from datetime import timedelta
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN, 
    LOGGER
    )

class SimpleChoresCoordinator(DataUpdateCoordinator):
    """Coordinator for SimpleChores."""

    def __init__(self, hass, storage_manager):
        super().__init__(
            hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),  # adjust later
        )

        self.storage = storage_manager
        self.data = None  # will hold chores + members

    async def _async_update_data(self):
        """Fetch latest data. For now, just return storage."""
        try:
            # later: compute overdue, next due, assignments, etc.
            return self.storage.data
        except Exception as err:
            raise UpdateFailed(f"Error updating SimpleChores: {err}")
