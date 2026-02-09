"""Number platform for SimpleChores."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN,
    CONF_POINTS_LABEL,
    DEFAULT_POINTS_LABEL,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL_CHORE,
    DEVICE_SW_VERSION,
    ICON_POINTS,
    LOGGER,
)
from .coordinator import SimpleChoresCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SimpleChores number entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    storage = hass.data[DOMAIN][entry.entry_id]["storage"]
    
    # Get chores from storage
    chores = storage.get_chores()

    entities = []
    
    # Create points number entity for each chore
    for chore_id, chore in chores.items():
        entities.append(ChorePointsNumber(coordinator, entry, chore_id, chore.name))

    async_add_entities(entities)


class ChorePointsNumber(CoordinatorEntity, NumberEntity):
    """Number entity to set chore points value."""

    def __init__(
        self,
        coordinator: SimpleChoresCoordinator,
        entry: ConfigEntry,
        chore_id: str,
        chore_name: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.chore_id = chore_id
        self.chore_name = chore_name
        self._entry = entry
        self._attr_has_entity_name = True
        points_label = entry.data.get(CONF_POINTS_LABEL, DEFAULT_POINTS_LABEL)
        self._attr_name = points_label
        self._attr_unique_id = f"{DOMAIN}_{chore_id}_points"
        self._attr_icon = ICON_POINTS
        self._attr_native_min_value = 0
        self._attr_native_max_value = 1000
        self._attr_native_step = 1
        self._attr_mode = NumberMode.BOX

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this chore."""
        # Get chore from storage to show status and assigned member
        storage = self.coordinator.storage
        chore = storage.get_chore(self.chore_id)
        
        if chore:
            hw_info = f"{chore.status.capitalize()}"
            if chore.assigned_to:
                hw_info += f" • Assigned to {chore.assigned_to}"
        else:
            hw_info = "Unknown"
        
        return DeviceInfo(
            identifiers={(DOMAIN, f"chore_{self.chore_id}")},
            name=self.chore_name,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL_CHORE,
            sw_version=DEVICE_SW_VERSION,
            hw_version=hw_info,
            suggested_area="Chores",
        )

    @property
    def native_value(self) -> float:
        """Return the current points value."""
        storage = self.coordinator.storage
        chore = storage.get_chore(self.chore_id)
        
        if chore is None:
            return 0
        return chore.points

    async def async_set_native_value(self, value: float) -> None:
        """Update the points value."""
        storage = self.coordinator.storage
        chore = storage.get_chore(self.chore_id)
        
        if chore is None:
            LOGGER.error(f"Chore {self.chore_id} not found")
            return
        
        # Update points value
        chore.points = int(value)
        
        # Update storage
        storage.update_chore(self.chore_id, chore)
        await storage.async_save()
        
        # Refresh coordinator to update all entities
        await self.coordinator.async_request_refresh()
        
        LOGGER.info(
            f"Chore '{self.chore_name}' points updated to {int(value)}"
        )
