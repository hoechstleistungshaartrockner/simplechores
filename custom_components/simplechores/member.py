"""Member class for SimpleChores."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict

from .const import (
    TRACKER_PERIOD_DAILY,
    TRACKER_PERIOD_WEEKLY,
    TRACKER_PERIOD_MONTHLY,
    TRACKER_PERIOD_YEARLY,
)


@dataclass
class Member:
    """Represents a household member."""
    
    name: str
    points_earned_today: int = 0
    points_earned_this_week: int = 0
    points_earned_this_month: int = 0
    points_earned_this_year: int = 0
    chores_completed_today: int = 0
    chores_completed_this_week: int = 0
    chores_completed_this_month: int = 0
    chores_completed_this_year: int = 0
    n_chores_pending: int = 0
    n_chores_overdue: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        """Convert the Member dataclass to a dictionary."""
        data = asdict(self)
        # Remove the 'name' key since it's used as the dictionary key in storage
        data.pop("name", None)
        return data
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, int]) -> Member:
        """Create a Member instance from a dictionary."""
        return cls(
            name=name,
            points_earned_today=data.get("points_earned_today", 0),
            points_earned_this_week=data.get("points_earned_this_week", 0),
            points_earned_this_month=data.get("points_earned_this_month", 0),
            points_earned_this_year=data.get("points_earned_this_year", 0),
            chores_completed_today=data.get("chores_completed_today", 0),
            chores_completed_this_week=data.get("chores_completed_this_week", 0),
            chores_completed_this_month=data.get("chores_completed_this_month", 0),
            chores_completed_this_year=data.get("chores_completed_this_year", 0),
            n_chores_pending=data.get("n_chores_pending", 0),
            n_chores_overdue=data.get("n_chores_overdue", 0),
        )
        
    # getting and setting points
    
    def get_points(self, period: str) -> int:
        """Get points for a specific period."""
        # Map period name to attribute name
        period_map = {
            "daily": "today",
            "weekly": "this_week",
            "monthly": "this_month",
            "yearly": "this_year",
        }
        attr_period = period_map.get(period, period)
        return getattr(self, f"points_earned_{attr_period}", 0)
    
    def set_points(self, period: str, points: int):
        """Set points for a specific period."""
        # Map period name to attribute name
        period_map = {
            "daily": "today",
            "weekly": "this_week",
            "monthly": "this_month",
            "yearly": "this_year",
        }
        attr_period = period_map.get(period, period)
        setattr(self, f"points_earned_{attr_period}", points)
    
    def add_points(self, points: int):
        """Add points to all periods."""
        self.points_earned_today += points
        self.points_earned_this_week += points
        self.points_earned_this_month += points
        self.points_earned_this_year += points
        
    def reset_points(self, period: str):
        """Reset points for a specific period."""
        self.set_points(period, 0)
        
    def subtract_points(self, points: int):
        """Subtract points from all periods."""
        self.points_earned_today = max(0, self.points_earned_today - points)
        self.points_earned_this_week = max(0, self.points_earned_this_week - points)
        self.points_earned_this_month = max(0, self.points_earned_this_month - points)
        self.points_earned_this_year = max(0, self.points_earned_this_year - points)
        
    def reset_all_points(self):
        """Reset points for all periods."""
        self.points_earned_today = 0
        self.points_earned_this_week = 0
        self.points_earned_this_month = 0
        self.points_earned_this_year = 0
    
    # getting and setting chores completed
    
    def get_chores_completed(self, period: str) -> int:
        """Get chores completed for a specific period."""
        # Map period name to attribute name
        period_map = {
            "daily": "today",
            "weekly": "this_week",
            "monthly": "this_month",
            "yearly": "this_year",
        }
        attr_period = period_map.get(period, period)
        return getattr(self, f"chores_completed_{attr_period}", 0)
    
    def set_chores_completed(self, period: str, chores_completed: int):
        """Set chores completed for a specific period."""
        # Map period name to attribute name
        period_map = {
            "daily": "today",
            "weekly": "this_week",
            "monthly": "this_month",
            "yearly": "this_year",
        }
        attr_period = period_map.get(period, period)
        setattr(self, f"chores_completed_{attr_period}", chores_completed)
        
    def add_chore_completed(self):
        """Increment chores completed for all periods."""
        self.chores_completed_today += 1
        self.chores_completed_this_week += 1
        self.chores_completed_this_month += 1
        self.chores_completed_this_year += 1
        
    def reset_chores_completed(self, period: str):
        """Reset chores completed for a specific period."""
        self.set_chores_completed(period, 0)
    
    def reset_all_chores_completed(self):
        """Reset chores completed for all periods."""
        self.chores_completed_today = 0
        self.chores_completed_this_week = 0
        self.chores_completed_this_month = 0
        self.chores_completed_this_year = 0
        
    # pending and overdue chores 
    
    # to be implemented later.
        