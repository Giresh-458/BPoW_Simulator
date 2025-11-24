"""
Helper utility functions for the PoW simulator UI.
Provides common utility functions used across UI components.
"""

from typing import Union

def short_hash(h: Union[str, int], length: int = 8) -> str:
    """
    Truncate a hash to a shorter representation.
    
    Args:
        h: Hash (string or integer) to truncate
        length: Length of the truncated hash (default 8)
    
    Returns:
        Truncated hash string with ellipsis if needed
    """
    if h is None:
        return "N/A"
    
    # Convert to string if it's an integer
    h_str = str(h)
    
    if len(h_str) <= length:
        return h_str
    
    return f"{h_str[:length]}..."
