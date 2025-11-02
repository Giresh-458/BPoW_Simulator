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

def compute_block_hash(prev_hash: str, data: str, nonce: int, timestamp: float, miner_id: str) -> str:
    """
    Compute the hash for a block using SHA256.
    
    Args:
        prev_hash: Previous block's hash
        data: Block data/message
        nonce: Nonce value
        timestamp: Block timestamp
        miner_id: ID of the miner
        
    Returns:
        SHA256 hash as hexadecimal string
    """
    # Create block content string
    block_content = f"{prev_hash}{data}{nonce}{timestamp}{miner_id}"
    return hashlib.sha256(block_content.encode()).hexdigest()

def check_hash_difficulty(block_hash: str, difficulty: int) -> bool:
    """
    Check if a hash meets the difficulty requirement (leading zeros).
    
    Args:
        block_hash: The hash to check
        difficulty: Number of leading zeros required
        
    Returns:
        True if hash meets difficulty, False otherwise
    """
    if difficulty <= 0:
        return True
    
    # Check if hash starts with required number of zeros
    required_prefix = '0' * difficulty
    return block_hash.startswith(required_prefix)

def fast_hash_check(nonce: int, difficulty: int) -> bool:
    """
    Fast pseudo-random hash check for simulation mode.
    Uses simple probability instead of actual hash computation.
    
    Args:
        nonce: Nonce value to check
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
