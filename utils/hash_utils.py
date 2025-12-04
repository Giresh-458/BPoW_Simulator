"""
Utility functions for hash computation and validation.
Uses simple modulo hash for educational purposes.
"""

import hashlib


def compute_block_hash(prev_hash: str, height: int, timestamp: float, data: str, nonce: int, miner_id: str) -> int:
    """
    Compute the hash of a block using modulo 1 crore (10 million) hash function.
    
    This is a simple educational hash function where:
    hash = (combined_value) % 10000000
    
    Args:
        prev_hash: Hash of the previous block (int or string)
        height: Block height
        timestamp: Block timestamp
        data: Block data
        nonce: Nonce value
        miner_id: ID of the miner
    
    Returns:
        Integer hash value (0-9999999)
    """
    # Convert prev_hash to int if it's a string
    if isinstance(prev_hash, str):
        # If it's a numeric string, convert it
        try:
            prev_hash_int = int(prev_hash)
        except ValueError:
            # If it's a hex or other string, use its hash
            prev_hash_int = hash(prev_hash)
    else:
        prev_hash_int = int(prev_hash)
    
    # Combine all components
    # Use Python's built-in hash for strings and multiply by prime numbers for better distribution
    combined = (
        prev_hash_int +
        height * 7919 +
        int(timestamp * 1000) * 6131 +
        hash(data) * 4969 +
        nonce * 3571 +
        hash(miner_id) * 2927
    )
    
    # Take modulo 10000000 (1 crore) to get hash in range [0, 9999999]
    return abs(combined) % 10000000


def hash_meets_difficulty(block_hash: int, difficulty: int) -> bool:
    """
    Check if a hash meets the difficulty requirement (threshold-based).
    
    For modulo hash (1 crore = 10,000,000), difficulty is a threshold value.
    Lower difficulty = easier to mine (higher threshold)
    Higher difficulty = harder to mine (lower threshold)
    
    Difficulty mapping (for 1 crore hash space):
    - 0: hash < 10,000,000 (100% chance - always valid)
    - 1: hash < 1,000,000 (10% chance)
    - 2: hash < 100,000 (1% chance)
    - 3: hash < 10,000 (0.1% chance)
    - 4: hash < 1,000 (0.01% chance)
    - 5: hash < 100 (0.001% chance)
    - 6: hash < 10 (0.0001% chance)
    - 7: hash < 5 (0.00005% chance)
    - 8: hash < 1 (0.00001% chance)
    
    Args:
        block_hash: Hash value (integer 0-9999999)
        difficulty: Difficulty level (0-8)
    
    Returns:
        True if hash meets difficulty, False otherwise
    """
    # Convert hash to int if it's a string
    if isinstance(block_hash, str):
        try:
            block_hash = int(block_hash)
        except ValueError:
            return False
    
    # Calculate threshold based on difficulty
    # Each difficulty level divides threshold by 10
    if difficulty == 0:
        threshold = 10000000  # 100% - always valid
    elif difficulty <= 6:
        threshold = 10 ** (7 - difficulty)  # 10^6, 10^5, 10^4, 10^3, 10^2, 10^1
    elif difficulty == 7:
        threshold = 5  # Extra hard
    else:  # difficulty 8
        threshold = 1  # Maximum difficulty
    
    return block_hash < threshold
