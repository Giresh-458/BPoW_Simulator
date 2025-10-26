"""
Helper utility functions for the PoW simulator UI.
Provides common utility functions used across UI components.
"""

from typing import Union

def short_hash(h: str, length: int = 8) -> str:
    """
    Truncate a hash string to a shorter representation.
    
    Args:
        h: Hash string to truncate
        length: Length of the truncated hash (default 8)
    
    Returns:
        Truncated hash string with ellipsis if needed
    """
    if not h or not isinstance(h, str):
        return "N/A"
    
    if len(h) <= length:
        return h
    
    return f"{h[:length]}..."
