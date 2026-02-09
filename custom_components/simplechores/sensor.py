"""Sensor platform for SimpleChores."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN,
    CONF_MEMBERS,
    CONF_POINTS_LABEL,
    DEFAULT_POINTS_LABEL,
    LOGGER,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL_MEMBER,
    DEVICE_SW_VERSION,
    ICON_POINTS,
    ICON_CHORES_COMPLETED,
    ICON_PENDING_CHORES,
    ICON_OVERDUE_CHORES,
    SENSOR_NAME_CHORES_COMPLETED,
    SENSOR_NAME_PENDING_CHORES,
    SENSOR_NAME_OVERDUE_CHORES,
    UNIT_CHORES,
)
from .coordinator import SimpleChoresCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SimpleChores sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    storage = hass.data[DOMAIN][entry.entry_id]["storage"]
    
    # Get members from storage (not entry.data)
    member_names = list(storage.get_members().keys())

    entities = []
    
    for member_name in member_names:
        # Points tracking sensors
        entities.append(MemberPointsSensor(coordinator, entry, member_name, "today"))
        entities.append(MemberPointsSensor(coordinator, entry, member_name, "this_week"))
        entities.append(MemberPointsSensor(coordinator, entry, member_name, "this_month"))
        entities.append(MemberPointsSensor(coordinator, entry, member_name, "this_year"))
        
        # Chore completion tracking sensors
        entities.append(MemberChoresSensor(coordinator, entry, member_name, "today"))
        entities.append(MemberChoresSensor(coordinator, entry, member_name, "this_week"))
        entities.append(MemberChoresSensor(coordinator, entry, member_name, "this_month"))
        entities.append(MemberChoresSensor(coordinator, entry, member_name, "this_year"))
        
        # Status sensors
        entities.append(MemberPendingChoresSensor(coordinator, entry, member_name))
        entities.append(MemberOverdueChoresSensor(coordinator, entry, member_name))

    async_add_entities(entities)


class SimpleChoresBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for SimpleChores sensors."""

    def __init__(
        self,
        coordinator: SimpleChoresCoordinator,
        entry: ConfigEntry,
        member_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.member_name = member_name
        self._entry = entry
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this member."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"member_{self.member_name}")},
            name=self.member_name,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL_MEMBER,
            sw_version=DEVICE_SW_VERSION,
        )


class MemberPointsSensor(SimpleChoresBaseSensor):
    """Sensor for tracking member points over different periods."""

    def __init__(
        self,
        coordinator: SimpleChoresCoordinator,
        entry: ConfigEntry,
        member_name: str,
        period: str,
    ) -> None:
        """Initialize the points sensor."""
        super().__init__(coordinator, entry, member_name)
        self.period = period
        points_label = entry.data.get(CONF_POINTS_LABEL, DEFAULT_POINTS_LABEL)
        self._attr_name = f"{period.capitalize()} {points_label}"
        self._attr_unique_id = f"{DOMAIN}_{member_name}_points_{period}"
        self._attr_icon = ICON_POINTS
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_native_unit_of_measurement = points_label.lower()

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        # Get member from storage
        member = self.coordinator.storage.get_member(self.member_name)
        if member is None:
            return 0
        
        # Get points for the period
        return member.get_points(self.period)


class MemberChoresSensor(SimpleChoresBaseSensor):
    """Sensor for tracking completed chores over different periods."""

    def __init__(
        self,
        coordinator: SimpleChoresCoordinator,
        entry: ConfigEntry,
        member_name: str,
        period: str,
    ) -> None:
        """Initialize the chores sensor."""
        super().__init__(coordinator, entry, member_name)
        self.period = period
        self._attr_name = f"{period.capitalize()} {SENSOR_NAME_CHORES_COMPLETED}"
        self._attr_unique_id = f"{DOMAIN}_{member_name}_chores_{period}"
        self._attr_icon = ICON_CHORES_COMPLETED
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_native_unit_of_measurement = UNIT_CHORES

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        # Get member from storage
        member = self.coordinator.storage.get_member(self.member_name)
        if member is None:
            return 0
        
        # Get chores completed for the period
        return member.get_chores_completed(self.period)


class MemberPendingChoresSensor(SimpleChoresBaseSensor):
    """Sensor for tracking pending chores assigned to a member."""

    def __init__(
        self,
        coordinator: SimpleChoresCoordinator,
        entry: ConfigEntry,
        member_name: str,
    ) -> None:
        """Initialize the pending chores sensor."""
        super().__init__(coordinator, entry, member_name)
        self._attr_name = SENSOR_NAME_PENDING_CHORES
        self._attr_unique_id = f"{DOMAIN}_{member_name}_pending_chores"
        self._attr_icon = ICON_PENDING_CHORES
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UNIT_CHORES

    @property
    def native_value(self) -> int:
        """Return the number of pending chores."""
        # Get all chores from storage
        chores = self.coordinator.storage.data.get("chores", {})
        
        # Count pending chores assigned to this member
        pending_count = 0
        for chore_id, chore_data in chores.items():
            if chore_data.get("assigned_to") == self.member_name:
                if chore_data.get("status") == "pending":
                    pending_count += 1
        
        return pending_count


class MemberOverdueChoresSensor(SimpleChoresBaseSensor):
    """Sensor for tracking overdue chores assigned to a member."""

    def __init__(
        self,
        coordinator: SimpleChoresCoordinator,
        entry: ConfigEntry,
        member_name: str,
    ) -> None:
        """Initialize the overdue chores sensor."""
        super().__init__(coordinator, entry, member_name)
        self._attr_name = SENSOR_NAME_OVERDUE_CHORES
        self._attr_unique_id = f"{DOMAIN}_{member_name}_overdue_chores"
        self._attr_icon = ICON_OVERDUE_CHORES
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UNIT_CHORES

    @property
    def native_value(self) -> int:
        """Return the number of overdue chores."""
        # Get all chores from storage
        chores = self.coordinator.storage.data.get("chores", {})
        
        # Count overdue chores assigned to this member
        overdue_count = 0
        for chore_id, chore_data in chores.items():
            if chore_data.get("assigned_to") == self.member_name:
                if chore_data.get("status") == "overdue":
                    overdue_count += 1
        
        return overdue_count
