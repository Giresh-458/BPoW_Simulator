"""
Core simulation package for Proof-of-Work blockchain simulator.
Exports main API functions for external use.
"""

from .core import Block, Blockchain
from .miner import Miner
from .network import Network
from .difficulty import DifficultyController

__all__ = [
    'start_simulation',
    'stop_simulation', 
    'set_miner_rate',
    'submit_data',
    'get_stats',
    'Block',
    'Blockchain',
    'Miner',
    'Network',
    'DifficultyController'
]

# Global simulation state
_simulation_instance = None
_simulation_running = False

def start_simulation(config: dict, ui_callback) -> None:
    """Start the blockchain simulation with given configuration."""
    # TODO: Implement simulation startup logic
    global _simulation_running
    _simulation_running = True
    print(f"Starting simulation with config: {config}")

def stop_simulation() -> None:
    """Stop the running simulation."""
    # TODO: Implement simulation shutdown logic
    global _simulation_running
    _simulation_running = False
    print("Stopping simulation")

def set_miner_rate(miner_id: str, rate: float) -> None:
    """Set the hash rate for a specific miner."""
    # TODO: Implement miner rate adjustment
    print(f"Setting miner {miner_id} rate to {rate}")

def submit_data(data_str: str) -> None:
    """Submit new data to be mined into the blockchain."""
    # TODO: Implement data submission to mining queue
    print(f"Submitting data: {data_str}")

def get_stats() -> dict:
    """Get current simulation statistics."""
    # TODO: Implement stats collection
    return {
        'blocks': [],
        'mining_log': 'No mining activity',
        'active_miners': 0,
        'total_hash_rate': 0
    }
