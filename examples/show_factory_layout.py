"""Show factory environment initial layout."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from realtimegym.environments.factory import FactoryEnv
from realtimegym.environments.factory.image_renderer import FactoryImageRenderer


def show_factory_layout():
    """Generate and save factory initial layout image."""
    print("=" * 60)
    print("Factory Environment - Initial Layout")
    print("=" * 60)

    # Create environment
    print("\n1. Creating Factory environment...")
    env = FactoryEnv()
    env.set_seed(42)
    env.reset()

    # Print layout info
    print("\n2. Factory Configuration:")
    print(f"   Grid size: {env.width} x {env.height}")
    print(f"   Production lines: {env.num_lines}")
    print(f"   Robot arms: {len(env.robot_arms)}")
    print(f"   Logistics robots: {len(env.logistics_robots)}")

    print("\n3. Station Layout:")
    for station_type, stations in env.stations.items():
        positions = [s.position for s in stations]
        print(f"   {station_type}: {positions}")

    # Create image renderer
    print("\n4. Creating layout image...")
    assets_dir = Path(__file__).parent.parent / "public"
    renderer = FactoryImageRenderer(env, assets_dir=assets_dir)

    output_path = "factory_layout.png"
    renderer.save_frame(output_path)

    print(f"\n[OK] Layout saved to: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    show_factory_layout()
