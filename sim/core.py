"""
Core blockchain data structures and validation logic.
"""

from dataclasses import dataclass
from typing import Optional
import time
import hashlib
import threading

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
            # Compute hash if not provided
            from utils.hash_utils import compute_block_hash
            self.hash = compute_block_hash(
                self.prev_hash, self.data, self.nonce, 
                self.timestamp, self.miner_id
            )

class Blockchain:
    """Manages the blockchain state and validation."""
    
    def __init__(self):
        """Initialize blockchain with genesis block."""
        self.blocks: list[Block] = []
        self.difficulty = 4  # Default difficulty
        self._lock = threading.Lock()  # Thread safety for concurrent mining
        
        # Create genesis block
        self._create_genesis_block()
        
    def _create_genesis_block(self) -> None:
        """Create the genesis block (first block in the chain)."""
        from utils.hash_utils import compute_block_hash
        
        genesis_timestamp = time.time()
        genesis_prev_hash = "0" * 64  # Genesis block has no previous hash
        genesis_data = "Genesis Block"
        genesis_nonce = 0
        genesis_miner_id = "genesis"
        
        # Compute genesis hash
        genesis_hash = compute_block_hash(
            genesis_prev_hash, genesis_data, genesis_nonce,
            genesis_timestamp, genesis_miner_id
        )
        
        genesis_block = Block(
            height=0,
            prev_hash=genesis_prev_hash,
            timestamp=genesis_timestamp,
            data=genesis_data,
            nonce=genesis_nonce,
            miner_id=genesis_miner_id,
            hash=genesis_hash,
            accepted=True
        )
        
        self.blocks.append(genesis_block)
        
    def add_block(self, block: Block) -> bool:
        """
        Add a new block to the blockchain.
        
        Args:
            block: The block to add
            
        Returns:
            True if block was added successfully, False otherwise
        """
        with self._lock:
            # Validate block before adding
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
        from utils.hash_utils import compute_block_hash, check_hash_difficulty
        
        # Check if hash exists
        if not block.hash:
            return False
        
        # Verify hash matches block content
        computed_hash = compute_block_hash(
            block.prev_hash, block.data, block.nonce,
            block.timestamp, block.miner_id
        )
        if computed_hash != block.hash:
            return False
        
        # Check if hash meets difficulty requirement (PoW validation)
        if not check_hash_difficulty(block.hash, self.difficulty):
            return False
        
        # Validate timestamp sanity (not in future, not too old)
        current_time = time.time()
        if block.timestamp > current_time + 60:  # Max 1 minute in future
            return False
        if block.timestamp < current_time - 3600:  # Max 1 hour old
            return False
        
        # Check chain continuity
        if len(self.blocks) > 0:
            last_block = self.blocks[-1]
            
            # Verify previous hash matches
            if block.prev_hash != last_block.hash:
                return False
            
            # Verify block height is correct
            if block.height != last_block.height + 1:
                return False
            
            # Verify timestamp is after previous block
            if block.timestamp < last_block.timestamp:
                return False
        else:
            # This should not happen as genesis block is created on init
            return False
        
        return True
    
    def get_latest_block(self) -> Optional[Block]:
        """Get the most recent block in the blockchain."""
        with self._lock:
            return self.blocks[-1] if self.blocks else None
    
    def get_block_count(self) -> int:
        """Get the total number of blocks in the blockchain."""
        with self._lock:
            return len(self.blocks)
    
    def set_difficulty(self, difficulty: int) -> None:
        """Set the mining difficulty for new blocks."""
        self.difficulty = difficulty
