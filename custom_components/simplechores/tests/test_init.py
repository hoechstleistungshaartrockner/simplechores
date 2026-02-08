"""Test SimpleChores integration setup."""
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from custom_components.simplechores.const import (
    DOMAIN,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL_MEMBER,
)


async def test_setup_entry(hass: HomeAssistant, mock_config_entry) -> None:
    """Test setting up an entry."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that data is stored
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]
    assert "storage" in hass.data[DOMAIN][mock_config_entry.entry_id]
    assert "coordinator" in hass.data[DOMAIN][mock_config_entry.entry_id]


async def test_devices_created(hass: HomeAssistant, mock_config_entry) -> None:
    """Test that devices are created for members."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    device_reg = dr.async_get(hass)
    
    # Check Alice's device
    alice_device = device_reg.async_get_device(
        identifiers={(DOMAIN, "member_Alice")}
    )
    assert alice_device is not None
    assert alice_device.name == "Alice"
    assert alice_device.manufacturer == DEVICE_MANUFACTURER
    assert alice_device.model == DEVICE_MODEL_MEMBER

    # Check Bob's device
    bob_device = device_reg.async_get_device(
        identifiers={(DOMAIN, "member_Bob")}
    )
    assert bob_device is not None
    assert bob_device.name == "Bob"


async def test_services_registered(hass: HomeAssistant, mock_config_entry) -> None:
    """Test that services are registered."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check services are registered
    assert hass.services.has_service(DOMAIN, "update_points")
    assert hass.services.has_service(DOMAIN, "reset_points")


async def test_unload_entry(hass: HomeAssistant, mock_config_entry) -> None:
    """Test unloading an entry."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Unload entry
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check data is removed
    assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})

    # Services should be unloaded
    assert not hass.services.has_service(DOMAIN, "update_points")
    assert not hass.services.has_service(DOMAIN, "reset_points")
