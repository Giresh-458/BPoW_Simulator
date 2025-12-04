"""
Core simulation package for Proof-of-Work blockchain simulator.
Package initialization is lightweight; modules are imported explicitly
by consumers (e.g., `from sim.core import Blockchain`).
"""

__all__ = [
    # Explicit submodules exported; import symbols from their modules
    'core',
    'miner',
    'network',
    'difficulty',
]
