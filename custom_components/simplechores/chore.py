"""Chore class for SimpleChores."""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Dict, List
from datetime import datetime, date
import random

from .const import (
    CHORE_STATE_PENDING,
    CHORE_STATE_COMPLETED,
    CHORE_STATE_OVERDUE,
    ASSIGN_MODE_ALWAYS,
    ASSIGN_MODE_ROTATE,
    ASSIGN_MODE_RANDOM,
)


@dataclass
class Chore:
    """Represents a household chore."""
    
    name: str
    points: int = 0
    status: str = CHORE_STATE_PENDING  # pending, completed, overdue
    last_completed: str | None = None  # ISO format date string
    next_due: str | None = None  # ISO format date string
    days_overdue: int = 0
    assignment_mode: str = ASSIGN_MODE_ALWAYS  # always, rotate, random
    assigned_to: str | None = None  # Current assignee member
    possible_assignees: List[str] = field(default_factory=list)  # List of members who can be assigned
    
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
            next_due=data.get("next_due"),
            days_overdue=data.get("days_overdue", 0),
            assignment_mode=data.get("assignment_mode", ASSIGN_MODE_ALWAYS),
            assigned_to=data.get("assigned_to"),
            possible_assignees=data.get("possible_assignees", []),
        )
    
    def mark_completed(self, member_name: str, completion_date: date | None = None) -> None:
        """Mark the chore as completed by a specific member."""
        if completion_date is None:
            completion_date = date.today()
        
        self.status = CHORE_STATE_COMPLETED
        self.last_completed = completion_date.isoformat()
        self.days_overdue = 0
        self.assign()
        
    def assign(self) -> None:
        """Assign the chore to a member based on the assignment mode."""
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
        self.days_overdue = 0
    
    def mark_overdue(self, days: int = 0) -> None:
        """Mark the chore as overdue."""
        self.status = CHORE_STATE_OVERDUE
        self.days_overdue = days
    
    def assign_to_member(self, member_name: str) -> None:
        """Assign this chore to a specific member."""
        self.assigned_to = member_name
        
    def is_overdue(self, current_date: date | None = None) -> bool:
        """Check if the chore is overdue based on next_due date."""
        if not self.next_due:
            return False
        
        if current_date is None:
            current_date = date.today()
        
        try:
            due_date = date.fromisoformat(self.next_due)
            return current_date > due_date and self.status != CHORE_STATE_COMPLETED
        except (ValueError, TypeError):
            return False
    
    def calculate_days_overdue(self, current_date: date | None = None) -> int:
        """Calculate how many days the chore is overdue."""
        if not self.next_due:
            return 0
        
        if current_date is None:
            current_date = date.today()
        
        try:
            due_date = date.fromisoformat(self.next_due)
            if current_date > due_date:
                return (current_date - due_date).days
            return 0
        except (ValueError, TypeError):
            return 0
    
    def update_overdue_status(self, current_date: date | None = None) -> None:
        """Update the overdue status and days overdue."""
        if self.is_overdue(current_date):
            days = self.calculate_days_overdue(current_date)
            self.mark_overdue(days)
        elif self.status == CHORE_STATE_OVERDUE:
            # Was overdue but isn't anymore
            self.mark_pending()
