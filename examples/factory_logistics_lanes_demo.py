"""Visualization of logistics robots moving along designated lanes with specific routes."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from realtimegym.environments.factory import FactoryEnv
from realtimegym.environments.factory.image_renderer import FactoryImageRenderer
from realtimegym.environments.factory.agents import LogisticsRobot, Task


class CustomFactoryEnv(FactoryEnv):
    """Custom factory environment with specific logistics lanes and routes."""

    def _setup_robots(self) -> None:
        """Setup robot agents with custom logistics lanes and routes."""
        self.robot_arms = []
        self.logistics_robots = []

        # We'll focus on Line 1 (left side) for this demo
        # Grid: Line 1 stations are at x=4, with lanes at x=2,3,4,5,6

        # Station positions for Line 1
        station_x = 4

        # Lane definitions (5 lanes total)
        # Lane 1 (x=2): ID=5 - Cooker to lower stations
        # Lane 2 (x=3): ID=1,3 - Washer↔Cutter, Cutter↔Cooker
        # Lane 3 (x=4): ID=0,7 - Storage↔Washer, VisionQA↔FinalStorage (center line)
        # Lane 4 (x=5): ID=2,4 - Washer↔Cutter, Cutter↔Cooker
        # Lane 5 (x=6): ID=6 - Cooker to lower stations

        # ID=0: Lane 3 (x=4) - Storage(y=0) ↔ Washer(y=4)
        self.logistics_robots.append(
            LogisticsRobot(
                robot_id=0,
                position=(4, 2),  # Start between Storage and Washer
            )
        )
        self.logistics_robots[-1].assigned_route = ("Storage", "Washer")
        self.logistics_robots[-1].lane_x = 4

        # ID=1: Lane 2 (x=3) - Washer(y=4) ↔ Cutter(y=9)
        self.logistics_robots.append(
            LogisticsRobot(
                robot_id=1,
                position=(3, 6),  # Start between Washer and Cutter
            )
        )
        self.logistics_robots[-1].assigned_route = ("Washer", "Cutter")
        self.logistics_robots[-1].lane_x = 3

        # ID=2: Lane 4 (x=5) - Washer(y=4) ↔ Cutter(y=9)
        self.logistics_robots.append(
            LogisticsRobot(
                robot_id=2,
                position=(5, 6),  # Start between Washer and Cutter
            )
        )
        self.logistics_robots[-1].assigned_route = ("Washer", "Cutter")
        self.logistics_robots[-1].lane_x = 5

        # ID=3: Lane 2 (x=3) - Cutter(y=9) ↔ Cooker(y=14)
        self.logistics_robots.append(
            LogisticsRobot(
                robot_id=3,
                position=(3, 11),  # Start between Cutter and Cooker
            )
        )
        self.logistics_robots[-1].assigned_route = ("Cutter", "Cooker")
        self.logistics_robots[-1].lane_x = 3

        # ID=4: Lane 4 (x=5) - Cutter(y=9) ↔ Cooker(y=14)
        self.logistics_robots.append(
            LogisticsRobot(
                robot_id=4,
                position=(5, 11),  # Start between Cutter and Cooker
            )
        )
        self.logistics_robots[-1].assigned_route = ("Cutter", "Cooker")
        self.logistics_robots[-1].lane_x = 5

        # ID=5: Lane 1 (x=2) - Cooker(y=14) to lower stations
        self.logistics_robots.append(
            LogisticsRobot(
                robot_id=5,
                position=(2, 18),  # Start below Cooker
            )
        )
        self.logistics_robots[-1].assigned_route = ("Cooker", "FinalStorage")
        self.logistics_robots[-1].lane_x = 2

        # ID=6: Lane 5 (x=6) - Cooker(y=14) to lower stations
        self.logistics_robots.append(
            LogisticsRobot(
                robot_id=6,
                position=(6, 18),  # Start below Cooker
            )
        )
        self.logistics_robots[-1].assigned_route = ("Cooker", "FinalStorage")
        self.logistics_robots[-1].lane_x = 6

        # ID=7: Lane 3 (x=4) - VisionQA(y=25) ↔ FinalStorage(y=29)
        self.logistics_robots.append(
            LogisticsRobot(
                robot_id=7,
                position=(4, 27),  # Start between VisionQA and FinalStorage
            )
        )
        self.logistics_robots[-1].assigned_route = ("VisionQA", "FinalStorage")
        self.logistics_robots[-1].lane_x = 4

        # Initialize automated movement for demonstration
        self._setup_logistics_movement()

    def _setup_logistics_movement(self):
        """Setup automated movement patterns for logistics robots."""
        # Station Y-coordinates for Line 1
        station_y_coords = {
            "Storage": 0,
            "Washer": 4,
            "Cutter": 9,
            "Cooker": 14,
            "Plating": 19,
            "Sealing": 22,
            "VisionQA": 25,
            "FinalStorage": 29,
        }

        for robot in self.logistics_robots:
            if hasattr(robot, 'assigned_route') and hasattr(robot, 'lane_x'):
                start_station, end_station = robot.assigned_route
                start_y = station_y_coords[start_station]
                end_y = station_y_coords[end_station]

                # Create movement pattern: move up and down between stations
                robot.patrol_start = (robot.lane_x, start_y)
                robot.patrol_end = (robot.lane_x, end_y)
                robot.moving_to_end = True

    def step(self, action: str):
        """Override step to include automated logistics movement."""
        obs, done, reward, reset = super().step(action)

        # Automated logistics robot patrol movement
        for robot in self.logistics_robots:
            if hasattr(robot, 'patrol_start') and hasattr(robot, 'patrol_end'):
                x, y = robot.position

                if robot.moving_to_end:
                    # Moving towards patrol_end
                    target_y = robot.patrol_end[1]
                    if y < target_y:
                        robot.position = (x, y + 1)
                    elif y > target_y:
                        robot.position = (x, y - 1)
                    else:
                        # Reached end, turn around
                        robot.moving_to_end = False
                else:
                    # Moving towards patrol_start
                    target_y = robot.patrol_start[1]
                    if y < target_y:
                        robot.position = (x, y + 1)
                    elif y > target_y:
                        robot.position = (x, y - 1)
                    else:
                        # Reached start, turn around
                        robot.moving_to_end = True

        return obs, done, reward, reset


def create_logistics_lanes_visualization():
    """Create animated GIF showing logistics robots in their designated lanes."""
    print("=" * 70)
    print("Factory Environment - Logistics Lanes Visualization")
    print("=" * 70)
    print("\nLane Assignment:")
    print("  Lane 1 (x=2): ID=5 - Cooker to lower stations")
    print("  Lane 2 (x=3): ID=1,3 - Washer↔Cutter, Cutter↔Cooker")
    print("  Lane 3 (x=4): ID=0,7 - Storage↔Washer, VisionQA↔FinalStorage (center)")
    print("  Lane 4 (x=5): ID=2,4 - Washer↔Cutter, Cutter↔Cooker")
    print("  Lane 5 (x=6): ID=6 - Cooker to lower stations")
    print("=" * 70)

    # Create custom environment
    print("\n1. Creating Custom Factory environment with logistics lanes...")
    env = CustomFactoryEnv()
    env.set_seed(42)

    # Create image renderer
    print("2. Creating image-based renderer...")
    assets_dir = Path(__file__).parent.parent / "public"
    renderer = FactoryImageRenderer(env, assets_dir=assets_dir)

    # Create animation showing logistics movement
    print("3. Generating animation...")
    print("   - 200 steps simulation")
    print("   - Logistics robots patrol their designated lanes")

    output_path = "factory_logistics_lanes.gif"

    # Reset and capture initial state
    env.reset()
    renderer.capture_frame()

    # Run simulation with automated logistics movement
    print("\n4. Running simulation...")
    num_steps = 200

    for step in range(num_steps):
        # Continue operations without spawning products to focus on logistics
        action = "continue"

        # Occasionally spawn a product to show workflow
        if step % 20 == 0 and step < 100:
            action = "produce_tomato_pasta"

        obs, done, reward, reset = env.step(action)

        # Capture every frame
        renderer.capture_frame()

        # Print progress
        if step % 25 == 0:
            print(f"   Step {step}/{num_steps}")

        if done:
            break

    # Print logistics robot positions
    print("\n5. Final logistics robot positions:")
    for robot in env.logistics_robots:
        route_info = f"{robot.assigned_route}" if hasattr(robot, 'assigned_route') else "N/A"
        lane_info = f"Lane x={robot.lane_x}" if hasattr(robot, 'lane_x') else "N/A"
        print(f"   ID={robot.robot_id}: {lane_info}, Route={route_info}, Pos={robot.position}")

    # Save as GIF
    print(f"\n6. Saving animation...")
    renderer.save_gif(output_path, duration=100, loop=0)  # 100ms per frame

    print(f"\n[OK] Animation complete!")
    print(f"[OK] Saved to: {output_path}")
    print(f"[OK] Shows logistics robots moving in their designated lanes")
    print("=" * 70)


if __name__ == "__main__":
    create_logistics_lanes_visualization()
