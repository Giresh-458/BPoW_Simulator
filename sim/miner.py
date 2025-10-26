"""
Miner implementation for Proof-of-Work simulation.
"""

import threading
import time
import random
import hashlib
from typing import Callable, Optional
from .core import Block

class Miner:
    """Represents a blockchain miner that attempts to find valid blocks."""
    
    def __init__(self, miner_id: str, hash_rate: float = 1.0):
        """
        Initialize a miner.
        
        Args:
            miner_id: Unique identifier for this miner
            hash_rate: Hash attempts per second (simulation speed)
        """
        self.id = miner_id
        self.hash_rate = hash_rate
        self.is_mining = False
        self.mining_thread: Optional[threading.Thread] = None
        self.on_block_found: Optional[Callable] = None
        self.use_real_sha256 = False
        self.difficulty = 4
        self.current_data = "Hello Blockchain!"
        
    def start(self, on_block_found: Callable, use_real_sha256: bool = False, 
              difficulty: int = 4, data: str = "Hello Blockchain!") -> None:
        """
        Start mining process in a separate thread.
        
        Args:
            on_block_found: Callback function when a block is found
            use_real_sha256: Whether to use real SHA256 or fast simulation
            difficulty: Mining difficulty target
            data: Data to include in the block
        """
        if self.is_mining:
            return
            
        self.on_block_found = on_block_found
        self.use_real_sha256 = use_real_sha256
        self.difficulty = difficulty
        self.current_data = data
        self.is_mining = True
        
        self.mining_thread = threading.Thread(target=self._mining_loop, daemon=True)
        self.mining_thread.start()
        
    def stop(self) -> None:
        """Stop the mining process."""
        self.is_mining = False
        if self.mining_thread:
            self.mining_thread.join(timeout=1.0)
            
    def _mining_loop(self) -> None:
        """Main mining loop that runs in a separate thread."""
        nonce = 0
        
        while self.is_mining:
            # Simulate mining attempt
            if self.use_real_sha256:
                # TODO: Implement real SHA256 mining
                is_valid = self._check_real_hash(nonce)
            else:
                # Fast simulation mode
                is_valid = self._check_fast_hash(nonce)
                
            if is_valid and self.is_mining:
                # Found a valid block!
                block = self._create_block(nonce)
                if self.on_block_found:
                    self.on_block_found(block)
                break
                
            nonce += 1
            
            # Simulate hash rate timing
            if self.hash_rate > 0:
                time.sleep(1.0 / self.hash_rate)
                
    def _check_real_hash(self, nonce: int) -> bool:
        """Check if nonce produces a valid hash using real SHA256."""
        # TODO: Implement real SHA256 hash checking
        # This should compute SHA256(data + nonce) and check difficulty
        return random.random() < 0.001  # Placeholder probability
        
    def _check_fast_hash(self, nonce: int) -> bool:
        """Fast simulation mode - pseudo-random check."""
        # Simple probability-based simulation
        # Higher difficulty = lower probability
        probability = 1.0 / (2 ** self.difficulty)
        return random.random() < probability
        
    def _create_block(self, nonce: int) -> Block:
        """Create a new block with the found nonce."""
        # TODO: Implement proper block creation with real hash
        timestamp = time.time()
        block_hash = f"block_{self.id}_{nonce}_{timestamp}"  # Placeholder hash
        
        return Block(
            height=0,  # TODO: Get from blockchain
            prev_hash="0" * 64,  # TODO: Get from blockchain
            timestamp=timestamp,
            data=self.current_data,
            nonce=nonce,
            miner_id=self.id,
            hash=block_hash
        )
        
    def set_hash_rate(self, rate: float) -> None:
        """Update the miner's hash rate."""
        self.hash_rate = rate
