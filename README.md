# Proof-of-Work Blockchain Simulator

A Streamlit-based simulator for Proof-of-Work blockchain networks with configurable miners, difficulty, and mining algorithms.

## Quick Start

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

4. Run tests:
```bash
pytest
```

## Development Workflow

- `main`: Production-ready code
- `dev`: Integration branch for features
- `feature-core`: Core blockchain simulation logic
- `feature-ui`: User interface improvements

## Architecture

- `app.py`: Streamlit UI entrypoint
- `sim_api.py`: API wrapper between UI and simulation
- `sim/`: Core simulation package (blocks, miners, network, difficulty)
- `utils/`: Utility functions for hashing
- `tests/`: Unit tests

## UI Development (Person A)

### Running the UI Locally

1. Set up virtual environment:
```bash
python -m venv .venv
.venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the Streamlit application:
```bash
streamlit run app.py
```

### Event Format Expected from sim_api

The UI expects events from `sim_api` in the following format:

```python
{
    "type": "block_found" | "block_accepted" | "block_stale" | "miner_status",
    "block": {
        "height": int,
        "hash": str,
        "prev_hash": str,
        "nonce": int,
        "miner_id": str,
        "timestamp": float,
        "accepted": bool
    },
    "miner_id": str,  # For miner_status events
    "hashrate": int,  # For miner_status events
    "timestamp": float
}
```