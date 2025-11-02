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

def compute_block_hash(prev_hash: str, height: int, timestamp: float, data: str, nonce: int, miner_id: str) -> str:
    """
    Compute the hash of a block given its components.

    Args:
        prev_hash: Hash of the previous block
        height: Block height
        timestamp: Block timestamp
        data: Block data
        nonce: Nonce value
        miner_id: ID of the miner

    Returns:
        SHA256 hash of the block as hexadecimal string
    """
    # Create block header string
    header = f"{prev_hash}{height}{timestamp}{data}{nonce}{miner_id}"
    return compute_sha256_hex(header.encode('utf-8'))

def hash_meets_difficulty(hash_hex: str, difficulty: int) -> bool:
    """
    Check if a hash meets the difficulty requirement (leading zeros).

    Args:
        hash_hex: Hash as hexadecimal string
        difficulty: Required number of leading zeros

    Returns:
        True if hash meets difficulty, False otherwise
    """
    # Check if hash starts with required number of zeros
    return hash_hex.startswith('0' * difficulty)
