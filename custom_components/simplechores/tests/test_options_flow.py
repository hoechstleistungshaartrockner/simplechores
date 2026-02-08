"""Test SimpleChores options flow."""
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr

from custom_components.simplechores.const import DOMAIN


async def test_options_flow_init(hass: HomeAssistant, mock_config_entry) -> None:
    """Test options flow initialization."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "init"
    assert "create_member" in result["menu_options"]
    assert "update_member" in result["menu_options"]
    assert "delete_member" in result["menu_options"]


async def test_create_member(hass: HomeAssistant, mock_config_entry) -> None:
    """Test creating a new member."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    
    # Select create member
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "create_member"}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "create_member"

    # Create new member
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"member_name": "Charlie"}
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY

    # Verify member was added
    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    members = storage.get_members()
    assert "Charlie" in members


async def test_create_member_duplicate_name(hass: HomeAssistant, mock_config_entry) -> None:
    """Test creating a member with duplicate name."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "create_member"}
    )

    # Try to create member with existing name
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"member_name": "Alice"}
    )

    assert result["type"] == FlowResultType.FORM
    assert "member_exists" in result["errors"]["member_name"]


async def test_update_member_name(hass: HomeAssistant, mock_config_entry) -> None:
    """Test updating a member's name."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    
    # Select update member
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "update_member"}
    )

    # Select Alice
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"member": "Alice"}
    )

    assert result["step_id"] == "update_member_details"

    # Change name to Alicia
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "new_name": "Alicia",
            "points_action": "none",
        }
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY

    # Verify name was changed
    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    members = storage.get_members()
    assert "Alicia" in members
    assert "Alice" not in members


async def test_update_member_reset_points(hass: HomeAssistant, mock_config_entry) -> None:
    """Test resetting a member's points."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Set some points first
    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    members = storage.get_members()
    members["Alice"]["points_daily"] = 100
    members["Alice"]["points_weekly"] = 200

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "update_member"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"member": "Alice"}
    )
    
    # Reset points
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "new_name": "Alice",
            "points_action": "reset",
        }
    )

    # Verify points were reset
    assert members["Alice"]["points_daily"] == 0
    assert members["Alice"]["points_weekly"] == 0


async def test_delete_member(hass: HomeAssistant, mock_config_entry) -> None:
    """Test deleting a member."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    
    # Select delete member
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "delete_member"}
    )

    # Delete Bob
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"member": "Bob"}
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY

    # Verify member was deleted
    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    members = storage.get_members()
    assert "Bob" not in members
    assert "Alice" in members  # Others should remain
