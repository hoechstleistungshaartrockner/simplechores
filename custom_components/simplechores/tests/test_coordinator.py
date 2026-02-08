"""Test SimpleChores coordinator."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from homeassistant.core import HomeAssistant

from custom_components.simplechores.const import (
    DOMAIN,
    PERIOD_DAILY,
    PERIOD_WEEKLY,
    PERIOD_MONTHLY,
    PERIOD_YEARLY,
)


async def test_coordinator_initialization(hass: HomeAssistant, mock_config_entry) -> None:
    """Test coordinator initialization."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    assert coordinator is not None
    assert coordinator.data is not None


async def test_daily_reset(hass: HomeAssistant, mock_config_entry) -> None:
    """Test daily counter reset."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    
    # Set some daily points
    members = storage.get_members()
    members["Alice"]["points_daily"] = 50
    members["Alice"]["chores_daily"] = 3
    
    # Mock the current date to be tomorrow
    tomorrow = datetime.now() + timedelta(days=1)
    with patch("custom_components.simplechores.coordinator.datetime") as mock_datetime:
        mock_datetime.now.return_value = tomorrow
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        # Trigger coordinator update
        await coordinator.async_refresh()
        await hass.async_block_till_done()
    
    # Check that daily counters were reset
    assert members["Alice"]["points_daily"] == 0
    assert members["Alice"]["chores_daily"] == 0


async def test_weekly_reset(hass: HomeAssistant, mock_config_entry) -> None:
    """Test weekly counter reset."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    
    # Set some weekly points
    members = storage.get_members()
    members["Bob"]["points_weekly"] = 100
    
    # Mock the current date to be next week
    next_week = datetime.now() + timedelta(days=7)
    with patch("custom_components.simplechores.coordinator.datetime") as mock_datetime:
        mock_datetime.now.return_value = next_week
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        # Trigger coordinator update
        await coordinator.async_refresh()
        await hass.async_block_till_done()
    
    # Check that weekly counters were reset
    assert members["Bob"]["points_weekly"] == 0


async def test_monthly_reset(hass: HomeAssistant, mock_config_entry) -> None:
    """Test monthly counter reset."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    
    # Set some monthly points
    members = storage.get_members()
    members["Alice"]["points_monthly"] = 500
    
    # Set last reset to last month
    storage.set_last_reset(PERIOD_MONTHLY, "2026-01-01")
    
    # Mock the current date to be in February
    february = datetime(2026, 2, 1)
    with patch("custom_components.simplechores.coordinator.datetime") as mock_datetime:
        mock_datetime.now.return_value = february
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        # Trigger coordinator update
        await coordinator.async_refresh()
        await hass.async_block_till_done()
    
    # Check that monthly counters were reset
    assert members["Alice"]["points_monthly"] == 0


async def test_no_reset_same_day(hass: HomeAssistant, mock_config_entry) -> None:
    """Test that counters are not reset on the same day."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    storage = hass.data[DOMAIN][mock_config_entry.entry_id]["storage"]
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    
    # Set some points
    members = storage.get_members()
    members["Alice"]["points_daily"] = 50
    
    # Set last reset to today
    today = datetime.now().date().isoformat()
    storage.set_last_reset(PERIOD_DAILY, today)
    
    # Trigger coordinator update
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    
    # Check that daily counters were NOT reset
    assert members["Alice"]["points_daily"] == 50


async def test_manual_refresh(hass: HomeAssistant, mock_config_entry) -> None:
    """Test manual coordinator refresh."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    
    # Manually trigger refresh
    await coordinator.async_refresh_data()
    await hass.async_block_till_done()
    
    # Should complete without error
    assert coordinator.last_update_success
