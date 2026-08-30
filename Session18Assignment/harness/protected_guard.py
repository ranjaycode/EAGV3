"""
protected_guard.py - Evaluation boundary enforcement module.
"""
import os
import re

PROTECTED_PATTERNS = [
    r"^tests/.*",
    r".*/tests/.*",
    r".*test_.*\.py$",
    r".*conftest\.py$",
    r"^\.github/.*",
]

def is_protected_path(filepath: str) -> bool:
    """
    Returns True if filepath matches any declared protected path pattern.
    """
    normalized = filepath.replace("\\", "/").strip("/")
    for pattern in PROTECTED_PATTERNS:
        if re.match(pattern, normalized, re.IGNORECASE):
            return True
    return False
