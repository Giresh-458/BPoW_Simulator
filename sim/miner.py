"""
Miner implementation for Proof-of-Work simulation.
"""

import threading
import time
import random
import hashlib
from typing import Callable, Optional
from .core import Block, Blockchain

class Miner:
    """Represents a blockchain miner that attempts to find valid blocks."""
    
    def __init__(self, miner_id: str, hash_rate: float = 1.0):
        """
        Initialize a miner.
        
        Args:
            miner_id: Unique identifier for this miner
            hash_rate: Hash attempts per second (computational power)
        """
        self.id = miner_id
        self.hash_rate = hash_rate  # Hashes per second
        self.is_mining = False
        self.mining_thread: Optional[threading.Thread] = None
        self.on_block_found: Optional[Callable] = None
        self.blockchain: Optional[Blockchain] = None
        self.use_real_sha256 = False
        self.difficulty = 4
        self.current_data = "Hello Blockchain!"
<<<<<<< HEAD
=======
        # Current mining work (set by sim_api)
        self.prev_hash = 0  # Integer hash for mod 10000
        self.height = 0
>>>>>>> origin
        
    def start(self, on_block_found: Callable, blockchain: Blockchain,
              use_real_sha256: bool = False, difficulty: int = 4, 
              data: str = "Hello Blockchain!") -> None:
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
        
        self.mining_thread = threading.Thread(target=self._mining_loop, daemon=True)
        self.mining_thread.start()
        
    def stop(self) -> None:
        """Stop the mining process."""
        self.is_mining = False
        if self.mining_thread:
            self.mining_thread.join(timeout=1.0)
            
    def _mining_loop(self) -> None:
<<<<<<< HEAD
        """Main mining loop that runs in a separate thread."""
        nonce = 0
        
        while self.is_mining:
            # Get current blockchain state
            if not self.blockchain:
                break
=======
        """
        Main mining loop that runs in a separate thread.
        
        Hash Power Explanation:
        -----------------------
        The hash_rate parameter (e.g., 1000) represents the number of hash 
        computations this miner attempts per second.
        
        Example: If hash_rate = 1000:
        - Every 0.1 seconds (cycle_time), the miner attempts 100 hashes
        - Each hash attempt tests a different nonce value
        - If a hash meets the difficulty requirement, a valid block is found
        
        With difficulty 4 (threshold 312), each hash has ~3.12% chance of success.
        So a miner with 1000 H/s will find a valid block approximately every:
        1000 attempts/sec ÷ (10000/312) = ~31 attempts/sec success rate
        → About 1 block every 0.03 seconds on average (very fast for testing!)
        
        In production PoW:
        - Bitcoin miners: ~100 TH/s (terahashes per second)
        - Difficulty adjusts so network finds 1 block every 10 minutes
        """
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
            # Example: hash_rate=1000, cycle_time=0.1 → attempts=100
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
>>>>>>> origin
                
            latest_block = self.blockchain.get_latest_block()
            if not latest_block:
                break
            
            # Calculate delay based on hash rate (computational power)
            # Higher hash_rate = more computational power = less delay
            if self.hash_rate > 0:
                delay = 1.0 / self.hash_rate
            else:
                delay = 1.0
            
            # Perform mining attempt
            if self.use_real_sha256:
                is_valid, block_hash = self._check_real_hash(nonce, latest_block)
            else:
                # Fast simulation mode
                is_valid, block_hash = self._check_fast_hash(nonce, latest_block)
                
            if is_valid and self.is_mining:
                # Found a valid block!
                block = self._create_block(nonce, latest_block, block_hash)
                if self.on_block_found:
                    self.on_block_found(block)
                # Reset nonce and continue mining next block
                nonce = 0
                time.sleep(0.1)  # Small delay before starting next block
            else:
                nonce += 1
                # Apply hash rate delay (computational power effect)
                time.sleep(delay)
                
    def _check_real_hash(self, nonce: int, prev_block: Block) -> tuple[bool, str]:
        """Check if nonce produces a valid hash using real SHA256."""
        from utils.hash_utils import compute_block_hash, check_hash_difficulty
        
        timestamp = time.time()
        
        # Compute the actual hash
        block_hash = compute_block_hash(
            prev_block.hash,
            self.current_data,
            nonce,
            timestamp,
            self.id
        )
        
        # Check if it meets difficulty requirement
        is_valid = check_hash_difficulty(block_hash, self.difficulty)
        
        return is_valid, block_hash
        
    def _check_fast_hash(self, nonce: int, prev_block: Block) -> tuple[bool, str]:
        """Fast simulation mode - pseudo-random check with proper hash computation."""
        from utils.hash_utils import compute_block_hash, check_hash_difficulty
        
        timestamp = time.time()
        
        # Compute actual hash even in fast mode
        block_hash = compute_block_hash(
            prev_block.hash,
            self.current_data,
            nonce,
            timestamp,
            self.id
        )
        
        # In fast mode, use probability to simulate finding the right nonce faster
        # but still check actual hash occasionally for realism
        if random.random() < 0.1:  # 10% chance to check real hash
            is_valid = check_hash_difficulty(block_hash, self.difficulty)
        else:
            # Use probability-based check for speed
            probability = 1.0 / (2 ** self.difficulty)
            # Scale probability by hash rate (more power = higher chance per attempt)
            adjusted_probability = probability * (self.hash_rate / 1000.0)
            is_valid = random.random() < adjusted_probability
            
            # If "valid" in fast mode, recompute hash to ensure it actually meets difficulty
            if is_valid:
                # Try to find an actual valid nonce near this one
                for offset in range(100):
                    test_nonce = nonce + offset
                    test_hash = compute_block_hash(
                        prev_block.hash,
                        self.current_data,
                        test_nonce,
                        timestamp,
                        self.id
                    )
                    if check_hash_difficulty(test_hash, self.difficulty):
                        return True, test_hash
                # If we can't find one quickly, mark as invalid
                is_valid = False
        
        return is_valid, block_hash
        
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