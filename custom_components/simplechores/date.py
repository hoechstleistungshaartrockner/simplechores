"""Date platform for SimpleChores."""
from __future__ import annotations

from datetime import date

from homeassistant.components.date import DateEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL_CHORE,
    DEVICE_SW_VERSION,
    LOGGER,
    CHORE_STATE_PENDING,
    CHORE_STATE_COMPLETED,
    CHORE_STATE_OVERDUE,
)
from .coordinator import SimpleChoresCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SimpleChores date entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    storage = hass.data[DOMAIN][entry.entry_id]["storage"]
    
    # Get chores from storage
    chores = storage.get_chores()

    entities = []
    
    # Create date entity for each chore
    for chore_id, chore in chores.items():
        entities.append(ChoreDueDate(coordinator, entry, chore_id, chore.name))

    async_add_entities(entities)


class ChoreDueDate(CoordinatorEntity, DateEntity):
    """Date entity for chore due date."""

    def __init__(
        self,
        coordinator: SimpleChoresCoordinator,
        entry: ConfigEntry,
        chore_id: str,
        chore_name: str,
    ) -> None:
        """Initialize the date entity."""
        super().__init__(coordinator)
        self.chore_id = chore_id
        self.chore_name = chore_name
        self._entry = entry
        self._attr_has_entity_name = True
        self._attr_name = "Due date"
        self._attr_unique_id = f"{DOMAIN}_{chore_id}_due_date"
        self._attr_icon = "mdi:calendar"

    def _get_related_entity_ids(self) -> dict[str, str]:
        """Get all related entity IDs for this chore."""
        return {
            "status": f"select.{self.chore_id}_status",
            "assigned_to": f"select.{self.chore_id}_assigned_to",
            "mark_completed_by": f"select.{self.chore_id}_mark_completed_by",
            "points": f"number.{self.chore_id}_points",
            "due_date": f"date.{self.chore_id}_due_date",
        }

    def _get_device_id(self) -> str | None:
        """Get the device_id for this entity's device."""
        device_registry = dr.async_get(self.hass)
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, f"chore_{self.chore_id}")}
        )
        if device:
            return device.id
        return None

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
    def native_value(self) -> date | None:
        """Return the due date."""
        storage = self.coordinator.storage
        chore = storage.get_chore(self.chore_id)
        
        if chore is None or chore.due_date is None:
            return None
        
        # Convert ISO string to date object
        try:
            return date.fromisoformat(chore.due_date)
        except (ValueError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        storage = self.coordinator.storage
        chore = storage.get_chore(self.chore_id)
        
        attrs = {
            "integration": DOMAIN,
            "chore_id": self.chore_id,
            "chore_name": self.chore_name,
            "related_entities": self._get_related_entity_ids(),
        }
        
        device_id = self._get_device_id()
        if device_id:
            attrs["device_id"] = device_id
        
        if chore:
            # Calculate days until due
            due_in_days = None
            if chore.due_date:
                try:
                    due_date = date.fromisoformat(chore.due_date)
                    today = date.today()
                    due_in_days = (due_date - today).days
                except (ValueError, TypeError):
                    pass
            
            attrs.update({
                "recurrence_pattern": chore.recurrence_pattern,
                "recurrence_interval": chore.recurrence_interval,
                "last_completed": chore.last_completed,
                "due_in_days": due_in_days,
                "status": chore.status,
                "assigned_to": chore.assigned_to,
            })
        
        return attrs

    async def async_set_value(self, value: date) -> None:
        """Update the due date."""
        storage = self.coordinator.storage
        chore = storage.get_chore(self.chore_id)
        
        if chore is None:
            LOGGER.error(f"Chore {self.chore_id} not found")
            return
        
        # Store date as ISO string
        chore.due_date = value.isoformat()
        
        # Adjust status based on due date
        today = date.today()
        if value < today:
            # Due date is in the past - mark as overdue
            chore.status = CHORE_STATE_OVERDUE
        elif value == today:
            # Due date is today - mark as pending
            chore.status = CHORE_STATE_PENDING
        else:
            # Due date is in the future - mark as completed (inactive state)
            chore.status = CHORE_STATE_COMPLETED
        
        # Update storage
        storage.update_chore(self.chore_id, chore)
        await storage.async_save()
        
        # Force immediate coordinator refresh to update all entities
        await self.coordinator.async_refresh()
        
        LOGGER.info(
            f"Chore '{self.chore_name}' due date updated to {value}"
        )
