"""Switch platform for SimpleChores dashboard filters."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    CHORE_FILTER_STATES,
    DOMAIN,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL_MEMBER,
    DEVICE_SW_VERSION,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SimpleChores dashboard filter switches."""
    storage = hass.data[DOMAIN][config_entry.entry_id]["storage"]
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    switches = []
    all_members = storage.get_members()

    # Create a switch for each member pair
    for member_name in all_members:
        member = storage.get_member(member_name)
        if not member:
            continue

        for other_member_name in all_members:
            if other_member_name == member_name:
                continue

            switches.append(
                DashboardUserFilterSwitch(
                    coordinator,
                    storage,
                    config_entry,
                    member_name,
                    other_member_name,
                )
            )

        member.init_dashboard_state_filters(CHORE_FILTER_STATES)

        for state_name in CHORE_FILTER_STATES:
            switches.append(
                DashboardStateFilterSwitch(
                    coordinator,
                    storage,
                    config_entry,
                    member_name,
                    state_name,
                )
            )

    await storage.async_save()
    async_add_entities(switches)


class DashboardUserFilterSwitch(SwitchEntity):
    """Switch entity for dashboard user filter."""

    def __init__(
        self,
        coordinator,
        storage,
        config_entry,
        member_name: str,
        other_member_name: str,
    ):
        """Initialize the switch."""
        self.coordinator = coordinator
        self.storage = storage
        self.config_entry = config_entry
        self.member_name = member_name
        self.other_member_name = other_member_name
        self._attr_unique_id = (
            f"{config_entry.entry_id}_{member_name}_filter_{other_member_name}"
        )
        self.entity_id = f"switch.{member_name}_dashboard_user_filter_{other_member_name}".lower().replace(
            " ", "_"
        )

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
    def name(self) -> str:
        """Return the name of the switch."""
        return f"Dashboard user filter {self.other_member_name}"

    @property
    def is_on(self) -> bool:
        """Return True if the filter is enabled."""
        member = self.storage.get_member(self.member_name)
        if member:
            return member.get_dashboard_filter(self.other_member_name)
        return False

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:filter-check"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return additional state attributes."""
        return {
            "dashboard_user_name": self.member_name,
            "target_user_name": self.other_member_name,
        }

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the filter."""
        member = self.storage.get_member(self.member_name)
        if member:
            member.set_dashboard_filter(self.other_member_name, True)
            self.storage.update_member(member)
            await self.storage.async_save()
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the filter."""
        member = self.storage.get_member(self.member_name)
        if member:
            member.set_dashboard_filter(self.other_member_name, False)
            self.storage.update_member(member)
            await self.storage.async_save()
            self.async_write_ha_state()


class DashboardStateFilterSwitch(SwitchEntity):
    """Switch entity for dashboard chore state filter."""

    def __init__(
        self,
        coordinator,
        storage,
        config_entry,
        member_name: str,
        state_name: str,
    ):
        """Initialize the switch."""
        self.coordinator = coordinator
        self.storage = storage
        self.config_entry = config_entry
        self.member_name = member_name
        self.state_name = state_name
        self._attr_unique_id = (
            f"{config_entry.entry_id}_{member_name}_state_filter_{state_name}"
        )
        self.entity_id = (
            f"switch.{member_name}_dashboard_state_filter_{state_name}".lower().replace(
                " ", "_"
            )
        )

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
    def name(self) -> str:
        """Return the name of the switch."""
        return f"Dashboard state filter {self.state_name}"

    @property
    def is_on(self) -> bool:
        """Return True if the filter is enabled."""
        member = self.storage.get_member(self.member_name)
        if member:
            return member.get_dashboard_state_filter(self.state_name)
        return False

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:filter-check"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return additional state attributes."""
        return {
            "dashboard_user_name": self.member_name,
            "filter_state": self.state_name,
        }

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the filter."""
        member = self.storage.get_member(self.member_name)
        if member:
            member.set_dashboard_state_filter(self.state_name, True)
            self.storage.update_member(member)
            await self.storage.async_save()
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the filter."""
        member = self.storage.get_member(self.member_name)
        if member:
            member.set_dashboard_state_filter(self.state_name, False)
            self.storage.update_member(member)
            await self.storage.async_save()
            self.async_write_ha_state()
