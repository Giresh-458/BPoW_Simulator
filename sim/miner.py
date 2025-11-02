"""
Miner implementation for Proof-of-Work simulation.
"""

import threading
import time
import random
from typing import Callable, Optional
from .core import Block
from utils.hash_utils import compute_block_hash, hash_meets_difficulty

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
        # Current mining work (set by sim_api)
        self.prev_hash = "0" * 64
        self.height = 0
        
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
        # Use a small cycle time to batch attempts and reduce Python overhead
        cycle_time = 0.1
        nonce = random.randint(0, 2**32 - 1)

        while self.is_mining:
            # Snapshot current work to detect changes during cycle
            prev_hash = self.prev_hash
            height = self.height
            data = self.current_data
            difficulty = self.difficulty

            # Number of attempts this cycle based on desired hash_rate
            attempts = max(1, int(self.hash_rate * cycle_time))

            # Use a fixed timestamp for the whole cycle (deterministic header)
            timestamp = time.time()

            for _ in range(attempts):
                # Compute canonical hash for this nonce
                h = compute_block_hash(prev_hash, height + 1, timestamp, data, nonce, self.id)
                if hash_meets_difficulty(h, difficulty):
                    # Found a valid block
                    block = Block(
                        height=height + 1,
                        prev_hash=prev_hash,
                        timestamp=timestamp,
                        data=data,
                        nonce=nonce,
                        miner_id=self.id,
                        hash=h
                    )
                    if self.on_block_found:
                        self.on_block_found(block)
                    # After announcing, break to let sim_api update heads/work
                    # Do not permanently stop the miner thread; sim_api will update work
                    break
                nonce = (nonce + 1) & 0xFFFFFFFF

            # Sleep briefly if still mining
            if self.is_mining:
                time.sleep(cycle_time)
                
    def _check_real_hash(self, nonce: int) -> bool:
        """Legacy helper: compute a single hash and check difficulty."""
        timestamp = time.time()
        h = compute_block_hash(self.prev_hash, self.height + 1, timestamp, self.current_data, nonce, self.id)
        return hash_meets_difficulty(h, self.difficulty)
        
    def _check_fast_hash(self, nonce: int) -> bool:
        """Fast simulation mode - pseudo-random check."""
        probability = 1.0 / (2 ** self.difficulty)
        return random.random() < probability
        
    def _create_block(self, nonce: int) -> Block:
        """Create a new block using current work (legacy helper)."""
        timestamp = time.time()
        h = compute_block_hash(self.prev_hash, self.height + 1, timestamp, self.current_data, nonce, self.id)
        return Block(
            height=self.height + 1,
            prev_hash=self.prev_hash,
            timestamp=timestamp,
            data=self.current_data,
            nonce=nonce,
            miner_id=self.id,
            hash=h
        )

    def set_work(self, prev_hash: str, height: int, data: str, difficulty: int) -> None:
        """Update the miner's current work atomically (called by sim_api)."""
        self.prev_hash = prev_hash
        self.height = height
        self.current_data = data
        self.difficulty = difficulty
        
    def set_hash_rate(self, rate: float) -> None:
        """Update the miner's hash rate."""
        self.hash_rate = rate
        
    def get_hash_rate(self) -> float:
        """Get the current hash rate."""
        return self.hash_rate
        
    def is_running(self) -> bool:
        """Check if the miner is currently running."""
        return self.is_mining