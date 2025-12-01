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

    Grid: 16 (rows) x 30 (columns)
    2 production lines
    Stations: Storage, Washer, Cutter, Cooker, Plating, Sealing, VisionQA
    Robots: 20 RobotArms, 24 LogisticRobots
    Recipes: Salad, Pasta, Fried Rice
    """

    def __init__(self, cognitive_load: str = "E") -> None:
        super().__init__()
        self.cognitive_load = cognitive_load
        self.grid_height = 16
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

        return self.observe(), self.terminal

    def _initialize_stations(self) -> None:
        """Initialize all stations in the factory."""
        self.stations: list[Station] = []
        station_id = 0

        # Line 1 stations (left side)
        # Storage (top)
        storage1 = Storage(station_id=station_id, station_type=StationType.STORAGE, position=(0, 4))
        station_id += 1
        storage1.random = self.random
        self.grid[0][4] = storage1
        self.stations.append(storage1)

        # Washer
        washer1 = Washer(station_id=station_id, station_type=StationType.WASHER, position=(2, 4))
        station_id += 1
        washer1.random = self.random
        self.grid[2][4] = washer1
        self.stations.append(washer1)

        # Cutter
        cutter1 = Cutter(station_id=station_id, station_type=StationType.CUTTER, position=(4, 2))
        station_id += 1
        cutter1.random = self.random
        self.grid[4][2] = cutter1
        self.stations.append(cutter1)

        # Cooker
        cooker1 = Cooker(station_id=station_id, station_type=StationType.COOKER, position=(6, 2))
        station_id += 1
        cooker1.random = self.random
        self.grid[6][2] = cooker1
        self.stations.append(cooker1)

        # Plating
        plating1 = Plating(station_id=station_id, station_type=StationType.PLATING, position=(9, 2))
        station_id += 1
        plating1.random = self.random
        self.grid[9][2] = plating1
        self.stations.append(plating1)

        # Sealing
        sealing1 = Sealing(station_id=station_id, station_type=StationType.SEALING, position=(11, 4))
        station_id += 1
        sealing1.random = self.random
        self.grid[11][4] = sealing1
        self.stations.append(sealing1)

        # VisionQA
        vqa1 = VisionQA(station_id=station_id, station_type=StationType.VISION_QA, position=(13, 3))
        station_id += 1
        vqa1.random = self.random
        self.grid[13][3] = vqa1
        self.stations.append(vqa1)

        # Storage (bottom)
        storage1_out = Storage(station_id=station_id, station_type=StationType.STORAGE, position=(15, 4))
        station_id += 1
        storage1_out.random = self.random
        self.grid[15][4] = storage1_out
        self.stations.append(storage1_out)

        # Line 2 stations (right side) - similar layout
        # Storage (top)
        storage2 = Storage(station_id=station_id, station_type=StationType.STORAGE, position=(0, 25))
        station_id += 1
        storage2.random = self.random
        self.grid[0][25] = storage2
        self.stations.append(storage2)

        # Washer
        washer2 = Washer(station_id=station_id, station_type=StationType.WASHER, position=(2, 25))
        station_id += 1
        washer2.random = self.random
        self.grid[2][25] = washer2
        self.stations.append(washer2)

        # Add more stations for line 2...
        # (Similar to line 1, positions mirrored)

        # Initialize storage inventory
        for station in self.stations:
            if isinstance(station, Storage):
                # Add initial raw materials
                station.add_to_inventory(ItemType.LETTUCE, 100)
                station.add_to_inventory(ItemType.TOMATO, 100)
                station.add_to_inventory(ItemType.RICE, 100)
                station.add_to_inventory(ItemType.SHRIMP, 50)
                # ... add other materials

    def _initialize_robots(self) -> None:
        """Initialize robot agents."""
        self.robot_arms: list[RobotArm] = []
        self.logistic_robots: list[LogisticRobot] = []

        robot_id = 0

        # Create robot arms (20 total, 10 per line)
        # Assign to each station
        for station in self.stations:
            if station.station_type != StationType.STORAGE:
                arm = RobotArm(
                    robot_id=robot_id,
                    position=station.position,
                    assigned_station=station,
                )
                robot_id += 1
                self.robot_arms.append(arm)

        # Create logistic robots (24 total)
        # Distributed across the factory floor
        for i in range(24):
            row = 1 + (i % 14)  # Spread across rows
            col = 7 + (i // 14) * 8  # Spread across columns
            logistic = LogisticRobot(robot_id=robot_id, position=(row, col))
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

        self.current_recipe = RecipeType.SALAD  # Start with salad

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
        """Simple rule-based behavior for logistic robots."""
        # Find stations that need input/output transport
        for robot in self.logistic_robots:
            if robot.status.value == "Idle" and len(robot.task_queue) == 0:
                # Find a station with output that needs transport
                for station in self.stations:
                    if station.can_provide_output() and station.station_type != StationType.STORAGE:
                        # Create transport task
                        task = Task(
                            task_id=len(robot.task_queue),
                            task_type="pick",
                            target_station=station,
                            target_position=station.position,
                            priority=1,
                        )
                        robot.assign_task(task)
                        break

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
    "ProductDesignAgent",
    "FacilityManagementAgent",
    "RobotCoordinationAgent",
    "QualityInspectionAgent",
    "create_upper_agents",
    # Environment
    "FactoryEnv",
    "setup_env",
]
