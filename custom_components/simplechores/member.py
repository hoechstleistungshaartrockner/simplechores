"""Member class for SimpleChores."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict

from .const import (
    TRACKER_PERIOD_TODAY,
    TRACKER_PERIOD_THIS_WEEK,
    TRACKER_PERIOD_THIS_MONTH,
    TRACKER_PERIOD_THIS_YEAR,
    MEMBER_FIELD_NAME,
    MEMBER_FIELD_POINTS_TODAY,
    MEMBER_FIELD_POINTS_THIS_WEEK,
    MEMBER_FIELD_POINTS_THIS_MONTH,
    MEMBER_FIELD_POINTS_THIS_YEAR,
    MEMBER_FIELD_CHORES_TODAY,
    MEMBER_FIELD_CHORES_THIS_WEEK,
    MEMBER_FIELD_CHORES_THIS_MONTH,
    MEMBER_FIELD_CHORES_THIS_YEAR,
    MEMBER_FIELD_PENDING_CHORES,
    MEMBER_FIELD_OVERDUE_CHORES,
    MEMBER_FIELD_PREFIX_POINTS,
    MEMBER_FIELD_PREFIX_CHORES,
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
        data.pop(MEMBER_FIELD_NAME, None)
        return data
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, int]) -> Member:
        """Create a Member instance from a dictionary."""
        return cls(
            name=name,
            points_earned_today=data.get(MEMBER_FIELD_POINTS_TODAY, 0),
            points_earned_this_week=data.get(MEMBER_FIELD_POINTS_THIS_WEEK, 0),
            points_earned_this_month=data.get(MEMBER_FIELD_POINTS_THIS_MONTH, 0),
            points_earned_this_year=data.get(MEMBER_FIELD_POINTS_THIS_YEAR, 0),
            chores_completed_today=data.get(MEMBER_FIELD_CHORES_TODAY, 0),
            chores_completed_this_week=data.get(MEMBER_FIELD_CHORES_THIS_WEEK, 0),
            chores_completed_this_month=data.get(MEMBER_FIELD_CHORES_THIS_MONTH, 0),
            chores_completed_this_year=data.get(MEMBER_FIELD_CHORES_THIS_YEAR, 0),
            n_chores_pending=data.get(MEMBER_FIELD_PENDING_CHORES, 0),
            n_chores_overdue=data.get(MEMBER_FIELD_OVERDUE_CHORES, 0),
        )
        
    # getting and setting points
    
    def get_points(self, period: str) -> int:
        """Get points for a specific period."""
        return getattr(self, f"{MEMBER_FIELD_PREFIX_POINTS}_{period}", 0)
    
    def set_points(self, period: str, points: int):
        """Set points for a specific period."""
        setattr(self, f"{MEMBER_FIELD_PREFIX_POINTS}_{period}", points)
    
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
        return getattr(self, f"{MEMBER_FIELD_PREFIX_CHORES}_{period}", 0)
    
    def set_chores_completed(self, period: str, chores_completed: int):
        """Set chores completed for a specific period."""
        setattr(self, f"{MEMBER_FIELD_PREFIX_CHORES}_{period}", chores_completed)
        
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
        