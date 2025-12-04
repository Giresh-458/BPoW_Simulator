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
import os

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

# Global event queue for thread-safe communication (avoid Streamlit context in threads)
EVENT_QUEUE = queue.Queue()

# Initialize session state
if 'events' not in st.session_state:
    st.session_state['events'] = []
if 'sim_running' not in st.session_state:
    st.session_state['sim_running'] = False
if 'paused' not in st.session_state:
    st.session_state['paused'] = False
if 'miner_rates' not in st.session_state:
    st.session_state['miner_rates'] = {}

def ui_callback(event: Dict[str, Any]) -> None:
    """
    Thread-safe callback function to handle simulation events.
    Called from mining threads - uses queue instead of direct session_state access.
    """
    # Use global queue for thread-safe communication; avoid Streamlit API in worker threads
    try:
        EVENT_QUEUE.put(event)
    except Exception:
        pass

def process_event_queue():
    """Process events from the queue into session state."""
    try:
        while not EVENT_QUEUE.empty():
            event = EVENT_QUEUE.get_nowait()
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
    Render a simple SVG tree: circles (nodes) with lines to parent.
    Main chain nodes are blue, forks are orange.
    """
    if not fork_tree or not fork_tree.get('genesis'):
        return '<div style="text-align:center;color:#999;padding:12px;">No blocks yet</div>'

    root = fork_tree.get('genesis')
    tip_height = fork_tree.get('tip_height', None)

    # Collect nodes by height (y-axis) and sibling index (x-axis)
    levels: Dict[int, List[Dict[str, Any]]] = {}

    def traverse(node: Dict[str, Any]):
        h = int(node.get('height', 0))
        levels.setdefault(h, []).append(node)
        for c in node.get('children', []) or []:
            traverse(c)

    traverse(root)

    # Limit to recent levels to cap drawn nodes for performance
    max_levels = int(st.session_state.get('graph_max_levels', 80))
    if levels:
        all_heights = sorted(levels.keys())
        max_h = max(all_heights)
        min_h = max(0, max_h - max_levels + 1)
        # Drop older levels outside the window
        levels = {h: levels[h] for h in all_heights if h >= min_h}

    # Hard node budget cap: auto-simplify when too many nodes
    node_budget = int(st.session_state.get('graph_node_budget', 600))
    total_nodes = sum(len(v) for v in levels.values())
    if total_nodes > node_budget:
        st.session_state['graph_show_labels'] = False
        st.session_state['graph_show_grid'] = False

    # Layout parameters (read from session for user-tunable layout)
    # Vertical layout: Y = height (top to bottom), X = sibling order (left to right)
    x_gap = int(st.session_state.get('graph_x_gap', 140))
    y_gap = int(st.session_state.get('graph_y_gap', 90))
    radius = int(st.session_state.get('graph_node_radius', 16))
    zoom = float(st.session_state.get('graph_zoom', 1.0))
    theme = st.session_state.get('graph_theme', 'light')
    color_by_miner = bool(st.session_state.get('graph_color_by_miner', True))
    padding = 40

    max_height = max(levels.keys()) if levels else 0
    max_rows = max(len(levels[h]) for h in levels) if levels else 1
    width = padding * 2 + max_rows * x_gap
    height = padding * 2 + (max_height + 1) * y_gap
    width = int(width * zoom)
    height = int(height * zoom)

    # Assign positions
    positions: Dict[str, tuple] = {}
    for h in sorted(levels.keys()):
        row = levels[h]
        # Center siblings around the middle to avoid left bias
        row_count = len(row)
        total_row_width = (row_count - 1) * x_gap
        base_x = padding + (max_rows * x_gap - total_row_width) / 2
        for idx, node in enumerate(row):
            # X determined by sibling index (centered), Y by block height
            x = base_x + idx * x_gap
            y = padding + h * y_gap
            positions[str(node.get('hash'))] = (x, y)

    # Build SVG elements
    lines = []
    circles = []
    labels = []

    # Theme colors
    if theme == 'dark':
        bg_color = '#0f172a'
        grid_color = '#233148'
        main_color = '#60a5fa'
        fork_color = '#f59e0b'
        label_color = '#e5e7eb'
        tip_color = '#22c55e'
        stroke_color = '#94a3b8'
    else:  # light
        bg_color = '#f8f9fa'
        grid_color = '#eeeeee'
        main_color = '#1e90ff'
        fork_color = '#ff8c00'
        label_color = '#ffffff'
        tip_color = '#2ecc71'
        stroke_color = '#999999'

    # Miner-based color palette
    miner_palette = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#f472b6', '#22c55e', '#eab308', '#a3a3a3']

    def color(node):
        if color_by_miner:
            miner_id = str(node.get('miner_id',''))
            # Hash the miner_id to index into palette
            idx = (abs(hash(miner_id)) % len(miner_palette)) if miner_id else 0
            return miner_palette[idx]
        return main_color if node.get('is_main', False) else fork_color

    # Draw connectors (orthogonal or curved) for a top-to-bottom vertical flow
    for h in sorted(levels.keys()):
        for node in levels[h]:
            prev = node.get('prev_hash')
            if prev:
                child_pos = positions.get(str(node.get('hash')))
                parent_pos = positions.get(str(prev))
                if child_pos and parent_pos:
                    x1, y1 = child_pos
                    x2, y2 = parent_pos
                    # In Cloud Mode with heavy load, prefer orthogonal connectors
                    use_curved = bool(st.session_state.get('graph_curved', True))
                    if st.session_state.get('cloud_mode', False):
                        # Recompute total_nodes and compare to budget
                        try:
                            node_budget = int(st.session_state.get('graph_node_budget', 600))
                            total_nodes = sum(len(v) for v in levels.values())
                            if total_nodes > node_budget:
                                use_curved = False
                        except Exception:
                            pass
                    if use_curved:
                        # Gentle vertical curve from parent to child
                        my = (y1 + y2) / 2
                        lines.append(
                            f'<path d="M {x2} {y2} C {x2} {my}, {x1} {my}, {x1} {y1}" stroke="{stroke_color}" stroke-width="1.2" fill="none" />'
                        )
                    else:
                        # Vertical-first orthogonal connector
                        lines.append(
                            f'<path d="M {x2} {y2} L {x2} {(y2+y1)/2} L {x1} {(y2+y1)/2} L {x1} {y1}" stroke="{stroke_color}" stroke-width="1.2" fill="none" />'
                        )

    # Draw nodes
    for h in sorted(levels.keys()):
        for node in levels[h]:
            x, y = positions.get(str(node.get('hash')), (padding, padding))
            fill = color(node)
            short_hash = str(node.get('hash'))[:6]
            short_prev = (str(node.get('prev_hash'))[:6] if node.get('prev_hash') else 'genesis')
            miner = node.get('miner_id','')
            # Node circle with tooltip
            circles.append(
                f"""
                <g>
                    <circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" opacity="0.9" />
                    <title>#{node.get('height',0)}\nhash:{short_hash}\nprev:{short_prev}\nminer:{miner}</title>
                </g>
                """
            )
            if st.session_state.get('graph_show_labels', True):
                labels.append(f'<text x="{x}" y="{y+4}" text-anchor="middle" font-size="10" fill="{label_color}" font-family="monospace">{short_hash}</text>')

            # Highlight tip node on main chain
            if tip_height is not None and node.get('is_main', False) and int(node.get('height', -1)) == tip_height:
                circles.append(f'<circle cx="{x}" cy="{y}" r="{radius+4}" fill="none" stroke="{tip_color}" stroke-width="2" />')
                labels.append(f'<text x="{x}" y="{y - radius - 6}" text-anchor="middle" font-size="10" fill="{tip_color}" font-family="monospace">TIP</text>')

    legend = """
        <g>
            <rect x="10" y="10" width="140" height="24" rx="6" fill="#fff" stroke="#ddd" />
            <circle cx="26" cy="22" r="6" fill="#1e90ff" />
            <text x="38" y="26" font-size="11" fill="#333">Main</text>
            <circle cx="86" cy="22" r="6" fill="#ff8c00" />
            <text x="98" y="26" font-size="11" fill="#333">Fork</text>
        </g>
    """

    # Optional light grid background to aid readability
    grid = []
    # In simple mode, hide grid regardless of toggle
    simple_mode = bool(st.session_state.get('graph_simple_mode', False))
    if st.session_state.get('graph_show_grid', True) and not simple_mode:
        for h in range(max_height + 1):
            y = padding + h * y_gap
            grid.append(f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="{grid_color}" stroke-width="1" />')

    svg = (
        f'<svg width="100%" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="background:{bg_color};border-radius:8px" preserveAspectRatio="xMidYMid meet">'
        + legend + ''.join(grid) + ''.join(lines) + ''.join(circles) + ''.join(labels) + '</svg>'
    )

    return svg

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
    
    # User-provided block data
    block_data = st.text_input(
        "Block data (message)",
        value=st.session_state.get('block_data', "Hello Blockchain!"),
        help="This message is included in mined blocks. You can change it anytime.")
    st.session_state['block_data'] = block_data
    
    # Number of miners slider
    num_miners = st.slider(
        "Number of miners",
        min_value=1,
        max_value=10,
        value=3,
        key="num_miners",
        disabled=st.session_state['sim_running']
    )

    # Network delay slider (ms)
    net_delay_ms = st.slider(
        "Network delay (ms)",
        min_value=0,
        max_value=1000,
        value=st.session_state.get('network_delay_ms', 100),
        help="Simulated propagation delay for blocks; higher increases fork chance."
    )
    st.session_state['network_delay_ms'] = net_delay_ms

    # Fork Stress Mode toggle (pre-start configuration)
    stress_col1, stress_col2 = st.columns([1,1])
    with stress_col1:
        fork_stress = st.checkbox("Fork Stress Mode", value=st.session_state.get('fork_stress', False))
        st.session_state['fork_stress'] = fork_stress
    with stress_col2:
        st.caption("Sets high delay, low difficulty, and equal high miner rates before start.")
    
    # Global difficulty slider with human-friendly description
    # Get live difficulty if simulation is running
    live_difficulty = None
    # Reconcile UI flags with backend state if available
    if SIM_API_AVAILABLE:
        try:
            stats = get_stats()
            if stats:
                # Sync flags
                backend_paused = bool(stats.get('paused', False))
                # If backend indicates not running (empty blocks and mining_log), keep UI safe defaults
                # We primarily sync pause flag; sim_running stays driven by Start/Reset to avoid flicker
                st.session_state['paused'] = backend_paused
                # Live difficulty
                if 'difficulty' in stats:
                    live_difficulty = stats['difficulty']
        except Exception:
            # If stats retrieval fails, keep the previous/default difficulty
            pass
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

    # Cloud mode: safer defaults for Streamlit Cloud/hosted environments
    cloud_env = bool(os.environ.get('STREAMLIT_CLOUD') or os.environ.get('STREAMLIT_SERVER_HEADLESS'))
    st.session_state['cloud_mode'] = st.sidebar.checkbox("Cloud Mode (safer defaults)", value=st.session_state.get('cloud_mode', cloud_env))
    if st.session_state['cloud_mode']:
        # Preseed conservative defaults if not set
        if 'graph_enabled' not in st.session_state:
            st.session_state['graph_enabled'] = False
        if 'graph_render_every_n' not in st.session_state:
            st.session_state['graph_render_every_n'] = 4
        if 'auto_refresh_secs' not in st.session_state:
            st.session_state['auto_refresh_secs'] = 3
        if 'graph_max_levels' not in st.session_state:
            st.session_state['graph_max_levels'] = 40
    
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

            # Apply Fork Stress Mode overrides
            if st.session_state.get('fork_stress', False):
                # Softer stress settings for responsiveness
                num_miners = max(num_miners, 6)
                difficulty = 2
                net_delay_ms = 500
                # Normalize miners to ~8k H/s
                miner_rates = {f"miner_{i+1}": 8000 for i in range(num_miners)}
            elif st.session_state.get('cloud_mode', False):
                # Cloud-friendly caps
                num_miners = min(num_miners, 6)
                miner_rates = {m: min(5000.0, float(r)) for m, r in miner_rates.items()}
            
            config = {
                'num_miners': num_miners,
                'difficulty': difficulty,
                # 'use_real_hash' removed — simulator uses internal hash model
                'data': block_data,
                'network_delay_ms': net_delay_ms,
                'miner_rates': miner_rates
            }
            
            if SIM_API_AVAILABLE:
                start_simulation(config, ui_callback)
            else:
                st.info("Mock mode: Simulation started")
            
            st.session_state['sim_running'] = True
            st.session_state['paused'] = False
            st.success("Simulation started!")
            st.rerun()
    
    with col_stop:
        # Pause/Resume controls (true pause without stopping components)
        # Use UI flag for pause state to avoid stale backend values
        ui_paused = st.session_state['paused']

        if st.session_state['sim_running'] and not ui_paused:
            if st.button("⏸️ Pause Simulation"):
                if SIM_API_AVAILABLE:
                    try:
                        from sim_api import pause_simulation
                        pause_simulation()
                    except Exception:
                        pass
                st.session_state['paused'] = True
                st.success("Simulation paused!")
                st.rerun()
        elif st.session_state['sim_running'] and ui_paused:
            if st.button("▶️ Resume Simulation"):
                if SIM_API_AVAILABLE:
                    try:
                        from sim_api import resume_simulation
                        resume_simulation()
                    except Exception:
                        pass
                st.session_state['paused'] = False
                st.success("Simulation resumed!")
                st.rerun()
    
    # Reset button
    if st.button("🔄 Reset Blockchain"):
        if SIM_API_AVAILABLE:
            reset_simulation()
        st.session_state['events'] = []
        st.session_state['sim_running'] = False
        st.session_state['paused'] = False
        # Clear cached visualization state
        if 'last_blocks' in st.session_state:
            del st.session_state['last_blocks']
        if 'last_fork_tree' in st.session_state:
            del st.session_state['last_fork_tree']
        st.success("Blockchain and events cleared!")
        st.rerun()

    # Removed "Submit Data To Miners" control to simplify UI
    
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
    metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
    
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
                    # Removed accidental f-string snippet
            except Exception:
                # Keep UI difficulty if stats retrieval fails
                pass
    avg_bt = None
    fork_rate = 0.0
    net_ms_display = st.session_state.get('network_delay_ms', 100)
    if SIM_API_AVAILABLE:
        try:
            stats = get_stats()
            avg_bt = stats.get('avg_block_time')
            fork_rate = stats.get('fork_rate', 0.0)
            net_ms_display = stats.get('network_delay_ms', net_ms_display)
        except Exception:
            pass
    with metrics_col3:
        st.metric("Avg Block Time (s)", f"{avg_bt:.2f}" if avg_bt else "—")
    with metrics_col4:
        st.metric("Fork/Stale Rate", f"{fork_rate*100:.1f}%")

    st.subheader(" Visualization")
    
    # Tabs: Overview (blocks + calculator) and Graph
    tab_overview, tab_graph = st.tabs(["Overview", "Graph"])
    
    # Block display area with scroll in Overview tab
    with tab_overview:
        st.markdown("**Blocks**")
        block_container = st.container()
        with block_container:
            block_area = st.empty()
    
    # 2D Block visualization area in Graph tab with controls
    with tab_graph:
        st.markdown("**Blockchain**")
        ctrl1, ctrl2, ctrl3, ctrl4, ctrl5, ctrl6, ctrl7 = st.columns([1,1,1,1,1,1,1])
        with ctrl1:
            st.session_state['graph_x_gap'] = st.slider("X gap", 80, 240, st.session_state.get('graph_x_gap', 140))
        with ctrl2:
            st.session_state['graph_y_gap'] = st.slider("Y gap", 60, 200, st.session_state.get('graph_y_gap', 90))
        with ctrl3:
            st.session_state['graph_node_radius'] = st.slider("Node size", 8, 28, st.session_state.get('graph_node_radius', 16))
        with ctrl4:
            st.session_state['graph_curved'] = st.checkbox("Curved connectors", value=st.session_state.get('graph_curved', True))
        with ctrl5:
            st.session_state['graph_show_labels'] = st.checkbox("Show labels", value=st.session_state.get('graph_show_labels', True))
        with ctrl6:
            st.session_state['graph_show_grid'] = st.checkbox("Show grid", value=st.session_state.get('graph_show_grid', True))
        with ctrl7:
            st.session_state['graph_zoom'] = st.slider("Zoom", 0.5, 2.0, float(st.session_state.get('graph_zoom', 1.0)))
        # Theme and coloring
        theme_col, miner_col = st.columns([1,1])
        with theme_col:
            st.session_state['graph_theme'] = st.selectbox("Theme", options=["light","dark"], index=(0 if st.session_state.get('graph_theme','light')=='light' else 1))
        with miner_col:
            st.session_state['graph_color_by_miner'] = st.checkbox("Color by miner", value=st.session_state.get('graph_color_by_miner', True))
        # Additional performance controls
        perf1, perf2 = st.columns([1,1])
        with perf1:
            st.session_state['graph_max_levels'] = st.slider("Max levels shown", 10, 200, int(st.session_state.get('graph_max_levels', 80)), help="Limit recent heights drawn to keep rendering light.")
        with perf2:
            st.session_state['auto_refresh_secs'] = st.slider("Auto-refresh (sec)", 2, 10, int(st.session_state.get('auto_refresh_secs', 2)), help="Lower refresh rate to reduce UI workload.")
        perf3, perf4 = st.columns([1,1])
        with perf3:
            st.session_state['graph_render_every_n'] = st.slider("Render every Nth refresh", 1, 10, int(st.session_state.get('graph_render_every_n', 2)), help="Only draw graph every Nth UI update.")
        with perf4:
            st.session_state['graph_simple_mode'] = st.checkbox("Simple graph mode", value=st.session_state.get('graph_simple_mode', False), help="Use simpler styling for heavy loads.")
        # Heavy render toggle to prevent UI freezes
        st.session_state['graph_enabled'] = st.checkbox("Render graph", value=st.session_state.get('graph_enabled', False), help="Enable to render the SVG graph. Disable if UI feels sluggish.")
        block_map_area = st.empty()

    # Manual PoW calculator (educational) inside Overview tab
    with tab_overview:
        st.markdown("**Manual PoW Calculator**")
        calc_col1, calc_col2, calc_col3 = st.columns([2,1,1])
        with calc_col1:
            calc_message = st.text_input(
                "Message to hash",
                value=st.session_state.get('calc_message', 'Demo Message'),
                key='calc_message_input'
            )
            st.session_state['calc_message'] = calc_message
        with calc_col2:
            calc_difficulty = st.slider(
                "Calc difficulty",
                min_value=0, max_value=8, value=st.session_state.get('calc_difficulty', difficulty), key='calc_difficulty_slider')
            st.session_state['calc_difficulty'] = calc_difficulty
        with calc_col3:
            run_calc = st.button("🔍 Find Nonce")

    calc_result_area = st.empty()
    if run_calc:
        # Perform a bounded PoW search to visualize hashing
        try:
            from utils.hash_utils import compute_block_hash, hash_meets_difficulty
            import time as _t, random as _r
            start_ts = _t.time()
            prev_hash_demo = '0'*64
            height_demo = 1
            attempts = 0
            max_attempts = 200000  # safety bound
            nonce = _r.randint(0, 2**32-1)
            found = None
            # Try quickly; yield UI every 5000 attempts
            while attempts < max_attempts:
                h = compute_block_hash(prev_hash_demo, height_demo, _t.time(), calc_message, nonce, 'manual')
                attempts += 1
                if hash_meets_difficulty(h, calc_difficulty):
                    found = (nonce, h)
                    break
                nonce = (nonce + 1) & 0xFFFFFFFF
                if attempts % 5000 == 0:
                    calc_result_area.info(f"Attempts: {attempts}")
            duration = _t.time() - start_ts
            if found:
                n, hval = found
                calc_result_area.success(f"Found nonce {n} in {attempts} attempts ({duration:.2f}s). Hash: {str(hval)[:16]}…")
            else:
                calc_result_area.warning(f"No valid nonce within {max_attempts} attempts. Try lowering difficulty.")
        except Exception as e:
            calc_result_area.error(f"Calculator error: {e}")

    # Simple block times chart (last 20)
    try:
        if SIM_API_AVAILABLE:
            stats = get_stats()
            rbt = stats.get('recent_block_times') or []
            if rbt:
                st.line_chart(rbt, height=120)
    except Exception:
        pass
    

# Events are processed earlier at startup via `process_event_queue()`

# Update displays
if st.session_state['sim_running'] and not st.session_state['paused']:
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
    # Initialize render cycle counter
    if 'graph_render_counter' not in st.session_state:
        st.session_state['graph_render_counter'] = 0

    try:
        if st.session_state.get('graph_enabled', False):
            stats = get_stats()
            if stats and 'fork_tree' in stats and stats['fork_tree'] and stats['fork_tree'].get('genesis'):
                # Defer initial heavy render until enough blocks exist
                accepted_blocks = stats.get('accepted_count') or 0
                if accepted_blocks < int(st.session_state.get('graph_min_blocks_to_render', 12)):
                    block_map_area.info("Graph will render after more blocks are mined...")
                else:
                    # Only render every Nth refresh to reduce load
                    st.session_state['graph_render_counter'] += 1
                    n = int(st.session_state.get('graph_render_every_n', 2))
                    if st.session_state['graph_render_counter'] % max(1, n) == 0:
                        svg = _render_2d_blocks(stats['fork_tree'])
                        centered_html = f"""
                        <div style='display:flex; justify-content:center; align-items:flex-start; padding:12px;'>
                            <div style='width:100%; max-width:1400px; height:800px; overflow:auto; border:1px solid #e5e7eb; border-radius:8px; background:#ffffff;'>
                                {svg}
                            </div>
                        </div>
                        """
                        import streamlit.components.v1 as components
                        components.html(centered_html, height=820, scrolling=True)
                        # Store in session state for paused view
                        st.session_state['last_fork_tree'] = stats['fork_tree']
            else:
                block_map_area.info("Waiting for blocks...")
        else:
            block_map_area.info("Graph rendering disabled")
    except Exception as e:
        block_map_area.info("Blocks loading...")
    
    # Auto-refresh using configured cadence.
    time.sleep(int(st.session_state.get('auto_refresh_secs', 2)))
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
        svg = _render_2d_blocks(st.session_state['last_fork_tree'])
        centered_html = f"""
        <div style='display:flex; justify-content:center; align-items:flex-start; padding:12px;'>
            <div style='width:100%; max-width:1400px; height:800px; overflow:auto; border:1px solid #e5e7eb; border-radius:8px; background:#ffffff;'>
                {svg}
            </div>
        </div>
        """
        import streamlit.components.v1 as components
        components.html(centered_html, height=820, scrolling=True)
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