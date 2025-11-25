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
_event_queue = None

def start_simulation(config: Dict[str, Any], ui_callback: Callable) -> None:
    """
    Start the blockchain simulation with given configuration.
    
    Args:
        config: Simulation configuration dictionary
        ui_callback: Function to call for UI updates
    """
    global _simulation_running, _blockchain, _miners, _network, _difficulty_controller, _ui_callback, _event_queue
    
    with _simulation_lock:
        if _simulation_running:
            return
        
        # Initialize event queue for UI updates
        import queue
        _event_queue = queue.Queue()
            
        # Initialize simulation components (reuse blockchain if it exists)
        if _blockchain is None:
            _blockchain = Blockchain()
            print("\n[BLOCKCHAIN] New blockchain initialized")
        else:
            print(f"\n[BLOCKCHAIN] Resuming blockchain at height {len(_blockchain.blocks)}")
            
        _miners = []
        _network = Network()
        _difficulty_controller = DifficultyController()
        _ui_callback = ui_callback
        
        # Configure blockchain
        _blockchain.set_difficulty(config.get('difficulty', 4))
        
        # Create miners with configured hash rates
        num_miners = config.get('num_miners', 3)
        miner_rates = config.get('miner_rates', {})
        for i in range(num_miners):
            miner_id = f"miner_{i+1}"
            hash_rate = miner_rates.get(miner_id, 500)  # Default 500 H/s for 1 crore hash space
            miner = Miner(miner_id, hash_rate=hash_rate)
            _miners.append(miner)
            print(f"Created {miner_id} with hash rate: {hash_rate} H/s")
            
        # Start network
        _network.start()
        
        # Set initial work and start miners
        head = _blockchain.get_latest_block()
        prev_hash = head.hash if head else 0
        height = head.height if head else 0
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
            
        # Update all miners with new data while preserving their current work
        head = _blockchain.get_latest_block()
        prev_hash = head.hash if head else 0
        height = head.height if head else 0
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

def _broadcast_new_work_to_miners():
    """Set current head/difficulty as work for all miners."""
    head = _blockchain.get_latest_block()
    prev_hash = head.hash if head else 0
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
        print(f"\n[MINING] [{block.miner_id}] Found block #{block.height} with hash {block.hash} (nonce: {block.nonce})")
        
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
            print(f"[ACCEPTED] Block #{block.height} ACCEPTED by network (hash: {block.hash}, prev: {block.prev_hash})")
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
            # STALE BLOCK EXPLANATION:
            # A block becomes "stale" when it's rejected by validation.
            # Common reasons:
            # 1. Built on old chain head (another miner found a block first)
            # 2. Hash doesn't meet difficulty requirement
            # 3. Invalid prev_hash (doesn't match current chain tip)
            # 4. Timestamp issues (too far in future, or not monotonic)
            # This is normal in PoW - miners sometimes work on outdated chain state.
            print(f"[REJECTED] Block #{block.height} REJECTED/STALE from {block.miner_id} (hash: {block.hash})")
            print(f"           Reason: Block doesn't meet validation (likely mining on old chain head)")
            stale_event = discovery_event.copy()
            stale_event['timestamp'] = time.time()
            stale_event['message'] = f'Block #{block.height} from {block.miner_id} is stale/rejected'
            stale_event['type'] = 'block_stale'
            stale_event['block']['accepted'] = False
            _event_queue.put(stale_event)

            # Update miners with current head (in case the head changed due to another block)
            _broadcast_new_work_to_miners()
