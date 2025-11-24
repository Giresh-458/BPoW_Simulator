"""
Core blockchain data structures and validation logic.
"""

from dataclasses import dataclass
from typing import Optional
import time
from utils.hash_utils import compute_block_hash, hash_meets_difficulty

@dataclass
class Block:
    """Represents a single block in the blockchain."""
    height: int
    prev_hash: str
    timestamp: float
    data: str
    nonce: int
    miner_id: str
    hash: Optional[int] = None
    accepted: bool = False
    
    def __post_init__(self):
        """Validate block data and compute hash if not provided."""
        if self.hash is None:
            # Compute hash using all block components
            self.hash = compute_block_hash(
                self.prev_hash, 
                self.height, 
                self.timestamp, 
                self.data, 
                self.nonce, 
                self.miner_id
            )

class Blockchain:
    """Manages the blockchain state and validation."""
    
    def __init__(self):
        """Initialize empty blockchain."""
        self.blocks: list[Block] = []
        self.difficulty = 4  # Default difficulty
        
    def add_block(self, block: Block) -> bool:
        """
        Add a new block to the blockchain.
        
        Args:
            block: The block to add
            
        Returns:
            True if block was added successfully, False otherwise
        """
        # TODO: Implement block validation and addition logic
        if self.validate_block(block):
            self.blocks.append(block)
            block.accepted = True
            return True
        return False
    
    def validate_block(self, block: Block) -> bool:
        """
        Validate a block before adding it to the blockchain.
        
        Performs comprehensive validation:
        1. Hash recomputation and verification
        2. Difficulty requirement check
        3. Timestamp validation (not too far in future, monotonic)
        4. Chain continuity (prev_hash, height)
        
        Args:
            block: The block to validate
            
        Returns:
            True if block is valid, False otherwise
        """
        # 1. Recompute hash and verify it matches
        computed_hash = compute_block_hash(
            block.prev_hash, 
            block.height, 
            block.timestamp, 
            block.data, 
            block.nonce, 
            block.miner_id
        )
        
        if computed_hash != block.hash:
            return False
        
        # 2. Check if hash meets difficulty requirement
        if not hash_meets_difficulty(block.hash, self.difficulty):
            return False
        
        # 3. Validate timestamp
        current_time = time.time()
        # Block timestamp cannot be more than 2 hours in the future
        if block.timestamp > current_time + 7200:
            return False
        
        # 4. Validate chain continuity if this is not the first block
        if len(self.blocks) > 0:
            last_block = self.blocks[-1]
            
            # Check previous hash matches
            if block.prev_hash != last_block.hash:
                return False
            
            # Check height is incremental
            if block.height != last_block.height + 1:
                return False
            
            # Check timestamp is monotonic (not earlier than previous block)
            if block.timestamp < last_block.timestamp:
                return False
        else:
            # First block should have height 1 and prev_hash of 0
            if block.height != 1:
                return False
        
        return True
    
    def get_latest_block(self) -> Optional[Block]:
        """Get the most recent block in the blockchain."""
        return self.blocks[-1] if self.blocks else None
    
    def get_block_count(self) -> int:
        """Get the total number of blocks in the blockchain."""
        return len(self.blocks)
    
    def set_difficulty(self, difficulty: int) -> None:
        """Set the mining difficulty for new blocks."""
        self.difficulty = difficulty
