# coordinator.py
from __future__ import annotations

from datetime import datetime, timedelta
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    LOGGER,
    TRACKER_PERIOD_TODAY,
    TRACKER_PERIOD_THIS_WEEK,
    TRACKER_PERIOD_THIS_MONTH,
    TRACKER_PERIOD_THIS_YEAR,
    DEFAULT_WEEK_START_DAY,
)

class SimpleChoresCoordinator(DataUpdateCoordinator):
    """Coordinator for SimpleChores."""

    def __init__(self, hass, storage_manager):
        super().__init__(
            hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),  # Hourly backup check for period resets
        )

        self.storage = storage_manager
        self.data = None  # will hold chores + members

    async def async_refresh_data(self):
        """Manually trigger a data refresh."""
        await self.async_request_refresh()

    async def _async_update_data(self):
        """Fetch latest data and handle period resets."""
        try:
            # Check and handle period resets
            await self._check_and_reset_periods()
            
            # later: compute overdue, next due, assignments, etc.
            return self.storage.data
        except Exception as err:
            raise UpdateFailed(f"Error updating SimpleChores: {err}")

    async def _check_and_reset_periods(self):
        """Check if any period boundaries have been crossed and reset counters."""
        now = datetime.now()
        save_needed = False

        # Check daily reset (midnight)
        if self._should_reset_daily(now):
            self.storage.reset_period_counters(TRACKER_PERIOD_TODAY)
            self.storage.set_last_reset(TRACKER_PERIOD_TODAY, now.date().isoformat())
            save_needed = True
            LOGGER.debug("Reset daily counters")

        # Check weekly reset (start of week)
        if self._should_reset_weekly(now):
            self.storage.reset_period_counters(TRACKER_PERIOD_THIS_WEEK)
            self.storage.set_last_reset(TRACKER_PERIOD_THIS_WEEK, now.date().isoformat())
            save_needed = True
            LOGGER.debug("Reset weekly counters")

        # Check monthly reset (1st of month)
        if self._should_reset_monthly(now):
            self.storage.reset_period_counters(TRACKER_PERIOD_THIS_MONTH)
            self.storage.set_last_reset(TRACKER_PERIOD_THIS_MONTH, now.date().isoformat())
            save_needed = True
            LOGGER.debug("Reset monthly counters")

        # Check yearly reset (January 1st)
        if self._should_reset_yearly(now):
            self.storage.reset_period_counters(TRACKER_PERIOD_THIS_YEAR)
            self.storage.set_last_reset(TRACKER_PERIOD_THIS_YEAR, now.date().isoformat())
            save_needed = True
            LOGGER.debug("Reset yearly counters")

        if save_needed:
            await self.storage.async_save()

    def _should_reset_daily(self, now: datetime) -> bool:
        """Check if daily counters should be reset."""
        last_reset = self.storage.get_last_reset(TRACKER_PERIOD_TODAY)
        if not last_reset:
            return True  # First run, initialize
        
        last_reset_date = datetime.fromisoformat(last_reset).date()
        return now.date() > last_reset_date

    def _should_reset_weekly(self, now: datetime) -> bool:
        """Check if weekly counters should be reset."""
        last_reset = self.storage.get_last_reset(TRACKER_PERIOD_THIS_WEEK)
        if not last_reset:
            return True  # First run, initialize
        
        last_reset_date = datetime.fromisoformat(last_reset).date()
        
        # Get start of current week (Monday by default)
        current_week_start = now.date() - timedelta(days=now.weekday() - DEFAULT_WEEK_START_DAY)
        if now.weekday() < DEFAULT_WEEK_START_DAY:
            current_week_start -= timedelta(days=7)
        
        return last_reset_date < current_week_start

    def _should_reset_monthly(self, now: datetime) -> bool:
        """Check if monthly counters should be reset."""
        last_reset = self.storage.get_last_reset(TRACKER_PERIOD_THIS_MONTH)
        if not last_reset:
            return True  # First run, initialize
        
        last_reset_date = datetime.fromisoformat(last_reset).date()
        
        # Check if we've entered a new month
        return (now.year, now.month) > (last_reset_date.year, last_reset_date.month)

    def _should_reset_yearly(self, now: datetime) -> bool:
        """Check if yearly counters should be reset."""
        last_reset = self.storage.get_last_reset(TRACKER_PERIOD_THIS_YEAR)
        if not last_reset:
            return True  # First run, initialize
        
        last_reset_date = datetime.fromisoformat(last_reset).date()
        
        # Check if we've entered a new year
        return now.year > last_reset_date.year
