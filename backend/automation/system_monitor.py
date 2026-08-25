import psutil
import platform
import sys

class SystemMonitor:
    """System performance and health monitoring module."""

    @classmethod
    def get_metrics(cls) -> dict:
        """Fetch live CPU, RAM, Disk, and Battery stats."""
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        battery_info = {"percent": 100, "power_plugged": True}
        try:
            battery = psutil.sensors_battery()
            if battery:
                battery_info = {
                    "percent": round(battery.percent, 1),
                    "power_plugged": battery.power_plugged
                }
        except Exception:
            pass

        return {
            "success": True,
            "metrics": {
                "cpu_percent": round(cpu_percent, 1),
                "ram_percent": round(memory.percent, 1),
                "ram_used_gb": round(memory.used / (1024 ** 3), 2),
                "ram_total_gb": round(memory.total / (1024 ** 3), 2),
                "disk_percent": round(disk.percent, 1),
                "disk_free_gb": round(disk.free / (1024 ** 3), 2),
                "battery": battery_info,
                "platform": sys.platform,
                "machine": platform.machine()
            }
        }
