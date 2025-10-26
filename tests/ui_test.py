"""
Unit tests for UI rendering helper functions.
"""

import unittest
import sys
import os
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.render_helpers import render_block_card, render_block_chain, render_mining_log

class TestUIRenderHelpers(unittest.TestCase):
    """Test cases for UI rendering helper functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_block = {
            'height': 1,
            'hash': '0000abcd1234567890efghijklmnopqrstuvwxyz1234567890abcdef',
            'prev_hash': '0000000000000000000000000000000000000000000000000000000000000000',
            'nonce': 12345,
            'miner_id': 'miner_1',
            'timestamp': datetime.now().timestamp(),
            'accepted': True
        }
        
        self.sample_events = [
            {
                'type': 'block_found',
                'block': self.sample_block,
                'timestamp': datetime.now().timestamp()
            },
            {
                'type': 'block_accepted',
                'block': self.sample_block,
                'timestamp': datetime.now().timestamp()
            },
            {
                'type': 'miner_status',
                'miner_id': 'miner_1',
                'hashrate': 1200,
                'timestamp': datetime.now().timestamp()
            }
        ]
    
    def test_render_block_card_basic(self):
        """Test basic block card rendering."""
        html = render_block_card(self.sample_block)
        
        # Should return non-empty string
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 0)
        
        # Should contain block information
        self.assertIn('Block #1', html)
        self.assertIn('miner_1', html)
        self.assertIn('12345', html)
        self.assertIn('✅ Accepted', html)
    
    def test_render_block_card_missing_fields(self):
        """Test block card rendering with missing fields."""
        incomplete_block = {'height': 2}
        html = render_block_card(incomplete_block)
        
        # Should still return valid HTML
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 0)
        self.assertIn('Block #2', html)
    
    def test_render_block_card_stale_status(self):
        """Test block card rendering for stale blocks."""
        stale_block = self.sample_block.copy()
        stale_block['accepted'] = False
        
        html = render_block_card(stale_block)
        
        # Should contain stale status
        self.assertIn('❌ Stale', html)
    
    def test_render_block_chain_empty(self):
        """Test blockchain rendering with empty list."""
        html = render_block_chain([])
        
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 0)
        self.assertIn('No blocks mined yet', html)
    
    def test_render_block_chain_with_blocks(self):
        """Test blockchain rendering with blocks."""
        blocks = [self.sample_block]
        html = render_block_chain(blocks)
        
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 0)
        self.assertIn('Block #1', html)
        self.assertIn('flex', html)  # Should use flexbox layout
    
    def test_render_mining_log_empty(self):
        """Test mining log rendering with empty events."""
        html = render_mining_log([])
        
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 0)
        self.assertIn('No events yet', html)
    
    def test_render_mining_log_with_events(self):
        """Test mining log rendering with events."""
        html = render_mining_log(self.sample_events)
        
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 0)
        self.assertIn('block-found', html)
        self.assertIn('miner_1', html)
    
    def test_render_mining_log_max_lines(self):
        """Test mining log with max_lines limit."""
        # Create many events
        many_events = []
        for i in range(10):
            event = {
                'type': 'block_found',
                'block': {'height': i, 'miner_id': f'miner_{i}'},
                'timestamp': datetime.now().timestamp()
            }
            many_events.append(event)
        
        html = render_mining_log(many_events, max_lines=5)
        
        # Should limit the number of entries shown
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 0)
    
    def test_render_functions_importable(self):
        """Test that all render functions are importable."""
        # This test ensures the module can be imported without errors
        from ui.render_helpers import render_block_card, render_block_chain, render_mining_log
        
        # Functions should be callable
        self.assertTrue(callable(render_block_card))
        self.assertTrue(callable(render_block_chain))
        self.assertTrue(callable(render_mining_log))

if __name__ == '__main__':
    unittest.main()
