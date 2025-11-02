## What needs to change to make this a real PoW simulator

This document lists concrete, actionable changes (file-level and behavioral) to turn the educational simulator into a deterministic Proof-of-Work (PoW) simulator that uses real SHA-256 block hashing, enforces difficulty, supports miner nonce search, and models basic network/fork behavior.

Keep changes small and test-driven: implement hashing and validation first, then miner loop, difficulty, and finally network/propagation.

---

## Goals

- Deterministic SHA-256 block hashing (canonical header -> hex digest).
- Difficulty enforcement: block accepted only if hash meets target.
- Miner loop performs nonce search (honest miners) and respects miner rate.
- Thread-safe sim_api providing mining work and consuming found blocks.
- Basic network propagation and stale block detection (forks/reorgs).
- Unit tests covering hashing, validation, miner correctness, and difficulty adjustment.

---

## File-by-file changes (concrete)

- `utils/hash_utils.py` (add)
  - compute_block_hash(prev_hash, height, timestamp, data, nonce, miner_id) -> hex
  - hash_meets_difficulty(hash_hex, difficulty) -> bool
  - Rationale: centralize hashing and difficulty logic for tests and consistency.

- `sim/core.py`
  - Block: add compute_hash() or call `compute_block_hash` in `__post_init__` when hash not provided.
  - Blockchain.validate_block:
    - Recompute hash and compare to provided hash.
    - Check hash meets difficulty via `hash_meets_difficulty`.
    - Enforce prev_hash == head.hash (or implement fork handling by tracking branches).
    - Validate timestamp (not far future) and height correctness.
  - Blockchain.add_block:
    - Use validate_block, append to chain on success, set accepted=True and emit events via sim_api queue.
    - Optionally implement branch storage and reorg when a longer chain appears.

- `sim/miner.py`
  - Replace probabilistic `_check_fast_hash`/_check_real_hash placeholders with deterministic hash computation using `compute_block_hash`.
  - Miner.start should request a mining work item from `sim_api` (prev_hash, height, difficulty, data) or accept periodic updates.
  - Miner._mining_loop should perform nonce search (0..2**32-1 or randomized start) and compute hashes in tight loops, batching attempts to match `hash_rate` (e.g., attempts_per_cycle then sleep).
  - When a valid hash is found, create `Block` using the current work's prev_hash/height and call `on_block_found(block)`.
  - If the head changes (another block accepted), abort current work and refresh prev_hash/height.
  - Keep the mining loop thread-safe and responsive to `stop()`.

- `sim_api.py`
  - Add `get_mining_work()` to return current work (prev_hash, height, difficulty, data) atomically to miners.
  - In `_on_block_found`, use blockchain.add_block and enqueue descriptive events: `block_found` (local), `block_accepted`, `block_stale` depending on outcome.
  - When difficulty changes, enqueue difficulty_update events and update miners.
  - Ensure all shared state (_blockchain, _miners, _event_queue) is protected by `_simulation_lock`.

- `sim/difficulty.py`
  - Replace placeholder logic with a controller that records last N block timestamps and computes adjustments towards a target block interval (e.g., 10s for testing).
  - Simple rule: if avg_time < target -> difficulty += 1, if avg_time > target -> difficulty -= 1, with min/max clamps.

- `sim/network.py`
  - Implement propagation delays: when a miner finds a block, simulate a delay before the block reaches all nodes/chain.
  - On arrival, add to blockchain; if a competing chain already exists, mark as stale when appropriate.

- `ui/` and `app.py`
  - Ensure UI event schema includes full block details: height, hash, prev_hash, nonce, miner_id, timestamp, accepted.
  - The UI should request `get_stats()` periodically and call `sim_api.submit_data()` to update miners' work.

- `tests/` (add/update)
  - `test_hash_utils.py`: hashing and difficulty checks.
  - `test_block_validation.py`: acceptance/rejection, prev_hash mismatch, bad hash, timestamp checks.
  - `test_miner_integration.py`: run a miner against a low difficulty and assert it finds a valid block.
  - `test_difficulty_adjustment.py`: simulate block times and ensure difficulty moves toward target.

---

## Suggested canonical header format

Use an explicit canonical string to compute hashes. Example:

header = f"{prev_hash}|{height}|{timestamp:.6f}|{data}|{miner_id}|{nonce}"
hash = sha256(header.encode('utf-8')).hexdigest()

Notes:
- Include height to prevent accidental accidental collisions with identical prev_hash/timestamp/data.
- Use fixed timestamp formatting to ensure deterministic hashing in tests.

---

## Difficulty model choices (pick one)

1. Leading hex zeros (simple): difficulty = number of leading '0' hex chars required. Easy to implement and tune in tests.
2. Compact integer target (Bitcoin-like): more precise; requires bit-level arithmetic and conversions. More accurate but more complex.

Recommendation: start with leading-hex-zero count for clarity and easy tuning;
move to integer target later if needed.

---

## Edge cases & design notes

- Forks: two miners can find blocks at nearly the same time. Keep alternate branches and choose the longest chain (or highest total work) on arrival.
- Stale blocks: a block mined on a now-non-head prev_hash should be reported as `block_stale`.
- Timestamp manipulation: disallow blocks that are too far in the future (> 2 hours) and ensure monotonic timestamps per chain.
- Concurrency: miners must read current head and abort when it changes; sim_api must hold locks when adding blocks.
- Performance: Python SHA-256 is not extremely fast. Use batch hashing per sleep cycle to simulate hash_rate accurately without sleeping for each nonce.

---

## Minimal implementation plan (PR-sized steps)

1. Add `utils/hash_utils.py` (hashing + difficulty check). (Done)
2. Wire hashing into `sim/core.Block` and `Blockchain.validate_block` to enforce hash correctness and difficulty. Add tests for hashing and validation. (~1–2 hours)
3. Implement `sim_api.get_mining_work()` and ensure miners can request current work atomically. Add event types for accepted/stale blocks. (~1 hour)
4. Replace miner probabilistic check with deterministic nonce search (`sim/miner.py`). Use batching for `hash_rate`. Add integration test for miner finding a block at very low difficulty (difficulty 1 or 2). (~2 hours)
5. Implement a simple difficulty controller (`sim/difficulty.py`) and wire adjustments in `_on_block_found`. Add tests to validate behavior. (~1–2 hours)
6. Implement network propagation delays (`sim/network.py`) to cause realistic races and stale blocks. Add tests for stale detection and fork resolution. (~2 hours)
7. Update UI events and documentation to match new event schema and fields. (~30–60 minutes)

Estimated total: 6–10 hours of focused work (depending on how thorough tests/fork handling are).

---

## Quick commands for development & verification

Use these to run the app and tests locally (Windows/cmd):

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest -q
streamlit run app.py
```

---

If you'd like, I can now implement steps 2 and 3 (wire validation and add `get_mining_work`) and run tests. Tell me to proceed and I will update the todo list and apply the patches.
