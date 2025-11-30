"""
Fried Rice Production Visualization

Creates an animated GIF showing logistics robots transporting fried rice items.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the custom environment
exec(open(Path(__file__).parent / "fried_rice_100_simulation.py", encoding='utf-8').read().split("def run_fried_rice_simulation")[0])

from realtimegym.environments.factory.image_renderer import FactoryImageRenderer


def visualize_fried_rice_production(quantity=20, output_file="fried_rice_production.gif"):
    """
    Create animated GIF of fried rice production.

    Args:
        quantity: Number of fried rice to produce
        output_file: Output GIF filename
    """
    print("=" * 70)
    print(f"Fried Rice Production Visualization - {quantity} units")
    print("=" * 70)

    # Create environment
    print("\n1. Creating Factory environment...")
    env = FriedRiceFactoryEnv()
    env.set_seed(42)
    env.reset()

    # Create renderer
    print("2. Creating image renderer...")
    assets_dir = Path(__file__).parent.parent / "public"
    renderer = FactoryImageRenderer(env, assets_dir=assets_dir)

    # Production parameters
    spawn_interval = 15  # Slower spawn for better visualization
    max_steps = 1500

    spawned_count = 0

    print(f"\n3. Running simulation...")
    print(f"   Target: {quantity} fried rice")
    print(f"   Spawn interval: every {spawn_interval} steps")
    print(f"   Max steps: {max_steps}")
    print(f"   Robots: {len(env.logistics_robots)}\n")

    # Capture initial frame
    renderer.capture_frame()

    for step in range(max_steps):
        # Spawn fried rice
        if step % spawn_interval == 0 and spawned_count < quantity:
            action = "produce_shrimp_fried_rice"
            spawned_count += 1
        else:
            action = "continue"

        obs, done, reward, reset = env.step(action)

        # Capture frame
        renderer.capture_frame()

        # Print progress
        if step % 100 == 0:
            completed = len(env.completed_products)
            in_progress = len(env.products_in_progress)
            carrying = sum(1 for r in env.logistics_robots if r.carrying)

            print(f"   Step {step:4d}: Spawned={spawned_count:2d}/{quantity}, " +
                  f"InProgress={in_progress:2d}, Carrying={carrying:2d}, " +
                  f"Done={completed:2d}")

        # Check completion
        if (spawned_count >= quantity and
            len(env.completed_products) + env.rejected_products >= quantity):
            print(f"\n   [OK] All items processed at step {step}!")
            break

        if done:
            break

    # Final statistics
    print(f"\n4. Simulation complete!")
    print(f"   Total spawned: {spawned_count}")
    print(f"   Completed: {len(env.completed_products)}")
    print(f"   Rejected: {env.rejected_products}")
    print(f"   Total frames captured: {len(renderer.frames)}")

    # Save GIF
    print(f"\n5. Saving animation to '{output_file}'...")
    print(f"   This may take a moment...")

    # Save with slower frame rate for better viewing
    renderer.save_gif(output_file, duration=50, loop=0)  # 50ms per frame = 20 fps

    print(f"\n[OK] Animation saved successfully!")
    print(f"[OK] File: {output_file}")
    print(f"[OK] Total frames: {len(renderer.frames)}")
    print(f"[OK] Shows logistics robots moving at 1 grid per step")
    print("=" * 70)


if __name__ == "__main__":
    # Create visualization with 20 items
    visualize_fried_rice_production(quantity=20, output_file="fried_rice_20_units.gif")
