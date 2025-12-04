"""
Streamlit entrypoint for Proof-of-Work blockchain simulator.
Provides UI controls and displays simulation results.
"""

import streamlit as st
import threading
import time
import json
import queue
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import simulation API
try:
    from sim_api import start_simulation, stop_simulation, reset_simulation, set_miner_rate, submit_data, get_stats
    SIM_API_AVAILABLE = True
except ImportError:
    SIM_API_AVAILABLE = False
    st.warning("⚠️ sim_api not available yet — UI loaded in mock mode")
    print("sim_api not available yet — UI loaded in mock mode")

# Import UI helpers
try:
    from ui.block_renderer import render_blocks
except ImportError:
    # Fallback if helpers don't exist yet
    def render_block_card(block: dict) -> str:
        return f"<div>Block #{block.get('height', '?')}</div>"
    def render_blocks(blocks: list) -> str:
        return "<div>No blocks</div>"

# Initialize session state
if 'events' not in st.session_state:
    st.session_state['events'] = []
if 'sim_running' not in st.session_state:
    st.session_state['sim_running'] = False
if 'event_queue' not in st.session_state:
    st.session_state['event_queue'] = queue.Queue()
if 'miner_rates' not in st.session_state:
    st.session_state['miner_rates'] = {}

def ui_callback(event: Dict[str, Any]) -> None:
    """
    Thread-safe callback function to handle simulation events.
    Called from mining threads - uses queue instead of direct session_state access.
    """
    # Use queue for thread-safe communication
    if 'event_queue' in st.session_state:
        st.session_state['event_queue'].put(event)

def process_event_queue():
    """Process events from the queue into session state."""
    try:
        while not st.session_state['event_queue'].empty():
            event = st.session_state['event_queue'].get_nowait()
            st.session_state['events'].append(event)

            # Keep only recent events to prevent memory issues
            if len(st.session_state['events']) > 1000:
                st.session_state['events'] = st.session_state['events'][-500:]
    except queue.Empty:
        pass

# Ensure we process any queued events early so metrics and logs reflect latest state
process_event_queue()

def _render_2d_blocks(fork_tree: Dict[str, Any]) -> str:
    """
    Render blocks in a simple blockchain explorer style with connections.
    Main chain horizontally, forks below.
    
    Args:
        fork_tree: Fork tree structure from get_fork_tree()
    
    Returns:
        HTML string for clean blockchain visualization
    """
    if not fork_tree or not fork_tree.get('genesis'):
        return '<div style="text-align: center; color: #999; padding: 20px;">No blocks yet</div>'
    
    genesis = fork_tree.get('genesis')
    
    # Collect all blocks by height
    def get_level_blocks(node):
        """Get blocks organized by height level."""
        levels = {}
        
        def traverse(block):
            height = block.get('height', 0)
            if height not in levels:
                levels[height] = []
            levels[height].append(block)
            
            for child in block.get('children', []):
                traverse(child)
        
        traverse(node)
        return levels
    
    levels = get_level_blocks(genesis)
    
    html = '<div style="background: #f8f9fa; padding: 20px; border-radius: 8px; overflow-x: auto;">'
    html += '<div style="margin-bottom: 10px; font-size: 12px;">'
    html += '<span style="background: #1e90ff; color: white; padding: 4px 8px; border-radius: 4px; margin-right: 10px;">■ Main Chain</span>'
    html += '<span style="background: #ff8c00; color: white; padding: 4px 8px; border-radius: 4px;">■ Stale/Fork</span>'
    html += '</div>'
    
    # Draw each height level horizontally
    for height in sorted(levels.keys()):
        blocks = levels[height]
        
        html += '<div style="display: flex; gap: 20px; margin-bottom: 30px; align-items: center; flex-wrap: wrap;">'
        
        for idx, block in enumerate(blocks):
            is_main = block.get('is_main', False)
            is_accepted = block.get('accepted', False)
            block_hash = block.get('hash', '?')[:8]
            miner_id = block.get('miner_id', '?')
            
            # Colors and styling
            if is_main:
                bg = '#1e90ff'
                text_color = 'white'
                border = '2px solid rgba(255,255,255,0.2)'
                label = '✓'
            else:
                bg = '#ff8c00'
                text_color = 'white'
                border = '2px dashed rgba(255,255,255,0.4)'
                label = '✗ STALE'
            
            # Block card
            html += f'''
            <div style="
                background: {bg};
                color: {text_color};
                padding: 12px 16px;
                border-radius: 6px;
                min-width: 110px;
                text-align: center;
                box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                border: {border};
                font-family: monospace;
            ">
                <div style="font-size: 9px; opacity: 0.8; margin-bottom: 2px;">{label}</div>
                <div style="font-weight: bold; font-size: 13px;">#{height}</div>
                <div style="font-size: 10px; margin-top: 4px;">{block_hash}</div>
                <div style="font-size: 9px; opacity: 0.7; margin-top: 2px;">{miner_id}</div>
            </div>
            '''
            
            # Add arrow between blocks (except last in row)
            if idx < len(blocks) - 1:
                html += '<div style="font-size: 20px; opacity: 0.5; margin: 0 10px;">→</div>'
        
        html += '</div>'
    
    html += '</div>'
    
    return html

# Page configuration
st.set_page_config(
    page_title="PoW Blockchain Simulator",
    page_icon="⛏️",
    layout="wide"
)

# Main title
st.title("Proof-of-Work Blockchain Simulator")

# Main layout: Left column (controls) and Right column (visualization)
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Controls")
    
    # Default block data (not shown to user)
    block_data = "PoW Block Data"
    
    # Number of miners slider
    num_miners = st.slider(
        "Number of miners",
        min_value=1,
        max_value=10,
        value=3,
        key="num_miners",
        disabled=st.session_state['sim_running']
    )
    
    # Global difficulty slider with human-friendly description
    # Get live difficulty if simulation is running
    live_difficulty = None
    if st.session_state['sim_running'] and SIM_API_AVAILABLE:
        try:
            stats = get_stats()
            if stats and 'difficulty' in stats:
                live_difficulty = stats['difficulty']
        except Exception:
            pass
    
    # Use live difficulty for slider value if available, otherwise use session state
    difficulty_value = live_difficulty if live_difficulty is not None else st.session_state.get('difficulty', 4)
    
    difficulty = st.slider(
        "Global difficulty (leading zeros)",
        min_value=0,
        max_value=8,
        value=difficulty_value,
        key="difficulty",
        disabled=st.session_state['sim_running']
    )
    
    # Difficulty description
    difficulty_descriptions = {
        0: "Very Easy (no leading zeros)",
        1: "Easy (1 leading zero)",
        2: "Medium (2 leading zeros)",
        3: "Hard (3 leading zeros)",
        4: "Very Hard (4 leading zeros)",
        5: "Extreme (5 leading zeros)",
        6: "Insane (6 leading zeros)",
        7: "Ultra Hard (7 leading zeros)",
        8: "Maximum (8 leading zeros)"
    }
    st.caption(f"Difficulty: {difficulty_descriptions.get(difficulty_value, 'Unknown')}")
    
    # Control buttons
    col_start, col_stop = st.columns(2)
    
    with col_start:
        if st.button("▶️ Start Simulation", disabled=st.session_state['sim_running']):
            # Collect miner hash rates from UI
            miner_rates = {}
            for i in range(num_miners):
                rate_key = f"miner_rate_{i}"
                if rate_key in st.session_state:
                    miner_rates[f"miner_{i+1}"] = st.session_state[rate_key]
                else:
                    miner_rates[f"miner_{i+1}"] = 500  # Default 500 H/s
            
            config = {
                'num_miners': num_miners,
                'difficulty': difficulty,
                # 'use_real_hash' removed — simulator uses internal hash model
                'data': block_data,
                'miner_rates': miner_rates
            }
            
            if SIM_API_AVAILABLE:
                start_simulation(config, ui_callback)
            else:
                st.info("Mock mode: Simulation started")
            
            st.session_state['sim_running'] = True
            st.success("Simulation started!")
            st.rerun()
    
    with col_stop:
        if st.session_state['sim_running']:
            if st.button("⏸️ Pause Simulation"):
                if SIM_API_AVAILABLE:
                    stop_simulation()
                st.session_state['sim_running'] = False
                st.success("Simulation paused!")
                st.rerun()
        else:
            if st.button("▶️ Resume Simulation"):
                # Resume with current configuration
                miner_rates = {}
                for i in range(num_miners):
                    rate_key = f"miner_rate_{i}"
                    if rate_key in st.session_state:
                        miner_rates[f"miner_{i+1}"] = st.session_state[rate_key]
                    else:
                        miner_rates[f"miner_{i+1}"] = 500
                
                # Get current difficulty from blockchain if it exists, otherwise use slider
                resume_difficulty = difficulty
                if SIM_API_AVAILABLE:
                    try:
                        stats = get_stats()
                        if stats and 'difficulty' in stats:
                            resume_difficulty = stats['difficulty']
                    except Exception:
                        pass
                
                config = {
                    'num_miners': num_miners,
                    'difficulty': resume_difficulty,
                    'data': block_data,
                    'miner_rates': miner_rates
                }
                
                if SIM_API_AVAILABLE:
                    start_simulation(config, ui_callback)
                st.session_state['sim_running'] = True
                st.success("Simulation resumed!")
                st.rerun()
    
    # Reset button
    if st.button("🔄 Reset Blockchain"):
        if SIM_API_AVAILABLE:
            reset_simulation()
        st.session_state['events'] = []
        # Clear cached visualization state
        if 'last_blocks' in st.session_state:
            del st.session_state['last_blocks']
        if 'last_fork_tree' in st.session_state:
            del st.session_state['last_fork_tree']
        st.success("Blockchain and events cleared!")
        st.rerun()
    
    # Miner rates expander
    with st.expander("Miner Rates (Hash/s)", expanded=False):
        st.caption("⚠️ Hash rates can only be set before starting the simulation")
        for i in range(num_miners):
            miner_id = f"miner_{i+1}"
            # Default progressive hash rates: 1000, 2000, 3000, etc.
            default_rate = 1000 * (i + 1)
            
            # Get saved rate or use default
            if miner_id not in st.session_state['miner_rates']:
                st.session_state['miner_rates'][miner_id] = default_rate
            
            current_rate = st.number_input(
                f"Miner {i+1} (hashes per second)",
                min_value=1,
                max_value=100000,
                value=500,  # Default 500 H/s for 1 crore hash space
                step=100,
                key=f"miner_rate_{i}",
                disabled=st.session_state['sim_running'],
                help="Number of hash attempts per second. Higher values = faster mining. Recommended: 100-1000 for realistic pacing with 1 crore hash space."
            )

with col2:


    st.markdown("**Metrics**")
    metrics_col1, metrics_col2 = st.columns(2)
    
    with metrics_col1:
        # Prefer authoritative count from sim API when available
        total_blocks = 0
        if SIM_API_AVAILABLE:
            try:
                stats = get_stats()
                if stats and 'blocks' in stats:
                    total_blocks = len(stats['blocks'])
            except Exception:
                # Fallback to events
                total_blocks = len([e for e in st.session_state['events'] if e.get('type') == 'block_accepted'])
        else:
            total_blocks = len([e for e in st.session_state['events'] if e.get('type') == 'block_accepted'])

        st.metric("Total Blocks", total_blocks)

    
    with metrics_col2:
        # Get live difficulty from simulation if running
        current_difficulty = difficulty
        if SIM_API_AVAILABLE:
            try:
                stats = get_stats()
                if stats and 'difficulty' in stats:
                    current_difficulty = stats['difficulty']
            except Exception:
                pass
        st.metric("Current Difficulty", current_difficulty)

    st.subheader(" Visualization")
    
    # Block display area with scroll
    st.markdown("**Blocks**")
    block_container = st.container()
    with block_container:
        block_area = st.empty()
    
    # 2D Block visualization area
    st.markdown("**Blockchain**")
    block_map_area = st.empty()
    

# Events are processed earlier at startup via `process_event_queue()`

# Update displays
if st.session_state['sim_running']:
    # Update block area - get blocks from stats (authoritative source)
    blocks = []
    
    if SIM_API_AVAILABLE:
        try:
            stats = get_stats()
            if stats and 'blocks' in stats:
                # Use blocks from blockchain (these have correct accepted status)
                blocks = stats['blocks']
                # Store in session state for paused view
                st.session_state['last_blocks'] = blocks
        except Exception as e:
            # Fallback to events if stats fails
            for event in st.session_state['events']:
                if event.get('type') == 'block_found' and 'block' in event:
                    event_block = event['block']
                    # Ensure accepted field exists (default to True for found blocks)
                    if 'accepted' not in event_block:
                        event_block['accepted'] = True
                    if not any(b.get('height') == event_block.get('height') for b in blocks):
                        blocks.append(event_block)
    
    if blocks:
        block_html = render_blocks(blocks)  # Show all blocks with scroll
        block_area.markdown(block_html, unsafe_allow_html=True)
    else:
        block_area.info("No blocks mined yet...")
    
    # Update 2D block visualization
    try:
        stats = get_stats()
        if stats and 'fork_tree' in stats and stats['fork_tree'] and stats['fork_tree'].get('genesis'):
            block_map_html = _render_2d_blocks(stats['fork_tree'])
            block_map_area.markdown(block_map_html, unsafe_allow_html=True)
            # Store in session state for paused view
            st.session_state['last_fork_tree'] = stats['fork_tree']
        else:
            block_map_area.info("Waiting for blocks...")
    except Exception as e:
        block_map_area.info("Blocks loading...")
    
    # Auto-refresh every 2 seconds
    time.sleep(2)
    st.rerun()
else:
    # Paused - show last known state
    # Display last known blocks
    if 'last_blocks' in st.session_state and st.session_state['last_blocks']:
        block_html = render_blocks(st.session_state['last_blocks'])
        block_area.markdown(block_html, unsafe_allow_html=True)
    else:
        block_area.info("No blocks mined yet...")
    
    # Display last known blockchain map
    if 'last_fork_tree' in st.session_state and st.session_state['last_fork_tree']:
        block_map_html = _render_2d_blocks(st.session_state['last_fork_tree'])
        block_map_area.markdown(block_map_html, unsafe_allow_html=True)
    else:
        block_map_area.info("No blocks to display")

# Add CSS styling
st.markdown("""
<style>
.block-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 10px;
    margin: 5px;
    background-color: #f9f9f9;
    display: inline-block;
    min-width: 200px;
    vertical-align: top;
}

.block-card.accepted {
    border-color: #28a745;
    background-color: #d4edda;
}

.block-card.stale {
    border-color: #6c757d;
    background-color: #e9ecef;
}

.mining-log {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 10px;
    font-family: monospace;
    font-size: 12px;
    max-height: 300px;
    overflow-y: auto;
}

.log-entry {
    margin: 2px 0;
    padding: 2px 5px;
    border-radius: 3px;
}

.log-entry.block-found {
    background-color: #d1ecf1;
    color: #0c5460;
}

.log-entry.block-accepted {
    background-color: #d4edda;
    color: #155724;
}

.log-entry.block-stale {
    background-color: #f8d7da;
    color: #721c24;
}
</style>
""", unsafe_allow_html=True)