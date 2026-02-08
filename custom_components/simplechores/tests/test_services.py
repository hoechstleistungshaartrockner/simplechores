"""Test SimpleChores services."""
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from custom_components.simplechores.const import (
    DOMAIN,
    SERVICE_UPDATE_POINTS,
    SERVICE_RESET_POINTS,
    PERIOD_DAILY,
    PERIOD_WEEKLY,
)


async def test_update_points_service(hass: HomeAssistant, mock_config_entry) -> None:
    """Test the update_points service."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Call update_points service
    await hass.services.async_call(
        DOMAIN,
        SERVICE_UPDATE_POINTS,
        {"member": "Alice", "offset": 50},
        blocking=True,
    )

    # Check that points were updated
    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    members = storage.get_members()
    assert members["Alice"]["points_daily"] == 50
    assert members["Alice"]["points_weekly"] == 50
    assert members["Alice"]["points_monthly"] == 50
    assert members["Alice"]["points_yearly"] == 50


async def test_update_points_specific_periods(hass: HomeAssistant, mock_config_entry) -> None:
    """Test update_points with specific periods."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Call update_points service for only daily and weekly
    await hass.services.async_call(
        DOMAIN,
        SERVICE_UPDATE_POINTS,
        {"member": "Bob", "offset": 25, "periods": [PERIOD_DAILY, PERIOD_WEEKLY]},
        blocking=True,
    )

    # Check that only specified periods were updated
    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    members = storage.get_members()
    assert members["Bob"]["points_daily"] == 25
    assert members["Bob"]["points_weekly"] == 25
    assert members["Bob"]["points_monthly"] == 0
    assert members["Bob"]["points_yearly"] == 0


async def test_update_points_negative_offset(hass: HomeAssistant, mock_config_entry) -> None:
    """Test update_points with negative offset."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Set initial points
    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    members = storage.get_members()
    members["Alice"]["points_daily"] = 100

    # Call update_points service with negative offset
    await hass.services.async_call(
        DOMAIN,
        SERVICE_UPDATE_POINTS,
        {"member": "Alice", "offset": -30},
        blocking=True,
    )

    # Check that points were reduced
    assert members["Alice"]["points_daily"] == 70


async def test_reset_points_service(hass: HomeAssistant, mock_config_entry) -> None:
    """Test the reset_points service."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Set some points
    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    members = storage.get_members()
    members["Alice"]["points_daily"] = 100
    members["Alice"]["points_weekly"] = 200
    members["Alice"]["points_monthly"] = 300
    members["Alice"]["points_yearly"] = 400

    # Call reset_points service
    await hass.services.async_call(
        DOMAIN,
        SERVICE_RESET_POINTS,
        {"member": "Alice"},
        blocking=True,
    )

    # Check that all points were reset
    assert members["Alice"]["points_daily"] == 0
    assert members["Alice"]["points_weekly"] == 0
    assert members["Alice"]["points_monthly"] == 0
    assert members["Alice"]["points_yearly"] == 0


async def test_reset_points_specific_periods(hass: HomeAssistant, mock_config_entry) -> None:
    """Test reset_points with specific periods."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Set some points
    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    members = storage.get_members()
    members["Bob"]["points_daily"] = 100
    members["Bob"]["points_weekly"] = 200
    members["Bob"]["points_monthly"] = 300

    # Call reset_points service for only daily
    await hass.services.async_call(
        DOMAIN,
        SERVICE_RESET_POINTS,
        {"member": "Bob", "periods": [PERIOD_DAILY]},
        blocking=True,
    )

    # Check that only daily was reset
    assert members["Bob"]["points_daily"] == 0
    assert members["Bob"]["points_weekly"] == 200
    assert members["Bob"]["points_monthly"] == 300


async def test_service_updates_sensors(hass: HomeAssistant, mock_config_entry) -> None:
    """Test that services trigger sensor updates."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Call update_points service
    await hass.services.async_call(
        DOMAIN,
        SERVICE_UPDATE_POINTS,
        {"member": "Alice", "offset": 75},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Check that sensor state was updated
    state = hass.states.get("sensor.alice_daily_points")
    assert state is not None
    assert state.state == "75"
