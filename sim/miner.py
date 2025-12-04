"""
Miner implementation for Proof-of-Work simulation.
"""

import threading
import time
import random
import hashlib
from typing import Callable, Optional
from .core import Block, Blockchain
from utils.hash_utils import compute_block_hash, hash_meets_difficulty

class Miner:
    """Represents a blockchain miner that attempts to find valid blocks.

    This miner uses a simple deterministic model: it performs N hash
    attempts every cycle, where N = int(hash_rate * cycle_time). Each
    attempt computes the block hash and checks against the difficulty
    using `hash_meets_difficulty`. The miner exposes `set_work` so the
    simulation can update the current head/difficulty without restarting
    the miner thread.
    """

    def __init__(self, miner_id: str, hash_rate: float = 1.0):
        """
        Initialize a miner.

        Args:
            miner_id: Unique identifier for this miner
            hash_rate: Hash attempts per second (computational power)
        """
        self.id = miner_id
        self.hash_rate = float(hash_rate)  # Hashes per second
        self.is_mining = False
        self.mining_thread: Optional[threading.Thread] = None
        self.on_block_found: Optional[Callable] = None
        self.blockchain: Optional[Blockchain] = None
        self.use_real_sha256 = False
        self.difficulty = 4
        self.current_data = "Hello Blockchain!"

        # Current mining work (set by sim_api)
        self.prev_hash = 0
        self.height = 0

        # Internal state
        self._nonce = random.randint(0, 2**32 - 1)
        self._lock = threading.Lock()
        
    def start(self, on_block_found: Callable, blockchain: Blockchain,
              use_real_sha256: bool = False, difficulty: int = 4, 
              data: str = "Test transaction") -> None:
        """
        Start mining process in a separate thread.
        
        Args:
            on_block_found: Callback function when a block is found
            blockchain: Reference to the blockchain to mine on
            use_real_sha256: Whether to use real SHA256 or fast simulation
            difficulty: Mining difficulty target
            data: Data to include in the block
        """
        if self.is_mining:
            return
            
        self.on_block_found = on_block_found
        self.blockchain = blockchain
        self.use_real_sha256 = use_real_sha256
        self.difficulty = difficulty
        self.current_data = data
        self.is_mining = True

        # Start mining thread
        self.mining_thread = threading.Thread(target=self._mining_loop, daemon=True)
        self.mining_thread.start()
        
    def stop(self) -> None:
        """Stop the mining process."""
        self.is_mining = False
        if self.mining_thread:
            self.mining_thread.join(timeout=1.0)
            
    def _mining_loop(self) -> None:
        """Main mining loop using a single consistent model.

        Every cycle we perform `attempts = max(1, int(hash_rate * cycle_time))`
        hash attempts. Each attempt computes an actual block hash and tests
        it against the current difficulty. If a valid block is found we call
        `on_block_found(block)` and then continue (the simulation will
        broadcast new work which `set_work` will apply).
        """
        cycle_time = 0.05  # Reduced from 0.1 to 0.05 for more responsive mining

        while self.is_mining:
            # Snapshot work atomically
            with self._lock:
                prev_hash = self.prev_hash
                height = self.height
                data = self.current_data
                difficulty = self.difficulty

            attempts = max(1, int(self.hash_rate * cycle_time))
            timestamp = time.time()

            found = False
            for _ in range(attempts):
                with self._lock:
                    nonce = self._nonce
                    # advance nonce for next attempt
                    self._nonce = (self._nonce + 1) & 0xFFFFFFFF

                h = compute_block_hash(prev_hash, height + 1, timestamp, data, nonce, self.id)
                if hash_meets_difficulty(h, difficulty):
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
                        try:
                            self.on_block_found(block)
                        except Exception:
                            pass
                    found = True
                    break

            # Sleep to respect cycle pacing
            if self.is_mining:
                time.sleep(cycle_time)

            # If we found a block, yield to allow simulation to update work
            if found:
                # small pause to let sim_api process block acceptance
                time.sleep(0.01)
                continue
                
    def _check_real_hash(self, nonce: int, prev_block: Block) -> tuple[bool, str]:
        """Check if nonce produces a valid hash using real hash computation."""
        timestamp = time.time()
        
        # Compute the actual hash
        block_hash = compute_block_hash(
            prev_block.hash,
            prev_block.height + 1,
            timestamp,
            self.current_data,
            nonce,
            self.id
        )
        
        # Check if it meets difficulty requirement
        is_valid = hash_meets_difficulty(block_hash, self.difficulty)
        
        return is_valid, block_hash
    # _check_fast_hash removed — mining now always computes actual hashes per attempt
        
    def _create_block(self, nonce: int, prev_block: Block, block_hash: str) -> Block:
        """Create a new block with the found nonce."""
        timestamp = time.time()
        
        return Block(
            height=prev_block.height + 1,
            prev_hash=prev_block.hash,
            timestamp=timestamp,
            data=self.current_data,
            nonce=nonce,
            miner_id=self.id,
            hash=block_hash
        )
        
    def set_hash_rate(self, rate: float) -> None:
        """Update the miner's hash rate (computational power)."""
        self.hash_rate = rate
        
    def get_hash_rate(self) -> float:
        """Get the current hash rate."""
        return self.hash_rate
        
    def is_running(self) -> bool:
        """Check if the miner is currently running."""
        return self.is_mining

    def set_work(self, prev_hash, height: int, data: str, difficulty: int) -> None:
        """Update current work (head) atomically without restarting miner."""
        with self._lock:
            self.prev_hash = prev_hash
            self.height = height
            self.current_data = data
            self.difficulty = difficulty
            # reset nonce to a random value to avoid aligned search
            self._nonce = random.randint(0, 2**32 - 1)