
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
    FREQUENCY_NONE,
    FREQUENCY_DAILY,
    FREQUENCY_MONTHLY_DAY,
    FREQUENCY_MONTHLY_WEEKDAY,
    FREQUENCY_INTERVAL_DAYS,
    FREQUENCY_AFTER_COMPLETION_DAYS,
    FREQUENCY_SPECIFIC_DAYS,
    FREQUENCY_ANNUAL,
    CONF_RECURRENCE_PATTERN,
    CONF_RECURRENCE_INTERVAL,
    CONF_RECURRENCE_DAY_OF_MONTH,
    CONF_RECURRENCE_WEEK_OF_MONTH,
    CONF_RECURRENCE_SPECIFIC_WEEKDAYS,
    CONF_RECURRENCE_ANNUAL_MONTH,
    CONF_RECURRENCE_ANNUAL_DAY,
)
from .member import Member
from .chore import Chore

from homeassistant.helpers import device_registry as dr, area_registry as ar



class SimpleChoresOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for SimpleChores."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self._selected_member = None
        self._selected_chore = None
        self._chore_data = {}  # Temporary storage for chore data during flow
        self._chore_mode = None  # Track if we're in 'add' or 'edit' mode

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
                    
                    # Store member name for next steps
                    self._selected_member = new_member_name
                    
                    # Check if there are any chores to assign
                    chores = storage.get_chores()
                    if chores:
                        # Move to chore assignment step
                        return await self.async_step_add_member_assign_chores()
                    else:
                        # No chores, complete the flow
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

    async def async_step_add_member_assign_chores(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Select which chores can be assigned to the new member."""
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        chores = storage.get_chores()
        
        if user_input is not None:
            selected_chores = user_input.get("chores", [])
            
            if selected_chores:
                # Store selected chores for next step
                self._chore_data = {"selected_chores": selected_chores}
                return await self.async_step_add_member_assignment_mode()
            else:
                # No chores selected, complete the flow
                self._selected_member = None
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                return self.async_create_entry(title="", data={})
        
        # Create chore choices
        chore_choices = {chore_id: chore.name for chore_id, chore in chores.items()}
        
        schema = vol.Schema({
            vol.Optional("chores", default=[]): cv.multi_select(chore_choices),
        })
        
        return self.async_show_form(
            step_id="add_member_assign_chores",
            data_schema=schema,
            description_placeholders={
                "member_name": self._selected_member,
            },
        )

    async def async_step_add_member_assignment_mode(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Select assignment mode for chores assigned to the new member."""
        errors = {}
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        selected_chore_ids = self._chore_data.get("selected_chores", [])
        
        if user_input is not None:
            assignment_mode = user_input.get("assignment_mode", ASSIGN_MODE_ALWAYS)
            
            # Update selected chores with new member and assignment mode
            for chore_id in selected_chore_ids:
                chore = storage.get_chore(chore_id)
                if chore:
                    # Add new member to possible_assignees if not already there
                    if self._selected_member not in chore.possible_assignees:
                        chore.possible_assignees.append(self._selected_member)
                    
                    # Validate and update assignment mode
                    if assignment_mode == ASSIGN_MODE_ALWAYS:
                        # For always mode, need exactly one assignee
                        if len(chore.possible_assignees) == 1:
                            chore.assignment_mode = ASSIGN_MODE_ALWAYS
                            chore.assigned_to = chore.possible_assignees[0]
                        else:
                            # More than one assignee, cannot use always mode
                            errors["assignment_mode"] = "always_mode_one_person"
                            break
                    elif assignment_mode in [ASSIGN_MODE_ROTATE, ASSIGN_MODE_RANDOM]:
                        # For rotate/random mode, need at least two assignees
                        if len(chore.possible_assignees) >= 2:
                            chore.assignment_mode = assignment_mode
                            # Keep current assignment or assign to new member if needed
                            if not chore.assigned_to or chore.assigned_to not in chore.possible_assignees:
                                chore.assigned_to = chore.possible_assignees[0]
                        else:
                            # Only one assignee, cannot use rotate/random mode
                            errors["assignment_mode"] = "rotate_random_two_people"
                            break
                    
                    storage.update_chore(chore_id, chore)
            
            if not errors:
                await storage.async_save()
                
                # Clear temporary data
                self._selected_member = None
                self._chore_data = {}
                
                # Reload entry to update entities
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                return self.async_create_entry(title="", data={})
        
        schema = vol.Schema({
            vol.Required("assignment_mode", default=ASSIGN_MODE_ALWAYS): vol.In({
                ASSIGN_MODE_ALWAYS: "Always (same person)",
                ASSIGN_MODE_ROTATE: "Rotate (take turns)",
                ASSIGN_MODE_RANDOM: "Random",
            }),
        })
        
        return self.async_show_form(
            step_id="add_member_assignment_mode",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "member_name": self._selected_member,
            },
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
            menu_options=["add_chore", "edit_chore", "delete_chore", "delete_all_chores"],
        )

    async def async_step_add_chore(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Add a new chore - entry point and form handler."""
        # Only initialize on first call (from menu)
        if user_input is None:
            storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
            members = storage.get_members()
            
            if not members:
                return self.async_abort(reason="no_members")
            
            # Initialize for add mode
            self._chore_mode = "add"
            self._chore_data = {}
            self._selected_chore = None
        
        # Delegate to shared basic info step
        return await self.async_step_chore_basic(user_input)

    async def async_step_chore_basic(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Shared step for basic chore information (add/edit)."""
        errors = {}
        area_registry = ar.async_get(self.hass)
        areas = {area.id: area.name for area in area_registry.async_list_areas()}
        areas["none"] = "No area"
        
        # Get defaults
        default_name = ""
        default_points = 0
        default_area = "none"
        
        if self._chore_mode == "edit" and self._selected_chore:
            storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
            chores = storage.get_chores()
            if self._selected_chore in chores:
                chore = chores[self._selected_chore]
                default_name = chore.name
                default_points = chore.points
                default_area = chore.area_id if chore.area_id else "none"
        
        if user_input is not None:
            chore_name = user_input.get("chore_name", "").strip()
            if not chore_name:
                errors["chore_name"] = "Name is required"
            else:
                self._chore_data["chore_name"] = chore_name
                self._chore_data["points"] = user_input.get("points", 0)
                self._chore_data["area_id"] = user_input.get("area_id", "none")
                return await self.async_step_chore_assignees()
        
        schema = vol.Schema({
            vol.Required("chore_name", default=default_name): cv.string,
            vol.Required("points", default=default_points): vol.Coerce(int),
            vol.Optional("area_id", default=default_area): vol.In(areas),
        })
        
        step_id = "edit_chore_basic" if self._chore_mode == "edit" else "add_chore"
        return self.async_show_form(
            step_id=step_id,
            data_schema=schema,
            errors=errors,
        )

    async def async_step_chore_assignees(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Shared step for assignment configuration (add/edit)."""
        errors = {}
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        members = storage.get_members()
        member_list = list(members.keys())
        
        # Get defaults
        default_assignees = member_list
        default_assignment_mode = ASSIGN_MODE_ALWAYS
        
        if self._chore_mode == "edit" and self._selected_chore:
            chores = storage.get_chores()
            if self._selected_chore in chores:
                chore = chores[self._selected_chore]
                default_assignees = chore.possible_assignees
                default_assignment_mode = chore.assignment_mode
        
        if user_input is not None:
            assignment_mode = user_input.get("assignment_mode", ASSIGN_MODE_ALWAYS)
            assignees = user_input.get("assignees", member_list)
            
            # Validate assignment mode and assignees combination
            if assignment_mode == ASSIGN_MODE_ALWAYS and len(assignees) != 1:
                errors["assignees"] = "always_mode_one_person"
            elif assignment_mode in [ASSIGN_MODE_ROTATE, ASSIGN_MODE_RANDOM] and len(assignees) < 2:
                errors["assignees"] = "rotate_random_two_people"
            
            if not errors:
                self._chore_data["assignment_mode"] = assignment_mode
                self._chore_data["assignees"] = assignees
                return await self.async_step_chore_recurrence()
        
        schema = vol.Schema({
            vol.Optional("assignees", default=default_assignees): cv.multi_select(
                {member: member for member in member_list}
            ),
            vol.Required("assignment_mode", default=default_assignment_mode): vol.In({
                ASSIGN_MODE_ALWAYS: "Always (same person)",
                ASSIGN_MODE_ROTATE: "Rotate (take turns)",
                ASSIGN_MODE_RANDOM: "Random",
            }),
        })
        
        step_id = "edit_chore_assignees" if self._chore_mode == "edit" else "add_chore_assignees"
        return self.async_show_form(
            step_id=step_id,
            data_schema=schema,
            errors=errors,
        )

    async def async_step_add_chore_assignees(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Add a new chore - Step 2: Assignment configuration."""
        return await self.async_step_chore_assignees(user_input)

    async def async_step_chore_recurrence(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Shared step for recurrence pattern selection (add/edit)."""
        # Get defaults
        default_pattern = FREQUENCY_DAILY
        
        if self._chore_mode == "edit" and self._selected_chore:
            storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
            chores = storage.get_chores()
            if self._selected_chore in chores:
                chore = chores[self._selected_chore]
                default_pattern = chore.recurrence_pattern
        
        if user_input is not None:
            recurrence_pattern = user_input.get(CONF_RECURRENCE_PATTERN, FREQUENCY_DAILY)
            self._chore_data[CONF_RECURRENCE_PATTERN] = recurrence_pattern
            
            # Move to interval configuration if pattern requires it
            if recurrence_pattern in [FREQUENCY_INTERVAL_DAYS, FREQUENCY_AFTER_COMPLETION_DAYS]:
                return await self.async_step_chore_interval()
            elif recurrence_pattern == FREQUENCY_MONTHLY_DAY:
                return await self.async_step_chore_monthly_day()
            elif recurrence_pattern == FREQUENCY_MONTHLY_WEEKDAY:
                return await self.async_step_chore_monthly_weekday()
            elif recurrence_pattern == FREQUENCY_SPECIFIC_DAYS:
                return await self.async_step_chore_specific_days()
            elif recurrence_pattern == FREQUENCY_ANNUAL:
                return await self.async_step_chore_annual()
            else:
                # For daily or none, finalize the chore
                return await self.async_step_chore_finalize()
        
        schema = vol.Schema({
            vol.Required(CONF_RECURRENCE_PATTERN, default=default_pattern): vol.In({
                FREQUENCY_NONE: "No recurrence",
                FREQUENCY_DAILY: "Daily",
                FREQUENCY_INTERVAL_DAYS: "Every X days",
                FREQUENCY_AFTER_COMPLETION_DAYS: "X days after completion",
                FREQUENCY_SPECIFIC_DAYS: "Specific weekdays",
                FREQUENCY_MONTHLY_DAY: "Monthly (specific day)",
                FREQUENCY_MONTHLY_WEEKDAY: "Monthly (specific weekday)",
                FREQUENCY_ANNUAL: "Annually",
            }),
        })
        
        step_id = "edit_chore_recurrence" if self._chore_mode == "edit" else "add_chore_recurrence"
        return self.async_show_form(
            step_id=step_id,
            data_schema=schema,
        )

    async def async_step_add_chore_recurrence(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Add a new chore - Step 3: Select recurrence pattern."""
        return await self.async_step_chore_recurrence(user_input)

    async def async_step_chore_interval(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Shared step for interval configuration (add/edit)."""
        # Get defaults
        default_interval = 1
        
        if self._chore_mode == "edit" and self._selected_chore:
            storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
            chores = storage.get_chores()
            if self._selected_chore in chores:
                chore = chores[self._selected_chore]
                default_interval = chore.recurrence_interval
        
        if user_input is not None:
            self._chore_data[CONF_RECURRENCE_INTERVAL] = user_input.get(CONF_RECURRENCE_INTERVAL, 1)
            return await self.async_step_chore_finalize()
        
        schema = vol.Schema({
            vol.Required(CONF_RECURRENCE_INTERVAL, default=default_interval): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=365)
            ),
        })
        
        step_id = "edit_chore_interval" if self._chore_mode == "edit" else "add_chore_interval"
        return self.async_show_form(
            step_id=step_id,
            data_schema=schema,
        )

    async def async_step_add_chore_interval(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Add a new chore - interval configuration."""
        return await self.async_step_chore_interval(user_input)

    async def async_step_chore_monthly_day(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Shared step for monthly day configuration (add/edit)."""
        # Get defaults
        default_day = 1
        
        if self._chore_mode == "edit" and self._selected_chore:
            storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
            chores = storage.get_chores()
            if self._selected_chore in chores:
                chore = chores[self._selected_chore]
                default_day = chore.recurrence_day_of_month or 1
        
        if user_input is not None:
            self._chore_data[CONF_RECURRENCE_DAY_OF_MONTH] = user_input.get(CONF_RECURRENCE_DAY_OF_MONTH, 1)
            return await self.async_step_chore_finalize()
        
        schema = vol.Schema({
            vol.Required(CONF_RECURRENCE_DAY_OF_MONTH, default=default_day): vol.All(
                vol.Coerce(int), vol.Range(min=-1, max=31)
            ),
        })
        
        step_id = "edit_chore_monthly_day" if self._chore_mode == "edit" else "add_chore_monthly_day"
        return self.async_show_form(
            step_id=step_id,
            data_schema=schema,
        )

    async def async_step_add_chore_monthly_day(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Add a new chore - monthly day configuration."""
        return await self.async_step_chore_monthly_day(user_input)

    async def async_step_chore_monthly_weekday(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Shared step for monthly weekday configuration (add/edit)."""
        # Get defaults
        default_week = 1
        default_weekday = 0
        
        if self._chore_mode == "edit" and self._selected_chore:
            storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
            chores = storage.get_chores()
            if self._selected_chore in chores:
                chore = chores[self._selected_chore]
                default_week = chore.recurrence_week_of_month or 1
                if chore.recurrence_specific_weekdays:
                    default_weekday = chore.recurrence_specific_weekdays[0]
        
        if user_input is not None:
            self._chore_data[CONF_RECURRENCE_WEEK_OF_MONTH] = user_input.get(CONF_RECURRENCE_WEEK_OF_MONTH, 1)
            self._chore_data[CONF_RECURRENCE_SPECIFIC_WEEKDAYS] = [user_input.get("weekday", 0)]
            return await self.async_step_chore_finalize()
        
        schema = vol.Schema({
            vol.Required(CONF_RECURRENCE_WEEK_OF_MONTH, default=default_week): vol.In({
                1: "First",
                2: "Second",
                3: "Third",
                4: "Fourth",
                -1: "Last",
            }),
            vol.Required("weekday", default=default_weekday): vol.In({
                0: "Monday",
                1: "Tuesday",
                2: "Wednesday",
                3: "Thursday",
                4: "Friday",
                5: "Saturday",
                6: "Sunday",
            }),
        })
        
        step_id = "edit_chore_monthly_weekday" if self._chore_mode == "edit" else "add_chore_monthly_weekday"
        return self.async_show_form(
            step_id=step_id,
            data_schema=schema,
        )

    async def async_step_add_chore_monthly_weekday(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Add a new chore - monthly weekday configuration."""
        return await self.async_step_chore_monthly_weekday(user_input)

    async def async_step_chore_specific_days(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Shared step for specific weekdays configuration (add/edit)."""
        # Get defaults
        default_weekdays = [0]
        
        if self._chore_mode == "edit" and self._selected_chore:
            storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
            chores = storage.get_chores()
            if self._selected_chore in chores:
                chore = chores[self._selected_chore]
                default_weekdays = chore.recurrence_specific_weekdays or [0]
        
        if user_input is not None:
            self._chore_data[CONF_RECURRENCE_SPECIFIC_WEEKDAYS] = user_input.get(CONF_RECURRENCE_SPECIFIC_WEEKDAYS, [0])
            return await self.async_step_chore_finalize()
        
        schema = vol.Schema({
            vol.Required(CONF_RECURRENCE_SPECIFIC_WEEKDAYS, default=default_weekdays): cv.multi_select({
                0: "Monday",
                1: "Tuesday",
                2: "Wednesday",
                3: "Thursday",
                4: "Friday",
                5: "Saturday",
                6: "Sunday",
            }),
        })
        
        step_id = "edit_chore_specific_days" if self._chore_mode == "edit" else "add_chore_specific_days"
        return self.async_show_form(
            step_id=step_id,
            data_schema=schema,
        )

    async def async_step_add_chore_specific_days(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Add a new chore - specific days configuration."""
        return await self.async_step_chore_specific_days(user_input)

    async def async_step_chore_annual(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Shared step for annual recurrence configuration (add/edit)."""
        # Get defaults
        default_month = 1
        default_day = 1
        
        if self._chore_mode == "edit" and self._selected_chore:
            storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
            chores = storage.get_chores()
            if self._selected_chore in chores:
                chore = chores[self._selected_chore]
                default_month = chore.recurrence_annual_month or 1
                default_day = chore.recurrence_annual_day or 1
        
        if user_input is not None:
            self._chore_data[CONF_RECURRENCE_ANNUAL_MONTH] = user_input.get(CONF_RECURRENCE_ANNUAL_MONTH, 1)
            self._chore_data[CONF_RECURRENCE_ANNUAL_DAY] = user_input.get(CONF_RECURRENCE_ANNUAL_DAY, 1)
            return await self.async_step_chore_finalize()
        
        schema = vol.Schema({
            vol.Required(CONF_RECURRENCE_ANNUAL_MONTH, default=default_month): vol.In({
                1: "January", 2: "February", 3: "March", 4: "April",
                5: "May", 6: "June", 7: "July", 8: "August",
                9: "September", 10: "October", 11: "November", 12: "December",
            }),
            vol.Required(CONF_RECURRENCE_ANNUAL_DAY, default=default_day): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=31)
            ),
        })
        
        step_id = "edit_chore_annual" if self._chore_mode == "edit" else "add_chore_annual"
        return self.async_show_form(
            step_id=step_id,
            data_schema=schema,
        )

    async def async_step_add_chore_annual(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Add a new chore - annual configuration."""
        return await self.async_step_chore_annual(user_input)

    async def async_step_chore_finalize(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Shared step to finalize chore creation or editing."""
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        members = storage.get_members()
        
        # Handle area_id "none" conversion
        area_id = self._chore_data.get("area_id")
        if area_id == "none":
            area_id = None
        
        if self._chore_mode == "add":
            # Create unique ID for chore (slugified name + timestamp)
            import time
            chore_name = self._chore_data["chore_name"]
            chore_id = f"{chore_name.lower().replace(' ', '_')}_{int(time.time())}"
            
            # Create the chore with all collected data
            chore = Chore(
                name=chore_name,
                points=self._chore_data.get("points", 0),
                assignment_mode=self._chore_data.get("assignment_mode", ASSIGN_MODE_ALWAYS),
                possible_assignees=self._chore_data.get("assignees", list(members.keys())),
                recurrence_pattern=self._chore_data.get(CONF_RECURRENCE_PATTERN, FREQUENCY_DAILY),
                recurrence_interval=self._chore_data.get(CONF_RECURRENCE_INTERVAL, 1),
                recurrence_day_of_month=self._chore_data.get(CONF_RECURRENCE_DAY_OF_MONTH),
                recurrence_week_of_month=self._chore_data.get(CONF_RECURRENCE_WEEK_OF_MONTH),
                recurrence_specific_weekdays=self._chore_data.get(CONF_RECURRENCE_SPECIFIC_WEEKDAYS, []),
                recurrence_annual_month=self._chore_data.get(CONF_RECURRENCE_ANNUAL_MONTH),
                recurrence_annual_day=self._chore_data.get(CONF_RECURRENCE_ANNUAL_DAY),
                area_id=area_id,
            )
            
            # Assign initial member if needed
            assignees = self._chore_data.get("assignees", [])
            assignment_mode = self._chore_data.get("assignment_mode", ASSIGN_MODE_ALWAYS)
            if assignment_mode == ASSIGN_MODE_ALWAYS and assignees:
                chore.assigned_to = assignees[0]
            elif assignment_mode == ASSIGN_MODE_ROTATE and assignees:
                chore.assigned_to = assignees[0]
            elif assignment_mode == ASSIGN_MODE_RANDOM and assignees:
                import random
                chore.assigned_to = random.choice(assignees)
            
            # Set the first due date to today
            from datetime import date
            chore.next_due = date.today().isoformat()
            
            # Add to storage
            storage.add_chore(chore_id, chore)
            
        else:  # edit mode
            chore_id = self._selected_chore
            chore = storage.get_chore(chore_id)
            
            if not chore:
                return self.async_abort(reason="chore_not_found")
            
            # Update the chore with all collected data
            chore.name = self._chore_data["chore_name"]
            chore.points = self._chore_data.get("points", 10)
            chore.area_id = area_id
            chore.assignment_mode = self._chore_data.get("assignment_mode", ASSIGN_MODE_ALWAYS)
            chore.possible_assignees = self._chore_data.get("assignees", [])
            chore.recurrence_pattern = self._chore_data.get(CONF_RECURRENCE_PATTERN, FREQUENCY_DAILY)
            chore.recurrence_interval = self._chore_data.get(CONF_RECURRENCE_INTERVAL, 1)
            chore.recurrence_day_of_month = self._chore_data.get(CONF_RECURRENCE_DAY_OF_MONTH)
            chore.recurrence_week_of_month = self._chore_data.get(CONF_RECURRENCE_WEEK_OF_MONTH)
            chore.recurrence_specific_weekdays = self._chore_data.get(CONF_RECURRENCE_SPECIFIC_WEEKDAYS, [])
            chore.recurrence_annual_month = self._chore_data.get(CONF_RECURRENCE_ANNUAL_MONTH)
            chore.recurrence_annual_day = self._chore_data.get(CONF_RECURRENCE_ANNUAL_DAY)
            
            # Update storage
            storage.update_chore(chore_id, chore)
            
            # Update device with new name and area if changed
            device_reg = dr.async_get(self.hass)
            device = device_reg.async_get_device(
                identifiers={(DOMAIN, f"chore_{chore_id}")}
            )
            if device:
                device_reg.async_update_device(
                    device.id,
                    name=chore.name,
                    area_id=area_id,
                )
        
        # Save storage
        await storage.async_save()
        
        # Clear temporary data
        self._chore_data = {}
        self._selected_chore = None
        
        # Reload entry to create/update device and entities
        await self.hass.config_entries.async_reload(self.config_entry.entry_id)
        
        return self.async_create_entry(title="", data={})

    async def async_step_edit_chore(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Select a chore to edit."""
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        chores = storage.get_chores()
        
        if not chores:
            return self.async_abort(reason="no_chores")
        
        if user_input is not None:
            self._selected_chore = user_input.get("chore")
            self._chore_mode = "edit"
            
            # Load chore data into _chore_data for editing
            chore = storage.get_chore(self._selected_chore)
            if chore:
                self._chore_data = {
                    "chore_name": chore.name,
                    "points": chore.points,
                    "area_id": chore.area_id or "none",
                    "assignment_mode": chore.assignment_mode,
                    "assignees": chore.possible_assignees,
                    CONF_RECURRENCE_PATTERN: chore.recurrence_pattern,
                    CONF_RECURRENCE_INTERVAL: chore.recurrence_interval,
                    CONF_RECURRENCE_DAY_OF_MONTH: chore.recurrence_day_of_month,
                    CONF_RECURRENCE_WEEK_OF_MONTH: chore.recurrence_week_of_month,
                    CONF_RECURRENCE_SPECIFIC_WEEKDAYS: chore.recurrence_specific_weekdays,
                    CONF_RECURRENCE_ANNUAL_MONTH: chore.recurrence_annual_month,
                    CONF_RECURRENCE_ANNUAL_DAY: chore.recurrence_annual_day,
                }
                # Move to basic info editing using shared step
                return await self.async_step_chore_basic()
        
        # Create chore choices with chore names as display
        chore_choices = {chore_id: chore.name for chore_id, chore in chores.items()}
        
        schema = vol.Schema({
            vol.Required("chore"): vol.In(chore_choices),
        })
        
        return self.async_show_form(
            step_id="edit_chore",
            data_schema=schema,
        )

    async def async_step_edit_chore_basic(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Edit chore - basic info."""
        return await self.async_step_chore_basic(user_input)

    async def async_step_edit_chore_assignees(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Edit chore - assignees."""
        return await self.async_step_chore_assignees(user_input)

    async def async_step_edit_chore_recurrence(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Edit chore - recurrence."""
        return await self.async_step_chore_recurrence(user_input)

    async def async_step_edit_chore_interval(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Edit chore - interval."""
        return await self.async_step_chore_interval(user_input)

    async def async_step_edit_chore_monthly_day(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Edit chore - monthly day."""
        return await self.async_step_chore_monthly_day(user_input)

    async def async_step_edit_chore_monthly_weekday(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Edit chore - monthly weekday."""
        return await self.async_step_chore_monthly_weekday(user_input)

    async def async_step_edit_chore_specific_days(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Edit chore - specific days."""
        return await self.async_step_chore_specific_days(user_input)

    async def async_step_edit_chore_annual(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Edit chore - annual."""
        return await self.async_step_chore_annual(user_input)

    async def async_step_delete_chore(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Delete a chore."""
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        chores = storage.get_chores()
        
        if not chores:
            return self.async_abort(reason="no_chores")
        
        if user_input is not None:
            chore_id = user_input.get("chore")
            chore = storage.get_chore(chore_id)
            
            if chore:
                # Remove chore from storage
                storage.delete_chore(chore_id)
                await storage.async_save()
                
                # Remove device
                device_reg = dr.async_get(self.hass)
                device = device_reg.async_get_device(
                    identifiers={(DOMAIN, f"chore_{chore_id}")}
                )
                if device:
                    device_reg.async_remove_device(device.id)
                
                # Refresh coordinator
                coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]["coordinator"]
                await coordinator.async_refresh_data()
            
            return self.async_create_entry(title="", data={})
        
        # Create chore choices with chore names as display
        chore_choices = {chore_id: chore.name for chore_id, chore in chores.items()}
        
        schema = vol.Schema({
            vol.Required("chore"): vol.In(chore_choices),
        })
        
        return self.async_show_form(
            step_id="delete_chore",
            data_schema=schema,
        )

    async def async_step_delete_all_chores(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Delete all chores with confirmation."""
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        chores = storage.get_chores()
        
        if not chores:
            return self.async_abort(reason="no_chores")
        
        if user_input is not None:
            if user_input.get("confirm"):
                device_reg = dr.async_get(self.hass)
                
                # Delete all chores
                for chore_id in list(chores.keys()):
                    # Remove device
                    device = device_reg.async_get_device(
                        identifiers={(DOMAIN, f"chore_{chore_id}")}
                    )
                    if device:
                        device_reg.async_remove_device(device.id)
                    
                    # Remove from storage
                    storage.delete_chore(chore_id)
                
                await storage.async_save()
                
                # Refresh coordinator
                coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]["coordinator"]
                await coordinator.async_refresh_data()
            
            return self.async_create_entry(title="", data={})
        
        # Show confirmation dialog
        schema = vol.Schema({
            vol.Required("confirm", default=False): bool,
        })
        
        return self.async_show_form(
            step_id="delete_all_chores",
            data_schema=schema,
            description_placeholders={
                "chore_count": str(len(chores)),
            },
        )

    async def async_step_delete_member(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Delete a household member - Step 1: Select member to delete."""
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        members = storage.get_members()
        
        if not members:
            return self.async_abort(reason="no_members")
        
        if len(members) == 1:
            return self.async_abort(reason="cannot_delete_last_member")
        
        if user_input is not None:
            self._selected_member = user_input.get("member")
            
            # Check if member has any assigned chores
            chores = storage.get_chores()
            has_assigned_chores = any(
                chore.assigned_to == self._selected_member or 
                self._selected_member in chore.possible_assignees
                for chore in chores.values()
            )
            
            if has_assigned_chores:
                # Need to reassign chores
                return await self.async_step_delete_member_reassign()
            else:
                # No chores to reassign, delete directly
                return await self._finalize_delete_member(None)
        
        schema = vol.Schema({
            vol.Required("member"): vol.In(list(members.keys())),
        })
        
        return self.async_show_form(
            step_id="delete_member",
            data_schema=schema,
        )

    async def async_step_delete_member_reassign(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Delete a household member - Step 2: Reassign their chores."""
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        members = storage.get_members()
        
        # Get remaining members (excluding the one being deleted)
        remaining_members = {k: v for k, v in members.items() if k != self._selected_member}
        
        if user_input is not None:
            reassign_to = user_input.get("reassign_to")
            return await self._finalize_delete_member(reassign_to)
        
        schema = vol.Schema({
            vol.Required("reassign_to"): vol.In(list(remaining_members.keys())),
        })
        
        return self.async_show_form(
            step_id="delete_member_reassign",
            data_schema=schema,
            description_placeholders={
                "member_name": self._selected_member,
            },
        )

    async def _finalize_delete_member(self, reassign_to: str | None) -> FlowResult:
        """Finalize member deletion and reassign chores if needed."""
        storage = self.hass.data[DOMAIN][self.config_entry.entry_id]["storage"]
        member_to_delete = self._selected_member
        
        # Update all chores
        chores = storage.get_chores()
        for chore_id, chore in chores.items():
            modified = False
            
            # If chore is assigned to deleted member, reassign it
            if chore.assigned_to == member_to_delete:
                chore.assigned_to = reassign_to
                modified = True
            
            # Remove deleted member from possible_assignees
            if member_to_delete in chore.possible_assignees:
                chore.possible_assignees.remove(member_to_delete)
                modified = True
            
            # Add reassign_to member to possible_assignees if not already there
            if reassign_to and reassign_to not in chore.possible_assignees:
                chore.possible_assignees.append(reassign_to)
                modified = True
            
            # If only one possible assignee remains, switch to "always" mode
            if len(chore.possible_assignees) == 1 and chore.assignment_mode in [ASSIGN_MODE_ROTATE, ASSIGN_MODE_RANDOM]:
                chore.assignment_mode = ASSIGN_MODE_ALWAYS
                chore.assigned_to = chore.possible_assignees[0]
                modified = True
            
            if modified:
                storage.update_chore(chore_id, chore)
        
        # Remove member from storage
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
        
        # Clear selected member
        self._selected_member = None
        
        return self.async_create_entry(title="", data={})
