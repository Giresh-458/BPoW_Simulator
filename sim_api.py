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
import math

# Global simulation state
_simulation_lock = threading.Lock()
_simulation_running = False
_simulation_paused = False
_blockchain: Blockchain = None
_miners: List[Miner] = []
_network: Network = None
_difficulty_controller: DifficultyController = None
_ui_callback: Callable = None
_event_queue = None
_pruning_thread: threading.Thread = None
_pruning_active = False
_recent_block_times: list[float] = []
_accepted_count = 0
_stale_count = 0
_network_delay = 0.1  # seconds

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
            if ui_callback:
                try:
                    ui_callback({
                        'timestamp': time.time(),
                        'type': 'log',
                        'message': '[BLOCKCHAIN] New blockchain initialized'
                    })
                except Exception:
                    pass
        else:
            if ui_callback:
                try:
                    ui_callback({
                        'timestamp': time.time(),
                        'type': 'log',
                        'message': f'[BLOCKCHAIN] Resuming blockchain at height {_blockchain.get_block_count()}'
                    })
                except Exception:
                    pass
            
        _miners = []
        _network = Network()
        _difficulty_controller = DifficultyController()
        _ui_callback = ui_callback
        
        # Configure blockchain with provided difficulty
        new_difficulty = config.get('difficulty', 4)
        _blockchain.set_difficulty(new_difficulty)
        # Sync difficulty controller with blockchain
        _difficulty_controller.current_difficulty = new_difficulty
        
        # Create miners with configured hash rates
        num_miners = config.get('num_miners', 3)
        miner_rates = config.get('miner_rates', {})
        for i in range(num_miners):
            miner_id = f"miner_{i+1}"
            hash_rate = miner_rates.get(miner_id, 500)  # Default 500 H/s for 1 crore hash space
            miner = Miner(miner_id, hash_rate=hash_rate)
            _miners.append(miner)
            if ui_callback:
                try:
                    ui_callback({
                        'timestamp': time.time(),
                        'type': 'log',
                        'message': f'Created {miner_id} with hash rate: {hash_rate} H/s'
                    })
                except Exception:
                    pass
            
        # Start network
        _network.start()
        
        # Set initial work and start miners
        head = _blockchain.get_latest_block()
        prev_hash = head.hash if head else 0
        height = head.height if head else 0
        # Stagger miner startups slightly to avoid initial burst
        for miner in _miners:
            miner.start(
                on_block_found=_on_block_found,
                blockchain=_blockchain,
                use_real_sha256=config.get('use_real_sha256', False),
                difficulty=config.get('difficulty', 4),
                data=config.get('data', 'Hello Blockchain!')
            )
            time.sleep(0.02)

        # Configure network delay from UI config (milliseconds)
        try:
            delay_ms = float(config.get('network_delay_ms', 100))
            global _network_delay
            _network_delay = max(0.0, delay_ms / 1000.0)
        except Exception:
            pass

        # Broadcast initial work (head/difficulty/data) to all miners
        _broadcast_new_work_to_miners()
        # Adjust difficulty based on current total hash rate to simulate network stability
        _apply_difficulty_for_hash_rate()
        
        # Start branch pruning thread
        global _pruning_thread, _pruning_active
        _pruning_active = True
        _pruning_thread = threading.Thread(target=_pruning_loop, daemon=True)
        _pruning_thread.start()
            
        _simulation_running = True
        
        # Notify UI with genesis block
        if _ui_callback:
            _ui_callback({
                'timestamp': time.time(),
                'message': f'Started simulation with {num_miners} miners',
                'type': 'simulation_start'
            })
            
            # Send genesis block to UI
            main_chain = _blockchain.get_main_chain()
            genesis_block = main_chain[0] if main_chain else None
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
    global _simulation_running, _pruning_active, _simulation_paused
    
    with _simulation_lock:
        if not _simulation_running:
            return
        
        # Stop pruning thread
        _pruning_active = False
            
        # Stop all miners
        for miner in _miners:
            miner.stop()
            
        # Stop network
        if _network:
            _network.stop()
            
        _simulation_running = False
        _simulation_paused = False
        
        # Notify UI
        if _ui_callback:
            _ui_callback({
                'timestamp': time.time(),
                'message': 'Simulation stopped',
                'type': 'simulation_stop'
            })

def pause_simulation() -> None:
    """Pause miners without stopping the simulation components."""
    global _simulation_paused
    with _simulation_lock:
        if not _simulation_running or _simulation_paused:
            return
        _simulation_paused = True
        for miner in _miners:
            miner.pause()
        if _ui_callback:
            _ui_callback({
                'timestamp': time.time(),
                'message': 'Simulation paused',
                'type': 'simulation_pause'
            })

def resume_simulation() -> None:
    """Resume miners if simulation is paused."""
    global _simulation_paused
    with _simulation_lock:
        if not _simulation_running or not _simulation_paused:
            return
        _simulation_paused = False
        for miner in _miners:
            miner.resume()
        # Broadcast current work to ensure miners sync to latest head/difficulty
        _broadcast_new_work_to_miners()
        # Recompute difficulty against active miners/hash rate
        _apply_difficulty_for_hash_rate()
        if _ui_callback:
            _ui_callback({
                'timestamp': time.time(),
                'message': 'Simulation resumed',
                'type': 'simulation_resume'
            })

def reset_simulation() -> None:
    """Reset the blockchain and all simulation state."""
    global _blockchain, _miners, _network, _difficulty_controller, _simulation_running, _pruning_active
    
    with _simulation_lock:
        # Stop simulation if running
        if _simulation_running:
            _pruning_active = False
            for miner in _miners:
                miner.stop()
            if _network:
                _network.stop()
            _simulation_running = False
        
        # Reset all global state
        _blockchain = None
        _miners = []
        _network = None
        _difficulty_controller = None
        # Reset counters
        global _recent_block_times, _accepted_count, _stale_count
        _recent_block_times = []
        _accepted_count = 0
        _stale_count = 0
        
        print("[RESET] Blockchain and simulation state cleared")

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
        # Re-apply difficulty targets based on aggregate hash rate
        _apply_difficulty_for_hash_rate()

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
                'difficulty': 0,
                'fork_tree': None
            }
            
        # Collect main chain block data with accepted status
        blocks = []
        try:
            main_chain = _blockchain.get_main_chain()
        except Exception:
            main_chain = []

        for block in main_chain:
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
        
        # Get fork tree for visualization
        try:
            fork_tree = _blockchain.get_fork_tree()
        except Exception:
            fork_tree = None
            
        # Calculate mining stats
        active_miners = sum(1 for miner in _miners if miner.is_mining and not miner.paused)
        total_hash_rate = sum(miner.hash_rate for miner in _miners)
        
        # Derive simple stability metrics
        fork_rate = 0.0
        total = _accepted_count + _stale_count
        if total > 0:
            fork_rate = _stale_count / total

        return {
            'blocks': blocks,
            'mining_log': f'Active miners: {active_miners}, Total hash rate: {total_hash_rate:.2f}',
            'active_miners': active_miners,
            'total_hash_rate': total_hash_rate,
            'difficulty': _difficulty_controller.get_current_difficulty() if _difficulty_controller else 0,
            'fork_tree': fork_tree,
            'recent_block_times': list(_recent_block_times),
            'avg_block_time': (sum(_recent_block_times)/len(_recent_block_times)) if _recent_block_times else None,
            'stale_count': _stale_count,
            'accepted_count': _accepted_count,
            'fork_rate': fork_rate,
            'network_delay_ms': int(_network_delay * 1000),
            'paused': _simulation_paused
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
        if _ui_callback:
            try:
                _ui_callback({
                    'timestamp': time.time(),
                    'type': 'log',
                    'message': f'[MINING] [{block.miner_id}] Found block #{block.height} with hash {block.hash} (nonce: {block.nonce})'
                })
            except Exception:
                pass
        
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
        # Put into internal event queue and notify UI via callback (if available)
        try:
            _event_queue.put(discovery_event)
        except Exception:
            pass
        if _ui_callback:
            try:
                _ui_callback(discovery_event)
            except Exception:
                pass

        # Queue block for delivery through network with delay
        network_delay = _network_delay  # configurable network delay
        
        # Schedule delayed acceptance via a callback
        # (in a real network, blocks would propagate over the network with latency)
        # Add small jitter to delay to avoid synchronized accepts
        jitter = min(0.2, max(0.0, network_delay * 0.2))
        delay = network_delay + (jitter * (0.5 - (time.time() % 1)))
        threading.Timer(
            max(0.0, delay),
            lambda: _accept_block_delayed(block, prev_head, discovery_event)
        ).start()

        # END OF NEW DELAYED NETWORK LOGIC


def _accept_block_delayed(block, prev_head, discovery_event) -> None:
    """
    Accept a block after network delay (called via Timer).
    
    Args:
        block: The block to accept
        prev_head: The previous chain head
        discovery_event: The discovery event that was already sent
    """
    with _simulation_lock:
        if not _simulation_running:
            return
        
        # Now validate and add the block
        added = _blockchain.add_block(block)
        _process_block_acceptance(block, added, prev_head, discovery_event)


def _process_block_acceptance(block, added, prev_head, discovery_event) -> None:
    """
    Process the result of block validation and acceptance.
    
    Args:
        block: The block that was validated
        added: Whether the block was added to the chain
        prev_head: The previous chain head
        discovery_event: The discovery event that was sent
    """
    if added:
        if _ui_callback:
            try:
                _ui_callback({
                    'timestamp': time.time(),
                    'type': 'log',
                    'message': f'[ACCEPTED] Block #{block.height} ACCEPTED by network (hash: {block.hash}, prev: {block.prev_hash})'
                })
            except Exception:
                pass
        accepted_event = discovery_event.copy()
        accepted_event['timestamp'] = time.time()
        accepted_event['message'] = f'Block #{block.height} accepted (by {block.miner_id})'
        accepted_event['type'] = 'block_accepted'
        accepted_event['block']['accepted'] = True
        try:
            _event_queue.put(accepted_event)
        except Exception:
            pass
        if _ui_callback:
            try:
                _ui_callback(accepted_event)
            except Exception:
                pass

        # If we had a previous head, compute block time
        if prev_head:
            block_time = block.timestamp - prev_head.timestamp
            if _difficulty_controller:
                _difficulty_controller.record_block_time(block_time)
            # Track recent block times (limit to last 20)
            try:
                global _recent_block_times, _accepted_count
                _recent_block_times.append(block_time)
                _recent_block_times = _recent_block_times[-20:]
                _accepted_count += 1
            except Exception:
                pass

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
        if _ui_callback:
            try:
                _ui_callback({
                    'timestamp': time.time(),
                    'type': 'log',
                    'message': f'[REJECTED] Block #{block.height} REJECTED/STALE from {block.miner_id} (hash: {block.hash})\n           Reason: Block doesn\'t meet validation (likely mining on old chain head)'
                })
            except Exception:
                pass
        stale_event = discovery_event.copy()
        stale_event['timestamp'] = time.time()
        stale_event['message'] = f'Block #{block.height} from {block.miner_id} is stale/rejected'
        stale_event['type'] = 'block_stale'
        stale_event['block']['accepted'] = False
        try:
            _event_queue.put(stale_event)
        except Exception:
            pass
        if _ui_callback:
            try:
                _ui_callback(stale_event)
            except Exception:
                pass

        # Update miners with current head (in case the head changed due to another block)
        _broadcast_new_work_to_miners()
        # Count stale
        try:
            global _stale_count
            _stale_count += 1
        except Exception:
            pass

def set_network_delay_ms(ms: int) -> None:
    """Update network propagation delay (ms) for block acceptance."""
    global _network_delay
    with _simulation_lock:
        try:
            _network_delay = max(0.0, float(ms) / 1000.0)
            if _event_queue:
                _event_queue.put({
                    'timestamp': time.time(),
                    'message': f'Network delay set to {ms} ms',
                    'type': 'network_delay_update',
                    'network_delay_ms': ms
                })
        except Exception:
            pass


def _pruning_loop() -> None:
    """
    Background thread that periodically prunes old fork branches and adjusts difficulty if mining is too slow.
    Runs every 5 seconds while simulation is active.
    """
    global _pruning_active, _blockchain, _difficulty_controller, _miners
    
    last_block_height = 0
    time_at_last_block = time.time()
    
    while _pruning_active:
        try:
            time.sleep(5)  # Check every 5 seconds
            
            if _blockchain and _simulation_running:
                with _simulation_lock:
                    # Prune branches that are more than 10 blocks behind main tip
                    pruned_count = _blockchain.prune_old_branches(max_depth_behind=10)
                    
                    if pruned_count > 0:
                        if _ui_callback:
                            try:
                                _ui_callback({
                                    'timestamp': time.time(),
                                    'type': 'log',
                                    'message': f'[PRUNING] Removed {pruned_count} old fork block(s)'
                                })
                            except Exception:
                                pass
                        
                        # Optionally notify UI about pruning
                        if _ui_callback:
                            try:
                                _ui_callback({
                                    'timestamp': time.time(),
                                    'message': f'Pruned {pruned_count} old fork block(s)',
                                    'type': 'pruning',
                                    'blocks_pruned': pruned_count
                                })
                            except Exception:
                                pass
                    
                    # Check if difficulty should be decreased due to timeout
                    current_height = _blockchain.get_block_count()
                    current_time = time.time()
                    
                    if current_height > last_block_height:
                        # New block mined, reset timer
                        last_block_height = current_height
                        time_at_last_block = current_time
                    else:
                        # No new block, check if we've waited too long
                        time_since_last_block = current_time - time_at_last_block
                        
                        # If no block for 15 seconds, decrease difficulty by 1
                        if time_since_last_block > 15 and _difficulty_controller:
                            current_diff = _difficulty_controller.get_current_difficulty()
                            if current_diff > 1:
                                new_difficulty = current_diff - 1  # Drop by exactly 1
                                _difficulty_controller.current_difficulty = new_difficulty
                                _blockchain.set_difficulty(new_difficulty)
                                
                                # Update miners' difficulty
                                for miner in _miners:
                                    miner.difficulty = new_difficulty
                                
                                # Broadcast new work with updated difficulty
                                _broadcast_new_work_to_miners()
                                
                                if _ui_callback:
                                    try:
                                        _ui_callback({
                                            'timestamp': time.time(),
                                            'type': 'log',
                                            'message': f'[TIMEOUT] No block for {time_since_last_block:.1f}s, decreasing difficulty to {new_difficulty}'
                                        })
                                    except Exception:
                                        pass
                                
                                # Notify UI
                                if _event_queue:
                                    _event_queue.put({
                                        'timestamp': time.time(),
                                        'message': f'Difficulty decreased to {new_difficulty} due to timeout',
                                        'type': 'difficulty_update',
                                        'difficulty': new_difficulty
                                    })
                                
                                # Reset timer after adjustment
                                time_at_last_block = current_time
                                
        except Exception as e:
            print(f"[PRUNING ERROR] {e}")
            pass

def _apply_difficulty_for_hash_rate() -> None:
    """Adjust difficulty based on total hash rate/active miners to simulate network tuning.

    Educational heuristic: higher aggregate hash rate increases difficulty;
    lower aggregate hash rate decreases difficulty, bounded to [1, 8].
    """
    global _blockchain, _difficulty_controller
    if not _blockchain:
        return
    try:
        total_hash_rate = sum(miner.hash_rate for miner in _miners if miner.is_mining and not miner.paused)
        # Simple bucketed mapping for clarity in UI
        # <1.5k -> 2, <3k -> 3, <6k -> 4, <12k -> 5, else 6
        if total_hash_rate < 1500:
            desired = 2
        elif total_hash_rate < 3000:
            desired = 3
        elif total_hash_rate < 6000:
            desired = 4
        elif total_hash_rate < 12000:
            desired = 5
        else:
            desired = 6

        desired = max(1, min(8, desired))

        current = _difficulty_controller.get_current_difficulty() if _difficulty_controller else _blockchain.difficulty
        if desired != current:
            _blockchain.set_difficulty(desired)
            if _difficulty_controller:
                _difficulty_controller.current_difficulty = desired
            for miner in _miners:
                miner.difficulty = desired
            _broadcast_new_work_to_miners()
            if _event_queue:
                _event_queue.put({
                    'timestamp': time.time(),
                    'message': f'Difficulty auto-adjusted to {desired} (active hash rate: {total_hash_rate:.0f} H/s)',
                    'type': 'difficulty_update',
                    'difficulty': desired
                })
    except Exception:
        pass
