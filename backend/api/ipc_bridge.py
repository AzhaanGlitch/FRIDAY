"""
Desktop IPC Communication Bridge
Handles protocol messages between the Python core and desktop frontend.
"""

import json
from typing import Dict, Any

class IPCBridge:
    def format_event(self, event_name: str, payload: Dict[str, Any]) -> str:
        return json.dumps({
            "event": event_name,
            "data": payload,
            "timestamp": "iso8601"
        })
