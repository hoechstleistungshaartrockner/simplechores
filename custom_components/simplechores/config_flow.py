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
)


class SimpleChoresConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SimpleChores."""

    VERSION = 1

    def __init__(self):
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Handle the initial step."""

        # Enforce single instance
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            self._data[CONF_ENABLE_POINTS_SYSTEM] = user_input.get(
                CONF_ENABLE_POINTS_SYSTEM, DEFAULT_ENABLE_POINTS_SYSTEM
            )
            self._data[CONF_POINTS_LABEL] = user_input.get(
                CONF_POINTS_LABEL, DEFAULT_POINTS_LABEL
            )
            self._data[CONF_N_MEMBERS] = user_input.get(
                CONF_N_MEMBERS, DEFAULT_N_MEMBERS
            )

            return self.async_create_entry(title="SimpleChores", data=self._data)

        form_schema = vol.Schema({
            vol.Optional(CONF_ENABLE_POINTS_SYSTEM, default=DEFAULT_ENABLE_POINTS_SYSTEM): cv.boolean,
            vol.Optional(CONF_POINTS_LABEL, default=DEFAULT_POINTS_LABEL): cv.string,
            vol.Optional(CONF_N_MEMBERS, default=DEFAULT_N_MEMBERS): cv.positive_int,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=form_schema,
        )
