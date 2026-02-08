"""Services for SimpleChores integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    LOGGER,
    SERVICE_UPDATE_POINTS,
    SERVICE_RESET_POINTS,
    TRACKER_PERIOD_DAILY,
    TRACKER_PERIOD_WEEKLY,
    TRACKER_PERIOD_MONTHLY,
    TRACKER_PERIOD_YEARLY,
)

# Service schemas
UPDATE_POINTS_SCHEMA = vol.Schema({
    vol.Required("member"): cv.string,
    vol.Required("offset"): vol.Coerce(int),
    vol.Optional("periods", default=[TRACKER_PERIOD_DAILY, TRACKER_PERIOD_WEEKLY, TRACKER_PERIOD_MONTHLY, TRACKER_PERIOD_YEARLY]): 
        vol.All(cv.ensure_list, [vol.In([TRACKER_PERIOD_DAILY, TRACKER_PERIOD_WEEKLY, TRACKER_PERIOD_MONTHLY, TRACKER_PERIOD_YEARLY])]),
})

RESET_POINTS_SCHEMA = vol.Schema({
    vol.Required("member"): cv.string,
    vol.Optional("periods", default=[TRACKER_PERIOD_DAILY, TRACKER_PERIOD_WEEKLY, TRACKER_PERIOD_MONTHLY, TRACKER_PERIOD_YEARLY]): 
        vol.All(cv.ensure_list, [vol.In([TRACKER_PERIOD_DAILY, TRACKER_PERIOD_WEEKLY, TRACKER_PERIOD_MONTHLY, TRACKER_PERIOD_YEARLY])]),
})


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for SimpleChores."""

    async def handle_update_points(call: ServiceCall) -> None:
        """Handle the update_points service call."""
        member_name = call.data["member"]
        offset = call.data["offset"]
        periods = call.data.get("periods", [TRACKER_PERIOD_DAILY, TRACKER_PERIOD_WEEKLY, TRACKER_PERIOD_MONTHLY, TRACKER_PERIOD_YEARLY])

        # Get the first config entry (we only allow one instance)
        entry_id = next(iter(hass.data[DOMAIN]))
        storage = hass.data[DOMAIN][entry_id]["storage"]
        coordinator = hass.data[DOMAIN][entry_id]["coordinator"]

        members = storage.get_members()
        if member_name not in members:
            LOGGER.error(f"Member '{member_name}' not found")
            return

        # Update points for specified periods
        member_data = members[member_name]
        for period in periods:
            current_points = member_data.get(f"points_{period}", 0)
            member_data[f"points_{period}"] = current_points + offset

        await storage.async_save()
        await coordinator.async_refresh_data()

        LOGGER.info(
            f"Updated points for {member_name}: offset={offset}, periods={periods}"
        )

    async def handle_reset_points(call: ServiceCall) -> None:
        """Handle the reset_points service call."""
        member_name = call.data["member"]
        periods = call.data.get("periods", [TRACKER_PERIOD_DAILY, TRACKER_PERIOD_WEEKLY, TRACKER_PERIOD_MONTHLY, TRACKER_PERIOD_YEARLY])

        # Get the first config entry (we only allow one instance)
        entry_id = next(iter(hass.data[DOMAIN]))
        storage = hass.data[DOMAIN][entry_id]["storage"]
        coordinator = hass.data[DOMAIN][entry_id]["coordinator"]

        members = storage.get_members()
        if member_name not in members:
            LOGGER.error(f"Member '{member_name}' not found")
            return

        # Reset points for specified periods
        member_data = members[member_name]
        for period in periods:
            member_data[f"points_{period}"] = 0

        await storage.async_save()
        await coordinator.async_refresh_data()

        LOGGER.info(f"Reset points for {member_name}: periods={periods}")

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_POINTS,
        handle_update_points,
        schema=UPDATE_POINTS_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_POINTS,
        handle_reset_points,
        schema=RESET_POINTS_SCHEMA,
    )

    LOGGER.debug("Services registered: update_points, reset_points")


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services."""
    hass.services.async_remove(DOMAIN, SERVICE_UPDATE_POINTS)
    hass.services.async_remove(DOMAIN, SERVICE_RESET_POINTS)
    LOGGER.debug("Services unloaded")
