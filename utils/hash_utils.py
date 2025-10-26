"""
Utility functions for hash computation and validation.
"""

import hashlib
import random

def compute_sha256_hex(data: bytes) -> str:
    """
    Compute SHA256 hash of input data and return as hexadecimal string.
    
    Args:
        data: Input data as bytes
        
    Returns:
        SHA256 hash as hexadecimal string
    """
    return hashlib.sha256(data).hexdigest()

def fast_hash_check(nonce: int, difficulty: int) -> bool:
    """
    Fast pseudo-random hash check for simulation mode.
    Uses simple probability instead of actual hash computation.
    
    Args:
        nononce: Nonce value to check
        difficulty: Difficulty level (higher = lower probability)
        
    Returns:
        True if hash would be valid, False otherwise
    """
    # Simple probability-based simulation
    # Higher difficulty = lower probability of success
    probability = 1.0 / (2 ** difficulty)
    
    # Use nonce as seed for deterministic but varied results
    random.seed(nonce)
    result = random.random() < probability
    random.seed()  # Reset seed
    
    return result
