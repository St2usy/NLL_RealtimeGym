"""Simulation for processing 100 fried rice with logistics robot transport."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from realtimegym.environments.factory import FactoryEnv
from realtimegym.environments.factory.agents import LogisticsRobot as BaseLogisticsRobot, Task
from realtimegym.environments.factory.recipes import RECIPES

try:
    from realtimegym.environments.factory.image_renderer import FactoryImageRenderer
    HAS_RENDERER = True
except ImportError:
    HAS_RENDERER = False
    print("Warning: PIL not installed. Running without GIF generation.")


class CustomLogisticsRobot(BaseLogisticsRobot):
    """Custom logistics robot that properly handles delivery."""

    def __init__(self, robot_id: int, position: tuple[int, int]):
        super().__init__(robot_id, position)
        self.delivery_station = None

    def step(self) -> None:
        """Execute one time step with proper delivery handling."""
        # Start new task if idle
        if self.current_task is None and len(self.task_queue) > 0:
            self.current_task = self.task_queue.pop(0)

            # If it's a drop task, store the delivery station
            if self.current_task.task_type == "drop":
                if hasattr(self.current_task, 'delivery_station'):
                    self.delivery_station = self.current_task.delivery_station

        # Execute current task
        if self.current_task is not None:
            if self.current_task.task_type == "move":
                if self.current_task.target_position:
                    if not self.is_at_position(self.current_task.target_position):
                        self.move_towards(self.current_task.target_position)
                        from realtimegym.environments.factory.agents import AgentStatus
                        self.status = AgentStatus.MOVING
                    else:
                        self.complete_task()

            elif self.current_task.task_type == "pick":
                # Pick up item
                if self.current_task.work_item and not self.carrying:
                    self.carried_item = self.current_task.work_item
                    self.carrying = True
                    self.complete_task()

            elif self.current_task.task_type == "drop":
                # Drop item and deliver to station
                if self.carrying and self.carried_item and self.delivery_station:
                    # Add to station before dropping
                    self.delivery_station.add_to_queue(self.carried_item)
                    self.carried_item = None
                    self.carrying = False
                    self.delivery_station = None
                    self.complete_task()
        else:
            from realtimegym.environments.factory.agents import AgentStatus
            self.status = AgentStatus.IDLE
            self.idle_steps += 1


class FriedRiceFactoryEnv(FactoryEnv):
    """Custom factory environment with real logistics robot transport."""

    def __init__(self):
        super().__init__()
        # Track station positions for routing
        self.station_positions = {}
        # Track which production line to use (for load balancing)
        self.next_production_line = 0

    def reset(self):
        """Reset the factory environment with custom setup."""
        # First, reset the base environment (but we'll replace the logistics robots)
        self.game_turn = 0
        self.terminal = False
        self.reward = 0

        # Clear all tracking
        self.product_counter = 0
        self.products_in_progress = []
        self.completed_products = []
        self.rejected_products = 0
        self.total_production = 0
        self.total_lead_time = 0
        self.collision_count = 0
        self.next_production_line = 0

        # Initialize stations
        self._setup_stations()

        # Initialize robots with custom logistics robots
        self._setup_custom_robots()

        # Build station position map for logistics routing
        self._build_station_map()

        return self.observe(), self.terminal

    def _setup_custom_robots(self):
        """Setup robot agents with custom logistics robots."""
        from realtimegym.environments.factory.agents import RobotArm

        self.robot_arms = []
        self.logistics_robots = []

        robot_id = 0

        # Setup robot arms (same as base class)
        for line_idx in range(self.num_lines):
            x_offset = line_idx * 8
            station_x = 4 + x_offset
            left_x = station_x - 1
            right_x = station_x + 1

            # 4 arms for Plating
            self.robot_arms.append(RobotArm(robot_id, (left_x, 18), "Plating"))
            robot_id += 1
            self.robot_arms.append(RobotArm(robot_id, (left_x, 20), "Plating"))
            robot_id += 1
            self.robot_arms.append(RobotArm(robot_id, (right_x, 19), "Plating"))
            robot_id += 1
            self.robot_arms.append(RobotArm(robot_id, (right_x, 21), "Plating"))
            robot_id += 1

            # 2 arms for VisionQA
            self.robot_arms.append(RobotArm(robot_id, (left_x, 25), "VisionQA"))
            robot_id += 1
            self.robot_arms.append(RobotArm(robot_id, (right_x, 26), "VisionQA"))
            robot_id += 1

        # Setup custom logistics robots (더 많은 로봇 추가)
        for line_idx in range(self.num_lines):
            x_offset = line_idx * 8
            station_x = 4 + x_offset
            left_x = station_x - 1
            right_x = station_x + 1
            left_x2 = station_x - 2
            right_x2 = station_x + 2

            # Storage 영역 (y=0-4) - 4개 로봇
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (station_x, 1)))
            robot_id += 1
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (station_x, 2)))
            robot_id += 1
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (left_x, 3)))
            robot_id += 1
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (right_x, 3)))
            robot_id += 1

            # Washer 영역 (y=4-9) - 4개 로봇
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (left_x, 6)))
            robot_id += 1
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (right_x, 6)))
            robot_id += 1
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (left_x, 7)))
            robot_id += 1
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (right_x, 7)))
            robot_id += 1

            # Cutter 영역 (y=9-14) - 4개 로봇
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (left_x, 11)))
            robot_id += 1
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (right_x, 11)))
            robot_id += 1
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (left_x, 12)))
            robot_id += 1
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (right_x, 12)))
            robot_id += 1

            # Cooker 이후 영역 (y=14-29) - 4개 로봇
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (left_x2, 16)))
            robot_id += 1
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (right_x2, 16)))
            robot_id += 1
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (station_x, 23)))
            robot_id += 1
            self.logistics_robots.append(CustomLogisticsRobot(robot_id, (station_x, 28)))
            robot_id += 1

    def _build_station_map(self):
        """Build a map of station types to their positions."""
        self.station_positions = {}
        for station_type, station_list in self.stations.items():
            self.station_positions[station_type] = [s.position for s in station_list]

    def _auto_workflow(self):
        """
        Custom workflow using logistics robots for transport.
        Logistics robots pick up items from output buffers and deliver to next stations.
        """
        workflow_order = [
            "Storage",
            "Washer",
            "Cutter",
            "Cooker",
            "Plating",
            "Sealing",
            "VisionQA",
        ]

        # Find available logistics robots
        available_robots = [
            robot for robot in self.logistics_robots
            if not robot.carrying and robot.current_task is None
        ]

        # Process each station type
        for station_type in workflow_order:
            # Re-check available robots for each station type
            available_robots = [
                robot for robot in self.logistics_robots
                if not robot.carrying and robot.current_task is None
            ]

            if not available_robots:
                continue  # Skip this station type if no robots available

            for station_idx, station in enumerate(self.stations[station_type]):
                # Check if station has completed items
                if len(station.output_buffer) > 0:
                    # Find nearest available robot
                    nearest_robot = self._find_nearest_robot(
                        station.position, available_robots
                    )

                    if nearest_robot:
                        # Pickup item
                        item = station.pickup_output()
                        if item is None:
                            continue

                        # Determine next station
                        recipe = RECIPES[item.product_type]
                        item.current_step += 1

                        if item.current_step < len(recipe.workflow):
                            next_station_type = recipe.workflow[item.current_step]
                            next_processing_time = recipe.processing_times[next_station_type]
                            item.time_remaining = next_processing_time

                            # Find next station (prefer same line)
                            next_station = self._get_next_station(
                                next_station_type, station_idx
                            )

                            if next_station:
                                # Assign transport task to robot
                                self._assign_transport_task(
                                    nearest_robot,
                                    item,
                                    station.position,
                                    next_station.position,
                                    next_station
                                )

                                # Remove from available list
                                available_robots.remove(nearest_robot)

    def _find_nearest_robot(self, position, robots):
        """Find the nearest available robot to a position."""
        if not robots:
            return None

        min_dist = float('inf')
        nearest = None

        for robot in robots:
            dist = abs(robot.position[0] - position[0]) + abs(robot.position[1] - position[1])
            if dist < min_dist:
                min_dist = dist
                nearest = robot

        return nearest

    def _get_next_station(self, station_type, preferred_line_idx):
        """Get next station, preferring the same production line."""
        stations = self.stations.get(station_type, [])
        if not stations:
            return None

        # For stations with multiple per line (Cutter, Cooker)
        # Try to use the same line index, or find the least busy one
        if preferred_line_idx < len(stations):
            # Check if this station has capacity
            preferred = stations[preferred_line_idx]
            if len(preferred.queue) < preferred.capacity:
                return preferred

        # Find least busy station
        least_busy = min(stations, key=lambda s: len(s.queue))
        return least_busy

    def _assign_transport_task(self, robot, item, pickup_pos, delivery_pos, delivery_station):
        """Assign a complete transport task to a logistics robot."""
        # Task 1: Move to pickup position
        robot.assign_task(Task(
            task_type="move",
            target_position=pickup_pos
        ))

        # Task 2: Pick up item
        robot.assign_task(Task(
            task_type="pick",
            work_item=item
        ))

        # Task 3: Move to delivery position
        robot.assign_task(Task(
            task_type="move",
            target_position=delivery_pos
        ))

        # Task 4: Drop item at destination
        # We'll store the delivery station reference for later
        drop_task = Task(
            task_type="drop",
            work_item=item,
            target_station=delivery_station.name
        )
        # Store reference to the actual station object
        drop_task.delivery_station = delivery_station  # type: ignore
        robot.assign_task(drop_task)

    def step(self, action: str):
        """Execute one time step with logistics robot handling."""
        self.game_turn += 1
        step_reward = 0

        # Process action
        if action.startswith("produce_"):
            product_type = action.replace("produce_", "")
            if product_type in RECIPES:
                # Create new product and add to storage (load balanced across lines)
                work_item = self._spawn_product(product_type)
                storage_idx = self.next_production_line
                self.stations["Storage"][storage_idx].add_to_queue(work_item)
                self.products_in_progress.append(work_item)
                # Alternate between production lines
                self.next_production_line = (self.next_production_line + 1) % self.num_lines

        elif action.startswith("maintain_cutter"):
            # Maintenance action
            try:
                line_idx = int(action.split("_")[-1])
                if 0 <= line_idx < self.num_lines:
                    cutter = self.stations["Cutter"][line_idx]
                    cutter.blade_sharpness = 1.0
                    cutter.wear_level = 0.0
                    cutter.failure_probability = 0.0
            except (ValueError, IndexError):
                pass

        # Simulate all stations processing
        for station_list in self.stations.values():
            for station in station_list:
                station.process_step(self.random)

        # Custom workflow automation using logistics robots
        self._auto_workflow()

        # Simulate all robots
        for robot in self.robot_arms:
            robot.step()

        for robot in self.logistics_robots:
            robot.step()

        # Check for completed products
        completed_this_step = 0
        for final_storage in self.stations["FinalStorage"]:
            while len(final_storage.output_buffer) > 0:
                item = final_storage.pickup_output()
                if item:
                    self.completed_products.append(item)
                    # Remove from in-progress list
                    if item in self.products_in_progress:
                        self.products_in_progress.remove(item)
                    completed_this_step += 1
                    # Calculate lead time
                    lead_time = self.game_turn
                    self.total_lead_time += lead_time

        # Calculate reward
        self.total_production += completed_this_step
        step_reward = completed_this_step * 10  # 10 points per completed product

        # Penalty for defects
        total_defects = sum(
            station.rejected_count for station in self.stations["VisionQA"]
        )
        defect_penalty = (total_defects - self.rejected_products) * -5
        self.rejected_products = total_defects
        step_reward += defect_penalty

        # Check termination
        if self.game_turn >= 2000:
            self.terminal = True

        self.reward = step_reward

        return self.observe(), self.terminal, self.reward, False


def run_fried_rice_simulation():
    """Run simulation for 100 fried rice production."""
    print("=" * 70)
    print("Fried Rice Production Simulation - 100 Units")
    print("=" * 70)
    print("\nFeatures:")
    print("  - Logistics robots physically transport items between stations")
    print("  - Movement speed: 1 grid per step")
    print("  - Target: 100 shrimp fried rice")
    print("=" * 70)

    # Create custom environment
    print("\n1. Creating Factory environment with logistics transport...")
    env = FriedRiceFactoryEnv()
    env.set_seed(42)

    # Create image renderer if available
    renderer = None
    output_path = "fried_rice_100_production.gif"

    if HAS_RENDERER:
        print("2. Creating image-based renderer...")
        assets_dir = Path(__file__).parent.parent / "public"
        renderer = FactoryImageRenderer(env, assets_dir=assets_dir)
    else:
        print("2. Renderer not available (PIL not installed)")

    # Reset and capture initial state
    print("3. Initializing production...")
    env.reset()
    if renderer:
        renderer.capture_frame()

    # Production parameters
    target_quantity = 100
    spawn_interval = 5  # Spawn every 5 steps (slower to avoid bottleneck)
    max_steps = 5000  # Increased to allow completion

    spawned_count = 0

    print(f"\n4. Starting production (max {max_steps} steps)...")
    print(f"   Target: {target_quantity} fried rice")
    print(f"   Spawn interval: every {spawn_interval} steps")

    for step in range(max_steps):
        # Spawn fried rice until we reach target
        if step % spawn_interval == 0 and spawned_count < target_quantity:
            action = "produce_shrimp_fried_rice"
            spawned_count += 1
        else:
            action = "continue"

        obs, done, reward, reset = env.step(action)
        if renderer:
            renderer.capture_frame()

        # Print progress every 100 steps
        if step % 100 == 0:
            in_progress = len(env.products_in_progress)
            completed = len(env.completed_products)
            rejected = env.rejected_products

            # Count items being carried
            items_in_transit = sum(1 for r in env.logistics_robots if r.carrying)

            # Count items in stations
            items_in_stations = {}
            for station_type, station_list in env.stations.items():
                count = sum(len(s.queue) + len(s.output_buffer) + (1 if s.current_work else 0)
                           for s in station_list)
                if count > 0:
                    items_in_stations[station_type] = count

            print(f"\n   Step {step}/{max_steps}:")
            print(f"     Spawned: {spawned_count}/{target_quantity}")
            print(f"     In progress: {in_progress}")
            print(f"     In transit (on robots): {items_in_transit}")
            print(f"     Completed: {completed}")
            print(f"     Rejected: {rejected}")
            if items_in_stations:
                print(f"     Items in stations: {items_in_stations}")

            # Debug Storage specifically if it has many items
            if step >= 200 and items_in_stations.get("Storage", 0) > 10:
                for idx, s in enumerate(env.stations["Storage"]):
                    if len(s.queue) > 0 or len(s.output_buffer) > 0 or s.current_work:
                        print(f"       Storage[{idx}]: queue={len(s.queue)}, current={'Y' if s.current_work else 'N'}, output={len(s.output_buffer)}")

        # Check if all products are completed
        if (spawned_count >= target_quantity and
            len(env.completed_products) + env.rejected_products >= target_quantity):
            print(f"\n   All {target_quantity} items processed at step {step}!")
            break

        if done:
            break

    # Final statistics
    print("\n5. Production Complete!")
    print("=" * 70)
    print(f"Final Statistics:")
    print(f"  Total spawned: {spawned_count}")
    print(f"  Completed: {len(env.completed_products)}")
    print(f"  Rejected (defects): {env.rejected_products}")
    print(f"  Still in progress: {len(env.products_in_progress)}")

    if env.total_production > 0:
        avg_lead_time = env.total_lead_time / env.total_production
        print(f"  Average lead time: {avg_lead_time:.1f} steps")

    # Logistics robot statistics
    total_moves = sum(r.total_moves for r in env.logistics_robots)
    total_tasks = sum(r.total_tasks_completed for r in env.logistics_robots)
    print(f"\nLogistics Robot Statistics:")
    print(f"  Total robots: {len(env.logistics_robots)}")
    print(f"  Total moves: {total_moves}")
    print(f"  Total tasks completed: {total_tasks}")
    print(f"  Average moves per robot: {total_moves / len(env.logistics_robots):.1f}")

    print("=" * 70)

    # Save as GIF
    if renderer:
        print(f"\n6. Saving animation to {output_path}...")
        renderer.save_gif(output_path, duration=50, loop=0)  # 50ms per frame

        print(f"\n[OK] Simulation complete!")
        print(f"[OK] Animation saved to: {output_path}")
        print(f"[OK] Shows logistics robots transporting {target_quantity} fried rice items")
    else:
        print(f"\n[OK] Simulation complete!")
        print(f"[OK] Install PIL/Pillow to generate GIF animation")
    print("=" * 70)


if __name__ == "__main__":
    run_fried_rice_simulation()
