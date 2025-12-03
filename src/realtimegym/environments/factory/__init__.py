"""Factory environment package - imports needed components."""

from typing import Any, Optional

from realtimegym.environments.base import BaseEnv
from realtimegym.environments.render.factory_render import FactoryRender

# Import components from submodules
from .items import RECIPES, Item, ItemType, Recipe, RecipeType
from .robots import LogisticRobot, RobotArm, Task
from .stations import (
    Cooker,
    Cutter,
    Plating,
    Sealing,
    Station,
    StationStatus,
    StationType,
    Storage,
    VisionQA,
    Washer,
)
from .design_agent import DesignAgent
from .llm_design_agent import LLMDesignAgent
from .llm_meta_planner import LLMMetaPlannerAgent
from .meta_planner import MetaPlannerAgent
from .upper_agents import (
    FacilityManagementAgent,
    ProductDesignAgent,
    QualityInspectionAgent,
    RobotCoordinationAgent,
    create_upper_agents,
)

# Seed mapping for difficulty levels
seed_mapping = {
    "E": {i: 1000 + i for i in range(32)},  # Easy
    "M": {i: 5000 + i for i in range(32)},  # Medium
    "H": {i: 8000 + i for i in range(32)},  # Hard
}


def setup_env(
    seed: int, cognitive_load: str, save_trajectory_gifs: bool = False
) -> tuple[BaseEnv, int, Optional[FactoryRender]]:
    """Setup Factory environment with given parameters."""
    env = FactoryEnv(cognitive_load=cognitive_load)
    env.set_seed(seed_mapping[cognitive_load][seed])
    render = None
    if save_trajectory_gifs:
        render = FactoryRender()
    return env, seed_mapping[cognitive_load][seed], render


class FactoryEnv(BaseEnv):
    """
    Factory Environment - Unmanned food production factory.

    Grid: 20 (rows) x 30 (columns)
    2 production lines
    Stations: Storage, Washer, Cutter, Cooker, Plating, Sealing, VisionQA
    Robots: 20 RobotArms, 24 LogisticRobots
    Recipes: Salad, Pasta, Fried Rice
    """

    def __init__(self, cognitive_load: str = "E") -> None:
        super().__init__()
        self.cognitive_load = cognitive_load
        self.grid_height = 20
        self.grid_width = 30
        self.max_steps = 1000  # 1000 steps = 10000 seconds = ~2.8 hours
        self.completed_products = 0
        self.defective_products = 0
        self.total_lead_time = 0.0
        self.collision_count = 0

    def reset(self) -> tuple[dict[str, Any], bool]:
        """Reset the environment."""
        self.game_turn = 0
        self.reward = 0
        self.terminal = False
        self.completed_products = 0
        self.defective_products = 0
        self.total_lead_time = 0.0
        self.collision_count = 0

        # Initialize grid
        self.grid: list[list[Optional[Station]]] = [
            [None for _ in range(self.grid_width)] for _ in range(self.grid_height)
        ]

        # Initialize stations
        self._initialize_stations()

        # Initialize robots
        self._initialize_robots()

        # Initialize production orders
        self._initialize_orders()

        # Set recipe for stations that need it (Cooker, Plating)
        recipe = RECIPES[self.current_recipe]
        for station in self.stations:
            if station.station_type in [StationType.COOKER, StationType.PLATING]:
                station.current_recipe = recipe

        # Disable malfunctions for smooth simulation
        for station in self.stations:
            station.malfunction_probability = 0.0

        return self.observe(), self.terminal

    def _initialize_stations(self) -> None:
        """Initialize all stations in the factory."""
        self.stations: list[Station] = []
        station_id = 0

        # Line 1 stations (left side, columns 0-14)
        # Each line: Storage(1) -> Washer(1) -> Cutter(2) -> Cooker(2) -> Plating(1) -> Sealing(1) -> VisionQA(1) -> Storage(1)

        # Line 1 - Compact spacing to fit in row 20
        line1_stations = [
            Storage(station_id=station_id, station_type=StationType.STORAGE, position=(1, 3), line=1),  # Input storage
        ]
        station_id += 1

        line1_stations.append(Washer(station_id=station_id, station_type=StationType.WASHER, position=(3, 3), line=1))
        station_id += 1

        # 2 Cutters - parallel processing
        line1_stations.append(Cutter(station_id=station_id, station_type=StationType.CUTTER, position=(5, 2), line=1))
        station_id += 1
        line1_stations.append(Cutter(station_id=station_id, station_type=StationType.CUTTER, position=(5, 4), line=1))
        station_id += 1

        # 2 Cookers - parallel processing
        line1_stations.append(Cooker(station_id=station_id, station_type=StationType.COOKER, position=(7, 2), line=1))
        station_id += 1
        line1_stations.append(Cooker(station_id=station_id, station_type=StationType.COOKER, position=(7, 4), line=1))
        station_id += 1

        # Plating with increased buffer
        plating = Plating(station_id=station_id, station_type=StationType.PLATING, position=(10, 3), line=1)
        plating.input_buffer_size = 10  # Increased from 5
        line1_stations.append(plating)
        station_id += 1

        line1_stations.append(Sealing(station_id=station_id, station_type=StationType.SEALING, position=(13, 3), line=1))
        station_id += 1

        line1_stations.append(VisionQA(station_id=station_id, station_type=StationType.VISION_QA, position=(16, 3), line=1))
        station_id += 1

        line1_stations.append(Storage(station_id=station_id, station_type=StationType.STORAGE, position=(19, 3), line=1))  # Output storage
        station_id += 1

        # Add Line 1 stations to grid and list
        for station in line1_stations:
            station.random = self.random
            row, col = station.position
            self.grid[row][col] = station
            self.stations.append(station)

        # Line 2 - Compact spacing to fit in row 20
        line2_stations = [
            Storage(station_id=station_id, station_type=StationType.STORAGE, position=(1, 26), line=2),  # Input storage
        ]
        station_id += 1

        line2_stations.append(Washer(station_id=station_id, station_type=StationType.WASHER, position=(3, 26), line=2))
        station_id += 1

        # 2 Cutters - parallel processing
        line2_stations.append(Cutter(station_id=station_id, station_type=StationType.CUTTER, position=(5, 25), line=2))
        station_id += 1
        line2_stations.append(Cutter(station_id=station_id, station_type=StationType.CUTTER, position=(5, 27), line=2))
        station_id += 1

        # 2 Cookers - parallel processing
        line2_stations.append(Cooker(station_id=station_id, station_type=StationType.COOKER, position=(7, 25), line=2))
        station_id += 1
        line2_stations.append(Cooker(station_id=station_id, station_type=StationType.COOKER, position=(7, 27), line=2))
        station_id += 1

        # Plating with increased buffer
        plating = Plating(station_id=station_id, station_type=StationType.PLATING, position=(10, 26), line=2)
        plating.input_buffer_size = 10  # Increased from 5
        line2_stations.append(plating)
        station_id += 1

        line2_stations.append(Sealing(station_id=station_id, station_type=StationType.SEALING, position=(13, 26), line=2))
        station_id += 1

        line2_stations.append(VisionQA(station_id=station_id, station_type=StationType.VISION_QA, position=(16, 26), line=2))
        station_id += 1

        line2_stations.append(Storage(station_id=station_id, station_type=StationType.STORAGE, position=(19, 26), line=2))  # Output storage
        station_id += 1

        # Add Line 2 stations to grid and list
        for station in line2_stations:
            station.random = self.random
            row, col = station.position
            self.grid[row][col] = station
            self.stations.append(station)

        # Initialize storage inventory
        for station in self.stations:
            if isinstance(station, Storage) and station.position[0] == 1:  # Input storages only
                # Add initial raw materials
                station.add_to_inventory(ItemType.LETTUCE, 200)
                station.add_to_inventory(ItemType.ROMAINE, 200)
                station.add_to_inventory(ItemType.SPROUTS, 200)
                station.add_to_inventory(ItemType.CHERRY_TOMATO, 200)
                station.add_to_inventory(ItemType.RICOTTA, 100)
                station.add_to_inventory(ItemType.NUTS, 100)

    def _initialize_robots(self) -> None:
        """Initialize robot agents."""
        self.robot_arms: list[RobotArm] = []
        self.logistic_robots: list[LogisticRobot] = []

        robot_id = 0

        # Create robot arms - one per non-storage station
        for station in self.stations:
            if station.station_type != StationType.STORAGE:
                arm = RobotArm(
                    robot_id=robot_id,
                    position=station.position,
                    assigned_station=station,
                )
                robot_id += 1
                self.robot_arms.append(arm)

        # Create logistic robots - 12 per line (24 total)
        # Robots positioned between stations (in corridors)
        # Each robot is assigned a segment (adjacent stations only)

        # Define segments for relay-style transport (Salad recipe: no Cooker)
        segments = [
            ("Washer", "Cutter"),      # Segment 1
            ("Cutter", "Plating"),     # Segment 2
            ("Plating", "Sealing"),    # Segment 3
            ("Sealing", "VisionQA"),   # Segment 4
            ("VisionQA", "Storage"),   # Segment 5
        ]

        # Line 1 robots - positioned between stations
        # Layout: Storage(1) -> Washer(3) -> Cutter(5) -> Cooker(7) -> Plating(10) -> Sealing(13) -> VisionQA(16) -> Storage(19)

        line1_positions = []
        corridors = [1, 5]  # Two main corridors
        # Select key robot positions covering all segment transitions
        # Stations: Storage(1), Washer(3), Cutter(5), Cooker(7), Plating(10), Sealing(13), VisionQA(16), Storage(19)
        robot_rows = [2, 4, 6, 9, 12, 15, 18]  # 7 robots per corridor (but we'll use 6)

        for corridor in corridors:
            for row in robot_rows[:6]:  # 6 robots per corridor (12 total per line)
                line1_positions.append((row, corridor))

        # Reserve robots: 2 per line (only row 6, one per corridor = 2 per line)
        # robot_rows[:6] = [2, 4, 6, 9, 12, 15]
        # row 6 and 9 both handle Cutter->Plating, so row 6 can be reserve
        reserve_rows = {6}  # Total 2 reserve robots per line (one per corridor)

        for i in range(min(12, len(line1_positions))):
            pos = line1_positions[i]
            row = pos[0]

            # Determine segment based on row position
            # Washer(3), Cutter(5), Cooker(7), Plating(10), Sealing(13), VisionQA(16), Storage(19)
            # robot_rows[:6] = [2, 4, 6, 9, 12, 15]
            if row <= 3:
                segment = segments[0]  # Washer → Cutter
            elif row <= 8:
                segment = segments[1]  # Cutter → Plating
            elif row <= 11:
                segment = segments[2]  # Plating → Sealing
            elif row <= 14:
                segment = segments[3]  # Sealing → VisionQA
            else:
                segment = segments[4]  # VisionQA → Storage

            # Reserve robots at specific rows (spread across segments)
            is_active = row not in reserve_rows

            logistic = LogisticRobot(robot_id=robot_id, position=pos, line=1, is_active=is_active)
            logistic.home_position = pos
            logistic.assigned_segment = segment
            robot_id += 1
            self.logistic_robots.append(logistic)

        # Line 2 robots - positioned between stations
        line2_positions = []
        corridors = [24, 28]  # Two main corridors

        for corridor in corridors:
            for row in robot_rows:  # 6 robots per corridor (12 total per line)
                line2_positions.append((row, corridor))

        for i in range(min(12, len(line2_positions))):
            pos = line2_positions[i]
            row = pos[0]

            # Determine segment based on row position
            # Washer(3), Cutter(5), Cooker(7), Plating(10), Sealing(13), VisionQA(16), Storage(19)
            # robot_rows[:6] = [2, 4, 6, 9, 12, 15]
            if row <= 3:
                segment = segments[0]  # Washer → Cutter
            elif row <= 8:
                segment = segments[1]  # Cutter → Plating
            elif row <= 11:
                segment = segments[2]  # Plating → Sealing
            elif row <= 14:
                segment = segments[3]  # Sealing → VisionQA
            else:
                segment = segments[4]  # VisionQA → Storage

            # Reserve robots at specific rows (spread across segments)
            is_active = row not in reserve_rows

            logistic = LogisticRobot(robot_id=robot_id, position=pos, line=2, is_active=is_active)
            logistic.home_position = pos
            logistic.assigned_segment = segment
            robot_id += 1
            self.logistic_robots.append(logistic)

    def _initialize_orders(self) -> None:
        """Initialize production orders."""
        # Based on difficulty, assign different order quantities
        if self.cognitive_load == "E":
            self.target_products = 10
        elif self.cognitive_load == "M":
            self.target_products = 25
        else:  # H
            self.target_products = 50

        self.current_recipe = RecipeType.SALAD  # Start with 

    def step(self, action: str) -> tuple[dict[str, Any], bool, float, bool]:
        """
        Execute one step in the environment.

        Action format: "WAIT" or specific high-level commands
        For now, we use rule-based automation, so action can be "AUTO"
        """
        self.game_turn += 1
        step_reward = 0.0

        # Rule-based automation: robots operate automatically
        # Process all stations
        for station in self.stations:
            station.process()
            # Check for malfunction
            if station.check_malfunction():
                step_reward -= 5.0  # Penalty for malfunction

        # Update robot arms
        for arm in self.robot_arms:
            arm.step()

        # Update logistic robots with simple rule-based behavior
        self._update_logistic_robots_rule_based()

        # Check for completed products
        completed_this_step = self._check_completed_products()
        step_reward += completed_this_step * 10.0  # Reward for completed products

        # Check terminal condition
        if self.game_turn >= self.max_steps or self.completed_products >= self.target_products:
            self.terminal = True
            # Final rewards based on KPIs
            step_reward += self._calculate_final_reward()

        self.reward += step_reward

        return self.observe(), self.terminal, step_reward, False

    def _update_logistic_robots_rule_based(self) -> None:
        """Rule-based behavior for logistic robots with segment assignment."""
        # Track which stations are already being serviced in this update cycle
        stations_being_serviced = set()

        for robot in self.logistic_robots:
            # Skip reserve robots
            if not robot.is_active:
                continue

            # If robot is idle and has no tasks, find work within assigned segment
            if robot.status.value == "Idle" and len(robot.task_queue) == 0:
                from_type, to_type = robot.assigned_segment

                # Find from_station (source) on the same line
                from_station = None
                for station in self.stations:
                    if (station.line == robot.line and
                        station.station_type.value == from_type and
                        station.can_provide_output() and
                        station.station_id not in stations_being_serviced):
                        from_station = station
                        break

                if from_station:
                    # Find to_station (destination) on the same line
                    # For parallel stations (Cutter/Cooker), choose least loaded one
                    to_station = None
                    candidate_stations = []
                    for station in self.stations:
                        if (station.line == robot.line and
                            station.station_type.value == to_type and
                            station.can_accept_input()):
                            # For Storage, only use output storage (row 19)
                            if to_type == "Storage" and station.position[0] != 19:
                                continue
                            candidate_stations.append(station)

                    # Choose station with least input buffer (for parallel processing)
                    if candidate_stations:
                        to_station = min(candidate_stations, key=lambda s: len(s.input_buffer))

                    if to_station:
                        # Mark station as being serviced
                        stations_being_serviced.add(from_station.station_id)

                        # Create pick task
                        pick_task = Task(
                            task_id=0,
                            task_type="pick",
                            target_station=from_station,
                            target_position=from_station.position,
                            priority=1,
                        )
                        # Create drop task
                        drop_task = Task(
                            task_id=1,
                            task_type="drop",
                            target_station=to_station,
                            target_position=to_station.position,
                            priority=1,
                        )
                        robot.assign_task(pick_task)
                        robot.assign_task(drop_task)

            # Execute robot step
            robot.step(self.grid)

    def _check_completed_products(self) -> int:
        """Check for completed products in final storage."""
        completed = 0
        for station in self.stations:
            if isinstance(station, Storage):
                # Check output buffer for completed products
                while station.can_provide_output():
                    item = station.take_output()
                    if item and item.item_type != ItemType.DEFECTIVE:
                        completed += 1
                        self.completed_products += 1
                    elif item and item.item_type == ItemType.DEFECTIVE:
                        self.defective_products += 1

        return completed

    def _calculate_final_reward(self) -> float:
        """Calculate final reward based on KPIs."""
        reward = 0.0

        # Production volume reward
        reward += self.completed_products * 10.0

        # Quality reward (low defect rate)
        if self.completed_products + self.defective_products > 0:
            quality_rate = self.completed_products / (self.completed_products + self.defective_products)
            reward += quality_rate * 100.0

        # Penalty for collisions
        reward -= self.collision_count * 2.0

        return reward

    def state_string(self) -> str:
        """Return state as string for visualization."""
        lines = []
        lines.append(f"=== Factory Environment (Turn {self.game_turn}/{self.max_steps}) ===")
        lines.append(f"Completed: {self.completed_products}/{self.target_products}")
        lines.append(f"Defective: {self.defective_products}")
        lines.append(f"Reward: {self.reward:.2f}")
        lines.append("")

        # Show station statuses
        lines.append("Station Status:")
        for station in self.stations[:5]:  # Show first 5 stations
            status = station.status.value
            in_buf = len(station.input_buffer)
            out_buf = len(station.output_buffer)
            lines.append(f"  {station.station_type.value}: {status} (In:{in_buf}, Out:{out_buf})")

        return "\n".join(lines)

    def state_builder(self) -> dict[str, Any]:
        """Build structured state for agents."""
        return {
            "grid_size": (self.grid_height, self.grid_width),
            "turn": self.game_turn,
            "max_turns": self.max_steps,
            "completed_products": self.completed_products,
            "target_products": self.target_products,
            "defective_products": self.defective_products,
            "stations": [s.get_state_dict() for s in self.stations],
            "robot_arms_count": len([r for r in self.robot_arms if r.status.value == "Idle"]),
            "logistic_robots_count": len([r for r in self.logistic_robots if r.status.value == "Idle"]),
            "collision_count": self.collision_count,
        }


__all__ = [
    # Items
    "Item",
    "ItemType",
    "Recipe",
    "RecipeType",
    "RECIPES",
    # Stations
    "Station",
    "StationType",
    "StationStatus",
    "Storage",
    "Washer",
    "Cutter",
    "Cooker",
    "Plating",
    "Sealing",
    "VisionQA",
    # Robots
    "RobotArm",
    "LogisticRobot",
    "Task",
    # Upper Agents
    "MetaPlannerAgent",
    "DesignAgent",
    "LLMMetaPlannerAgent",
    "LLMDesignAgent",
    "ProductDesignAgent",
    "FacilityManagementAgent",
    "RobotCoordinationAgent",
    "QualityInspectionAgent",
    "create_upper_agents",
    # Environment
    "FactoryEnv",
    "setup_env",
]
