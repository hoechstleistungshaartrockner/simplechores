
"""Config flow for SimpleChores integration."""

from __future__ import annotations

from typing import Any, Optional
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import (
    DOMAIN,
    CONF_ENABLE_POINTS_SYSTEM,
    DEFAULT_ENABLE_POINTS_SYSTEM,
    CONF_POINTS_LABEL,
    DEFAULT_POINTS_LABEL,
    CONF_N_MEMBERS,
    DEFAULT_N_MEMBERS,
    CONF_MEMBERS,
    TRACKER_PERIOD_DAILY,
    TRACKER_PERIOD_WEEKLY,
    TRACKER_PERIOD_MONTHLY,
    TRACKER_PERIOD_YEARLY,
    DEVICE_MANUFACTURER, DEVICE_MODEL_MEMBER, DEVICE_SW_VERSION,
)






class SimpleChoresOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for SimpleChores."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self._selected_member = None
        self._operation = None

    async def async_step_init(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Manage the options for member management."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["create_member", "update_member", "delete_member"],
        )

    async def async_step_create_member(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Create a new household member."""
        errors = {}
        
        if user_input is not None:
            new_member_name = user_input.get("member_name", "").strip()
            
            # Validate member name
            if not new_member_name:
                errors["member_name"] = "name_required"
            else:
                # Get existing members from storage
                storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
                members = storage.get_members()
                
                if new_member_name in members:
                    errors["member_name"] = "member_exists"
                else:
                    # Add new member to storage
                    
                    members[new_member_name] = {
                        f"points_{TRACKER_PERIOD_DAILY}": 0,
                        f"points_{TRACKER_PERIOD_WEEKLY}": 0,
                        f"points_{TRACKER_PERIOD_MONTHLY}": 0,
                        f"points_{TRACKER_PERIOD_YEARLY}": 0,
                        f"chores_{TRACKER_PERIOD_DAILY}": 0,
                        f"chores_{TRACKER_PERIOD_WEEKLY}": 0,
                        f"chores_{TRACKER_PERIOD_MONTHLY}": 0,
                        f"chores_{TRACKER_PERIOD_YEARLY}": 0,
                    }
                    await storage.async_save()
                    
                    # Create device for new member
                    
                    device_reg = dr.async_get(self.hass)
                    device_reg.async_get_or_create(
                        config_entry_id=self.config_entry.entry_id,
                        identifiers={(DOMAIN, f"member_{new_member_name}")},
                        name=new_member_name,
                        manufacturer=DEVICE_MANUFACTURER,
                        model=DEVICE_MODEL_MEMBER,
                        sw_version=DEVICE_SW_VERSION,
                    )
                    
                    # Reload the integration to create new entities
                    await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                    
                    return self.async_create_entry(title="", data={})
        
        schema = vol.Schema({
            vol.Required("member_name"): cv.string,
        })
        
        return self.async_show_form(
            step_id="create_member",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_update_member(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Select a member to update."""
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        members = storage.get_members()
        
        if not members:
            return self.async_abort(reason="no_members")
        
        if user_input is not None:
            self._selected_member = user_input.get("member")
            return await self.async_step_update_member_details()
        
        schema = vol.Schema({
            vol.Required("member"): vol.In(list(members.keys())),
        })
        
        return self.async_show_form(
            step_id="update_member",
            data_schema=schema,
        )

    async def async_step_update_member_details(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Update member details."""
        errors = {}
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        members = storage.get_members()
        member_data = members.get(self._selected_member, {})
        
        if user_input is not None:
            new_name = user_input.get("new_name", "").strip()
            points_action = user_input.get("points_action")
            points_offset = user_input.get("points_offset", 0)
            
            # Validate new name
            if not new_name:
                errors["new_name"] = "name_required"
            elif new_name != self._selected_member and new_name in members:
                errors["new_name"] = "member_exists"
            
            if not errors:
                
                # Handle points action
                if points_action == "offset":
                    for period in [TRACKER_PERIOD_DAILY, TRACKER_PERIOD_WEEKLY, TRACKER_PERIOD_MONTHLY, TRACKER_PERIOD_YEARLY]:
                        member_data[f"points_{period}"] = member_data.get(f"points_{period}", 0) + points_offset
                elif points_action == "reset":
                    for period in [TRACKER_PERIOD_DAILY, TRACKER_PERIOD_WEEKLY, TRACKER_PERIOD_MONTHLY, TRACKER_PERIOD_YEARLY]:
                        member_data[f"points_{period}"] = 0
                
                # Handle name change
                if new_name != self._selected_member:
                    # Update storage
                    members[new_name] = member_data
                    del members[self._selected_member]
                    
                    # Update device registry
                    
                    device_reg = dr.async_get(self.hass)
                    
                    # Remove old device
                    old_device = device_reg.async_get_device(
                        identifiers={(DOMAIN, f"member_{self._selected_member}")}
                    )
                    if old_device:
                        device_reg.async_remove_device(old_device.id)
                    
                    # Create new device
                    device_reg.async_get_or_create(
                        config_entry_id=self.config_entry.entry_id,
                        identifiers={(DOMAIN, f"member_{new_name}")},
                        name=new_name,
                        manufacturer=DEVICE_MANUFACTURER,
                        model=DEVICE_MODEL_MEMBER,
                        sw_version=DEVICE_SW_VERSION,
                    )
                else:
                    members[self._selected_member] = member_data
                
                await storage.async_save()
                
                # Refresh coordinator
                coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]["coordinator"]
                await coordinator.async_refresh_data()
                
                # Reload if name changed to recreate entities
                if new_name != self._selected_member:
                    await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                
                return self.async_create_entry(title="", data={})
        
        schema = vol.Schema({
            vol.Required("new_name", default=self._selected_member): cv.string,
            vol.Required("points_action", default="none"): vol.In({
                "none": "No change",
                "offset": "Offset points",
                "reset": "Reset all points to 0"
            }),
            vol.Optional("points_offset", default=0): vol.Coerce(int),
        })
        
        return self.async_show_form(
            step_id="update_member_details",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "member_name": self._selected_member,
            },
        )

    async def async_step_delete_member(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Delete a household member."""
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        members = storage.get_members()
        
        if not members:
            return self.async_abort(reason="no_members")
        
        if user_input is not None:
            member_to_delete = user_input.get("member")
            
            # Remove from storage
            if member_to_delete in members:
                del members[member_to_delete]
                await storage.async_save()
                
                # Remove device
                device_reg = dr.async_get(self.hass)
                device = device_reg.async_get_device(
                    identifiers={(DOMAIN, f"member_{member_to_delete}")}
                )
                if device:
                    device_reg.async_remove_device(device.id)
                
                # Refresh coordinator
                coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]["coordinator"]
                await coordinator.async_refresh_data()
            
            return self.async_create_entry(title="", data={})
        
        schema = vol.Schema({
            vol.Required("member"): vol.In(list(members.keys())),
        })
        
        return self.async_show_form(
            step_id="delete_member",
            data_schema=schema,
        )
