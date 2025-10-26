"""
Log rendering utilities for the PoW simulator UI.
Provides formatted log display for mining events and simulation activities.
"""

from typing import List, Dict, Any
from datetime import datetime

def render_logs(events: List[Dict[str, Any]], limit: int = 200) -> str:
    """
    Render events as a formatted log display (reverse chronological).
    
    Args:
        events: List of event dictionaries
        limit: Maximum number of events to display
    
    Returns:
        HTML formatted log string
    """
    if not events:
        return """
        <div style="padding: 20px; text-align: center; color: #666; font-style: italic;">
            No events yet. Start the simulation to see mining activity.
        </div>
        """
    
    # Sort events by timestamp (most recent first)
    sorted_events = sorted(events, key=lambda x: x.get('timestamp', 0), reverse=True)
    
    # Limit the number of events
    recent_events = sorted_events[:limit]
    
    html_parts = [
        """
        <div style="
            background-color: #1e1e1e; 
            color: #ffffff; 
            padding: 15px; 
            border-radius: 8px; 
            font-family: 'Courier New', monospace; 
            font-size: 12px; 
            max-height: 400px; 
            overflow-y: auto;
            border: 1px solid #333;
        ">
        """
    ]
    
    for event in recent_events:
        timestamp = event.get('timestamp', 0)
        
        # Format timestamp
        if isinstance(timestamp, (int, float)):
            try:
                dt = datetime.fromtimestamp(timestamp)
                time_str = dt.strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
            except (ValueError, OSError):
                time_str = "Invalid"
        else:
            time_str = str(timestamp)
        
        event_type = event.get('type', 'unknown')
        message = event.get('message', '')
        
        # Color coding based on event type
        if event_type == 'block_found':
            color = "#00ff00"  # Green
            icon = "⛏️"
        elif event_type == 'block_accepted':
            color = "#00ff00"  # Green
            icon = "✅"
        elif event_type == 'simulation_start':
            color = "#00bfff"  # Blue
            icon = "🚀"
        elif event_type == 'simulation_stop':
            color = "#ff6b6b"  # Red
            icon = "⏹️"
        elif event_type == 'miner_status':
            color = "#ffd700"  # Gold
            icon = "⚡"
        elif event_type == 'difficulty_adjusted':
            color = "#ff8c00"  # Orange
            icon = "📊"
        elif event_type == 'data_submission':
            color = "#9370db"  # Purple
            icon = "📤"
        else:
            color = "#ffffff"  # White
            icon = "ℹ️"
        
        # Create log entry
        log_entry = f"""
        <div style="margin-bottom: 8px; padding: 4px 0; border-bottom: 1px solid #333;">
            <span style="color: #888;">[{time_str}]</span>
            <span style="color: {color}; font-weight: bold;">{icon} {event_type.upper()}</span>
            <span style="color: #ffffff;">{message}</span>
        """
        
        # Add additional details for specific event types
        if event_type == 'block_found' and 'block' in event:
            block = event['block']
            log_entry += f"""
            <div style="margin-left: 20px; color: #ccc; font-size: 11px;">
                Block #{block.get('height', '?')} | Hash: {block.get('hash', 'N/A')[:16]}... | Miner: {block.get('miner_id', 'N/A')}
            </div>
            """
        elif event_type == 'miner_status':
            miner_id = event.get('miner_id', 'N/A')
            hashrate = event.get('hashrate', 0)
            log_entry += f"""
            <div style="margin-left: 20px; color: #ccc; font-size: 11px;">
                {miner_id}: {hashrate:,.0f} H/s
            </div>
            """
        elif event_type == 'difficulty_adjusted':
            old_diff = event.get('old_difficulty', 'N/A')
            new_diff = event.get('new_difficulty', 'N/A')
            log_entry += f"""
            <div style="margin-left: 20px; color: #ccc; font-size: 11px;">
                {old_diff} → {new_diff}
            </div>
            """
        
        log_entry += "</div>"
        html_parts.append(log_entry)
    
    html_parts.append("</div>")
    
    return "".join(html_parts)
