"""Station classes for the factory environment."""

from dataclasses import dataclass
from enum import Enum


class StationStatus(Enum):
    """Station operational status."""

    IDLE = "idle"
    PROCESSING = "processing"
    WAITING_PICKUP = "waiting_pickup"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class WorkItem:
    """Work item being processed in a station."""

    product_type: str  # ricotta_salad, shrimp_fried_rice, tomato_pasta
    product_id: int  # Unique ID for this product instance
    current_step: int  # Current step in the workflow
    time_remaining: int  # Steps remaining for current station processing
    ingredients: list[str]


class Station:
    """Base class for all stations."""

    def __init__(self, name: str, position: tuple[int, int], capacity: int = 1):
        self.name = name
        self.position = position  # (x, y) on the grid
        self.capacity = capacity
        self.status = StationStatus.IDLE
        self.queue: list[WorkItem] = []
        self.current_work: WorkItem | None = None
        self.output_buffer: list[WorkItem] = []  # Completed items waiting for pickup

        # Maintenance properties
        self.wear_level = 0.0  # 0.0 to 1.0
        self.failure_probability = 0.0
        self.total_processed = 0

    def add_to_queue(self, item: WorkItem) -> bool:
        """Add item to processing queue."""
        if len(self.queue) < self.capacity:
            self.queue.append(item)
            return True
        return False

    def start_processing(self) -> bool:
        """Start processing next item in queue."""
        if self.current_work is None and len(self.queue) > 0:
            self.current_work = self.queue.pop(0)
            self.status = StationStatus.PROCESSING
            return True
        return False

    def process_step(self, random_state) -> None:
        """Process one time step."""
        if self.current_work is not None:
            self.current_work.time_remaining -= 1

            if self.current_work.time_remaining <= 0:
                # Processing complete
                self.output_buffer.append(self.current_work)
                self.current_work = None
                self.status = StationStatus.WAITING_PICKUP
                self.total_processed += 1

                # Update wear
                self.wear_level = min(1.0, self.wear_level + 0.001)

        # Try to start next item if idle
        if self.current_work is None and len(self.queue) > 0:
            self.start_processing()

        # Update status
        if self.current_work is None and len(self.output_buffer) > 0:
            self.status = StationStatus.WAITING_PICKUP
        elif self.current_work is None and len(self.queue) == 0:
            self.status = StationStatus.IDLE

    def pickup_output(self) -> WorkItem | None:
        """Pick up completed item from output buffer."""
        if len(self.output_buffer) > 0:
            item = self.output_buffer.pop(0)
            if len(self.output_buffer) == 0 and self.current_work is None:
                self.status = StationStatus.IDLE
            return item
        return None

    def get_state(self) -> dict:
        """Get current state of the station."""
        return {
            "name": self.name,
            "position": self.position,
            "status": self.status.value,
            "queue_size": len(self.queue),
            "output_size": len(self.output_buffer),
            "processing": self.current_work is not None,
            "wear_level": round(self.wear_level, 3),
            "total_processed": self.total_processed,
        }


class Storage(Station):
    """Storage station for raw materials and finished products."""

    def __init__(self, position: tuple[int, int], is_final: bool = False):
        super().__init__(
            name="FinalStorage" if is_final else "Storage",
            position=position,
            capacity=100,
        )
        self.is_final = is_final
        self.inventory = {}  # ingredient/product -> quantity

    def get_state(self) -> dict:
        state = super().get_state()
        state["is_final"] = self.is_final
        state["inventory_items"] = len(self.inventory)
        return state


class Washer(Station):
    """Washing station for vegetables and meat."""

    def __init__(self, position: tuple[int, int]):
        super().__init__(name="Washer", position=position, capacity=3)


class Cutter(Station):
    """Cutting/slicing station."""

    def __init__(self, position: tuple[int, int]):
        super().__init__(name="Cutter", position=position, capacity=2)
        self.blade_sharpness = 1.0  # 0.0 to 1.0

    def process_step(self, random_state) -> None:
        """Process with blade wear."""
        super().process_step(random_state)

        # Blade wears faster
        self.blade_sharpness = max(0.0, self.blade_sharpness - 0.002)
        self.failure_probability = 0.01 * (1.0 - self.blade_sharpness)

        # Check for failure
        if random_state.random() < self.failure_probability:
            self.status = StationStatus.ERROR

    def get_state(self) -> dict:
        state = super().get_state()
        state["blade_sharpness"] = round(self.blade_sharpness, 3)
        state["failure_probability"] = round(self.failure_probability, 4)
        return state


class Cooker(Station):
    """Cooking/mixing station."""

    def __init__(self, position: tuple[int, int]):
        super().__init__(name="Cooker", position=position, capacity=2)
        self.batch_size = 30  # Can cook 20-30 servings at once
        self.temperature = 0.0  # Current temperature (0.0 to 1.0 normalized)

    def get_state(self) -> dict:
        state = super().get_state()
        state["batch_size"] = self.batch_size
        state["temperature"] = round(self.temperature, 2)
        return state


class Plating(Station):
    """Plating/assembly station."""

    def __init__(self, position: tuple[int, int]):
        super().__init__(name="Plating", position=position, capacity=3)


class Sealing(Station):
    """Sealing/packaging station."""

    def __init__(self, position: tuple[int, int]):
        super().__init__(name="Sealing", position=position, capacity=2)
        self.pressure = 1.0  # Sealing pressure parameter

    def process_step(self, random_state) -> None:
        """Process with potential defect generation."""
        super().process_step(random_state)

        # Defect probability based on pressure and wear
        defect_prob = 0.01 * (1.0 - self.pressure) + 0.01 * self.wear_level

        if self.current_work and random_state.random() < defect_prob:
            # Mark as potentially defective (will be caught by QA)
            if not hasattr(self.current_work, 'defective'):
                self.current_work.defective = True  # type: ignore

    def get_state(self) -> dict:
        state = super().get_state()
        state["pressure"] = round(self.pressure, 2)
        return state


class VisionQA(Station):
    """Vision-based quality assurance station."""

    def __init__(self, position: tuple[int, int]):
        super().__init__(name="VisionQA", position=position, capacity=2)
        self.rejected_count = 0

    def process_step(self, random_state) -> None:
        """Process with quality inspection."""
        if self.current_work is not None:
            self.current_work.time_remaining -= 1

            if self.current_work.time_remaining <= 0:
                # Inspect for defects
                is_defective = getattr(self.current_work, 'defective', False)

                if is_defective:
                    # Reject defective item
                    self.rejected_count += 1
                    # Don't add to output buffer - item is discarded
                else:
                    # Accept good item
                    self.output_buffer.append(self.current_work)
                    self.status = StationStatus.WAITING_PICKUP

                self.current_work = None
                self.total_processed += 1

        # Try to start next item
        if self.current_work is None and len(self.queue) > 0:
            self.start_processing()

        # Update status
        if self.current_work is None and len(self.output_buffer) > 0:
            self.status = StationStatus.WAITING_PICKUP
        elif self.current_work is None and len(self.queue) == 0:
            self.status = StationStatus.IDLE

    def get_state(self) -> dict:
        state = super().get_state()
        state["rejected_count"] = self.rejected_count
        state["defect_rate"] = (
            round(self.rejected_count / self.total_processed, 3)
            if self.total_processed > 0
            else 0.0
        )
        return state
