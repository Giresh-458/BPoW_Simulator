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
    from sim_api import start_simulation, stop_simulation, set_miner_rate, submit_data, get_stats
    SIM_API_AVAILABLE = True
except ImportError:
    SIM_API_AVAILABLE = False
    st.warning("⚠️ sim_api not available yet — UI loaded in mock mode")
    print("sim_api not available yet — UI loaded in mock mode")

# Import UI helpers
try:
    from ui.render_helpers import render_block_card, render_block_chain, render_mining_log
except ImportError:
    # Fallback if helpers don't exist yet
    def render_block_card(block: dict) -> str:
        return f"<div>Block #{block.get('height', '?')}</div>"
    def render_block_chain(blocks: list) -> str:
        return "<div>No blocks</div>"
    def render_mining_log(events: list, max_lines: int = 200) -> str:
        return "No events"

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

# Page configuration
st.set_page_config(
    page_title="PoW Blockchain Simulator",
    page_icon="⛏️",
    layout="wide"
)

# Main title
st.title("⛏️ Proof-of-Work Blockchain Simulator")

# Main layout: Left column (controls) and Right column (visualization)
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🎛️ Controls")
    
    # Block data input
    block_data = st.text_input(
        "Block data / message",
        value="Hello Blockchain!",
        key="block_data",
        disabled=st.session_state['sim_running']
    )
    
    # Use real SHA-256 checkbox
    use_real_hash = st.checkbox(
        "Use real SHA-256",
        value=False,
        key="use_real_hash",
        disabled=st.session_state['sim_running']
    )
    
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
    difficulty = st.slider(
        "Global difficulty (leading zeros)",
        min_value=0,
        max_value=6,
        value=4,
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
        6: "Insane (6 leading zeros)"
    }
    st.caption(f"Difficulty: {difficulty_descriptions.get(difficulty, 'Unknown')}")
    
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
                'use_real_hash': use_real_hash,
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
        if st.button("⏹️ Stop Simulation", disabled=not st.session_state['sim_running']):
            if SIM_API_AVAILABLE:
                stop_simulation()
            else:
                st.info("Mock mode: Simulation stopped")
            
            st.session_state['sim_running'] = False
            st.success("Simulation stopped!")
            st.rerun()
    
    # Reset events button
    if st.button("🔄 Reset Events"):
        st.session_state['events'] = []
        st.success("Events cleared!")
        st.rerun()
    
    # Submit data button
    if st.button("📤 Submit Data", disabled=not st.session_state['sim_running']):
        if SIM_API_AVAILABLE:
            submit_data(block_data)
        else:
            st.info("Mock mode: Data submitted")
        st.success(f"Submitted: {block_data}")
    
    # Download events button
    if st.button("💾 Download Events (JSON)"):
        events_json = json.dumps(st.session_state['events'], indent=2, default=str)
        st.download_button(
            label="Download JSON",
            data=events_json,
            file_name=f"pow_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    # Miner rates expander
    with st.expander("⚡ Miner Rates (Hash/s)", expanded=False):
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
    st.subheader("📊 Visualization")
    
    # Block display area with scroll
    st.markdown("**🔗 Blockchain (scrollable)**")
    block_container = st.container()
    with block_container:
        block_area = st.empty()
    
    # Mining log area
    st.markdown("**📝 Mining Log**")
    mining_log = st.empty()
    
    # Metrics area
    st.markdown("**📈 Metrics**")
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
    
    with metrics_col1:
        total_blocks = len([e for e in st.session_state['events'] if e.get('type') == 'block_found'])
        st.metric("Total Blocks", total_blocks)
    
    with metrics_col2:
        accepted_blocks = len([e for e in st.session_state['events'] if e.get('type') == 'block_accepted'])
        st.metric("Accepted Blocks", accepted_blocks)
    
    with metrics_col3:
        stale_blocks = len([e for e in st.session_state['events'] if e.get('type') == 'block_stale'])
        st.metric("Stale Blocks", stale_blocks)
    
    # Additional metrics
    metrics_col4, metrics_col5 = st.columns(2)
    
    with metrics_col4:
        st.metric("Current Difficulty", difficulty)
    
    with metrics_col5:
        # Calculate average block time from events
        block_times = []
        for event in st.session_state['events']:
            if event.get('type') == 'block_found' and 'timestamp' in event:
                block_times.append(event['timestamp'])
        
        if len(block_times) > 1:
            avg_time = (max(block_times) - min(block_times)) / max(len(block_times) - 1, 1)
            st.metric("Avg Block Time", f"{avg_time:.1f}s")
        else:
            st.metric("Avg Block Time", "N/A")
    
    # Selected miner details
    st.markdown("**👤 Selected Miner Details**")
    
    # Get active miners from events
    active_miners = set()
    for event in st.session_state['events']:
        if 'miner_id' in event:
            active_miners.add(event['miner_id'])
    
    if active_miners:
        selected_miner = st.selectbox(
            "Select Miner",
            options=list(active_miners),
            index=0
        )
        
        # Show last nonce and hash for selected miner
        last_nonce = "N/A"
        last_hash = "N/A"
        
        for event in reversed(st.session_state['events']):
            if (event.get('type') == 'block_found' and 
                event.get('block', {}).get('miner_id') == selected_miner):
                last_nonce = event['block'].get('nonce', 'N/A')
                last_hash = event['block'].get('hash', 'N/A')[:16] + "..."
                break
        
        st.text(f"Last Nonce: {last_nonce}")
        st.text(f"Last Hash: {last_hash}")
    else:
        st.info("No active miners")

# Process events from queue (thread-safe)
process_event_queue()

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
        block_html = render_block_chain(blocks)  # Show all blocks with scroll
        block_area.markdown(block_html, unsafe_allow_html=True)
    else:
        block_area.info("No blocks mined yet...")
    
    # Update mining log with events
    if st.session_state['events']:
        log_html = render_mining_log(st.session_state['events'], max_lines=200)
        mining_log.markdown(log_html, unsafe_allow_html=True)
    else:
        mining_log.info("No mining activity yet...")
    
    # Auto-refresh every 2 seconds
    time.sleep(2)
    st.rerun()
else:
    # Not running - show last state
    if st.session_state['events']:
        # Show blocks from last run
        blocks = []
        for event in st.session_state['events']:
            if event.get('type') == 'block_found' and 'block' in event:
                event_block = event['block']
                if 'accepted' not in event_block:
                    event_block['accepted'] = True
                if not any(b.get('height') == event_block.get('height') for b in blocks):
                    blocks.append(event_block)
        
        if blocks:
            blocks_sorted = sorted(blocks, key=lambda b: b.get('height', 0))
            block_html = render_block_chain(blocks_sorted[-10:])
            block_area.markdown(block_html, unsafe_allow_html=True)
        else:
            block_area.info("No blocks mined yet...")
        
        log_html = render_mining_log(st.session_state['events'], max_lines=200)
        mining_log.markdown(log_html, unsafe_allow_html=True)
    else:
        block_area.info("Simulation stopped - No data")
        mining_log.info("No mining activity")

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