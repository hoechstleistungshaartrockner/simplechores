"""Select platform for SimpleChores."""
from __future__ import annotations

from datetime import date, timedelta

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers import area_registry as ar
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
    """Set up SimpleChores select entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    storage = hass.data[DOMAIN][entry.entry_id]["storage"]
    
    # Get chores from storage
    chores = storage.get_chores()

    entities = []
    
    # Create select entities for each chore
    for chore_id, chore in chores.items():
        entities.append(ChoreStatusSelect(coordinator, entry, chore_id, chore.name))
        entities.append(ChoreAssigneeSelect(coordinator, entry, chore_id, chore.name))
        entities.append(ChoreCompletedBySelect(coordinator, entry, chore_id, chore.name))

    async_add_entities(entities)


class ChoreAssigneeSelect(CoordinatorEntity, SelectEntity):
    """Select entity to change who a chore is assigned to."""

    def __init__(
        self,
        coordinator: SimpleChoresCoordinator,
        entry: ConfigEntry,
        chore_id: str,
        chore_name: str,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self.chore_id = chore_id
        self.chore_name = chore_name
        self._entry = entry
        self._attr_has_entity_name = True
        self._attr_name = "Assigned to"
        self._attr_unique_id = f"{DOMAIN}_{chore_id}_assigned_to"
        self._attr_icon = "mdi:account-arrow-right"

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
    def options(self) -> list[str]:
        """Return list of possible assignees for this chore."""
        storage = self.coordinator.storage
        chore = storage.get_chore(self.chore_id)
        
        if chore and chore.possible_assignees:
            return chore.possible_assignees
        
        # Fallback to all members if no specific assignees
        members = storage.get_members()
        return list(members.keys())

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        attrs = {
            "integration": DOMAIN,
            "chore_id": self.chore_id,
            "chore_name": self.chore_name,
            "related_entities": self._get_related_entity_ids(),
        }
        device_id = self._get_device_id()
        if device_id:
            attrs["device_id"] = device_id
        return attrs

    @property
    def current_option(self) -> str | None:
        """Return the currently assigned member."""
        storage = self.coordinator.storage
        chore = storage.get_chore(self.chore_id)
        
        if chore:
            return chore.assigned_to
        return None

    async def async_select_option(self, option: str) -> None:
        """Handle member selection - assign chore to selected member."""
        storage = self.coordinator.storage
        chore = storage.get_chore(self.chore_id)
        
        if chore is None:
            LOGGER.error(f"Chore {self.chore_id} not found")
            return
        
        # Verify the member exists
        member = storage.get_member(option)
        if member is None:
            LOGGER.error(f"Member {option} not found")
            return
        
        # Assign chore to member
        chore.assign_to_member(option)
        
        # Update storage
        storage.update_chore(self.chore_id, chore)
        await storage.async_save()
        
        # Force immediate coordinator refresh to update all entities
        await self.coordinator.async_refresh()
        
        LOGGER.info(
            f"Chore '{self.chore_name}' assigned to {option}"
        )


class ChoreCompletedBySelect(CoordinatorEntity, SelectEntity):
    """Select entity to mark a chore as completed by a specific member."""

    def __init__(
        self,
        coordinator: SimpleChoresCoordinator,
        entry: ConfigEntry,
        chore_id: str,
        chore_name: str,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self.chore_id = chore_id
        self.chore_name = chore_name
        self._entry = entry
        self._attr_has_entity_name = True
        self._attr_name = "Mark completed by"
        self._attr_unique_id = f"{DOMAIN}_{chore_id}_mark_completed_by"
        self._attr_icon = "mdi:account-check"

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
    def options(self) -> list[str]:
        """Return list of available members."""
        storage = self.coordinator.storage
        members = storage.get_members()
        return list(members.keys())

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        attrs = {
            "integration": DOMAIN,
            "chore_id": self.chore_id,
            "chore_name": self.chore_name,
            "related_entities": self._get_related_entity_ids(),
        }
        device_id = self._get_device_id()
        if device_id:
            attrs["device_id"] = device_id
        return attrs

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option (always None - it's an action trigger)."""
        return None

    async def async_select_option(self, option: str) -> None:
        """Handle member selection - mark chore as completed by selected member."""
        storage = self.coordinator.storage
        chore = storage.get_chore(self.chore_id)
        
        if chore is None:
            LOGGER.error(f"Chore {self.chore_id} not found")
            return
        
        member = storage.get_member(option)
        if member is None:
            LOGGER.error(f"Member {option} not found")
            return
        
        # Mark chore as completed (handles points and counter updates)
        chore.mark_completed(option, storage, date.today())
        
        # Update storage
        storage.update_chore(self.chore_id, chore)
        await storage.async_save()
        
        # Force immediate coordinator refresh to update all entities
        await self.coordinator.async_refresh()
        
        LOGGER.info(
            f"Chore '{self.chore_name}' marked as completed by {option}"
        )


class ChoreStatusSelect(CoordinatorEntity, SelectEntity):
    """Select entity to change chore status."""

    def __init__(
        self,
        coordinator: SimpleChoresCoordinator,
        entry: ConfigEntry,
        chore_id: str,
        chore_name: str,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self.chore_id = chore_id
        self.chore_name = chore_name
        self._entry = entry
        self._attr_has_entity_name = True
        self._attr_name = "Status"
        self._attr_unique_id = f"{DOMAIN}_{chore_id}_status"
        self._attr_icon = "mdi:clipboard-check"

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
    def options(self) -> list[str]:
        """Return list of available status options."""
        return [CHORE_STATE_PENDING, CHORE_STATE_COMPLETED, CHORE_STATE_OVERDUE]

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
            # Add assigned_to attribute
            if chore.assigned_to:
                attrs["assigned_to"] = chore.assigned_to
            
            # Add due_date attribute
            if chore.due_date:
                attrs["due_date"] = chore.due_date
                
                # Calculate and add due_in_days
                try:
                    due_date = date.fromisoformat(chore.due_date)
                    today = date.today()
                    due_in_days = (due_date - today).days
                    attrs["due_in_days"] = due_in_days
                except (ValueError, TypeError):
                    pass
            
            # Add area information
            if chore.area_id:
                attrs["area_id"] = chore.area_id
                # Get area name from registry
                area_reg = ar.async_get(self.hass)
                area = area_reg.async_get_area(chore.area_id)
                if area:
                    attrs["area_name"] = area.name
        
        return attrs

    @property
    def current_option(self) -> str | None:
        """Return the current status."""
        storage = self.coordinator.storage
        chore = storage.get_chore(self.chore_id)
        
        if chore:
            return chore.status
        return None

    async def async_select_option(self, option: str) -> None:
        """Handle status selection - update chore status."""
        storage = self.coordinator.storage
        chore = storage.get_chore(self.chore_id)
        
        if chore is None:
            LOGGER.error(f"Chore {self.chore_id} not found")
            return
        
        # Update chore status based on selection
        if option == CHORE_STATE_PENDING:
            chore.mark_pending()
        elif option == CHORE_STATE_OVERDUE:
            chore.mark_overdue()
        elif option == CHORE_STATE_COMPLETED:
            # When marking as completed manually, use the assigned member if available
            # Otherwise, don't award points to anyone
            if chore.assigned_to:
                chore.mark_completed(chore.assigned_to, storage)
            else:
                chore.status = CHORE_STATE_COMPLETED
                chore.last_completed = date.today().isoformat()
        
        # Update storage
        storage.update_chore(self.chore_id, chore)
        await storage.async_save()
        
        # Force immediate coordinator refresh to update all entities
        await self.coordinator.async_refresh()
        
        LOGGER.info(
            f"Chore '{self.chore_name}' status updated to {option}"
        )
