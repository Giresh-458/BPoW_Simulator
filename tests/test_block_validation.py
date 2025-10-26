"""
Unit tests for block validation functionality.
"""

import unittest
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sim.core import Block, Blockchain

class TestBlockValidation(unittest.TestCase):
    """Test cases for block validation logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.blockchain = Blockchain()
        
    def test_block_creation(self):
        """Test basic block creation."""
        block = Block(
            height=1,
            prev_hash="0" * 64,
            timestamp=1234567890.0,
            data="Test data",
            nonce=12345,
            miner_id="miner_1",
            hash="abc123" * 10  # Placeholder hash
        )
        
        self.assertEqual(block.height, 1)
        self.assertEqual(block.data, "Test data")
        self.assertEqual(block.miner_id, "miner_1")
        self.assertFalse(block.accepted)  # Should be False by default
        
    def test_blockchain_initialization(self):
        """Test blockchain initialization."""
        self.assertEqual(len(self.blockchain.blocks), 0)
        self.assertEqual(self.blockchain.difficulty, 4)
        
    def test_blockchain_validate_block_callable(self):
        """Test that validate_block method is callable."""
        block = Block(
            height=1,
            prev_hash="0" * 64,
            timestamp=1234567890.0,
            data="Test data",
            nonce=12345,
            miner_id="miner_1",
            hash="abc123" * 10
        )
        
        # Should be callable and return boolean
        result = self.blockchain.validate_block(block)
        self.assertIsInstance(result, bool)
        
    def test_blockchain_add_block_callable(self):
        """Test that add_block method is callable."""
        block = Block(
            height=1,
            prev_hash="0" * 64,
            timestamp=1234567890.0,
            data="Test data",
            nonce=12345,
            miner_id="miner_1",
            hash="abc123" * 10
        )
        
        # Should be callable and return boolean
        result = self.blockchain.add_block(block)
        self.assertIsInstance(result, bool)
        
    def test_blockchain_get_latest_block(self):
        """Test getting latest block from empty blockchain."""
        latest = self.blockchain.get_latest_block()
        self.assertIsNone(latest)
        
    def test_blockchain_get_block_count(self):
        """Test getting block count."""
        count = self.blockchain.get_block_count()
        self.assertEqual(count, 0)

if __name__ == '__main__':
    unittest.main()
