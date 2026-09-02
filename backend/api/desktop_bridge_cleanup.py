"""
Sanitization and Cleanup of Deprecated Desktop Bridge APIs
"""

def clean_payload(data: dict) -> dict:
    return {k: v for k, v in data.items() if v is not None}
