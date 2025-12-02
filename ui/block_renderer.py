"""
Block visualization renderer for the PoW simulator UI.
Provides HTML rendering for blockchain blocks as horizontal cards.
"""

from typing import List, Dict, Any
from datetime import datetime
import html

def short_hash(hash_value: Any, length: int = 8) -> str:
    """Shorten a hash for display."""
    hash_str = str(hash_value)
    if len(hash_str) > length:
        return hash_str[:length] + "..."
    return hash_str

def render_blocks(blocks: List[Dict[str, Any]]) -> str:
    """
    Render a horizontal strip of block cards as HTML.
    
    Args:
        blocks: List of block dictionaries with fields:
                height, hash, prev_hash, nonce, miner_id, timestamp, accepted
    
    Returns:
        HTML string for rendering block cards
    """
    if not blocks:
        return '<p style="text-align: center; color: #666; padding: 20px;">No blocks to display</p>'
    
    # Start container
    html_output = '<div style="display: flex; overflow-x: auto; gap: 12px; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; margin: 10px 0; box-shadow: inset 0 2px 10px rgba(0,0,0,0.2);">'
    
    for block in blocks:
        # Determine block status styling
        accepted = block.get('accepted', True)
        
        if accepted:
            border_color = "#28a745"
            status_text = "✅ Accepted"
            bg_color = "#d4edda"
            bg_gradient = "#c3e6cb"
            text_color = "#155724"
        else:
            border_color = "#dc3545"
            status_text = "❌ Stale"
            bg_color = "#f8d7da"
            bg_gradient = "#f1b0b7"
            text_color = "#721c24"
        
        # Format timestamp
        timestamp = block.get('timestamp', 0)
        if isinstance(timestamp, (int, float)) and timestamp > 0:
            try:
                dt = datetime.fromtimestamp(timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except (ValueError, OSError):
                time_str = "Invalid"
        else:
            time_str = "N/A"
        
        # Get and escape values
        height = html.escape(str(block.get('height', '?')))
        block_hash = html.escape(str(block.get('hash', 'N/A')))
        prev_hash = html.escape(str(block.get('prev_hash', 'N/A')))
        nonce = html.escape(str(block.get('nonce', 'N/A')))
        miner_id = html.escape(str(block.get('miner_id', 'N/A')))
        
        # Shorten hashes
        short_block_hash = short_hash(block_hash, 12)
        short_prev_hash = short_hash(prev_hash, 8)
        
        # Build block card
        html_output += f'''
<div style="min-width: 220px; max-width: 220px; padding: 16px; border: 3px solid {border_color}; border-radius: 12px; background: linear-gradient(145deg, {bg_color}, {bg_gradient}); box-shadow: 0 4px 8px rgba(0,0,0,0.15), 0 1px 3px rgba(0,0,0,0.1); font-family: Segoe UI, Tahoma, sans-serif; font-size: 12px; color: {text_color};">
<div style="font-weight: bold; margin-bottom: 8px; font-size: 14px;">Block #{height}</div>
<div style="margin-bottom: 6px;"><strong>Hash:</strong><br><span style="background: #fff; padding: 3px 6px; border-radius: 4px; color: #000; font-family: Courier New, monospace; font-size: 11px; display: inline-block; margin-top: 2px;">{short_block_hash}</span></div>
<div style="margin-bottom: 6px;"><strong>Prev:</strong><br><span style="background: #fff; padding: 3px 6px; border-radius: 4px; color: #000; font-family: Courier New, monospace; font-size: 11px; display: inline-block; margin-top: 2px;">{short_prev_hash}</span></div>
<div style="margin-bottom: 4px;"><strong>Nonce:</strong> {nonce}</div>
<div style="margin-bottom: 4px;"><strong>Miner:</strong> {miner_id}</div>
<div style="margin-bottom: 8px;"><strong>Time:</strong> {time_str}</div>
<div style="text-align: center; margin-top: 8px; padding: 4px; font-weight: bold; border-top: 1px solid {border_color};">{status_text}</div>
</div>
'''
    
    # Close container
    html_output += '</div>'
    
    return html_output