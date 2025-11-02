"""
Test script to verify the fixes for:
1. Computational power advantage for miners
2. Genesis block creation with prev_hash = "0" * 64
3. Block validation with PoW target enforcement
4. Difficulty applied to actual computed hashes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sim.core import Block, Blockchain
from sim.miner import Miner
from utils.hash_utils import compute_block_hash, check_hash_difficulty
import time

def test_genesis_block():
    """Test that blockchain creates genesis block with correct prev_hash."""
    print("\n=== Test 1: Genesis Block Creation ===")
    blockchain = Blockchain()
    
    # Check that blockchain has exactly one block (genesis)
    assert len(blockchain.blocks) == 1, "Blockchain should start with genesis block"
    
    genesis = blockchain.blocks[0]
    print(f"Genesis block height: {genesis.height}")
    print(f"Genesis block prev_hash: {genesis.prev_hash}")
    print(f"Genesis block hash: {genesis.hash}")
    print(f"Genesis block miner: {genesis.miner_id}")
    
    # Verify genesis block properties
    assert genesis.height == 0, "Genesis block should have height 0"
    assert genesis.prev_hash == "0" * 64, "Genesis block prev_hash should be all zeros"
    assert genesis.miner_id == "system", "Genesis block should be created by system"
    assert genesis.accepted is True, "Genesis block should be accepted"
    
    print("✓ Genesis block created correctly!")
    return blockchain

def test_hash_computation():
    """Test that hashes are computed correctly."""
    print("\n=== Test 2: Hash Computation ===")
    
    prev_hash = "0" * 64
    data = "Test Block"
    nonce = 12345
    timestamp = time.time()
    height = 1
    
    # Compute hash
    block_hash = compute_block_hash(prev_hash, data, nonce, timestamp, height)
    print(f"Computed hash: {block_hash}")
    print(f"Hash length: {len(block_hash)}")
    
    # Verify hash is 64 characters (SHA256 hex)
    assert len(block_hash) == 64, "Hash should be 64 characters (SHA256 hex)"
    
    # Compute again with same inputs - should be deterministic
    block_hash2 = compute_block_hash(prev_hash, data, nonce, timestamp, height)
    assert block_hash == block_hash2, "Hash computation should be deterministic"
    
    print("✓ Hash computation works correctly!")

def test_difficulty_checking():
    """Test that difficulty is properly enforced."""
    print("\n=== Test 3: Difficulty Enforcement ===")
    
    # Test hashes with different leading zeros
    test_cases = [
        ("0000abcd" + "0" * 56, 4, True),   # 4 leading zeros
        ("000abcd" + "0" * 57, 4, False),   # Only 3 leading zeros
        ("00000abc" + "0" * 56, 4, True),   # 5 leading zeros (still valid)
        ("abcd" + "0" * 60, 4, False),      # No leading zeros
    ]
    
    for hash_str, difficulty, expected in test_cases:
        result = check_hash_difficulty(hash_str, difficulty)
        status = "✓" if result == expected else "✗"
        print(f"{status} Hash {hash_str[:8]}... with difficulty {difficulty}: {result} (expected {expected})")
        assert result == expected, f"Difficulty check failed for {hash_str[:8]}"
    
    print("✓ Difficulty checking works correctly!")

def test_block_validation():
    """Test that block validation enforces all rules."""
    print("\n=== Test 4: Block Validation ===")
    
    blockchain = Blockchain()
    blockchain.set_difficulty(2)  # Set difficulty to 2 leading zeros
    
    # Get genesis block
    genesis = blockchain.blocks[0]
    print(f"Genesis hash: {genesis.hash}")
    
    # Try to create a valid next block
    # We need to find a nonce that gives us 2 leading zeros
    print("Mining a valid block...")
    nonce = 0
    max_attempts = 100000
    valid_block = None
    
    while nonce < max_attempts:
        block_hash = compute_block_hash(
            genesis.hash,
            "Test Data",
            nonce,
            time.time(),
            1
        )
        
        if check_hash_difficulty(block_hash, 2):
            valid_block = Block(
                height=1,
                prev_hash=genesis.hash,
                timestamp=time.time(),
                data="Test Data",
                nonce=nonce,
                miner_id="test_miner",
                hash=block_hash
            )
            print(f"Found valid block with nonce {nonce}")
            print(f"Block hash: {block_hash}")
            break
        nonce += 1
    
    if valid_block:
        # This block should be valid
        is_valid = blockchain.validate_block(valid_block)
        print(f"Valid block validation result: {is_valid}")
        assert is_valid, "Valid block should pass validation"
        
        # Add it to blockchain
        added = blockchain.add_block(valid_block)
        assert added, "Valid block should be added"
        assert len(blockchain.blocks) == 2, "Blockchain should have 2 blocks"
        print("✓ Valid block accepted!")
        
        # Test invalid block - wrong prev_hash
        invalid_block = Block(
            height=2,
            prev_hash="wrong_hash",
            timestamp=time.time(),
            data="Invalid",
            nonce=0,
            miner_id="test",
            hash="0" * 64
        )
        is_valid = blockchain.validate_block(invalid_block)
        print(f"Invalid block (wrong prev_hash) validation result: {is_valid}")
        assert not is_valid, "Block with wrong prev_hash should fail validation"
        print("✓ Invalid block rejected!")
        
        # Test invalid block - doesn't meet difficulty
        easy_hash = "abcdef" + "0" * 58  # No leading zeros
        invalid_block2 = Block(
            height=2,
            prev_hash=valid_block.hash,
            timestamp=time.time(),
            data="Invalid",
            nonce=0,
            miner_id="test",
            hash=easy_hash
        )
        is_valid = blockchain.validate_block(invalid_block2)
        print(f"Invalid block (doesn't meet difficulty) validation result: {is_valid}")
        assert not is_valid, "Block not meeting difficulty should fail validation"
        print("✓ Block not meeting difficulty rejected!")
    else:
        print("⚠ Could not find valid block in max attempts")

def test_computational_power():
    """Test that miners with more hash rate have advantage."""
    print("\n=== Test 5: Computational Power Advantage ===")
    
    from utils.hash_utils import fast_hash_check
    
    # Test with different hash rates
    difficulty = 4
    num_attempts = 1000
    
    # Low hash rate miner
    low_successes = 0
    for nonce in range(num_attempts):
        if fast_hash_check(nonce, difficulty, hash_rate_multiplier=1.0):
            low_successes += 1
    
    # High hash rate miner (10x more powerful)
    high_successes = 0
    for nonce in range(num_attempts):
        if fast_hash_check(nonce, difficulty, hash_rate_multiplier=10.0):
            high_successes += 1
    
    print(f"Low hash rate (1.0x) successes: {low_successes}/{num_attempts}")
    print(f"High hash rate (10.0x) successes: {high_successes}/{num_attempts}")
    
    # High hash rate should have more successes
    # Allow some variance due to randomness
    assert high_successes > low_successes, "Higher hash rate should have more successes"
    print("✓ Computational power advantage works!")

def test_chain_continuity():
    """Test that blocks properly chain together."""
    print("\n=== Test 6: Blockchain Continuity ===")
    
    blockchain = Blockchain()
    blockchain.set_difficulty(1)  # Low difficulty for faster testing
    
    print(f"Starting with genesis block (height {blockchain.blocks[0].height})")
    
    # Add 3 blocks
    for i in range(1, 4):
        latest = blockchain.get_latest_block()
        print(f"\nMining block {i}...")
        print(f"Previous block hash: {latest.hash[:16]}...")
        
        # Mine a valid block
        nonce = 0
        while nonce < 100000:
            block_hash = compute_block_hash(
                latest.hash,
                f"Block {i} Data",
                nonce,
                time.time(),
                i
            )
            
            if check_hash_difficulty(block_hash, 1):
                new_block = Block(
                    height=i,
                    prev_hash=latest.hash,
                    timestamp=time.time(),
                    data=f"Block {i} Data",
                    nonce=nonce,
                    miner_id=f"miner_{i}",
                    hash=block_hash
                )
                
                if blockchain.add_block(new_block):
                    print(f"✓ Block {i} added successfully")
                    print(f"  Hash: {block_hash[:16]}...")
                    print(f"  Prev: {new_block.prev_hash[:16]}...")
                    break
            nonce += 1
    
    # Verify chain continuity
    print(f"\nFinal blockchain has {len(blockchain.blocks)} blocks")
    for i, block in enumerate(blockchain.blocks):
        print(f"Block {i}: height={block.height}, hash={block.hash[:16]}..., prev={block.prev_hash[:16]}...")
        if i > 0:
            assert block.prev_hash == blockchain.blocks[i-1].hash, f"Block {i} prev_hash doesn't match"
    
    print("✓ Blockchain continuity verified!")

if __name__ == "__main__":
    print("=" * 60)
    print("BLOCKCHAIN FIXES VERIFICATION TEST")
    print("=" * 60)
    
    try:
        test_genesis_block()
        test_hash_computation()
        test_difficulty_checking()
        test_block_validation()
        test_computational_power()
        test_chain_continuity()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
