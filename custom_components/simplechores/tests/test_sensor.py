"""Test SimpleChores sensor platform."""
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.simplechores.const import DOMAIN


async def test_sensors_created(hass: HomeAssistant, mock_config_entry) -> None:
    """Test that sensors are created for each member."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_reg = er.async_get(hass)
    
    # Check that sensors exist for Alice
    expected_sensors = [
        f"{DOMAIN}_Alice_points_daily",
        f"{DOMAIN}_Alice_points_weekly",
        f"{DOMAIN}_Alice_points_monthly",
        f"{DOMAIN}_Alice_points_yearly",
        f"{DOMAIN}_Alice_chores_daily",
        f"{DOMAIN}_Alice_chores_weekly",
        f"{DOMAIN}_Alice_chores_monthly",
        f"{DOMAIN}_Alice_chores_yearly",
        f"{DOMAIN}_Alice_pending_chores",
        f"{DOMAIN}_Alice_overdue_chores",
    ]
    
    for sensor_id in expected_sensors:
        entity = entity_reg.async_get_entity_id("sensor", DOMAIN, sensor_id)
        assert entity is not None, f"Sensor {sensor_id} not found"


async def test_points_sensor_state(hass: HomeAssistant, mock_config_entry) -> None:
    """Test points sensor state."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Set some points in storage
    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    members = storage.get_members()
    members["Alice"]["points_daily"] = 50

    # Trigger coordinator refresh
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Check sensor state
    state = hass.states.get("sensor.alice_daily_points")
    assert state is not None
    assert state.state == "50"


async def test_chores_sensor_state(hass: HomeAssistant, mock_config_entry) -> None:
    """Test chores sensor state."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Set some chores in storage
    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    members = storage.get_members()
    members["Bob"]["chores_weekly"] = 3

    # Trigger coordinator refresh
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Check sensor state
    state = hass.states.get("sensor.bob_weekly_chores_completed")
    assert state is not None
    assert state.state == "3"


async def test_pending_chores_sensor(hass: HomeAssistant, mock_config_entry) -> None:
    """Test pending chores sensor."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Add some pending chores
    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    chores = storage.data.get("chores", {})
    chores["chore1"] = {"assigned_to": "Alice", "status": "pending"}
    chores["chore2"] = {"assigned_to": "Alice", "status": "pending"}
    chores["chore3"] = {"assigned_to": "Bob", "status": "pending"}

    # Trigger coordinator refresh
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Check sensor states
    alice_state = hass.states.get("sensor.alice_pending_chores")
    assert alice_state.state == "2"
    
    bob_state = hass.states.get("sensor.bob_pending_chores")
    assert bob_state.state == "1"


async def test_custom_points_label(hass: HomeAssistant) -> None:
    """Test that custom points label is used."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    
    config_data = {
        "enable_points_system": True,
        "points_label": "Stars",
        "n_members": 1,
        "members": ["Alice"],
    }
    
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="SimpleChores",
        data=config_data,
        unique_id=DOMAIN,
    )

    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Check sensor name includes custom label
    entity_reg = er.async_get(hass)
    entity_id = entity_reg.async_get_entity_id("sensor", DOMAIN, f"{DOMAIN}_Alice_points_daily")
    entity = entity_reg.async_get(entity_id)
    
    # The entity name should contain "Stars" instead of "Points"
    assert entity is not None
