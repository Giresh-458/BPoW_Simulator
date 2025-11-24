"""
UI rendering helper functions for blockchain visualization.
Provides HTML rendering functions for blocks, blockchain, and mining logs.
"""

from typing import List, Dict, Any
from datetime import datetime

def render_block_card(block: Dict[str, Any]) -> str:
    """
    Render a single block as an HTML card.
    
    Args:
        block: Block dictionary with height, hash, prev_hash, nonce, miner_id, timestamp, accepted
        
    Returns:
        HTML string for the block card
    """
    # Extract block data with defaults
    height = block.get('height', '?')
    block_hash = block.get('hash', 'N/A')
    prev_hash = block.get('prev_hash', 'N/A')
    nonce = block.get('nonce', 'N/A')
    miner_id = block.get('miner_id', 'N/A')
    timestamp = block.get('timestamp', 0)
    accepted = block.get('accepted', False)
    
    # Format timestamp
    try:
        dt = datetime.fromtimestamp(timestamp)
        time_str = dt.strftime('%H:%M:%S')
    except:
        time_str = 'N/A'
    
    # Determine card class and colors based on status
    if accepted:
        card_class = "block-card accepted"
        bg_color = "#d4edda"
        border_color = "#28a745"
        text_color = "#155724"
    else:
        card_class = "block-card stale"
        bg_color = "#f8d7da"
        border_color = "#dc3545"
        text_color = "#721c24"
    
    # Shorten hashes for display (convert to string if integer)
    block_hash_str = str(block_hash)
    prev_hash_str = str(prev_hash)
    short_hash = block_hash_str[:8] + "..." if len(block_hash_str) > 8 else block_hash_str
    short_prev_hash = prev_hash_str[:8] + "..." if len(prev_hash_str) > 8 else prev_hash_str
    
    html = f"""
    <div class="{card_class}" style="border: 2px solid {border_color}; border-radius: 8px; padding: 10px; margin: 5px; background-color: {bg_color}; display: inline-block; min-width: 200px; vertical-align: top; color: {text_color};">
        <div style="font-weight: bold; font-size: 14px; margin-bottom: 8px; color: {text_color};">
            Block #{height}
        </div>
        <div style="font-size: 11px; margin: 2px 0; color: {text_color};">
            <strong>Hash:</strong> {short_hash}
        </div>
        <div style="font-size: 11px; margin: 2px 0; color: {text_color};">
            <strong>Prev:</strong> {short_prev_hash}
        </div>
        <div style="font-size: 11px; margin: 2px 0; color: {text_color};">
            <strong>Nonce:</strong> {nonce}
        </div>
        <div style="font-size: 11px; margin: 2px 0; color: {text_color};">
            <strong>Miner:</strong> {miner_id}
        </div>
        <div style="font-size: 11px; margin: 2px 0; color: {text_color};">
            <strong>Time:</strong> {time_str}
        </div>
        <div style="font-size: 11px; margin: 2px 0; color: {text_color};">
            <strong>Status:</strong> {'✅ Accepted' if accepted else '❌ Stale'}
        </div>
    </div>
    """
    
    return html

def render_block_chain(blocks: List[Dict[str, Any]]) -> str:
    """
    Render a list of blocks as a horizontal flow of cards with scrolling.
    
    Args:
        blocks: List of block dictionaries
        
    Returns:
        HTML string for the blockchain visualization
    """
    if not blocks:
        return '<div style="text-align: center; color: #666; padding: 20px;">No blocks mined yet...</div>'
    
    # Render each block as a card
    block_cards = []
    for block in blocks:
        card_html = render_block_card(block)
        block_cards.append(card_html)
    
    # Wrap in a scrollable flexbox container
    html = f"""
    <div style="display: flex; flex-wrap: wrap; gap: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6; max-height: 600px; overflow-y: auto;">
        {''.join(block_cards)}
    </div>
    """
    
    return html

def render_mining_log(events: List[Dict[str, Any]], max_lines: int = 200) -> str:
    """
    Render mining events as a log display.
    
    Args:
        events: List of event dictionaries
        max_lines: Maximum number of log entries to show
        
    Returns:
        HTML string for the mining log
    """
    if not events:
        return '<div class="mining-log">No events yet...</div>'
    
    # Take only recent events
    recent_events = events[-max_lines:] if len(events) > max_lines else events
    
    log_entries = []
    for event in reversed(recent_events):  # Show newest first
        event_type = event.get('type', 'unknown')
        timestamp = event.get('timestamp', 0)
        
        # Format timestamp
        try:
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime('%H:%M:%S')
        except:
            time_str = 'N/A'
        
        # Create log entry based on event type
        if event_type == 'block_found':
            block = event.get('block', {})
            miner_id = block.get('miner_id', 'Unknown')
            height = block.get('height', '?')
            entry_class = "log-entry block-found"
            message = f"[{time_str}] Block #{height} found by {miner_id}"
            
        elif event_type == 'block_accepted':
            block = event.get('block', {})
            height = block.get('height', '?')
            entry_class = "log-entry block-accepted"
            message = f"[{time_str}] Block #{height} accepted by network"
            
        elif event_type == 'block_stale':
            block = event.get('block', {})
            height = block.get('height', '?')
            entry_class = "log-entry block-stale"
            message = f"[{time_str}] Block #{height} became stale"
            
        elif event_type == 'miner_status':
            miner_id = event.get('miner_id', 'Unknown')
            hashrate = event.get('hashrate', 0)
            entry_class = "log-entry"
            message = f"[{time_str}] {miner_id} hash rate: {hashrate} H/s"
            
        elif event_type == 'simulation_start':
            entry_class = "log-entry"
            message = f"[{time_str}] Simulation started"
            
        elif event_type == 'simulation_stop':
            entry_class = "log-entry"
            message = f"[{time_str}] Simulation stopped"
            
        else:
            # Handle unknown event types
            entry_class = "log-entry"
            message = f"[{time_str}] {event_type}: {str(event)[:100]}..."
        
        log_entries.append(f'<div class="{entry_class}">{message}</div>')
    
    # Combine all log entries
    html = f"""
    <div class="mining-log" style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 10px; font-family: monospace; font-size: 12px; max-height: 300px; overflow-y: auto;">
        {''.join(log_entries)}
    </div>
    """
    
    return html
