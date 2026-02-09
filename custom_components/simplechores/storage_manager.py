# storage_manager.py
from __future__ import annotations

from typing import Dict

from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_VERSION, DATA_CHORES, DATA_MEMBERS, STORAGE_KEY_PREFIX_LAST_RESET
from .member import Member
from .chore import Chore


class SimpleChoresStorageManager:
    """Handle persistent storage for SimpleChores."""

    def __init__(self, hass):
        self.hass = hass
        self.store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.json")
        self.data = {
            DATA_CHORES: {},
            DATA_MEMBERS: {},
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
    def get_chores(self) -> Dict[str, Chore]:
        """Get all chores as Chore objects."""
        chores_data = self.data.get(DATA_CHORES, {})
        return {
            chore_id: Chore.from_dict(data)
            for chore_id, data in chores_data.items()
        }
    
    def get_chore(self, chore_id: str) -> Chore | None:
        """Get a specific chore by ID."""
        chores_data = self.data.get(DATA_CHORES, {})
        if chore_id in chores_data:
            return Chore.from_dict(chores_data[chore_id])
        return None
    
    def add_chore(self, chore_id: str, chore: Chore) -> None:
        """Add a new chore."""
        self.data[DATA_CHORES][chore_id] = chore.to_dict()
    
    def update_chore(self, chore_id: str, chore: Chore) -> None:
        """Update an existing chore."""
        self.data[DATA_CHORES][chore_id] = chore.to_dict()
    
    def delete_chore(self, chore_id: str) -> bool:
        """Delete a chore. Returns True if deleted, False if not found."""
        if chore_id in self.data.get(DATA_CHORES, {}):
            del self.data[DATA_CHORES][chore_id]
            return True
        return False
    
    def chore_exists(self, chore_id: str) -> bool:
        """Check if a chore exists."""
        return chore_id in self.data.get(DATA_CHORES, {})

    def get_members(self) -> Dict[str, Member]:
        """Get all members as Member objects."""
        members_data = self.data.get(DATA_MEMBERS, {})
        return {
            name: Member.from_dict(name, data)
            for name, data in members_data.items()
        }
    
    def get_member(self, name: str) -> Member | None:
        """Get a specific member by name."""
        members_data = self.data.get(DATA_MEMBERS, {})
        if name in members_data:
            return Member.from_dict(name, members_data[name])
        return None
    
    def add_member(self, member: Member) -> None:
        """Add a new member."""
        self.data[DATA_MEMBERS][member.name] = member.to_dict()
    
    def update_member(self, member: Member) -> None:
        """Update an existing member."""
        self.data[DATA_MEMBERS][member.name] = member.to_dict()
    
    def delete_member(self, name: str) -> bool:
        """Delete a member. Returns True if deleted, False if not found."""
        if name in self.data.get(DATA_MEMBERS, {}):
            del self.data[DATA_MEMBERS][name]
            return True
        return False
    
    def member_exists(self, name: str) -> bool:
        """Check if a member exists."""
        return name in self.data.get(DATA_MEMBERS, {})

    def reset_period_counters(self, period: str):
        """Reset counters for all members for a given period."""
        members_data = self.data.get(DATA_MEMBERS, {})
        for name, data in members_data.items():
            member = Member.from_dict(name, data)
            member.reset_points(period)
            member.reset_chores_completed(period)
            self.data[DATA_MEMBERS][name] = member.to_dict()

    def get_last_reset(self, period: str) -> str | None:
        """Get the last reset timestamp for a period."""
        return self.data.get(f"{STORAGE_KEY_PREFIX_LAST_RESET}_{period}")

    def set_last_reset(self, period: str, timestamp: str):
        """Set the last reset timestamp for a period."""
        self.data[f"{STORAGE_KEY_PREFIX_LAST_RESET}_{period}"] = timestamp
