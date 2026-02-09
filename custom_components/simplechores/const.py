"""
Constants for the SimpleChores integration.

This file is used for defining constant values that are used throughout
the SimpleChores integration. These constants help maintain consistency
and make it easier to manage configuration and state within the integration.
"""

from homeassistant.const import Platform
import logging


# General constants
DOMAIN = "simplechores"
LOGGER = logging.getLogger(__package__)
PLATFORMS = [
    Platform.SENSOR,
    Platform.SELECT,
    Platform.NUMBER,
    ]

# Storage and Versioning
STORAGE_KEY = "simplechores_storage"
STORAGE_VERSION = 1
DATA_CHORES = "chores"
DATA_MEMBERS = "members"

# Update Interval
UPDATE_INTERVAL = 10  # in minutes

# Configuration Keys
CONF_CHORE_NAME = "chore_name"
CONF_MEMBERS = "members"
CONF_N_MEMBERS = "n_members"
CONF_POINTS_LABEL = "points_label"
CONF_POINTS_ICON = "points_icon"
CONF_ENABLE_POINTS_SYSTEM = "enable_points_system"
CONF_ENABLE_REMINDERS = "enable_reminders"

# Options Flow Management
OPTIONS_FLOW_ENABLE_POINTS_SYSTEM = "enable_points_system"
OPTIONS_FLOW_ENABLE_REMINDERS = "enable_reminders"
OPTIONS_FLOW_RESET_CHORE_COUNTS = "reset_chore_counts"
OPTIONS_FLOW_RESET_POINTS = "reset_points"


# Default Values
DEFAULT_CHORE_NAME = "New Chore"
DEFAULT_MEMBERS = ["Default Member"]
DEFAULT_N_MEMBERS = 1
DEFAULT_POINTS_LABEL = "Points"
DEFAULT_POINTS_ICON = "mdi:star"
DEFAULT_ENABLE_POINTS_SYSTEM = True
DEFAULT_ENABLE_REMINDERS = True
DEFAULT_RESET_CHORE_COUNTS = False
DEFAULT_RESET_POINTS = False

# Recurrence Intervals
CONF_RECURRENCE_PATTERN = "recurrence_pattern"
CONF_RECURRENCE_INTERVAL = "recurrence_interval"
CONF_RECURRENCE_DAY_OF_MONTH = "recurrence_day_of_month"
CONF_RECURRENCE_WEEK_OF_MONTH = "recurrence_week_of_month"  # 1-4 or -1 for last
CONF_RECURRENCE_DAY_OF_WEEK = "recurrence_day_of_week"  # 0-6 (Monday-Sunday)
CONF_RECURRENCE_SPECIFIC_WEEKDAYS = "recurrence_specific_weekdays"  # List of days
CONF_RECURRENCE_ANNUAL_MONTH = "recurrence_annual_month"
CONF_RECURRENCE_ANNUAL_DAY = "recurrence_annual_day"

# recurrence patterns
FREQUENCY_NONE = "none"
FREQUENCY_DAILY = "daily"
FREQUENCY_MONTHLY_DAY = "monthly_day"
FREQUENCY_MONTHLY_WEEKDAY = "monthly_weekday"
FREQUENCY_INTERVAL_DAYS = "interval_days"
FREQUENCY_AFTER_COMPLETION_DAYS = "after_completion_days"
FREQUENCY_SPECIFIC_DAYS = "specific_days"
FREQUENCY_ANNUAL = "annual"
DEFAULT_RECURRENCE_PATTERN = FREQUENCY_DAILY

# Assignment Modes 
ASSIGN_MODE_ALWAYS = "always"  # Each member does their own (e.g., clean own desk)
ASSIGN_MODE_ROTATE = "rotate"  # Take turns doing community task
ASSIGN_MODE_RANDOM = "random"  # Random member does community task
DEFAULT_ASSIGN_MODE = ASSIGN_MODE_ALWAYS

# Chore State Attributes
CHORE_STATE_COMPLETED = "completed"
CHORE_STATE_PENDING = "pending"
CHORE_STATE_OVERDUE = "overdue"

# Device Info
DEVICE_MANUFACTURER = "SimpleChores"
DEVICE_MODEL_MEMBER = "Household Member"
DEVICE_MODEL_CHORE = "Household Chore"
DEVICE_SW_VERSION = "1.0.0"

# Sensor Icons
ICON_POINTS = "mdi:star"
ICON_CHORES_COMPLETED = "mdi:checkbox-marked-circle"
ICON_PENDING_CHORES = "mdi:clipboard-list"
ICON_OVERDUE_CHORES = "mdi:alert-circle"

# Sensor Names
SENSOR_NAME_POINTS = "Points"
SENSOR_NAME_CHORES_COMPLETED = "Chores completed"
SENSOR_NAME_PENDING_CHORES = "Chores pending"
SENSOR_NAME_OVERDUE_CHORES = "Chores overdue"

# Units
UNIT_CHORES = "chores"

# Service Names
SERVICE_UPDATE_POINTS = "update_points"
SERVICE_RESET_POINTS = "reset_points"
SERVICE_TOGGLE_CHORE = "toggle_chore"

# Chore tracker and point tracker Period Types
TRACKER_PERIOD_TODAY = "today"
TRACKER_PERIOD_THIS_WEEK = "this_week"
TRACKER_PERIOD_THIS_MONTH = "this_month"
TRACKER_PERIOD_THIS_YEAR = "this_year"

# Reset Configuration
CONF_WEEK_START_DAY = "week_start_day"  # 0 = Monday, 6 = Sunday
DEFAULT_WEEK_START_DAY = 0  # Monday

# Storage Keys for Last Reset Timestamps
KEY_LAST_RESET_TODAY = "last_reset_today"
KEY_LAST_RESET_THIS_WEEK = "last_reset_this_week"
KEY_LAST_RESET_THIS_MONTH = "last_reset_this_month"
KEY_LAST_RESET_THIS_YEAR = "last_reset_this_year"

# Member Data Field Keys
MEMBER_FIELD_NAME = "name"
MEMBER_FIELD_POINTS_TODAY = "points_earned_today"
MEMBER_FIELD_POINTS_THIS_WEEK = "points_earned_this_week"
MEMBER_FIELD_POINTS_THIS_MONTH = "points_earned_this_month"
MEMBER_FIELD_POINTS_THIS_YEAR = "points_earned_this_year"
MEMBER_FIELD_CHORES_TODAY = "chores_completed_today"
MEMBER_FIELD_CHORES_THIS_WEEK = "chores_completed_this_week"
MEMBER_FIELD_CHORES_THIS_MONTH = "chores_completed_this_month"
MEMBER_FIELD_CHORES_THIS_YEAR = "chores_completed_this_year"
MEMBER_FIELD_PENDING_CHORES = "n_chores_pending"
MEMBER_FIELD_OVERDUE_CHORES = "n_chores_overdue"

# Field name prefixes
MEMBER_FIELD_PREFIX_POINTS = "points_earned"
MEMBER_FIELD_PREFIX_CHORES = "chores_completed"

# Last reset field prefix
STORAGE_KEY_PREFIX_LAST_RESET = "last_reset"

# Chore data field keys
CHORE_FIELD_ASSIGNED_TO = "assigned_to"
CHORE_FIELD_STATUS = "status"