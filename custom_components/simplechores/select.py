"""Select platform for SimpleChores."""
from __future__ import annotations

from datetime import date

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

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
        self._attr_unique_id = f"{DOMAIN}_{chore_id}_assignee"
        self._attr_icon = "mdi:account-arrow-right"

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
        
        # Refresh coordinator to update all entities
        await self.coordinator.async_request_refresh()
        
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
        self._attr_unique_id = f"{DOMAIN}_{chore_id}_completed_by"
        self._attr_icon = "mdi:account-check"

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
        
        # Mark chore as completed
        chore.mark_completed(option, date.today())
        
        # Add points to member
        if chore.points > 0:
            member.add_points(chore.points)
        
        # Increment chore completion counter
        member.add_chore_completed()
        
        # Update storage
        storage.update_chore(self.chore_id, chore)
        storage.update_member(member)
        await storage.async_save()
        
        # Refresh coordinator to update all entities
        await self.coordinator.async_request_refresh()
        
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
                chore.mark_completed(chore.assigned_to)
            else:
                chore.status = CHORE_STATE_COMPLETED
                chore.last_completed = date.today().isoformat()
                chore.days_overdue = 0
        
        # Update storage
        storage.update_chore(self.chore_id, chore)
        await storage.async_save()
        
        # Refresh coordinator to update all entities
        await self.coordinator.async_request_refresh()
        
        LOGGER.info(
            f"Chore '{self.chore_name}' status updated to {option}"
        )
