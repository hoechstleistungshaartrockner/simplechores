"""Test the SimpleChores config flow."""
import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.simplechores.const import (
    DOMAIN,
    CONF_ENABLE_POINTS_SYSTEM,
    CONF_POINTS_LABEL,
    CONF_N_MEMBERS,
    CONF_MEMBERS,
    DEFAULT_POINTS_LABEL,
)


async def test_user_step(hass: HomeAssistant) -> None:
    """Test the initial user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_point_system_step_enabled(hass: HomeAssistant) -> None:
    """Test point system step with points enabled."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Submit user step
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "point_system"

    # Enable points system
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENABLE_POINTS_SYSTEM: True}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "points_label"


async def test_point_system_step_disabled(hass: HomeAssistant) -> None:
    """Test point system step with points disabled."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Submit user step
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    # Disable points system
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENABLE_POINTS_SYSTEM: False}
    )

    # Should skip points label and go to members
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "n_members"


async def test_points_label_step(hass: HomeAssistant) -> None:
    """Test points label step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENABLE_POINTS_SYSTEM: True}
    )

    assert result["step_id"] == "points_label"

    # Set custom points label
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_POINTS_LABEL: "Stars"}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "n_members"


async def test_member_names_step(hass: HomeAssistant) -> None:
    """Test member names collection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Go through all steps
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENABLE_POINTS_SYSTEM: True}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_POINTS_LABEL: "Points"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_N_MEMBERS: 2}
    )

    # First member
    assert result["step_id"] == "member_names"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"member_name": "Alice"}
    )

    # Second member
    assert result["step_id"] == "member_names"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"member_name": "Bob"}
    )

    # Should create entry
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "SimpleChores"
    assert result["data"][CONF_MEMBERS] == ["Alice", "Bob"]
    assert result["data"][CONF_POINTS_LABEL] == "Points"


async def test_single_instance_allowed(hass: HomeAssistant) -> None:
    """Test that only one instance is allowed."""
    # Create first entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENABLE_POINTS_SYSTEM: False}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_N_MEMBERS: 1}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"member_name": "Test"}
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY

    # Try to create second instance
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
