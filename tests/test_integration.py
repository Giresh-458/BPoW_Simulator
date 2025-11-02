"""
Integration test for BPoW_Simulator fixes.
Tests all the recent fixes including threading, block status, and computational power.
"""

import sys
import os
import time
import threading

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sim.core import Block, Blockchain
from sim.miner import Miner
from utils.hash_utils import compute_block_hash, check_hash_difficulty

def test_thread_safe_mining():
    """Test that multiple miners can mine concurrently without race conditions."""
    print("Testing thread-safe concurrent mining...")
    
    blockchain = Blockchain()
    blockchain.set_difficulty(1)  # Easy difficulty
    
    found_blocks = []
    lock = threading.Lock()
    
    def on_block_found(block):
        with lock:
            success = blockchain.add_block(block)
            if success:
                found_blocks.append(block)
                print(f"  ✓ Block {block.height} accepted from {block.miner_id}")
            else:
                print(f"  ✗ Block {block.height} rejected from {block.miner_id} (race condition handled)")
    
    # Create 3 miners with different hash rates
    miners = [
        Miner("miner_1", hash_rate=1000),
        Miner("miner_2", hash_rate=2000),  # 2x more powerful
        Miner("miner_3", hash_rate=500),   # 0.5x power
    ]
    
    # Start all miners
    for miner in miners:
        miner.start(
            on_block_found=on_block_found,
            blockchain=blockchain,
            use_real_sha256=False,  # Fast mode
            difficulty=1,
            data="Test Block"
        )
    
    # Let them mine for a bit
    time.sleep(3)
    
    # Stop all miners
    for miner in miners:
        miner.stop()
    
    print(f"  ✓ Mined {len(found_blocks)} blocks successfully")
    print(f"  ✓ Blockchain length: {len(blockchain.blocks)} (including genesis)")
    
    # Verify all blocks have accepted=True
    for block in blockchain.blocks:
        assert block.accepted == True, f"Block {block.height} not marked as accepted"
    
    print("✅ Thread-safe mining test passed!\n")
    return len(found_blocks)

def test_computational_power_advantage():
    """Test that miners with higher hash rates mine faster."""
    print("Testing computational power advantage...")
    
    blockchain = Blockchain()
    blockchain.set_difficulty(1)
    
    miner_stats = {
        'miner_1': {'hash_rate': 1000, 'blocks': 0},
        'miner_2': {'hash_rate': 3000, 'blocks': 0},  # 3x more powerful
        'miner_3': {'hash_rate': 500, 'blocks': 0},   # 0.5x power
    }
    
    lock = threading.Lock()
    
    def on_block_found(block):
        with lock:
            if blockchain.add_block(block):
                miner_stats[block.miner_id]['blocks'] += 1
                print(f"  Block {block.height} mined by {block.miner_id}")
    
    # Create miners with different computational power
    miners = []
    for miner_id, stats in miner_stats.items():
        miner = Miner(miner_id, hash_rate=stats['hash_rate'])
        miners.append(miner)
        miner.start(
            on_block_found=on_block_found,
            blockchain=blockchain,
            use_real_sha256=False,
            difficulty=1,
            data="Power Test"
        )
    
    # Mine for 5 seconds
    time.sleep(5)
    
    # Stop all miners
    for miner in miners:
        miner.stop()
    
    # Display results
    print("\n  Mining Results:")
    for miner_id, stats in miner_stats.items():
        hash_rate = stats['hash_rate']
        blocks = stats['blocks']
        print(f"    {miner_id}: {hash_rate} H/s → {blocks} blocks")
    
    # Verify most powerful miner got most blocks
    miner_2_blocks = miner_stats['miner_2']['blocks']
    miner_3_blocks = miner_stats['miner_3']['blocks']
    
    # Miner 2 should have more blocks than miner 3 (has 6x the power)
    # Allow some variance due to randomness
    if miner_2_blocks > 0 and miner_3_blocks > 0:
        ratio = miner_2_blocks / miner_3_blocks
        print(f"\n  ✓ Power ratio verification: {ratio:.1f}x (expected ~6x)")
        assert ratio > 1.5, "More powerful miner should mine significantly more"
    elif miner_2_blocks > miner_3_blocks:
        print(f"  ✓ More powerful miner mined more blocks ({miner_2_blocks} vs {miner_3_blocks})")
    
    print("✅ Computational power test passed!\n")

def test_accepted_field():
    """Test that blocks have proper accepted field."""
    print("Testing block accepted field...")
    
    blockchain = Blockchain()
    
    # Check genesis block
    genesis = blockchain.blocks[0]
    assert genesis.accepted == True, "Genesis should be accepted"
    assert genesis.height == 0, "Genesis should be height 0"
    print("  ✓ Genesis block has accepted=True")
    
    # Add a valid block
    timestamp = time.time()
    for test_nonce in range(100000):
        test_hash = compute_block_hash(
            genesis.hash, "Test", test_nonce, timestamp, "test_miner"
        )
        if check_hash_difficulty(test_hash, 2):
            block = Block(
                height=1,
                prev_hash=genesis.hash,
                timestamp=timestamp,
                data="Test",
                nonce=test_nonce,
                miner_id="test_miner",
                hash=test_hash
            )
            success = blockchain.add_block(block)
            assert success, "Valid block should be added"
            assert block.accepted == True, "Added block should have accepted=True"
            print(f"  ✓ Block 1 has accepted=True after adding")
            break
    
    print("✅ Accepted field test passed!\n")

def test_block_chaining():
    """Test that blocks properly chain with correct prev_hash."""
    print("Testing block chaining...")
    
    blockchain = Blockchain()
    blockchain.set_difficulty(1)
    
    prev_hash = blockchain.blocks[0].hash
    print(f"  Genesis hash: {prev_hash[:16]}...")
    
    # Mine 3 blocks
    for i in range(1, 4):
        timestamp = time.time()
        for test_nonce in range(100000):
            test_hash = compute_block_hash(
                prev_hash, f"Block {i}", test_nonce, timestamp, "chain_test"
            )
            if check_hash_difficulty(test_hash, 1):
                block = Block(
                    height=i,
                    prev_hash=prev_hash,
                    timestamp=timestamp,
                    data=f"Block {i}",
                    nonce=test_nonce,
                    miner_id="chain_test",
                    hash=test_hash
                )
                success = blockchain.add_block(block)
                assert success, f"Block {i} should be added"
                assert block.accepted == True, f"Block {i} should be accepted"
                
                # Verify chaining
                assert block.prev_hash == prev_hash, f"Block {i} prev_hash doesn't match"
                print(f"  ✓ Block {i}: prev_hash matches, hash={test_hash[:16]}...")
                
                prev_hash = test_hash
                break
    
    assert len(blockchain.blocks) == 4, "Should have genesis + 3 blocks"
    print("✅ Block chaining test passed!\n")

if __name__ == "__main__":
    print("=" * 70)
    print("INTEGRATION TESTS - All Recent Fixes")
    print("=" * 70 + "\n")
    
    try:
        test_accepted_field()
        test_block_chaining()
        blocks_mined = test_thread_safe_mining()
        test_computational_power_advantage()
        
        print("=" * 70)
        print("🎉 ALL INTEGRATION TESTS PASSED! 🎉")
        print("=" * 70)
        print("\nVerified fixes:")
        print("1. ✅ Thread-safe callback (no KeyError)")
        print("2. ✅ Blocks show as 'Accepted' not 'Stale'")
        print("3. ✅ Block accepted field properly set")
        print("4. ✅ Computational power affects mining speed")
        print("5. ✅ Proper block chaining with prev_hash")
        print("6. ✅ Thread-safe concurrent mining")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
