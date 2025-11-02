"""
API wrapper between Streamlit UI and simulation core.
Provides thread-safe interface for simulation control.
"""

import threading
import time
import queue
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
_event_queue: queue.Queue = queue.Queue()

def start_simulation(config: Dict[str, Any], ui_callback: Callable = None) -> None:
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
        
        # Create miners
        num_miners = config.get('num_miners', 3)
        for i in range(num_miners):
            miner = Miner(f"miner_{i+1}", hash_rate=1.0)
            _miners.append(miner)
            
        # Start network
        _network.start()
        
        # Set initial work and start miners
        head = _blockchain.get_latest_block()
        prev_hash = head.hash if head else "0"*64
        height = head.height if head else 0
        for miner in _miners:
            miner.set_work(prev_hash, height, config.get('data','Hello Blockchain!'), _blockchain.difficulty)
            miner.start(
                on_block_found=_on_block_found,
                use_real_sha256=config.get('use_real_sha256', False),
                difficulty=_blockchain.difficulty,
                data=config.get('data', 'Hello Blockchain!')
            )
            
        _simulation_running = True
        
        # Add start event to queue
        _event_queue.put({
            'timestamp': time.time(),
            'message': f'Started simulation with {num_miners} miners',
            'type': 'simulation_start'
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
        
        # Add stop event to queue
        _event_queue.put({
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
            
        # Update all miners with new data while preserving their current work
        head = _blockchain.get_latest_block()
        prev_hash = head.hash if head else "0" * 64
        height = head.height if head else 0
        for miner in _miners:
            miner.set_work(prev_hash, height, data_str, _blockchain.difficulty)
            
        # Add data submission event to queue
        _event_queue.put({
            'timestamp': time.time(),
            'message': f'Submitted data: {data_str}',
            'type': 'data_submission'
        })

def get_pending_events() -> List[Dict[str, Any]]:
    """
    Get all pending events from the event queue.
    This should be called from the main thread (Streamlit).
    
    Returns:
        List of pending events
    """
    events = []
    try:
        while True:
            event = _event_queue.get_nowait()
            events.append(event)
    except queue.Empty:
        pass
    return events

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
            
        # Collect block data
        blocks = []
        for block in _blockchain.blocks:
            blocks.append({
                'height': block.height,
                'hash': block.hash,
                'miner_id': block.miner_id,
                'data': block.data,
                'timestamp': block.timestamp,
                'nonce': block.nonce
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

def _broadcast_new_work_to_miners():
    """Set current head/difficulty as work for all miners."""
    head = _blockchain.get_latest_block()
    prev_hash = head.hash if head else "0" * 64
    height = head.height if head else 0
    current_data = _miners[0].current_data if _miners else 'Hello Blockchain!'
    current_difficulty = _blockchain.difficulty
    for miner in _miners:
        try:
            miner.set_work(prev_hash, height, current_data, current_difficulty)
        except Exception:
            pass

def _on_block_found(block) -> None:
    """
    Callback when a miner finds a new block.
    
    Args:
        block: The newly found block
    """
    with _simulation_lock:
        if not _simulation_running:
            return

        # Capture previous head to compute block interval
        prev_head = _blockchain.get_latest_block()

        # Announce that a block was found (discovery)
        discovery_event = {
            'timestamp': time.time(),
            'message': f'Block discovered (candidate) by {block.miner_id}',
            'type': 'block_found',
            'block': {
                'height': block.height,
                'hash': block.hash,
                'prev_hash': block.prev_hash,
                'miner_id': block.miner_id,
                'data': block.data,
                'timestamp': block.timestamp,
                'nonce': block.nonce,
                'accepted': False
            }
        }
        _event_queue.put(discovery_event)

        # Try to add block to blockchain (validation happens inside)
        added = _blockchain.add_block(block)

        if added:
            accepted_event = discovery_event.copy()
            accepted_event['timestamp'] = time.time()
            accepted_event['message'] = f'Block #{block.height} accepted (by {block.miner_id})'
            accepted_event['type'] = 'block_accepted'
            accepted_event['block']['accepted'] = True
            _event_queue.put(accepted_event)

            # If we had a previous head, compute block time
            if prev_head:
                block_time = block.timestamp - prev_head.timestamp
                if _difficulty_controller:
                    _difficulty_controller.record_block_time(block_time)

                    # Adjust difficulty if controller desires
                    if _difficulty_controller.should_adjust_difficulty():
                        new_difficulty = _difficulty_controller.adjust_difficulty(_difficulty_controller.block_times)
                        _blockchain.set_difficulty(new_difficulty)
                        # Update miners' difficulty/work
                        for miner in _miners:
                            miner.difficulty = new_difficulty
                        # Broadcast the change
                        _event_queue.put({
                            'timestamp': time.time(),
                            'message': f'Difficulty adjusted to {new_difficulty}',
                            'type': 'difficulty_update',
                            'difficulty': new_difficulty
                        })

            # Broadcast new work (new head) to miners
            _broadcast_new_work_to_miners()

        else:
            stale_event = discovery_event.copy()
            stale_event['timestamp'] = time.time()
            stale_event['message'] = f'Block #{block.height} from {block.miner_id} is stale/rejected'
            stale_event['type'] = 'block_stale'
            stale_event['block']['accepted'] = False
            _event_queue.put(stale_event)

            # Update miners with current head (in case the head changed due to another block)
            _broadcast_new_work_to_miners()
