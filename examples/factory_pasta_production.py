"""Demo script for mass pasta production in factory environment."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from realtimegym.environments.factory import FactoryEnv
from realtimegym.environments.factory.image_renderer import FactoryImageRenderer


def create_pasta_mass_production():
    """Create animated GIF of mass pasta production."""
    print("=" * 60)
    print("Factory Environment - Mass Pasta Production")
    print("=" * 60)

    # Create environment
    print("\n1. Creating Factory environment...")
    env = FactoryEnv()
    env.set_seed(42)

    # Create image renderer
    print("2. Creating image-based renderer...")
    assets_dir = Path(__file__).parent.parent / "public"
    renderer = FactoryImageRenderer(env, assets_dir=assets_dir)

    # Create animation with mass pasta production
    print("3. Generating animation (this will take a few minutes)...")
    print("   - 500 steps simulation")
    print("   - Spawning pasta every 3 steps")
    print("   - Maximum pasta production!")

    output_path = "factory_pasta_mass_production.gif"

    # Custom actions for mass pasta production
    actions = []
    for step in range(500):
        # Spawn pasta every 3 steps for maximum production
        if step % 3 == 0:
            actions.append("produce_tomato_pasta")
        else:
            actions.append("continue")

    # Reset and capture initial state
    env.reset()
    renderer.capture_frame()

    # Run simulation and capture frames
    print("\n4. Running simulation...")
    for step in range(len(actions)):
        action = actions[step]
        obs, done, reward, reset = env.step(action)

        # Capture every frame
        renderer.capture_frame()

        # Print progress every 50 steps
        if step % 50 == 0:
            print(f"   Step {step}/500: {len(env.products_in_progress)} in progress, "
                  f"{len(env.completed_products)} completed")

        if done:
            break

    # Final stats
    print(f"\n5. Production complete!")
    print(f"   Total completed: {len(env.completed_products)}")
    print(f"   Total rejected: {env.rejected_products}")
    print(f"   Still in progress: {len(env.products_in_progress)}")

    # Save as GIF
    print(f"\n6. Saving animation...")
    renderer.save_gif(output_path, duration=100, loop=0)  # 100ms per frame for faster playback

    print(f"\n[OK] Animation complete!")
    print(f"[OK] Saved to: {output_path}")
    print(f"[OK] Total pasta produced: {len(env.completed_products)}")
    print("=" * 60)


if __name__ == "__main__":
    create_pasta_mass_production()
