"""
Block visualization renderer for the PoW simulator UI.
Provides HTML rendering for blockchain blocks as horizontal cards.
"""

from typing import List, Dict, Any
from datetime import datetime
from ui.helpers import short_hash

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
        return "<p>No blocks to display</p>"
    
    html_parts = [
        """
        <div style="display: flex; overflow-x: auto; gap: 10px; padding: 10px; 
                    background-color: #f8f9fa; border-radius: 8px; margin: 10px 0;">
        """
    ]
    
    for block in blocks:
        # Determine block status styling
        if block.get('accepted', True):
            border_color = "#28a745"  # Green for accepted
            status_text = "✅ Accepted"
            bg_color = "#d4edda"
        else:
            border_color = "#dc3545"  # Red for stale/rejected
            status_text = "❌ Stale"
            bg_color = "#f8d7da"
        
        # Format timestamp
        timestamp = block.get('timestamp', 0)
        if isinstance(timestamp, (int, float)):
            try:
                dt = datetime.fromtimestamp(timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except (ValueError, OSError):
                time_str = "Invalid"
        else:
            time_str = str(timestamp)
        
        # Create block card HTML
        block_html = f"""
        <div style="
            min-width: 200px; 
            padding: 12px; 
            border: 2px solid {border_color}; 
            border-radius: 8px; 
            background-color: {bg_color};
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-family: 'Courier New', monospace;
            font-size: 12px;
        ">
            <div style="font-weight: bold; margin-bottom: 8px; color: #333;">
                Block #{block.get('height', '?')}
            </div>
            
            <div style="margin-bottom: 4px;">
                <strong>Hash:</strong><br>
                <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">
                    {short_hash(block.get('hash', 'N/A'), 12)}
                </code>
            </div>
            
            <div style="margin-bottom: 4px;">
                <strong>Prev:</strong><br>
                <code style="background: #e9ecef; padding: 2px 4px; border-radius: 3px;">
                    {short_hash(block.get('prev_hash', 'N/A'), 8)}
                </code>
            </div>
            
            <div style="margin-bottom: 4px;">
                <strong>Nonce:</strong> {block.get('nonce', 'N/A')}
            </div>
            
            <div style="margin-bottom: 4px;">
                <strong>Miner:</strong> {block.get('miner_id', 'N/A')}
            </div>
            
            <div style="margin-bottom: 4px;">
                <strong>Time:</strong> {time_str}
            </div>
            
            <div style="text-align: center; margin-top: 8px; font-weight: bold;">
                {status_text}
            </div>
        </div>
        """
        
        html_parts.append(block_html)
    
    html_parts.append("</div>")
    
    return "".join(html_parts)
