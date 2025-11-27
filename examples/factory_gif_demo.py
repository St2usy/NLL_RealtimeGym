"""Demo script for creating factory environment GIF animation."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from realtimegym.environments.factory import FactoryEnv
from realtimegym.environments.factory.image_renderer import FactoryImageRenderer


def create_factory_animation():
    """Create animated GIF of factory operation."""
    print("=" * 60)
    print("Factory Environment - GIF Animation Demo")
    print("=" * 60)

    # Create environment
    print("\n1. Creating Factory environment...")
    env = FactoryEnv()
    env.set_seed(42)

    # Create image renderer
    print("2. Creating image-based renderer...")
    assets_dir = Path(__file__).parent.parent / "public"
    renderer = FactoryImageRenderer(env, assets_dir=assets_dir)

    # Create animation
    print("3. Generating animation (this may take a minute)...")
    print("   - Products will spawn every 5 steps for the first 50 steps")
    print("   - This will create ~10 products in total")
    output_path = "factory_simulation.gif"

    renderer.create_animation(
        num_steps=150,  # Increased to 150 steps to see more production
        output_path=output_path,
        frame_duration=200  # 200ms per frame (faster animation)
    )

    print(f"\n[OK] Animation complete!")
    print(f"[OK] Saved to: {output_path}")
    print("=" * 60)


def create_factory_snapshots():
    """Create snapshot images at different stages."""
    print("=" * 60)
    print("Factory Environment - Snapshot Demo")
    print("=" * 60)

    # Create environment
    print("\n1. Creating Factory environment...")
    env = FactoryEnv()
    env.set_seed(42)
    env.reset()

    # Create image renderer
    assets_dir = Path(__file__).parent.parent / "public"
    renderer = FactoryImageRenderer(env, assets_dir=assets_dir)

    # Initial state
    print("2. Capturing initial state...")
    renderer.save_frame("factory_initial.png")

    # Run simulation with continuous product spawning
    print("3. Running simulation and capturing snapshots...")
    print("   - Spawning products every 5 steps...")

    product_types = ["ricotta_salad", "shrimp_fried_rice", "tomato_pasta"]

    for i in range(100):
        # Spawn products every 5 steps for first 50 steps
        if i % 5 == 0 and i < 50:
            product_idx = (i // 5) % len(product_types)
            action = f"produce_{product_types[product_idx]}"
            env.step(action)
            if i % 10 == 0:
                print(f"   Step {i}: Spawned {product_types[product_idx]}")
        else:
            env.step("continue")

        # Capture snapshots at intervals
        if i % 10 == 0:
            renderer.save_frame(f"factory_step_{i}.png")
            print(f"   Captured snapshot at step {i} (Products: {len(env.products_in_progress)} in progress, {len(env.completed_products)} completed)")

    print("\n[OK] Snapshots created!")
    print(f"[OK] Final stats: {len(env.completed_products)} completed, {env.rejected_products} rejected")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Factory GIF animation demo")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["animation", "snapshots"],
        default="animation",
        help="Demo mode",
    )

    args = parser.parse_args()

    if args.mode == "animation":
        create_factory_animation()
    elif args.mode == "snapshots":
        create_factory_snapshots()
