"""Chore class for SimpleChores."""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Dict, List
from datetime import datetime, date, timedelta
import random

from .const import (
    CHORE_STATE_PENDING,
    CHORE_STATE_COMPLETED,
    CHORE_STATE_OVERDUE,
    ASSIGN_MODE_ALWAYS,
    ASSIGN_MODE_ROTATE,
    ASSIGN_MODE_RANDOM,
    FREQUENCY_NONE,
    FREQUENCY_DAILY,
    FREQUENCY_MONTHLY_DAY,
    FREQUENCY_MONTHLY_WEEKDAY,
    FREQUENCY_INTERVAL_DAYS,
    FREQUENCY_SPECIFIC_DAYS,
    FREQUENCY_ANNUAL,
)


@dataclass
class Chore:
    """Represents a household chore."""
    
    name: str
    points: int = 0
    status: str = CHORE_STATE_PENDING  # pending, completed, overdue
    last_completed: str | None = None  # ISO format date string
    due_date: str | None = None  # ISO format date string
    assignment_mode: str = ASSIGN_MODE_ALWAYS  # always, rotate, random
    assigned_to: str | None = None  # Current assignee member
    possible_assignees: List[str] = field(default_factory=list)  # List of members who can be assigned
    recurrence_pattern: str = FREQUENCY_DAILY
    recurrence_interval: int = 1 # e.g., every 1 day, every 2 days, etc.
    recurrence_day_of_month: int | None = None # for monthly recurrence on a specific day of the month (1-31, -1 for last day)
    recurrence_week_of_month: int | None = None # e.g. last wednesday of the month would be week_of_month=-1 and specific_weekday=2 (0=Monday, 1=Tuesday, etc.)
    recurrence_specific_weekdays: List[int] = field(default_factory=list) # for recurrence on specific weekdays (0=Monday, 1=Tuesday, etc.)
    recurrence_annual_month: int | None = None # for annual recurrence on a specific month (1-12)
    recurrence_annual_day: int | None = None # for annual recurrence on a specific day (1-365, -1 for last day of the year)
    area_id: str | None = None  # Home Assistant area ID for this chore
    
    def to_dict(self) -> Dict:
        """Convert the Chore dataclass to a dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> Chore:
        """Create a Chore instance from a dictionary."""
        return cls(
            name=data.get("name", ""),
            points=data.get("points", 0),
            status=data.get("status", CHORE_STATE_PENDING),
            last_completed=data.get("last_completed"),
            due_date=data.get("due_date"),
            assignment_mode=data.get("assignment_mode", ASSIGN_MODE_ALWAYS),
            assigned_to=data.get("assigned_to"),
            possible_assignees=data.get("possible_assignees", []),
            recurrence_pattern=data.get("recurrence_pattern", FREQUENCY_DAILY),
            recurrence_interval=data.get("recurrence_interval", 1),
            recurrence_day_of_month=data.get("recurrence_day_of_month"),
            recurrence_week_of_month=data.get("recurrence_week_of_month"),
            recurrence_specific_weekdays=data.get("recurrence_specific_weekdays", []),
            recurrence_annual_month=data.get("recurrence_annual_month"),
            recurrence_annual_day=data.get("recurrence_annual_day"),
            area_id=data.get("area_id"),
        )
    
    def mark_completed(self, member_name: str, storage=None, completion_date: date | None = None) -> None:
        """Mark the chore as completed by a specific member.
        
        Args:
            member_name: Name of the member completing the chore
            storage: Storage manager instance (optional, for updating member points/counters)
            completion_date: Date of completion (defaults to today)
        """
        if completion_date is None:
            completion_date = date.today()
        
        self.last_completed = completion_date.isoformat()
        
        # Calculate and set due date
        self.schedule_due_date(completion_date)
        
        # After scheduling, set status to completed (will be updated to pending/overdue by coordinator on the due date)
        self.status = CHORE_STATE_COMPLETED
        
        # Assign to next member
        self.assign()
        
        # Update member points and counters if storage is provided
        if storage is not None:
            member = storage.get_member(member_name)
            if member is not None:
                # Add points to member
                if self.points > 0:
                    member.add_points(self.points)
                
                # Increment chore completion counter
                member.add_chore_completed()
                
                # Update member in storage
                storage.update_member(member)
        
    def assign(self) -> None:
        """Assign the chore to a member based on the assignment mode.
        
        This is called after a chore is completed to determine who should do it next.
        """
        if self.assignment_mode == ASSIGN_MODE_ALWAYS:
            # Keep the same assignee
            return
        elif self.assignment_mode == ASSIGN_MODE_ROTATE:
            if self.assigned_to in self.possible_assignees:
                current_index = self.possible_assignees.index(self.assigned_to)
                next_index = (current_index + 1) % len(self.possible_assignees)
                self.assigned_to = self.possible_assignees[next_index]
            elif self.possible_assignees:
                self.assigned_to = self.possible_assignees[0]
        elif self.assignment_mode == ASSIGN_MODE_RANDOM:
            if self.possible_assignees:
                self.assigned_to = random.choice(self.possible_assignees)
                
    def mark_pending(self) -> None:
        """Mark the chore as pending."""
        self.status = CHORE_STATE_PENDING
        self.due_date = date.today().isoformat()
    
    def mark_overdue(self) -> None:
        """Mark the chore as overdue."""
        self.status = CHORE_STATE_OVERDUE
        self.due_date = (date.today() - timedelta(days=1)).isoformat()
    
    def assign_to_member(self, member_name: str) -> None:
        """Assign this chore to a specific member."""
        self.assigned_to = member_name
        
    def is_overdue(self, current_date: date | None = None) -> bool:
        """Check if the chore is overdue based on due_date."""
        if not self.due_date:
            return False
        
        if current_date is None:
            current_date = date.today()
        
        try:
            due_date = date.fromisoformat(self.due_date)
            return current_date > due_date and self.status != CHORE_STATE_COMPLETED
        except (ValueError, TypeError):
            return False
    
    def update_overdue_status(self, current_date: date | None = None) -> None:
        """Update the overdue status."""
        if self.is_overdue(current_date):
            self.mark_overdue()
        elif self.status == CHORE_STATE_OVERDUE:
            # Was overdue but isn't anymore
            self.mark_pending()

    def schedule_due_date(self, from_date: date | None = None) -> None:
        """Calculate and set the due date based on the recurrence pattern.
        
        Args:
            from_date: Date to calculate from (defaults to today)
        """
        if from_date is None:
            from_date = date.today()
        
        if self.recurrence_pattern == FREQUENCY_NONE:
            # No recurrence, leave due_date as None
            self.due_date = None
        elif self.recurrence_pattern == FREQUENCY_DAILY:
            self._schedule_daily(from_date)
        elif self.recurrence_pattern == FREQUENCY_INTERVAL_DAYS:
            self._schedule_interval_days(from_date)
        elif self.recurrence_pattern == FREQUENCY_SPECIFIC_DAYS:
            self._schedule_specific_days(from_date)
        elif self.recurrence_pattern == FREQUENCY_MONTHLY_DAY:
            self._schedule_monthly_day(from_date)
        elif self.recurrence_pattern == FREQUENCY_MONTHLY_WEEKDAY:
            self._schedule_monthly_weekday(from_date)
        elif self.recurrence_pattern == FREQUENCY_ANNUAL:
            self._schedule_annual(from_date)
        else:
            # Unknown pattern, default to daily
            self._schedule_daily(from_date)
    
    def _schedule_daily(self, from_date: date) -> None:
        """Schedule due date for daily recurrence."""
        due_date = from_date + timedelta(days=1)
        self.due_date = due_date.isoformat()
    
    def _schedule_interval_days(self, from_date: date) -> None:
        """Schedule due date based on interval from the last due date."""
        # Use last_completed or current due_date as base, or from_date if neither exists
        if self.last_completed:
            base_date = date.fromisoformat(self.last_completed)
        elif self.due_date:
            try:
                base_date = date.fromisoformat(self.due_date)
            except (ValueError, TypeError):
                base_date = from_date
        else:
            base_date = from_date
        
        due_date = base_date + timedelta(days=self.recurrence_interval)
        self.due_date = due_date.isoformat()
    
    def _schedule_specific_days(self, from_date: date) -> None:
        """Schedule due date on specific weekdays."""
        if not self.recurrence_specific_weekdays:
            # No weekdays specified, default to tomorrow
            self.due_date = (from_date + timedelta(days=1)).isoformat()
            return
        
        # Find the next occurrence of any specified weekday
        current_weekday = from_date.weekday()
        days_ahead = None
        
        # Check next 7 days to find the nearest matching weekday
        for i in range(1, 8):
            check_date = from_date + timedelta(days=i)
            if check_date.weekday() in self.recurrence_specific_weekdays:
                days_ahead = i
                break
        
        if days_ahead is not None:
            due_date = from_date + timedelta(days=days_ahead)
            self.due_date = due_date.isoformat()
        else:
            # Fallback: just use tomorrow
            self.due_date = (from_date + timedelta(days=1)).isoformat()
    
    def _schedule_monthly_day(self, from_date: date) -> None:
        """Schedule due date on a specific day of the month."""
        if self.recurrence_day_of_month is None:
            self.due_date = (from_date + timedelta(days=30)).isoformat()
            return
        
        # Start with next month
        if from_date.month == 12:
            next_month = 1
            next_year = from_date.year + 1
        else:
            next_month = from_date.month + 1
            next_year = from_date.year
        
        # Handle -1 for last day of month
        if self.recurrence_day_of_month == -1:
            # Get last day of next month
            if next_month == 12:
                last_day_next_month = date(next_year, next_month, 31)
            else:
                # Get first day of month after next, then subtract 1 day
                first_of_following_month = date(next_year, next_month + 1, 1) if next_month < 12 else date(next_year + 1, 1, 1)
                last_day_next_month = first_of_following_month - timedelta(days=1)
            due_date = last_day_next_month
        else:
            # Try to create date with specified day
            try:
                due_date = date(next_year, next_month, self.recurrence_day_of_month)
            except ValueError:
                # Day doesn't exist in this month (e.g., Feb 30), use last day of month
                if next_month == 12:
                    first_of_following_month = date(next_year + 1, 1, 1)
                else:
                    first_of_following_month = date(next_year, next_month + 1, 1)
                due_date = first_of_following_month - timedelta(days=1)
        
        self.due_date = due_date.isoformat()
    
    def _schedule_monthly_weekday(self, from_date: date) -> None:
        """Schedule due date on a specific weekday of a specific week in the month."""
        if self.recurrence_week_of_month is None or not self.recurrence_specific_weekdays:
            self.due_date = (from_date + timedelta(days=30)).isoformat()
            return
        
        target_weekday = self.recurrence_specific_weekdays[0]  # Use first weekday in list
        week_of_month = self.recurrence_week_of_month
        
        # Start with next month
        if from_date.month == 12:
            next_month = 1
            next_year = from_date.year + 1
        else:
            next_month = from_date.month + 1
            next_year = from_date.year
        
        # Find the target weekday occurrence in next month
        first_of_month = date(next_year, next_month, 1)
        first_weekday = first_of_month.weekday()
        
        # Calculate days until target weekday
        days_until_target = (target_weekday - first_weekday) % 7
        first_occurrence = first_of_month + timedelta(days=days_until_target)
        
        if week_of_month == -1:
            # Last occurrence - find all occurrences and pick the last
            current_occurrence = first_occurrence
            last_occurrence = first_occurrence
            
            while True:
                next_occurrence = current_occurrence + timedelta(weeks=1)
                if next_occurrence.month != next_month:
                    break
                last_occurrence = next_occurrence
                current_occurrence = next_occurrence
            
            due_date = last_occurrence
        else:
            # Specific week (1-4)
            due_date = first_occurrence + timedelta(weeks=week_of_month - 1)
        
        self.due_date = due_date.isoformat()
    
    def _schedule_annual(self, from_date: date) -> None:
        """Schedule due date annually on a specific date."""
        if self.recurrence_annual_month is None or self.recurrence_annual_day is None:
            self.due_date = (from_date + timedelta(days=365)).isoformat()
            return
        
        # Try next occurrence this year
        try:
            due_date = date(from_date.year, self.recurrence_annual_month, self.recurrence_annual_day)
            if due_date <= from_date:
                # Already passed this year, use next year
                due_date = date(from_date.year + 1, self.recurrence_annual_month, self.recurrence_annual_day)
        except ValueError:
            # Invalid date (e.g., Feb 30), default to next year same day
            due_date = from_date.replace(year=from_date.year + 1)
        
        self.due_date = due_date.isoformat()
    
    
        
        
        
        
        