"""
Core blockchain data structures and validation logic.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Any
import time
import threading
from utils.hash_utils import compute_block_hash, hash_meets_difficulty

@dataclass
class Block:
    """Represents a single block in the blockchain."""
    height: int
    prev_hash: str
    timestamp: float
    data: str
    nonce: int
    miner_id: str
    hash: Optional[int] = None
    accepted: bool = False
    
    def __post_init__(self):
        """Validate block data and compute hash if not provided."""
        if self.hash is None:
            # Compute hash using all block components
            self.hash = compute_block_hash(
                self.prev_hash, 
                self.height, 
                self.timestamp, 
                self.data, 
                self.nonce, 
                self.miner_id
            )

class Blockchain:
    """Manages the blockchain state and validation."""
    
    def __init__(self):
        """Initialize blockchain with genesis block."""
        # All known blocks by hash (including forks)
        self._blocks: Dict[str, Block] = {}
        # Main chain (list of blocks from genesis -> tip)
        self._main_chain: List[Block] = []
        self.difficulty = 4  # Default difficulty
        self._lock = threading.Lock()  # Thread safety for concurrent mining

        # Create genesis block
        self._create_genesis_block()
        
    def _create_genesis_block(self) -> None:
        """Create the genesis block (first block in the chain)."""
        from utils.hash_utils import compute_block_hash
        
        genesis_timestamp = time.time()
        genesis_prev_hash = "0" * 64  # Genesis block has no previous hash
        genesis_data = "Genesis Block"
        genesis_nonce = 0
        genesis_miner_id = "genesis"
        genesis_height = 0
        
        # Compute genesis hash
        genesis_hash = compute_block_hash(
            genesis_prev_hash, genesis_height, genesis_timestamp,
            genesis_data, genesis_nonce, genesis_miner_id
        )
        
        genesis_block = Block(
            height=0,
            prev_hash=genesis_prev_hash,
            timestamp=genesis_timestamp,
            data=genesis_data,
            nonce=genesis_nonce,
            miner_id=genesis_miner_id,
            hash=genesis_hash,
            accepted=True
        )

        # Register genesis in blocks and main chain
        self._blocks[str(genesis_block.hash)] = genesis_block
        self._main_chain = [genesis_block]
        
    def add_block(self, block: Block) -> bool:
        """
        Add a new block to the blockchain.
        
        Args:
            block: The block to add
            
        Returns:
            True if block was added successfully, False otherwise
        """
        with self._lock:
            # Validate block before adding (ensures prev exists and hash/timestamp/difficulty ok)
            if not self.validate_block(block):
                return False

            # Register block in global pool
            self._blocks[str(block.hash)] = block

            # Update tips / main chain: check whether this block extends an existing chain
            # We consider chain length via block.height
            # If the new block's height is greater than current main chain tip, switch main chain
            current_tip = self._main_chain[-1]
            if block.height > current_tip.height:
                # Attempt to build the chain back to genesis
                chain = []
                cursor = block
                while True:
                    chain.append(cursor)
                    if str(cursor.prev_hash) in self._blocks:
                        cursor = self._blocks[str(cursor.prev_hash)]
                        # Stop if we reach genesis
                        if cursor.height == 0:
                            chain.append(cursor)
                            break
                    else:
                        # Missing ancestor — cannot make it main chain
                        chain = None
                        break

                if chain:
                    # Reconstruct main chain from genesis to new tip
                    new_main = list(reversed(chain))
                    # Mark accepted flags appropriately
                    for b in self._main_chain:
                        b.accepted = False
                    for b in new_main:
                        b.accepted = True

                    self._main_chain = new_main
                    return True

            # If block does not extend the main chain tip to a longer chain, it's a fork/orphan
            # Still keep it in _blocks for visualization, just mark as not accepted
            block.accepted = False
            # Block is already in _blocks (added at line 96), so it will appear in fork tree
            return False
    
    def validate_block(self, block: Block) -> bool:
        """
        Validate a block before adding it to the blockchain.
        
        Performs comprehensive validation:
        1. Hash recomputation and verification
        2. Difficulty requirement check
        3. Timestamp validation (not too far in future, monotonic)
        4. Chain continuity (prev_hash, height)
        
        Args:
            block: The block to validate
            
        Returns:
            True if block is valid, False otherwise
        """
        # 1. Recompute hash and verify it matches
        computed_hash = compute_block_hash(
            block.prev_hash,
            block.height,
            block.timestamp,
            block.data,
            block.nonce,
            block.miner_id,
        )

        if computed_hash != block.hash:
            return False

        # 2. Check if hash meets difficulty requirement
        if not hash_meets_difficulty(block.hash, self.difficulty):
            return False

        # 3. Validate timestamp
        current_time = time.time()
        # Block timestamp cannot be more than 2 hours in the future
        if block.timestamp > current_time + 7200:
            return False

        # 4. Validate continuity: prev_hash must be known (we don't accept unknown orphans)
        if block.height == 0:
            return True

        prev_key = str(block.prev_hash)
        if prev_key not in self._blocks:
            # previous block unknown — reject
            return False

        prev_block = self._blocks[prev_key]
        # Check height is incremental
        if block.height != prev_block.height + 1:
            return False

        # Check timestamp is monotonic (not earlier than previous block)
        if block.timestamp < prev_block.timestamp:
            return False

        return True
    
    def get_latest_block(self) -> Optional[Block]:
        """Get the most recent block in the blockchain."""
        with self._lock:
            return self._main_chain[-1] if self._main_chain else None
    
    def get_block_count(self) -> int:
        """Get the total number of blocks in the blockchain."""
        with self._lock:
            return len(self._main_chain)
    
    def set_difficulty(self, difficulty: int) -> None:
        """Set the mining difficulty for new blocks."""
        self.difficulty = difficulty

    def get_main_chain(self) -> List[Block]:
        """Return the current main chain (genesis -> tip)."""
        with self._lock:
            return list(self._main_chain)

    def get_all_blocks(self) -> Dict[str, Block]:
        """Return all known blocks including forks."""
        with self._lock:
            return dict(self._blocks)

    def get_fork_tree(self) -> Dict[str, Any]:
        """
        Build a tree structure showing all branches (main chain and forks).
        
        Returns:
            Dictionary with 'genesis' key containing tree starting from genesis.
        """
        with self._lock:
            # Build a map of children for each block
            children_map: Dict[str, List[Block]] = {}
            for block in self._blocks.values():
                parent_key = str(block.prev_hash)
                if parent_key not in children_map:
                    children_map[parent_key] = []
                children_map[parent_key].append(block)
            
            # Sort children by height (descending) so longest chains appear first
            for children in children_map.values():
                children.sort(key=lambda b: b.height, reverse=True)
            
            # Recursively build tree
            def build_tree(block: Block) -> Dict[str, Any]:
                block_hash = str(block.hash)
                children_list = children_map.get(block_hash, [])
                
                is_main = block in self._main_chain
                
                return {
                    'hash': block_hash,
                    'height': block.height,
                    'miner_id': block.miner_id,
                    'is_main': is_main,
                    'accepted': block.accepted,
                    'timestamp': block.timestamp,
                    'children': [build_tree(child) for child in children_list]
                }
            
            # Start from genesis
            genesis = self._main_chain[0] if self._main_chain else None
            if genesis:
                return {'genesis': build_tree(genesis), 'tip_height': len(self._main_chain) - 1}
            return {'genesis': None, 'tip_height': 0}

    def prune_old_branches(self, max_depth_behind: int = 10) -> int:
        """
        Remove blocks from shorter branches that fell behind the main chain.
        This prevents memory growth from accumulating old fork blocks.
        
        Args:
            max_depth_behind: Blocks at heights more than this many blocks behind
                             the main tip will be pruned (except main chain blocks).
        
        Returns:
            Number of blocks pruned.
        """
        with self._lock:
            if not self._main_chain:
                return 0
            
            main_tip_height = self._main_chain[-1].height
            threshold_height = max(0, main_tip_height - max_depth_behind)
            
            blocks_to_remove = []
            for block_hash, block in self._blocks.items():
                # Never remove blocks on the main chain
                if block in self._main_chain:
                    continue
                
                # Remove blocks that are too far behind
                if block.height < threshold_height:
                    blocks_to_remove.append(block_hash)
            
            for block_hash in blocks_to_remove:
                del self._blocks[block_hash]
            
            return len(blocks_to_remove)

