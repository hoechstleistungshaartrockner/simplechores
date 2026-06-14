"""Number platform for SimpleChores."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    CONF_POINTS_LABEL,
    DEFAULT_POINTS_LABEL,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL_CHORE,
    DEVICE_MODEL_MEMBER,
    DEVICE_SW_VERSION,
    ICON_POINTS,
    LOGGER,
    SORT_OPTION_AREA,
    SORT_OPTION_DUE_DATE,
    SORT_OPTION_NAME,
    SIGNAL_SORT_PRIORITY_UPDATED,
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
    members = storage.get_members()

    entities = []

    # Create points number entity for each chore
    for chore_id, chore in chores.items():
        entities.append(ChorePointsNumber(coordinator, entry, chore_id, chore.name))

    # Create sorting priority number entities for each member and sort criterion
    for member_name in members:
        for criterion in [
            SORT_OPTION_AREA,
            SORT_OPTION_DUE_DATE,
            SORT_OPTION_NAME,
        ]:
            entities.append(
                DashboardSortingPriorityNumber(
                    coordinator,
                    entry,
                    storage,
                    member_name,
                    criterion,
                )
            )

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
        self.entity_id = f"number.{chore_id}_points".lower().replace(" ", "_")

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
    def native_value(self) -> float:
        """Return the current points value."""
        storage = self.coordinator.storage
        chore = storage.get_chore(self.chore_id)

        if chore is None:
            return 0
        return chore.points

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

        # Force immediate coordinator refresh to update all entities
        await self.coordinator.async_refresh()

        LOGGER.info(f"Chore '{self.chore_name}' points updated to {int(value)}")


class DashboardSortingPriorityNumber(NumberEntity):
    """Number entity for dashboard sorting priority."""

    def __init__(
        self,
        coordinator: SimpleChoresCoordinator,
        entry: ConfigEntry,
        storage,
        member_name: str,
        criterion: str,
    ) -> None:
        """Initialize the number entity."""
        self.coordinator = coordinator
        self.storage = storage
        self.entry = entry
        self.member_name = member_name
        self.criterion = criterion
        self._attr_has_entity_name = True
        self._attr_name = f"Sorting priority {criterion.replace('_', ' ').title()}"
        self._attr_unique_id = (
            f"{entry.entry_id}_{member_name}_sort_priority_{criterion}"
        )
        self._attr_icon = "mdi:sort-numeric-ascending"
        self._attr_native_min_value = 1
        self._attr_native_max_value = 3
        self._attr_native_step = 1
        self._attr_mode = NumberMode.BOX
        self.entity_id = (
            f"number.{member_name}_sort_priority_{criterion}".lower().replace(" ", "_")
        )
        self._update_dispatcher_unsub = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for the member."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"member_{self.member_name}")},
            name=self.member_name,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL_MEMBER,
            sw_version=DEVICE_SW_VERSION,
        )

    @property
    def native_value(self) -> float:
        """Return the current sort priority level."""
        member = self.storage.get_member(self.member_name)
        if member is None:
            return 1
        return float(member.get_sort_priority(self.criterion) or 1)

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        attrs = {
            "dashboard_user_name": self.member_name,
            "sort_criterion": self.criterion,
            "integration": DOMAIN,
        }
        return attrs

    async def async_added_to_hass(self) -> None:
        """Register dispatcher update handler."""
        self._update_dispatcher_unsub = async_dispatcher_connect(
            self.hass,
            SIGNAL_SORT_PRIORITY_UPDATED,
            self._handle_sort_priority_updated,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unregister dispatcher update handler."""
        if self._update_dispatcher_unsub is not None:
            self._update_dispatcher_unsub()
            self._update_dispatcher_unsub = None

    def _handle_sort_priority_updated(self, member_name: str) -> None:
        """Handle sort priority updates for the current member.

        This callback may be invoked from a worker thread. Schedule the
        entity state write on the event loop thread to avoid thread-safety
        errors when calling `async_write_ha_state()`.
        """
        if member_name != self.member_name:
            return
        try:
            self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
        except Exception as exc:  # defensive: should not normally fail
            LOGGER.exception("Failed to schedule state write: %s", exc)

    async def async_set_native_value(self, value: float) -> None:
        """Update the sort priority value."""
        member = self.storage.get_member(self.member_name)
        if member is None:
            LOGGER.error(f"Member {self.member_name} not found")
            return

        member.set_sort_priority(self.criterion, int(value))

        self.async_write_ha_state()
        async_dispatcher_send(self.hass, SIGNAL_SORT_PRIORITY_UPDATED, self.member_name)
        LOGGER.info(
            f"Member '{self.member_name}' sort priority for {self.criterion} updated to {int(value)}"
        )
