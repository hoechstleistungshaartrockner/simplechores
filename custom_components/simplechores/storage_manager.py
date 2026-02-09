# storage_manager.py
from __future__ import annotations

from typing import Dict

from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_VERSION
from .member import Member


class SimpleChoresStorageManager:
    """Handle persistent storage for SimpleChores."""

    def __init__(self, hass):
        self.hass = hass
        self.store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.json")
        self.data = {
            "chores": {},
            "members": {},
        }

    async def async_load(self):
        """Load stored data from disk."""
        stored = await self.store.async_load()
        if stored:
            self.data = stored

    async def async_save(self):
        """Persist current data to disk."""
        await self.store.async_save(self.data)

    # convenience helpers for later
    def get_chores(self):
        return self.data.get("chores", {})

    def get_members(self) -> Dict[str, Member]:
        """Get all members as Member objects."""
        members_data = self.data.get("members", {})
        return {
            name: Member.from_dict(name, data)
            for name, data in members_data.items()
        }
    
    def get_member(self, name: str) -> Member | None:
        """Get a specific member by name."""
        members_data = self.data.get("members", {})
        if name in members_data:
            return Member.from_dict(name, members_data[name])
        return None
    
    def add_member(self, member: Member) -> None:
        """Add a new member."""
        self.data["members"][member.name] = member.to_dict()
    
    def update_member(self, member: Member) -> None:
        """Update an existing member."""
        self.data["members"][member.name] = member.to_dict()
    
    def delete_member(self, name: str) -> bool:
        """Delete a member. Returns True if deleted, False if not found."""
        if name in self.data.get("members", {}):
            del self.data["members"][name]
            return True
        return False
    
    def member_exists(self, name: str) -> bool:
        """Check if a member exists."""
        return name in self.data.get("members", {})

    def reset_period_counters(self, period: str):
        """Reset counters for all members for a given period."""
        members_data = self.data.get("members", {})
        for name, data in members_data.items():
            member = Member.from_dict(name, data)
            member.reset_points(period)
            member.reset_chores_completed(period)
            self.data["members"][name] = member.to_dict()

    def get_last_reset(self, period: str) -> str | None:
        """Get the last reset timestamp for a period."""
        return self.data.get(f"last_reset_{period}")

    def set_last_reset(self, period: str, timestamp: str):
        """Set the last reset timestamp for a period."""
        self.data[f"last_reset_{period}"] = timestamp
