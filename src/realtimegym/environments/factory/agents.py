"""Robot agent classes for the factory environment."""

from dataclasses import dataclass
from enum import Enum

from .stations import WorkItem


class AgentStatus(Enum):
    """Robot agent operational status."""

    IDLE = "idle"
    MOVING = "moving"
    OPERATING = "operating"
    ERROR = "error"


@dataclass
class Task:
    """Task assigned to a robot."""

    task_type: str  # "move", "operate", "pick", "drop"
    target_position: tuple[int, int] | None = None
    target_station: str | None = None
    work_item: WorkItem | None = None


class Robot:
    """Base class for robot agents."""

    def __init__(self, robot_id: int, position: tuple[int, int], robot_type: str):
        self.robot_id = robot_id
        self.position = position
        self.robot_type = robot_type  # "arm" or "logistics"
        self.status = AgentStatus.IDLE
        self.current_task: Task | None = None
        self.task_queue: list[Task] = []
        self.error_flag = False

        # Statistics
        self.total_moves = 0
        self.total_tasks_completed = 0
        self.idle_steps = 0

    def assign_task(self, task: Task) -> bool:
        """Assign a new task to the robot."""
        if len(self.task_queue) < 5:  # Max queue size
            self.task_queue.append(task)
            return True
        return False

    def move_towards(self, target: tuple[int, int]) -> None:
        """Move one step towards target position."""
        x, y = self.position
        tx, ty = target

        # Simple Manhattan distance movement
        if x < tx:
            x += 1
        elif x > tx:
            x -= 1
        elif y < ty:
            y += 1
        elif y > ty:
            y -= 1

        self.position = (x, y)
        self.total_moves += 1

    def is_at_position(self, target: tuple[int, int]) -> bool:
        """Check if robot is at target position."""
        return self.position == target

    def step(self) -> None:
        """Execute one time step."""
        # Start new task if idle
        if self.current_task is None and len(self.task_queue) > 0:
            self.current_task = self.task_queue.pop(0)
            self.status = AgentStatus.MOVING

        # Execute current task
        if self.current_task is not None:
            if self.current_task.task_type == "move":
                if self.current_task.target_position:
                    if not self.is_at_position(self.current_task.target_position):
                        self.move_towards(self.current_task.target_position)
                        self.status = AgentStatus.MOVING
                    else:
                        # Reached destination
                        self.complete_task()
        else:
            self.status = AgentStatus.IDLE
            self.idle_steps += 1

    def complete_task(self) -> None:
        """Complete current task."""
        self.current_task = None
        self.total_tasks_completed += 1
        self.status = AgentStatus.IDLE

    def get_state(self) -> dict:
        """Get current state of the robot."""
        return {
            "robot_id": self.robot_id,
            "type": self.robot_type,
            "position": self.position,
            "status": self.status.value,
            "has_task": self.current_task is not None,
            "queue_size": len(self.task_queue),
            "error": self.error_flag,
            "total_moves": self.total_moves,
            "total_tasks": self.total_tasks_completed,
            "idle_steps": self.idle_steps,
        }


class RobotArm(Robot):
    """Robot arm for processing operations at stations."""

    def __init__(self, robot_id: int, position: tuple[int, int], assigned_station: str):
        super().__init__(robot_id, position, "arm")
        self.assigned_station = assigned_station
        self.operation_time_remaining = 0

    def step(self) -> None:
        """Execute one time step with operation capability."""
        # Handle ongoing operation
        if self.status == AgentStatus.OPERATING:
            self.operation_time_remaining -= 1
            if self.operation_time_remaining <= 0:
                self.complete_task()
            return

        # Start new task if idle
        if self.current_task is None and len(self.task_queue) > 0:
            self.current_task = self.task_queue.pop(0)

        # Execute current task
        if self.current_task is not None:
            if self.current_task.task_type == "operate":
                # Start operation
                self.status = AgentStatus.OPERATING
                self.operation_time_remaining = 2  # Takes 2 steps to operate
            elif self.current_task.task_type == "move":
                if self.current_task.target_position:
                    if not self.is_at_position(self.current_task.target_position):
                        self.move_towards(self.current_task.target_position)
                        self.status = AgentStatus.MOVING
                    else:
                        self.complete_task()
        else:
            self.status = AgentStatus.IDLE
            self.idle_steps += 1

    def get_state(self) -> dict:
        state = super().get_state()
        state["assigned_station"] = self.assigned_station
        state["operation_remaining"] = self.operation_time_remaining
        return state


class LogisticsRobot(Robot):
    """Logistics robot for material transport."""

    def __init__(self, robot_id: int, position: tuple[int, int]):
        super().__init__(robot_id, position, "logistics")
        self.carrying = False
        self.carried_item: WorkItem | None = None

    def step(self) -> None:
        """Execute one time step with pickup/drop capability."""
        # Start new task if idle
        if self.current_task is None and len(self.task_queue) > 0:
            self.current_task = self.task_queue.pop(0)

        # Execute current task
        if self.current_task is not None:
            if self.current_task.task_type == "move":
                if self.current_task.target_position:
                    if not self.is_at_position(self.current_task.target_position):
                        self.move_towards(self.current_task.target_position)
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
                # Drop item
                if self.carrying:
                    self.carried_item = None
                    self.carrying = False
                    self.complete_task()
        else:
            self.status = AgentStatus.IDLE
            self.idle_steps += 1

    def get_state(self) -> dict:
        state = super().get_state()
        state["carrying"] = self.carrying
        state["carried_item"] = (
            self.carried_item.product_type if self.carried_item else None
        )
        return state
