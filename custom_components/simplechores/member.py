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
    DEFAULT_SORT_HIERARCHY,
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
    dashboard_filter: Dict[str, bool] = None
    dashboard_state_filter: Dict[str, bool] = None
    dashboard_sort_hierarchy: list[str] = None

    def __post_init__(self):
        """Initialize dashboard filter state if not provided."""
        if self.dashboard_filter is None:
            self.dashboard_filter = {}
        if self.dashboard_state_filter is None:
            self.dashboard_state_filter = {}
        if self.dashboard_sort_hierarchy is None:
            self.dashboard_sort_hierarchy = DEFAULT_SORT_HIERARCHY.copy()

    def to_dict(self) -> Dict:
        """Convert the Member dataclass to a dictionary."""
        data = asdict(self)
        # Remove the 'name' key since it's used as the dictionary key in storage
        data.pop(MEMBER_FIELD_NAME, None)
        return data

    @classmethod
    def from_dict(cls, name: str, data: Dict) -> Member:
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
            dashboard_filter=data.get("dashboard_filter", {}),
            dashboard_state_filter=data.get("dashboard_state_filter", {}),
            dashboard_sort_hierarchy=data.get(
                "dashboard_sort_hierarchy", DEFAULT_SORT_HIERARCHY.copy()
            ),
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

    # Dashboard filter helpers

    def set_dashboard_filter(self, other_user_name: str, enabled: bool):
        """Set the dashboard filter state for another user."""
        self.dashboard_filter[other_user_name] = enabled

    def get_dashboard_filter(self, other_user_name: str) -> bool:
        """Get the dashboard filter state for another user."""
        return self.dashboard_filter.get(other_user_name, False)

    def init_dashboard_filters(self, all_member_names: list[str]):
        """Initialize dashboard filters for all other members."""
        for member_name in all_member_names:
            if member_name != self.name and member_name not in self.dashboard_filter:
                self.dashboard_filter[member_name] = False

    def remove_dashboard_filter(self, other_user_name: str):
        """Remove dashboard filter for a user (when they're deleted)."""
        self.dashboard_filter.pop(other_user_name, None)

    def set_dashboard_state_filter(self, state: str, enabled: bool):
        """Set the dashboard filter state for a chore state."""
        self.dashboard_state_filter[state] = enabled

    def get_dashboard_state_filter(self, state: str) -> bool:
        """Get the dashboard filter state for a chore state."""
        return self.dashboard_state_filter.get(state, False)

    def init_dashboard_state_filters(self, state_names: list[str]):
        """Initialize dashboard state filters for all known chore states."""
        for state_name in state_names:
            if state_name not in self.dashboard_state_filter:
                self.dashboard_state_filter[state_name] = False

    def get_sort_priority(self, criterion: str) -> int | None:
        """Get the sort priority for a specific criterion."""
        if criterion in self.dashboard_sort_hierarchy:
            return self.dashboard_sort_hierarchy.index(criterion) + 1
        return None

    def set_sort_priority(self, criterion: str, level: int):
        """Set the sort priority for a criterion."""
        if criterion not in self.dashboard_sort_hierarchy:
            return
        if not (1 <= level <= len(self.dashboard_sort_hierarchy)):
            return

        current_index = self.dashboard_sort_hierarchy.index(criterion)
        if current_index == level - 1:
            return

        self.dashboard_sort_hierarchy.pop(current_index)
        self.dashboard_sort_hierarchy.insert(level - 1, criterion)

    def get_sort_hierarchy_level(self, level: int) -> str:
        """Get the sort option for a specific level (1-indexed)."""
        if 1 <= level <= len(self.dashboard_sort_hierarchy):
            return self.dashboard_sort_hierarchy[level - 1]
        return None

    def set_sort_hierarchy_level(self, level: int, sort_option: str):
        """Set the sort option for a specific level and rotate others to prevent duplicates."""
        if not (1 <= level <= len(self.dashboard_sort_hierarchy)):
            return

        # Find if this sort_option is already used elsewhere
        current_index = level - 1
        old_value = self.dashboard_sort_hierarchy[current_index]

        # If the value is the same, no change needed
        if old_value == sort_option:
            return

        # Set the new value at this level
        self.dashboard_sort_hierarchy[current_index] = sort_option

        # Find where the old value was and rotate values
        for i, val in enumerate(self.dashboard_sort_hierarchy):
            if i != current_index and val == sort_option:
                # Move this value to where we came from
                self.dashboard_sort_hierarchy[i] = old_value
                break

    # pending and overdue chores

    # to be implemented later.
