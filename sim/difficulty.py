"""
Difficulty adjustment controller for Proof-of-Work simulation.
"""

import time
from typing import List

class DifficultyController:
    """Manages mining difficulty adjustment based on block timing."""
    
    def __init__(self, target_block_time: float = 10.0):
        """
        Initialize difficulty controller.
        
        Args:
            target_block_time: Target time between blocks in seconds
        """
        self.target_block_time = target_block_time
        self.current_difficulty = 4
        self.block_times: List[float] = []
        self.last_adjustment_time = time.time()
        
    def adjust_difficulty(self, recent_block_times: List[float]) -> int:
        """
        Adjust difficulty based on recent block times.
        
        Args:
            recent_block_times: List of recent block intervals
            
        Returns:
            New difficulty value
        """
        # TODO: Implement difficulty adjustment algorithm
        # - Calculate average block time from recent blocks
        # - Compare to target block time
        # - Adjust difficulty up/down accordingly
        # - Implement bounds checking
        
        if not recent_block_times:
            return self.current_difficulty
            
        avg_block_time = sum(recent_block_times) / len(recent_block_times)
        
        # Simple adjustment logic
        if avg_block_time < self.target_block_time * 0.8:
            # Blocks coming too fast, increase difficulty
            self.current_difficulty = min(self.current_difficulty + 1, 8)
        elif avg_block_time > self.target_block_time * 1.2:
            # Blocks coming too slow, decrease difficulty
            self.current_difficulty = max(self.current_difficulty - 1, 1)
            
        return self.current_difficulty
        
    def set_target_block_time(self, target_time: float) -> None:
        """Set the target block time for difficulty adjustment."""
        self.target_block_time = target_time
        
    def record_block_time(self, block_time: float) -> None:
        """Record a new block time for difficulty calculation."""
        self.block_times.append(block_time)
        # Keep only recent block times (last 10 blocks)
        if len(self.block_times) > 10:
            self.block_times.pop(0)
            
    def should_adjust_difficulty(self) -> bool:
        """Check if it's time to adjust difficulty."""
        # TODO: Implement timing logic for difficulty adjustments
        # Typically adjust every N blocks or after certain time intervals
        current_time = time.time()
        return (current_time - self.last_adjustment_time) > 60.0  # Adjust every minute
        
    def get_current_difficulty(self) -> int:
        """Get the current difficulty level."""
        return self.current_difficulty