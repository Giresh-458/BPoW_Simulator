"""
Streamlit entrypoint for Proof-of-Work blockchain simulator.
Provides UI controls and displays simulation results.
"""

import streamlit as st
import sim_api
from typing import Dict, Any

# Initialize session state
if 'events' not in st.session_state:
    st.session_state['events'] = []
if 'simulation_running' not in st.session_state:
    st.session_state['simulation_running'] = False

def ui_callback(event: Dict[str, Any]) -> None:
    """Callback function to handle simulation events and update UI."""
    st.session_state['events'].append(event)
    # Update events display
    events_container.empty()
    events_text = "\n".join([f"{e.get('timestamp', '')}: {e.get('message', '')}" 
                            for e in st.session_state['events'][-10:]])  # Show last 10 events
    events_container.text(events_text)

# UI Layout
st.title("🔗 Proof-of-Work Blockchain Simulator")

# Control Panel
col1, col2 = st.columns(2)

with col1:
    st.subheader("Simulation Controls")
    
    # Start/Stop buttons
    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("▶️ Start Simulation", disabled=st.session_state['simulation_running']):
            config = {
                'num_miners': st.session_state.get('num_miners', 3),
                'difficulty': st.session_state.get('difficulty', 4),
                'use_real_sha256': st.session_state.get('use_real_sha256', False),
                'data': st.session_state.get('data', 'Hello Blockchain!')
            }
            sim_api.start_simulation(config, ui_callback)
            st.session_state['simulation_running'] = True
            st.rerun()
    
    with col_stop:
        if st.button("⏹️ Stop Simulation", disabled=not st.session_state['simulation_running']):
            sim_api.stop_simulation()
            st.session_state['simulation_running'] = False
            st.rerun()

with col2:
    st.subheader("Configuration")
    
    # Configuration sliders and inputs
    st.session_state['num_miners'] = st.slider(
        "Number of Miners", 
        min_value=1, 
        max_value=10, 
        value=3,
        disabled=st.session_state['simulation_running']
    )
    
    st.session_state['difficulty'] = st.slider(
        "Global Difficulty", 
        min_value=1, 
        max_value=8, 
        value=4,
        disabled=st.session_state['simulation_running']
    )
    
    st.session_state['data'] = st.text_input(
        "Data to Mine", 
        value="Hello Blockchain!",
        disabled=st.session_state['simulation_running']
    )
    
    st.session_state['use_real_sha256'] = st.checkbox(
        "Use Real SHA256", 
        value=False,
        disabled=st.session_state['simulation_running']
    )

# Display Areas
st.subheader("📊 Simulation Status")
status_container = st.empty()
status_container.text("Simulation stopped")

st.subheader("📝 Events Log")
events_container = st.empty()
events_container.text("No events yet")

st.subheader("🔗 Blockchain")
blockchain_container = st.empty()
blockchain_container.markdown("**No blocks mined yet**", unsafe_allow_html=True)

st.subheader("⛏️ Mining Log")
mining_log_container = st.empty()
mining_log_container.text("Mining log will appear here...")

# Update displays based on simulation state
if st.session_state['simulation_running']:
    status_container.text("🟢 Simulation running...")
    
    # Get current stats and update displays
    stats = sim_api.get_stats()
    if stats:
        # Update blockchain display
        blockchain_html = "<h4>Latest Blocks:</h4>"
        for block in stats.get('blocks', [])[-5:]:  # Show last 5 blocks
            blockchain_html += f"""
            <div style="border: 1px solid #ccc; padding: 10px; margin: 5px 0; border-radius: 5px;">
                <strong>Block #{block.get('height', '?')}</strong><br>
                Hash: <code>{block.get('hash', 'N/A')[:16]}...</code><br>
                Miner: {block.get('miner_id', 'N/A')}<br>
                Data: {block.get('data', 'N/A')}
            </div>
            """
        blockchain_container.markdown(blockchain_html, unsafe_allow_html=True)
        
        # Update mining log
        mining_log = stats.get('mining_log', 'No mining activity')
        mining_log_container.text(mining_log)
else:
    status_container.text("🔴 Simulation stopped")
