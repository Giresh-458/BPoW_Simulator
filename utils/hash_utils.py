"""
Utility functions for hash computation and validation.
Uses simple modulo hash for educational purposes.
"""

import hashlib


def compute_block_hash(prev_hash: str, height: int, timestamp: float, data: str, nonce: int, miner_id: str) -> int:
    """
    Compute the hash of a block using modulo 10000 hash function.
    
    This is a simple educational hash function where:
    hash = (combined_value) % 10000
    
    Args:
        prev_hash: Hash of the previous block (int or string)
        height: Block height
        timestamp: Block timestamp
        data: Block data
        nonce: Nonce value
        miner_id: ID of the miner
    
    Returns:
        Integer hash value (0-9999)
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
    
    # Take modulo 10000 to get hash in range [0, 9999]
    return abs(combined) % 10000


def hash_meets_difficulty(block_hash: int, difficulty: int) -> bool:
    """
    Check if a hash meets the difficulty requirement (threshold-based).
    
    For modulo hash, difficulty is a threshold value.
    Lower difficulty = easier to mine (higher threshold)
    Higher difficulty = harder to mine (lower threshold)
    
    Difficulty mapping:
    - 0: hash < 5000 (50% chance)
    - 1: hash < 2500 (25% chance)
    - 2: hash < 1250 (12.5% chance)
    - 3: hash < 625 (6.25% chance)
    - 4: hash < 312 (3.12% chance)
    - 5: hash < 156 (1.56% chance)
    - 6: hash < 78 (0.78% chance)
    
    Args:
        block_hash: Hash value (integer 0-9999)
        difficulty: Difficulty level (0-6+)
    
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
    # Each difficulty level halves the probability
    threshold = 5000 // (2 ** difficulty)
    
    return block_hash < threshold


def compute_sha256_hex(data: bytes) -> str:
    """
    Compute SHA256 hash of input data and return as hexadecimal string.
    (Kept for compatibility, not used in main simulation)
    
    Args:
        data: Input data as bytes
        
    Returns:
        SHA256 hash as hexadecimal string
    """
    return hashlib.sha256(data).hexdigest()
<<<<<<< HEAD

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
=======
>>>>>>> origin
