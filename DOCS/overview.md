## Proof-of-Work Blockchain Simulator — What it does

This repository is a lightweight, educational Proof-of-Work (PoW) blockchain simulator with a Streamlit-based UI. It mimics mining activity with configurable miners, difficulty, and simple network behavior so you can observe how blocks are found, accepted, or become stale.

The simulator is intended for learning, UI prototyping, and testing mining-related visualizations rather than for production use.

## High-level components

- `app.py` — Streamlit UI entrypoint. Provides controls (start/stop, miner count, difficulty, data input), displays metrics, mining log, and a simple blockchain visualization. Supports a mock mode when the simulation API is unavailable.
- `sim_api.py` — Thread-safe API wrapper between the UI and the simulation core. Exposes `start_simulation`, `stop_simulation`, `set_miner_rate`, `submit_data`, `get_pending_events`, `get_stats`.
- `sim/` — Core simulation package:
  - `core.py` — `Block` and `Blockchain` classes, basic validation and chain management.
  - `miner.py` — `Miner` class that simulates mining (both fast probabilistic simulation and a placeholder for real SHA-256 mining).
  - `network.py` — Simple network simulation (start/stop) used by `sim_api`.
  - `difficulty.py` — Difficulty controller used to record block times and adjust difficulty (placeholder logic present).
- `ui/` — UI helpers and renderers used by `app.py` for rendering blocks, chain, and logs.
- `utils/` — Utility code such as `hash_utils.py` for hashing helpers.
- `tests/` — Unit tests (example: `test_block_validation.py`).

## Event / message model

The UI and `sim_api` communicate using an event queue. Events pushed to the UI typically follow this shape:

```json
{
  "type": "block_found" | "block_accepted" | "block_stale" | "simulation_start" | "simulation_stop" | "data_submission",
  "timestamp": 1234567890.0,
  "message": "Human readable message",
  "block": {
    "height": 1,
    "hash": "...",
    "prev_hash": "...",
    "nonce": 12345,
    "miner_id": "miner_1",
    "timestamp": 1234567890.0,
    "accepted": true
  }
}
```

`app.py` can also run in a mock mode (when `sim_api` can't be imported) and generates synthetic `block_found` events for UI development.

## How it works (flow)

1. UI calls `sim_api.start_simulation(config)` with a config dict (e.g., `num_miners`, `difficulty`, `use_real_sha256`, `data`).
2. `sim_api` initializes the `Blockchain`, creates `Miner` instances, starts the `Network`, and starts each miner thread.
3. Each `Miner` runs a mining loop. On success it constructs a `Block` and calls the `_on_block_found` callback.
4. `_on_block_found` in `sim_api` attempts to add the block to the `Blockchain` and enqueues an event describing the result. The UI polls `sim_api.get_pending_events()` and updates visuals.

## Key files and responsibilities

- `app.py` — UI interactions, session state, mock UI callback.
- `sim_api.py` — Simulation lifecycle, thread-safety, event queue.
- `sim/core.py` — Block data model and validation. (Validation and hashing are partially TODO.)
- `sim/miner.py` — Mining simulation (fast probabilistic mode and placeholder for real SHA-256 mining).
- `sim/difficulty.py` — Difficulty controller (records times and adjusts difficulty — currently placeholder logic).
- `ui/*` — Rendering helpers for blocks and logs used by the UI.

## How to run (development)

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the Streamlit UI:

```powershell
streamlit run app.py
```

4. Run tests:

```powershell
pytest -q
```

## Current limitations & TODOs

- Several core pieces are intentionally simplified or marked TODO:
  - `sim/core.Block.__post_init__` uses a placeholder hash when not provided.
  - `sim/core.Blockchain.validate_block` and `add_block` have minimal validation and should be hardened (timestamp checks, hash/difficulty verification, reorg handling).
  - `sim/miner.Miner` contains a probabilistic fast-simulation mode; real SHA-256 mining is not implemented (placeholder methods exist).
  - Difficulty controller uses stubbed timings and adjustment logic.
- Network, latency, forks, and chain reorganization behavior are simplified or unimplemented.

## Suggested next steps (small, safe fixes)

1. Implement real hash computation and verification in `utils/hash_utils.py` and wire it into `Miner._check_real_hash` and `Block` creation.
2. Harden `Blockchain.validate_block` to verify hash difficulty, timestamps, and previous hash strictly.
3. Add unit tests for difficulty adjustment, miner behavior, and block validation (expand `tests/`).

## Where to look when extending the project

- Start with `sim_api.py` for lifecycle and event queue usage.
- Follow miner -> core -> blockchain to add real hashing and validation.
- `app.py` demonstrates the UI contract and event consumption pattern.

---

If you want, I can:

- expand this into a user-facing `README` replacement,
- add quick diagrams or sequence diagrams,
- implement one of the TODOs (for example: real SHA-256 mining or improved validation) and add tests.

Tell me what you'd like next.
