"""
Pre-compiled Regex Pattern Cache for High-Frequency Voice Intent Routing
"""

import re
from typing import Dict, Pattern

_COMPILED_CACHE: Dict[str, Pattern] = {}

def get_compiled_regex(pattern_str: str, flags: int = re.IGNORECASE) -> Pattern:
    key = f"{pattern_str}_{flags}"
    if key not in _COMPILED_CACHE:
        _COMPILED_CACHE[key] = re.compile(pattern_str, flags)
    return _COMPILED_CACHE[key]
