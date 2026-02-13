"""Services for SimpleChores integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from datetime import date

from .const import (
    DOMAIN,
    LOGGER,
    SERVICE_UPDATE_POINTS,
    SERVICE_RESET_POINTS,
    SERVICE_TOGGLE_CHORE,
    SERVICE_UPDATE_CHORES,
    TRACKER_PERIOD_TODAY,
    TRACKER_PERIOD_THIS_WEEK,
    TRACKER_PERIOD_THIS_MONTH,
    TRACKER_PERIOD_THIS_YEAR,
    CHORE_STATE_PENDING,
    CHORE_STATE_COMPLETED,
    CHORE_STATE_OVERDUE,
)

# Service schemas
UPDATE_POINTS_SCHEMA = vol.Schema({
    vol.Required("member"): cv.string,
    vol.Required("offset"): vol.Coerce(int),
    vol.Optional("periods", default=[TRACKER_PERIOD_TODAY, TRACKER_PERIOD_THIS_WEEK, TRACKER_PERIOD_THIS_MONTH, TRACKER_PERIOD_THIS_YEAR]): 
        vol.All(cv.ensure_list, [vol.In([TRACKER_PERIOD_TODAY, TRACKER_PERIOD_THIS_WEEK, TRACKER_PERIOD_THIS_MONTH, TRACKER_PERIOD_THIS_YEAR])]),
})

RESET_POINTS_SCHEMA = vol.Schema({
    vol.Required("member"): cv.string,
    vol.Optional("periods", default=[TRACKER_PERIOD_TODAY, TRACKER_PERIOD_THIS_WEEK, TRACKER_PERIOD_THIS_MONTH, TRACKER_PERIOD_THIS_YEAR]): 
        vol.All(cv.ensure_list, [vol.In([TRACKER_PERIOD_TODAY, TRACKER_PERIOD_THIS_WEEK, TRACKER_PERIOD_THIS_MONTH, TRACKER_PERIOD_THIS_YEAR])]),
})

TOGGLE_CHORE_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required("member"): cv.string,
})


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for SimpleChores."""

    async def handle_update_points(call: ServiceCall) -> None:
        """Handle the update_points service call."""
        member_name = call.data["member"]
        offset = call.data["offset"]
        periods = call.data.get("periods", [TRACKER_PERIOD_TODAY, TRACKER_PERIOD_THIS_WEEK, TRACKER_PERIOD_THIS_MONTH, TRACKER_PERIOD_THIS_YEAR])

        # Get the first config entry (we only allow one instance)
        entry_id = next(iter(hass.data[DOMAIN]))
        storage = hass.data[DOMAIN][entry_id]["storage"]
        coordinator = hass.data[DOMAIN][entry_id]["coordinator"]

        member = storage.get_member(member_name)
        if member is None:
            LOGGER.error(f"Member '{member_name}' not found")
            return

        # Update points for specified periods
        for period in periods:
            current_points = member.get_points(period)
            member.set_points(period, current_points + offset)
        
        storage.update_member(member)
        await storage.async_save()
        await coordinator.async_refresh_data()

        LOGGER.info(
            f"Updated points for {member_name}: offset={offset}, periods={periods}"
        )

    async def handle_reset_points(call: ServiceCall) -> None:
        """Handle the reset_points service call."""
        member_name = call.data["member"]
        periods = call.data.get("periods", [TRACKER_PERIOD_TODAY, TRACKER_PERIOD_THIS_WEEK, TRACKER_PERIOD_THIS_MONTH, TRACKER_PERIOD_THIS_YEAR])

        # Get the first config entry (we only allow one instance)
        entry_id = next(iter(hass.data[DOMAIN]))
        storage = hass.data[DOMAIN][entry_id]["storage"]
        coordinator = hass.data[DOMAIN][entry_id]["coordinator"]

        member = storage.get_member(member_name)
        if member is None:
            LOGGER.error(f"Member '{member_name}' not found")
            return

        # Reset points for specified periods
        for period in periods:
            member.reset_points(period)
        
        storage.update_member(member)
        await storage.async_save()
        await coordinator.async_refresh_data()

        LOGGER.info(f"Reset points for {member_name}: periods={periods}")

    async def handle_toggle_chore(call: ServiceCall) -> None:
        """Handle the toggle_chore service call."""
        entity_id = call.data["entity_id"]
        member_name = call.data["member"]

        # Get entity state to read chore_id from attributes
        entity_state = hass.states.get(entity_id)
        if entity_state is None:
            LOGGER.error(f"Entity {entity_id} not found")
            return
        
        # Get chore_id from entity attributes
        chore_id = entity_state.attributes.get("chore_id")
        if chore_id is None:
            LOGGER.error(f"Entity {entity_id} does not have a chore_id attribute")
            return

        # Get the first config entry
        entry_id = next(iter(hass.data[DOMAIN]))
        storage = hass.data[DOMAIN][entry_id]["storage"]
        coordinator = hass.data[DOMAIN][entry_id]["coordinator"]

        # Get chore
        chore = storage.get_chore(chore_id)
        if chore is None:
            LOGGER.error(f"Chore '{chore_id}' not found")
            return

        # Get member
        member = storage.get_member(member_name)
        if member is None:
            LOGGER.error(f"Member '{member_name}' not found")
            return

        # Toggle logic
        
        if chore.status == CHORE_STATE_COMPLETED:
            # If completed, mark as pending
            chore.mark_pending()
            LOGGER.info(f"Chore '{chore.name}' marked as pending")
        else:
            # If pending or overdue, mark as completed (handles points and counter updates)
            chore.mark_completed(member_name, storage, date.today())
            
            LOGGER.info(
                f"Chore '{chore.name}' marked as completed by {member_name}, "
                f"awarded {chore.points} points"
            )
        
        # Update chore in storage
        storage.update_chore(chore_id, chore)
        
        # Immediately update coordinator data to refresh UI
        coordinator.async_set_updated_data(storage.data)
        
        # Save to disk in background (don't await to avoid blocking)
        hass.async_create_task(storage.async_save())

    async def handle_update_chores(call: ServiceCall) -> None:
        """Handle the update_chores service call."""
        # Get the first config entry
        entry_id = next(iter(hass.data[DOMAIN]))
        storage = hass.data[DOMAIN][entry_id]["storage"]
        coordinator = hass.data[DOMAIN][entry_id]["coordinator"]

        # Get all chores
        chores = storage.get_chores()
        today = date.today()
        updated_count = 0

        for chore_id, chore in chores.items():
            if chore.due_date is None:
                continue
            
            try:
                due_date = date.fromisoformat(chore.due_date)
                old_status = chore.status
                
                # Update status based on due date
                if due_date < today:
                    chore.status = CHORE_STATE_OVERDUE
                elif due_date == today:
                    chore.status = CHORE_STATE_PENDING
                else:
                    chore.status = CHORE_STATE_COMPLETED
                
                # Only update if status changed
                if old_status != chore.status:
                    storage.update_chore(chore_id, chore)
                    updated_count += 1
                    LOGGER.debug(
                        f"Chore '{chore.name}' status updated from {old_status} to {chore.status}"
                    )
            except (ValueError, TypeError):
                LOGGER.warning(f"Invalid due_date for chore '{chore.name}': {chore.due_date}")
                continue

        # Save and refresh if any changes were made
        if updated_count > 0:
            await storage.async_save()
            coordinator.async_set_updated_data(storage.data)
            LOGGER.info(f"Updated {updated_count} chore(s) status based on due dates")
        else:
            LOGGER.debug("No chore status updates needed")

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

    hass.services.async_register(
        DOMAIN,
        SERVICE_TOGGLE_CHORE,
        handle_toggle_chore,
        schema=TOGGLE_CHORE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_CHORES,
        handle_update_chores,
    )

    LOGGER.debug("Services registered: update_points, reset_points, toggle_chore, update_chores")


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services."""
    hass.services.async_remove(DOMAIN, SERVICE_UPDATE_POINTS)
    hass.services.async_remove(DOMAIN, SERVICE_RESET_POINTS)
    hass.services.async_remove(DOMAIN, SERVICE_TOGGLE_CHORE)
    hass.services.async_remove(DOMAIN, SERVICE_UPDATE_CHORES)
    LOGGER.debug("Services unloaded")
