"""
Core blockchain data structures and validation logic.
"""

from dataclasses import dataclass
from typing import Optional
import time
import hashlib

@dataclass
class Block:
    """Represents a single block in the blockchain."""
    height: int
    prev_hash: str
    timestamp: float
    data: str
    nonce: int
    miner_id: str
    hash: str
    accepted: bool = False
    
    def __post_init__(self):
        """Validate block data after initialization."""
        if not self.hash:
            # TODO: Compute hash if not provided
            self.hash = "0" * 64  # Placeholder

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
        
        Args:
            block: The block to validate
            
        Returns:
            True if block is valid, False otherwise
        """
        # TODO: Implement comprehensive block validation
        # - Check hash meets difficulty requirement
        # - Verify previous hash matches
        # - Validate timestamp
        # - Check block height
        
        if not block.hash:
            return False
            
        if len(self.blocks) > 0:
            last_block = self.blocks[-1]
            if block.prev_hash != last_block.hash:
                return False
            if block.height != last_block.height + 1:
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
