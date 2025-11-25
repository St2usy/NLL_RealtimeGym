"""Factory environment for unmanned food production simulation."""

from typing import Optional

from ..base import BaseEnv
from .factory_env import FactoryEnv

# Seed mapping for different cognitive loads
seed_mapping = {
    "E": {i: 10000 + i for i in range(32)},  # Easy
    "M": {i: 15000 + i for i in range(32)},  # Medium
    "H": {i: 18000 + i for i in range(32)},  # Hard
}


def setup_env(
    seed: int, cognitive_load: str, save_trajectory_gifs: bool = False
) -> tuple[BaseEnv, int, Optional[None]]:
    """
    Setup factory environment.

    Args:
        seed: Random seed index (0-31)
        cognitive_load: Difficulty level ("E", "M", "H")
        save_trajectory_gifs: Whether to save trajectory gifs (not implemented for factory)

    Returns:
        Tuple of (environment, actual_seed, renderer)
    """
    env = FactoryEnv()
    actual_seed = seed_mapping[cognitive_load][seed]
    env.set_seed(actual_seed)

    # Renderer not implemented yet for factory
    render = None

    return env, actual_seed, render


__all__ = ["FactoryEnv", "setup_env"]
