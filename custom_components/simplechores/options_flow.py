
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
    TRACKER_PERIOD_TODAY,
    TRACKER_PERIOD_THIS_WEEK,
    TRACKER_PERIOD_THIS_MONTH,
    TRACKER_PERIOD_THIS_YEAR,
    DEVICE_MANUFACTURER, DEVICE_MODEL_MEMBER, DEVICE_SW_VERSION,
    ASSIGN_MODE_ALWAYS,
    ASSIGN_MODE_ROTATE,
    ASSIGN_MODE_RANDOM,
)
from .member import Member
from .chore import Chore

from homeassistant.helpers import device_registry as dr



class SimpleChoresOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for SimpleChores."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self._selected_member = None
        self._selected_chore = None

    async def async_step_init(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Main menu - select between managing members or chores."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["manage_members", "manage_chores"],
        )

    # === Member Management Menu ===
    
    async def async_step_manage_members(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Show member management submenu."""
        return self.async_show_menu(
            step_id="manage_members",
            menu_options=["add_member", "edit_member", "delete_member"],
        )

    async def async_step_add_member(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Add a new household member."""
        errors = {}
        
        if user_input is not None:
            new_member_name = user_input.get("member_name", "").strip()
            
            # Validate member name
            if not new_member_name:
                errors["member_name"] = "name_required"
            else:
                # Get existing members from storage
                storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
                
                if storage.member_exists(new_member_name):
                    errors["member_name"] = "member_exists"
                else:
                    # Create new member
                    new_member = Member(name=new_member_name)
                    storage.add_member(new_member)
                    await storage.async_save()
                    
                    # Create device
                    device_reg = dr.async_get(self.hass)
                    device_reg.async_get_or_create(
                        config_entry_id=self.config_entry.entry_id,
                        identifiers={(DOMAIN, f"member_{new_member_name}")},
                        name=new_member_name,
                        manufacturer=DEVICE_MANUFACTURER,
                        model=DEVICE_MODEL_MEMBER,
                        sw_version=DEVICE_SW_VERSION,
                    )
                    
                    # Reload entry to create entities
                    await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                    return self.async_create_entry(title="", data={})
        
        schema = vol.Schema({
            vol.Required("member_name"): cv.string,
        })
        
        return self.async_show_form(
            step_id="add_member",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_edit_member(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Select a member to edit."""
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        members = storage.get_members()
        
        if not members:
            return self.async_abort(reason="no_members")
        
        if user_input is not None:
            self._selected_member = user_input.get("member")
            return await self.async_step_edit_member_details()
        
        schema = vol.Schema({
            vol.Required("member"): vol.In(list(members.keys())),
        })
        
        return self.async_show_form(
            step_id="edit_member",
            data_schema=schema,
        )

    async def async_step_edit_member_details(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Edit member details."""
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
                # Get the member object
                member = storage.get_member(self._selected_member)
                if member is None:
                    errors["base"] = "member_not_found"
                    return self.async_show_form(
                        step_id="edit_member_details",
                        data_schema=schema,
                        errors=errors,
                    )
                
                # Handle points action
                if points_action == "offset":
                    for period in [TRACKER_PERIOD_TODAY, TRACKER_PERIOD_THIS_WEEK, TRACKER_PERIOD_THIS_MONTH, TRACKER_PERIOD_THIS_YEAR]:
                        current = member.get_points(period)
                        member.set_points(period, current + points_offset)
                elif points_action == "reset":
                    member.reset_all_points()
                
                # Handle name change
                if new_name != self._selected_member:
                    # Update member name in storage
                    member.name = new_name
                    storage.delete_member(self._selected_member)
                    storage.add_member(member)
                    
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
                    # Just update existing member data
                    storage.update_member(member)
                
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
            step_id="edit_member_details",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "member_name": self._selected_member,
            },
        )

    # === Chore Management Menu ===
    
    async def async_step_manage_chores(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Show chore management submenu."""
        return self.async_show_menu(
            step_id="manage_chores",
            menu_options=["add_chore", "edit_chore", "delete_chore"],
        )

    async def async_step_add_chore(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Add a new chore."""
        errors = {}
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        members = storage.get_members()
        
        if not members:
            return self.async_abort(reason="no_members")
        
        if user_input is not None:
            chore_name = user_input.get("chore_name", "").strip()
            points = user_input.get("points", 0)
            assignment_mode = user_input.get("assignment_mode", ASSIGN_MODE_ALWAYS)
            assignees = user_input.get("assignees", [])
            
            # Validate chore name
            if not chore_name:
                errors["chore_name"] = "name_required"
            else:
                # Create unique ID for chore (slugified name + timestamp)
                import time
                chore_id = f"{chore_name.lower().replace(' ', '_')}_{int(time.time())}"
                
                # Create the chore
                chore = Chore(
                    name=chore_name,
                    points=points,
                    assignment_mode=assignment_mode,
                    possible_assignees=assignees if assignees else list(members.keys()),
                )
                
                # Assign initial member if needed
                if assignment_mode == ASSIGN_MODE_ALWAYS and assignees:
                    chore.assigned_to = assignees[0]
                elif assignment_mode == ASSIGN_MODE_ROTATE and assignees:
                    chore.assigned_to = assignees[0]
                elif assignment_mode == ASSIGN_MODE_RANDOM and assignees:
                    import random
                    chore.assigned_to = random.choice(assignees)
                
                # Add to storage
                storage.add_chore(chore_id, chore)
                await storage.async_save()
                
                # Reload entry to create device and entities for the new chore
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                
                return self.async_create_entry(title="", data={})
        
        # Create member list for assignees
        member_list = list(members.keys())
        
        schema = vol.Schema({
            vol.Required("chore_name"): cv.string,
            vol.Optional("points", default=10): cv.positive_int,
            vol.Required("assignment_mode", default=ASSIGN_MODE_ALWAYS): vol.In({
                ASSIGN_MODE_ALWAYS: "Always (same person)",
                ASSIGN_MODE_ROTATE: "Rotate (take turns)",
                ASSIGN_MODE_RANDOM: "Random",
            }),
            vol.Optional("assignees", default=member_list): cv.multi_select(
                {member: member for member in member_list}
            ),
        })
        
        return self.async_show_form(
            step_id="add_chore",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_edit_chore(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Select a chore to edit."""
        # TODO: Implement chore editing
        return self.async_abort(reason="not_implemented")

    async def async_step_delete_chore(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Delete a chore."""
        # TODO: Implement chore deletion
        return self.async_abort(reason="not_implemented")

    async def async_step_delete_member(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Delete a household member."""
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        members = storage.get_members()
        
        if not members:
            return self.async_abort(reason="no_members")
        
        if user_input is not None:
            member_to_delete = user_input.get("member")
            
            # Remove from storage
            if storage.delete_member(member_to_delete):
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
