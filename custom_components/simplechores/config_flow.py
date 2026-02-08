"""Config flow for SimpleChores."""

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

from homeassistant.helpers import device_registry as dr


class SimpleChoresConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SimpleChores."""

    VERSION = 1

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._member_names: list[str] = [] # Temporary storage for member names during the flow

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return SimpleChoresOptionsFlow(config_entry)

    async def async_step_user(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Entry point - display welcome message."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        
        if user_input is not None:
            return await self.async_step_point_system()
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )

    async def async_step_point_system(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Step 1: Ask if points system should be enabled."""
        
        if user_input is not None:
            # Store the points system preference
            self._data[CONF_ENABLE_POINTS_SYSTEM] = user_input.get(
                CONF_ENABLE_POINTS_SYSTEM, DEFAULT_ENABLE_POINTS_SYSTEM
            )
            
            # If points system is enabled, ask for points label
            if self._data[CONF_ENABLE_POINTS_SYSTEM]:
                return await self.async_step_points_label()
            else:
                # If disabled, use default and skip to members
                self._data[CONF_POINTS_LABEL] = DEFAULT_POINTS_LABEL
                return await self.async_step_n_members()
        
        schema = vol.Schema({
            vol.Optional(CONF_ENABLE_POINTS_SYSTEM, default=DEFAULT_ENABLE_POINTS_SYSTEM): cv.boolean,
        })

        return self.async_show_form(
            step_id="point_system",
            data_schema=schema,
        )

    async def async_step_points_label(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Step 2: Ask for points label (only if points system is enabled)."""

        if user_input is not None:
            self._data[CONF_POINTS_LABEL] = user_input.get(
                CONF_POINTS_LABEL, DEFAULT_POINTS_LABEL
            )
            return await self.async_step_n_members()

        schema = vol.Schema({
            vol.Optional(CONF_POINTS_LABEL, default=DEFAULT_POINTS_LABEL): cv.string,
        })

        return self.async_show_form(
            step_id="points_label",
            data_schema=schema,
        )

    async def async_step_n_members(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Step 3: Ask for number of household members."""
        
        if user_input is not None:
            # Store the number of members
            self._data[CONF_N_MEMBERS] = user_input.get(
                CONF_N_MEMBERS, DEFAULT_N_MEMBERS
            )
            
            # Continue to ask for member names
            return await self.async_step_member_names()
        
        schema = vol.Schema({
            vol.Optional(CONF_N_MEMBERS, default=DEFAULT_N_MEMBERS): cv.positive_int,
        })

        return self.async_show_form(
            step_id="n_members",
            data_schema=schema,
        )

    async def async_step_member_names(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Step 4: Ask for names of each household member."""
        
        n_members = self._data[CONF_N_MEMBERS]
        current_member_index = len(self._member_names)
        
        if user_input is not None:
            # Store the member name
            member_name = user_input.get("member_name", f"Member {current_member_index + 1}")
            self._member_names.append(member_name)
            
            # If we have all member names, create the entry
            if len(self._member_names) >= n_members:
                self._data[CONF_MEMBERS] = self._member_names
                return self.async_create_entry(title="SimpleChores", data=self._data)
            
            # Otherwise, ask for the next member name
            return await self.async_step_member_names()
        
        # Show form for current member
        schema = vol.Schema({
            vol.Required("member_name", default=f"Member {current_member_index + 1}"): cv.string,
        })

        return self.async_show_form(
            step_id="member_names",
            data_schema=schema,
            description_placeholders={
                "member_number": str(current_member_index + 1),
                "total_members": str(n_members),
            },
        )

