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
        <div style="display: flex; overflow-x: auto; gap: 12px; padding: 15px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 12px; 
                    margin: 10px 0;
                    box-shadow: inset 0 2px 10px rgba(0,0,0,0.2);">
        """
    ]
    
    for block in blocks:
        # Determine block status styling
        if block.get('accepted', True):
            border_color = "#28a745"  # Green for accepted
            status_text = "✅ Accepted"
            bg_color = "#d4edda"
            text_color = "#155724"  # Dark green text
        else:
            border_color = "#dc3545"  # Red for stale/rejected
            status_text = "❌ Stale"
            bg_color = "#f8d7da"
            text_color = "#721c24"  # Dark red text
        
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
        
        # Create block card HTML with improved styling
        block_html = f"""
        <div style="
            min-width: 220px;
            max-width: 220px;
            padding: 16px; 
            border: 3px solid {border_color}; 
            border-radius: 12px; 
            background: linear-gradient(145deg, {bg_color}, {'#c3e6cb' if block.get('accepted', True) else '#f1b0b7'});
            box-shadow: 0 4px 8px rgba(0,0,0,0.15), 0 1px 3px rgba(0,0,0,0.1);
            font-family: 'Segoe UI', 'Courier New', monospace;
            font-size: 12px;
            color: {text_color};
        ">
            <div style="font-weight: bold; margin-bottom: 8px; color: {text_color};">
                Block #{block.get('height', '?')}
            </div>
            
            <div style="margin-bottom: 4px; color: {text_color};">
                <strong>Hash:</strong><br>
                <code style="background: #fff; padding: 2px 4px; border-radius: 3px; color: #000;">
                    {short_hash(block.get('hash', 'N/A'), 12)}
                </code>
            </div>
            
            <div style="margin-bottom: 4px; color: {text_color};">
                <strong>Prev:</strong><br>
                <code style="background: #fff; padding: 2px 4px; border-radius: 3px; color: #000;">
                    {short_hash(block.get('prev_hash', 'N/A'), 8)}
                </code>
            </div>
            
            <div style="margin-bottom: 4px; color: {text_color};">
                <strong>Nonce:</strong> {block.get('nonce', 'N/A')}
            </div>
            
            <div style="margin-bottom: 4px; color: {text_color};">
                <strong>Miner:</strong> {block.get('miner_id', 'N/A')}
            </div>
            
            <div style="margin-bottom: 4px; color: {text_color};">
                <strong>Time:</strong> {time_str}
            </div>
            
            <div style="text-align: center; margin-top: 8px; font-weight: bold; color: {text_color};">
                {status_text}
            </div>
        </div>
        """
        
        html_parts.append(block_html)
    
    html_parts.append("</div>")
    
    return "".join(html_parts)
