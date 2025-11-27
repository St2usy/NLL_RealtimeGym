"""Main Factory environment implementation."""

from typing import Any, Union

from ..base import BaseEnv
from .agents import LogisticsRobot, RobotArm, Task
from .recipes import RECIPES, Recipe
from .stations import Cooker, Cutter, Plating, Sealing, Station, Storage, VisionQA, Washer, WorkItem


class FactoryEnv(BaseEnv):
    """
    Unmanned food factory environment with multi-agent coordination.

    Grid size: 16 x 30
    Production lines: 2
    Products: Ricotta Salad, Shrimp Fried Rice, Tomato Pasta
    """

    def __init__(self):
        super().__init__()
        self.width = 30
        self.height = 16
        self.num_lines = 2

        # Stations and robots
        self.stations: dict[str, list[Station]] = {}
        self.robot_arms: list[RobotArm] = []
        self.logistics_robots: list[LogisticsRobot] = []

        # Production tracking
        self.product_counter = 0
        self.products_in_progress: list[WorkItem] = []
        self.completed_products: list[WorkItem] = []
        self.rejected_products = 0

        # KPIs
        self.total_production = 0
        self.total_lead_time = 0
        self.collision_count = 0

        # Production schedule
        self.production_queue: list[tuple[str, int]] = []  # (product_type, quantity)

        # Robot lookup by ID (for coordinator agent task assignment)
        self.robot_lookup: dict[str, Union[RobotArm, LogisticsRobot]] = {}

    def reset(self) -> tuple[dict[str, Any], bool]:
        """Reset the factory environment."""
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

        # Initialize stations for 2 production lines
        self._setup_stations()

        # Initialize robots
        self._setup_robots()

        # Schedule initial production
        self._schedule_production()

        return self.observe(), self.terminal

    def _setup_stations(self) -> None:
        """Setup stations for both production lines."""
        self.stations = {
            "Storage": [],
            "Washer": [],
            "Cutter": [],
            "Cooker": [],
            "Plating": [],
            "Sealing": [],
            "VisionQA": [],
            "FinalStorage": [],
        }

        # Line 1 (left side, x=0-14)
        # Line 2 (right side, x=15-29)
        for line_idx in range(self.num_lines):
            x_offset = line_idx * 15

            # Storage at top
            self.stations["Storage"].append(Storage(position=(1 + x_offset, 1)))

            # Washer
            self.stations["Washer"].append(Washer(position=(3 + x_offset, 3)))

            # Cutter
            self.stations["Cutter"].append(Cutter(position=(3 + x_offset, 6)))

            # Cooker
            self.stations["Cooker"].append(Cooker(position=(3 + x_offset, 9)))

            # Plating
            self.stations["Plating"].append(Plating(position=(3 + x_offset, 11)))

            # Sealing
            self.stations["Sealing"].append(Sealing(position=(5 + x_offset, 13)))

            # VisionQA
            self.stations["VisionQA"].append(VisionQA(position=(7 + x_offset, 13)))

            # Final Storage at bottom
            self.stations["FinalStorage"].append(
                Storage(position=(10 + x_offset, 14), is_final=True)
            )

    def _setup_robots(self) -> None:
        """Setup robot agents."""
        self.robot_arms = []
        self.logistics_robots = []
        self.robot_lookup = {}

        robot_id = 0

        # Setup robot arms (6 processing + 4 plating per line = 10 per line = 20 total)
        for line_idx in range(self.num_lines):
            x_offset = line_idx * 15

            # 2 arms for Washer
            for i in range(2):
                self.robot_arms.append(
                    RobotArm(
                        robot_id=robot_id,
                        position=(2 + x_offset, 3 + i),
                        assigned_station="Washer",
                    )
                )
                robot_id += 1

            # 2 arms for Cutter
            for i in range(2):
                self.robot_arms.append(
                    RobotArm(
                        robot_id=robot_id,
                        position=(2 + x_offset, 6 + i),
                        assigned_station="Cutter",
                    )
                )
                robot_id += 1

            # 2 arms for Cooker
            for i in range(2):
                self.robot_arms.append(
                    RobotArm(
                        robot_id=robot_id,
                        position=(2 + x_offset, 9 + i),
                        assigned_station="Cooker",
                    )
                )
                robot_id += 1

            # 2 arms for Plating
            for i in range(2):
                self.robot_arms.append(
                    RobotArm(
                        robot_id=robot_id,
                        position=(2 + x_offset, 11 + i),
                        assigned_station="Plating",
                    )
                )
                robot_id += 1

            # 1 arm for Sealing
            self.robot_arms.append(
                RobotArm(
                    robot_id=robot_id,
                    position=(4 + x_offset, 13),
                    assigned_station="Sealing",
                )
            )
            robot_id += 1

            # 1 arm for VisionQA
            self.robot_arms.append(
                RobotArm(
                    robot_id=robot_id,
                    position=(6 + x_offset, 13),
                    assigned_station="VisionQA",
                )
            )
            robot_id += 1

        # Setup logistics robots (8 + 4 per line = 12 per line = 24 total)
        for line_idx in range(self.num_lines):
            x_offset = line_idx * 15

            # 12 logistics robots distributed along the line
            for i in range(12):
                y_pos = 2 + i
                self.logistics_robots.append(
                    LogisticsRobot(
                        robot_id=robot_id,
                        position=(5 + x_offset, y_pos),
                    )
                )
                robot_id += 1

        # Build robot lookup dictionary
        for i, robot in enumerate(self.robot_arms):
            # Name robot arms by their assigned station
            station_name = robot.assigned_station.lower()
            robot_name = f"robot_arm_{station_name}_{i}"
            self.robot_lookup[robot_name] = robot

        for i, robot in enumerate(self.logistics_robots):
            robot_name = f"logistics_{i}"
            self.robot_lookup[robot_name] = robot

    def _schedule_production(self) -> None:
        """Schedule initial production orders."""
        # Simple production schedule
        self.production_queue = [
            ("ricotta_salad", 10),
            ("shrimp_fried_rice", 10),
            ("tomato_pasta", 10),
        ]

    def _spawn_product(self, product_type: str) -> WorkItem:
        """Create a new product instance."""
        recipe = RECIPES[product_type]
        self.product_counter += 1

        work_item = WorkItem(
            product_type=product_type,
            product_id=self.product_counter,
            current_step=0,
            time_remaining=recipe.processing_times[recipe.workflow[0]],
            ingredients=recipe.ingredients.copy(),
        )

        return work_item

    def _auto_workflow(self) -> None:
        """
        Automatic workflow management for prototype.
        In production, this would be handled by upper-level agents.
        """
        # Process each station type in workflow order (exclude FinalStorage as it's the end)
        workflow_order = [
            "Storage",
            "Washer",
            "Cutter",
            "Cooker",
            "Plating",
            "Sealing",
            "VisionQA",
        ]

        for station_type in workflow_order:
            for station in self.stations[station_type]:
                # Move completed items to next station
                while len(station.output_buffer) > 0:
                    item = station.pickup_output()
                    if item is None:
                        break

                    # Find next station in workflow
                    recipe = RECIPES[item.product_type]
                    item.current_step += 1

                    if item.current_step < len(recipe.workflow):
                        next_station_type = recipe.workflow[item.current_step]
                        next_processing_time = recipe.processing_times[next_station_type]

                        # Update work item
                        item.time_remaining = next_processing_time

                        # Add to next station (use same line index)
                        line_idx = self.stations[station_type].index(station)
                        if line_idx < len(self.stations[next_station_type]):
                            next_station = self.stations[next_station_type][line_idx]
                            next_station.add_to_queue(item)

    def step(self, action: Union[str, dict]) -> tuple[dict[str, Any], bool, float, bool]:
        """
        Execute one time step in the factory.

        Args:
            action: Either:
                - String: High-level command ("produce_salad", "continue", etc.)
                - Dict: Task assignments from coordinator agent
                    Format: {"robot_id": {"type": "task_type", ...}, ...}

        For string actions:
        - "produce_salad": Start producing ricotta salad
        - "produce_rice": Start producing shrimp fried rice
        - "produce_pasta": Start producing tomato pasta
        - "maintain_cutter_X": Perform maintenance on cutter at line X
        - "continue": Continue current operations
        """
        self.game_turn += 1
        step_reward = 0

        # Determine if using coordinator agent mode
        coordinator_mode = isinstance(action, dict)

        # Process action
        if coordinator_mode:
            # Coordinator agent mode: assign tasks to robots
            self._assign_tasks_to_robots(action)

        elif isinstance(action, str):
            # String action mode (legacy/high-level commands)
            if action.startswith("produce_"):
                product_type = action.replace("produce_", "")
                if product_type in RECIPES:
                    # Create new product and add to first storage
                    work_item = self._spawn_product(product_type)
                    self.stations["Storage"][0].add_to_queue(work_item)
                    self.products_in_progress.append(work_item)

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

        # Auto workflow only if NOT in coordinator mode
        if not coordinator_mode:
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
                    completed_this_step += 1
                    # Calculate lead time (simplified: current turn - product_id as proxy)
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

        # Check termination (after 500 steps or production queue empty)
        if self.game_turn >= 500:
            self.terminal = True

        self.reward = step_reward

        return self.observe(), self.terminal, self.reward, False

    def state_string(self) -> str:
        """Generate string visualization of factory state."""
        lines = []
        lines.append("=" * 60)
        lines.append(f"FACTORY STATE - Turn {self.game_turn}")
        lines.append("=" * 60)

        # Production stats
        lines.append(f"\nProduction:")
        lines.append(f"  In Progress: {len(self.products_in_progress)}")
        lines.append(f"  Completed: {len(self.completed_products)}")
        lines.append(f"  Rejected: {self.rejected_products}")

        avg_lead_time = (
            self.total_lead_time / self.total_production
            if self.total_production > 0
            else 0
        )
        lines.append(f"  Avg Lead Time: {avg_lead_time:.1f} steps")

        # Station status
        lines.append(f"\nStations (Line 1 | Line 2):")
        for station_type in [
            "Storage",
            "Washer",
            "Cutter",
            "Cooker",
            "Plating",
            "Sealing",
            "VisionQA",
            "FinalStorage",
        ]:
            stations = self.stations[station_type]
            if len(stations) >= 2:
                s1, s2 = stations[0], stations[1]
                lines.append(
                    f"  {station_type:12s}: {s1.status.value:12s} (Q:{len(s1.queue):2d}) | "
                    f"{s2.status.value:12s} (Q:{len(s2.queue):2d})"
                )

        # Robot stats
        idle_arms = sum(1 for r in self.robot_arms if r.status.value == "idle")
        idle_logistics = sum(
            1 for r in self.logistics_robots if r.status.value == "idle"
        )

        lines.append(f"\nRobots:")
        lines.append(
            f"  Arms: {len(self.robot_arms)} ({idle_arms} idle, "
            f"{len(self.robot_arms) - idle_arms} busy)"
        )
        lines.append(
            f"  Logistics: {len(self.logistics_robots)} ({idle_logistics} idle, "
            f"{len(self.logistics_robots) - idle_logistics} busy)"
        )

        lines.append("=" * 60)

        return "\n".join(lines)

    def state_builder(self) -> dict[str, Any]:
        """Build structured state for agents."""
        # Aggregate station states
        station_states = {}
        for station_type, station_list in self.stations.items():
            station_states[station_type] = [s.get_state() for s in station_list]

        # Aggregate robot states
        robot_arm_states = [r.get_state() for r in self.robot_arms]
        logistics_states = [r.get_state() for r in self.logistics_robots]

        # Calculate KPIs
        total_stations = sum(len(sl) for sl in self.stations.values())
        idle_stations = sum(
            1
            for sl in self.stations.values()
            for s in sl
            if s.status.value == "idle"
        )
        station_idle_ratio = idle_stations / total_stations if total_stations > 0 else 0

        robot_idle_ratio = (
            sum(1 for r in self.robot_arms if r.status.value == "idle")
            + sum(1 for r in self.logistics_robots if r.status.value == "idle")
        ) / (len(self.robot_arms) + len(self.logistics_robots))

        avg_lead_time = (
            self.total_lead_time / self.total_production
            if self.total_production > 0
            else 0
        )

        defect_rate = (
            self.rejected_products / (self.total_production + self.rejected_products)
            if (self.total_production + self.rejected_products) > 0
            else 0
        )

        return {
            "turn": self.game_turn,
            "stations": station_states,
            "robot_arms": robot_arm_states,
            "logistics_robots": logistics_states,
            "kpis": {
                "production": self.total_production,
                "in_progress": len(self.products_in_progress),
                "rejected": self.rejected_products,
                "avg_lead_time": round(avg_lead_time, 2),
                "station_idle_ratio": round(station_idle_ratio, 3),
                "robot_idle_ratio": round(robot_idle_ratio, 3),
                "collision_count": self.collision_count,
                "defect_rate": round(defect_rate, 3),
            },
            "production_queue": self.production_queue,
        }

    def observe(self) -> dict[str, Any]:
        """
        Return observation for agents (implementing BaseEnv interface).

        Returns:
            Dictionary with state_string, game_turn, and detailed state
        """
        return {
            "state_string": self.state_string(),
            "game_turn": self.game_turn,
            "state": self._build_state_for_coordinator(),
        }

    def _build_state_for_coordinator(self) -> dict[str, Any]:
        """
        Build state specifically for coordinator agent.

        Includes production queue, station states, robot states, and KPIs.
        """
        # Get base state
        base_state = self.state_builder()

        # Build robots dict with string IDs
        robots = {}
        for robot_name, robot in self.robot_lookup.items():
            robots[robot_name] = robot.get_state()

        # Build stations dict with detailed info
        stations = {}
        for station_type, station_list in self.stations.items():
            stations[station_type] = []
            for station in station_list:
                state = station.get_state()
                # Add current item if processing
                if hasattr(station, "current_item") and station.current_item:
                    state["current_item"] = station.current_item.product_type
                else:
                    state["current_item"] = None
                stations[station_type].append(state)

        return {
            "game_turn": self.game_turn,
            "production_queue": self.production_queue,
            "stations": stations,
            "robots": robots,
            "kpis": base_state["kpis"],
        }

    def _assign_tasks_to_robots(self, task_assignments: dict[str, dict]) -> None:
        """
        Assign tasks from coordinator agent to robots.

        Args:
            task_assignments: Dict mapping robot_id to task dict
                Example: {"logistics_0": {"type": "pick_and_deliver", "from": "Storage", ...}}
        """
        for robot_name, task_dict in task_assignments.items():
            if robot_name not in self.robot_lookup:
                print(f"[FactoryEnv] Warning: Unknown robot '{robot_name}'")
                continue

            robot = self.robot_lookup[robot_name]

            # Only assign to idle robots
            if robot.status.value != "idle":
                continue

            # Create Task object based on task type
            task_type = task_dict.get("type")

            if task_type == "pick_and_deliver":
                # Logistics robot: pick from source, deliver to destination
                from_station = task_dict.get("from")
                to_station = task_dict.get("to")

                if from_station and to_station:
                    # Get station positions
                    from_pos = self._get_station_position(from_station, 0)  # Line 0 for now
                    to_pos = self._get_station_position(to_station, 0)

                    if from_pos and to_pos:
                        # Assign move task to source
                        robot.assign_task(
                            Task(task_type="move", target_position=from_pos)
                        )

            elif task_type == "operate_station":
                # Robot arm: operate assigned station
                if isinstance(robot, RobotArm):
                    robot.assign_task(Task(task_type="operate"))

            elif task_type == "wait":
                # Do nothing
                pass

            elif task_type == "return_to_base":
                # Move back to idle position (simplified: current position)
                pass

    def _get_station_position(self, station_type: str, line_idx: int) -> tuple[int, int] | None:
        """Get position of a station by type and line index."""
        if station_type in self.stations and line_idx < len(self.stations[station_type]):
            return self.stations[station_type][line_idx].position
        return None
