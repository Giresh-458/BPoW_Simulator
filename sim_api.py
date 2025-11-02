"""
API wrapper between Streamlit UI and simulation core.
Provides thread-safe interface for simulation control.
"""

import threading
import time
from typing import Dict, Any, Callable, List
from sim.core import Blockchain
from sim.miner import Miner
from sim.network import Network
from sim.difficulty import DifficultyController

# Global simulation state
_simulation_lock = threading.Lock()
_simulation_running = False
_blockchain: Blockchain = None
_miners: List[Miner] = []
_network: Network = None
_difficulty_controller: DifficultyController = None
_ui_callback: Callable = None

def start_simulation(config: Dict[str, Any], ui_callback: Callable) -> None:
    """
    Start the blockchain simulation with given configuration.
    
    Args:
        config: Simulation configuration dictionary
        ui_callback: Function to call for UI updates
    """
    global _simulation_running, _blockchain, _miners, _network, _difficulty_controller, _ui_callback
    
    with _simulation_lock:
        if _simulation_running:
            return
            
        # Initialize simulation components
        _blockchain = Blockchain()
        _miners = []
        _network = Network()
        _difficulty_controller = DifficultyController()
        _ui_callback = ui_callback
        
        # Configure blockchain
        _blockchain.set_difficulty(config.get('difficulty', 4))
        
        # Create miners with configured hash rates (computational power)
        num_miners = config.get('num_miners', 3)
        miner_rates = config.get('miner_rates', {})
        
        for i in range(num_miners):
            miner_id = f"miner_{i+1}"
            # Use configured rate or default progressive rate
            hash_rate = miner_rates.get(miner_id, 1000 * (i + 1))
            miner = Miner(miner_id, hash_rate=hash_rate)
            _miners.append(miner)
            
        # Start network
        _network.start()
        
        # Start miners with blockchain reference
        for miner in _miners:
            miner.start(
                on_block_found=_on_block_found,
                blockchain=_blockchain,
                use_real_sha256=config.get('use_real_sha256', False),
                difficulty=config.get('difficulty', 4),
                data=config.get('data', 'Hello Blockchain!')
            )
            
        _simulation_running = True
        
        # Notify UI with genesis block
        if _ui_callback:
            _ui_callback({
                'timestamp': time.time(),
                'message': f'Started simulation with {num_miners} miners',
                'type': 'simulation_start'
            })
            
            # Send genesis block to UI
            genesis_block = _blockchain.blocks[0] if _blockchain.blocks else None
            if genesis_block:
                _ui_callback({
                    'timestamp': time.time(),
                    'message': f'Genesis block created (height 0)',
                    'type': 'block_found',
                    'block': {
                        'height': genesis_block.height,
                        'hash': genesis_block.hash,
                        'prev_hash': genesis_block.prev_hash,
                        'nonce': genesis_block.nonce,
                        'miner_id': genesis_block.miner_id,
                        'timestamp': genesis_block.timestamp,
                        'accepted': genesis_block.accepted
                    }
                })

def stop_simulation() -> None:
    """Stop the running simulation."""
    global _simulation_running
    
    with _simulation_lock:
        if not _simulation_running:
            return
            
        # Stop all miners
        for miner in _miners:
            miner.stop()
            
        # Stop network
        if _network:
            _network.stop()
            
        _simulation_running = False
        
        # Notify UI
        if _ui_callback:
            _ui_callback({
                'timestamp': time.time(),
                'message': 'Simulation stopped',
                'type': 'simulation_stop'
            })

def set_miner_rate(miner_id: str, rate: float) -> None:
    """
    Set the hash rate for a specific miner.
    
    Args:
        miner_id: ID of the miner to update
        rate: New hash rate
    """
    with _simulation_lock:
        if not _simulation_running:
            return
            
        for miner in _miners:
            if miner.id == miner_id:
                miner.set_hash_rate(rate)
                break

def submit_data(data_str: str) -> None:
    """
    Submit new data to be mined into the blockchain.
    
    Args:
        data_str: Data to include in next block
    """
    with _simulation_lock:
        if not _simulation_running:
            return
            
        # TODO: Implement data submission to mining queue
        # This should update all miners with new data to mine
        for miner in _miners:
            miner.current_data = data_str
            
        if _ui_callback:
            _ui_callback({
                'timestamp': time.time(),
                'message': f'Submitted data: {data_str}',
                'type': 'data_submission'
            })

def get_stats() -> Dict[str, Any]:
    """
    Get current simulation statistics.
    
    Returns:
        Dictionary containing simulation stats
    """
    with _simulation_lock:
        if not _simulation_running:
            return {
                'blocks': [],
                'mining_log': 'Simulation not running',
                'active_miners': 0,
                'total_hash_rate': 0,
                'difficulty': 0
            }
            
        # Collect block data with accepted status
        blocks = []
        for block in _blockchain.blocks:
            blocks.append({
                'height': block.height,
                'hash': block.hash,
                'prev_hash': block.prev_hash,
                'miner_id': block.miner_id,
                'data': block.data,
                'timestamp': block.timestamp,
                'nonce': block.nonce,
                'accepted': block.accepted  # Include accepted status
            })
            
        # Calculate mining stats
        active_miners = sum(1 for miner in _miners if miner.is_mining)
        total_hash_rate = sum(miner.hash_rate for miner in _miners)
        
        return {
            'blocks': blocks,
            'mining_log': f'Active miners: {active_miners}, Total hash rate: {total_hash_rate:.2f}',
            'active_miners': active_miners,
            'total_hash_rate': total_hash_rate,
            'difficulty': _difficulty_controller.get_current_difficulty() if _difficulty_controller else 0
        }

def _on_block_found(block) -> None:
    """
    Callback when a miner finds a new block.
    
    Args:
        block: The newly found block
    """
    with _simulation_lock:
        if not _simulation_running:
            return
            
        # Add block to blockchain
        if _blockchain.add_block(block):
            # Notify UI with block dictionary
            if _ui_callback:
                _ui_callback({
                    'timestamp': time.time(),
                    'message': f'Block #{block.height} found by {block.miner_id}',
                    'type': 'block_found',
                    'block': {
                        'height': block.height,
                        'hash': block.hash,
                        'prev_hash': block.prev_hash,
                        'nonce': block.nonce,
                        'miner_id': block.miner_id,
                        'timestamp': block.timestamp,
                        'accepted': block.accepted  # Include accepted status
                    }
                })
                
            # Record block time for difficulty adjustment
            if _difficulty_controller:
                # TODO: Calculate actual block time
                _difficulty_controller.record_block_time(10.0)  # Placeholder
                
                # Adjust difficulty if needed
                if _difficulty_controller.should_adjust_difficulty():
                    new_difficulty = _difficulty_controller.adjust_difficulty(_difficulty_controller.block_times)
                    _blockchain.set_difficulty(new_difficulty)
                    
                    # Update all miners with new difficulty
                    for miner in _miners:
                        miner.difficulty = new_difficulty
