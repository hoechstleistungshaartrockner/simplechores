"""Common fixtures for SimpleChores tests."""
import pytest
from unittest.mock import patch
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from custom_components.simplechores.const import (
    DOMAIN,
    CONF_ENABLE_POINTS_SYSTEM,
    CONF_POINTS_LABEL,
    CONF_N_MEMBERS,
    CONF_MEMBERS,
)

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_config_entry_data():
    """Return mock config entry data."""
    return {
        CONF_ENABLE_POINTS_SYSTEM: True,
        CONF_POINTS_LABEL: "Points",
        CONF_N_MEMBERS: 2,
        CONF_MEMBERS: ["Alice", "Bob"],
    }


@pytest.fixture
def mock_config_entry(mock_config_entry_data):
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="SimpleChores",
        data=mock_config_entry_data,
        unique_id=DOMAIN,
        entry_id="test_entry",
    )


@pytest.fixture
def mock_storage(hass: HomeAssistant):
    """Mock storage operations."""
    with patch(
        "custom_components.simplechores.storage_manager.Store"
    ) as mock_store:
        store_data = {
            "members": {},
            "chores": {},
        }
        
        async def async_load():
            return store_data
        
        async def async_save(data):
            store_data.update(data)
        
        mock_store.return_value.async_load = async_load
        mock_store.return_value.async_save = async_save
        
        yield mock_store
