"""
Battery Saver Mode Configuration
Adjusts background polling frequency on laptop battery power.
"""

DEFAULT_POLL_INTERVAL = 1.0
BATTERY_SAVER_POLL_INTERVAL = 3.5

def get_interval(on_battery: bool = False) -> float:
    return BATTERY_SAVER_POLL_INTERVAL if on_battery else DEFAULT_POLL_INTERVAL
