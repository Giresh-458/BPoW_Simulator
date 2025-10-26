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

## TODO

- Implement full mining logic
- Add network latency simulation
- Implement difficulty adjustment algorithm
- Add comprehensive testing
