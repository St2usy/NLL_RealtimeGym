"""Rule-based robot agents for Factory environment."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .items import Item
from .stations import Station


class RobotStatus(Enum):
    """Robot operational status."""

    IDLE = "Idle"
    MOVING = "Moving"
    OPERATING = "Operating"
    ERROR = "Error"


class Direction(Enum):
    """Movement directions."""

    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)
    STAY = (0, 0)


@dataclass
class Task:
    """Task for robots."""

    task_id: int
    task_type: str  # "transport", "operate", "wait"
    target_station: Optional[Station] = None
    target_position: Optional[tuple[int, int]] = None
    item: Optional[Item] = None
    priority: int = 0
    completed: bool = False


@dataclass
class RobotArm:
    """Rule-based robot arm agent for station operations."""

    robot_id: int
    position: tuple[int, int]  # (row, col)
    assigned_station: Station
    status: RobotStatus = RobotStatus.IDLE
    current_task: Optional[Task] = None
    task_queue: list[Task] = field(default_factory=list)
    operation_progress: int = 0
    operation_time: int = 6  # Steps needed to complete operation
    error_count: int = 0
    observation_range: int = 3  # Can see 3x3 grid

    def get_observation(self, grid: list[list[Optional[Station]]]) -> dict:
        """Get 3x3 observation around robot."""
        row, col = self.position
        obs = {
            "position": self.position,
            "status": self.status.value,
            "station": self.assigned_station.get_state_dict(),
            "task": self.current_task.task_type if self.current_task else None,
            "nearby_stations": [],
        }

        # Get nearby stations
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                r, c = row + dr, col + dc
                if 0 <= r < len(grid) and 0 <= c < len(grid[0]) and grid[r][c] is not None:
                    obs["nearby_stations"].append(grid[r][c].get_state_dict())

        return obs

    def assign_task(self, task: Task) -> None:
        """Assign a task to the robot."""
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)

    def step(self) -> None:
        """Execute one step of robot action."""
        if self.status == RobotStatus.ERROR:
            return

        # Get next task if idle
        if self.status == RobotStatus.IDLE and len(self.task_queue) > 0:
            self.current_task = self.task_queue.pop(0)
            self.status = RobotStatus.OPERATING
            self.operation_progress = 0

        # Execute current task
        if self.status == RobotStatus.OPERATING and self.current_task:
            self.operation_progress += 1

            if self.operation_progress >= self.operation_time:
                self._complete_task()

    def _complete_task(self) -> None:
        """Complete current task."""
        if not self.current_task:
            return

        task_type = self.current_task.task_type

        if task_type == "operate":
            # Process the station
            self.assigned_station.process()

        elif task_type == "start_operation":
            # Start station operation
            if self.assigned_station.status.value == "Idle":
                self.assigned_station.status = "Busy"  # type: ignore

        self.current_task.completed = True
        self.current_task = None
        self.status = RobotStatus.IDLE
        self.operation_progress = 0

    def raise_error(self) -> None:
        """Raise error flag."""
        self.status = RobotStatus.ERROR
        self.error_count += 1

    def reset_error(self) -> None:
        """Reset error status."""
        self.status = RobotStatus.IDLE
        self.error_count = 0


@dataclass
class LogisticRobot:
    """Rule-based logistic robot for material transport."""

    robot_id: int
    position: tuple[int, int]  # (row, col)
    status: RobotStatus = RobotStatus.IDLE
    carrying_item: Optional[Item] = None
    current_task: Optional[Task] = None
    task_queue: list[Task] = field(default_factory=list)
    path: list[tuple[int, int]] = field(default_factory=list)
    error_count: int = 0
    observation_range: int = 3

    def get_observation(self, grid: list[list[Optional[Station]]]) -> dict:
        """Get 3x3 observation around robot."""
        row, col = self.position
        obs = {
            "position": self.position,
            "status": self.status.value,
            "carrying": self.carrying_item.item_type.value if self.carrying_item else None,
            "task": self.current_task.task_type if self.current_task else None,
            "nearby_stations": [],
        }

        # Get nearby stations
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                r, c = row + dr, col + dc
                if 0 <= r < len(grid) and 0 <= c < len(grid[0]) and grid[r][c] is not None:
                    obs["nearby_stations"].append(grid[r][c].get_state_dict())

        return obs

    def assign_task(self, task: Task) -> None:
        """Assign transport task to the robot."""
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)

    def step(self, grid: list[list[Optional[Station]]]) -> None:
        """Execute one step of robot movement/action."""
        if self.status == RobotStatus.ERROR:
            return

        # Get next task if idle
        if self.status == RobotStatus.IDLE and len(self.task_queue) > 0:
            self.current_task = self.task_queue.pop(0)
            if self.current_task.target_position:
                self._plan_path(self.current_task.target_position)
                self.status = RobotStatus.MOVING

        # Move along path
        if self.status == RobotStatus.MOVING and len(self.path) > 0:
            next_pos = self.path.pop(0)
            # Simple collision avoidance - just move
            self.position = next_pos

            # Check if reached destination
            if len(self.path) == 0:
                self._execute_task_at_destination()

    def _plan_path(self, target: tuple[int, int]) -> None:
        """Plan simple Manhattan path to target."""
        self.path = []
        current = self.position

        # Simple greedy path - move row first, then column
        while current[0] != target[0]:
            if current[0] < target[0]:
                current = (current[0] + 1, current[1])
            else:
                current = (current[0] - 1, current[1])
            self.path.append(current)

        while current[1] != target[1]:
            if current[1] < target[1]:
                current = (current[0], current[1] + 1)
            else:
                current = (current[0], current[1] - 1)
            self.path.append(current)

    def _execute_task_at_destination(self) -> None:
        """Execute task when reached destination."""
        if not self.current_task:
            return

        task_type = self.current_task.task_type

        if task_type == "pick":
            # Pick item from station
            if self.current_task.target_station and not self.carrying_item:
                item = self.current_task.target_station.take_output()
                if item:
                    self.carrying_item = item

        elif task_type == "drop":
            # Drop item to station
            if self.current_task.target_station and self.carrying_item:
                success = self.current_task.target_station.add_input(self.carrying_item)
                if success:
                    self.carrying_item = None

        self.current_task.completed = True
        self.current_task = None
        self.status = RobotStatus.IDLE

    def raise_error(self) -> None:
        """Raise error flag."""
        self.status = RobotStatus.ERROR
        self.error_count += 1

    def reset_error(self) -> None:
        """Reset error status."""
        self.status = RobotStatus.IDLE
        self.error_count = 0
