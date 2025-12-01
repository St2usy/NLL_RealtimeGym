"""Station classes for Factory environment."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np

from .items import Item, ItemType


class StationType(Enum):
    """Types of stations."""

    STORAGE = "Storage"
    WASHER = "Washer"
    CUTTER = "Cutter"
    COOKER = "Cooker"
    PLATING = "Plating"
    SEALING = "Sealing"
    VISION_QA = "VisionQA"


class StationStatus(Enum):
    """Station operational status."""

    IDLE = "Idle"
    BUSY = "Busy"
    WAITING = "Waiting"  # Waiting for material
    ERROR = "Error"
    DOWN = "Down"  # Maintenance required


@dataclass
class Station:
    """Base class for all stations."""

    station_id: int
    station_type: StationType
    position: tuple[int, int]  # (row, col)
    status: StationStatus = StationStatus.IDLE
    input_buffer: list[Item] = field(default_factory=list)
    output_buffer: list[Item] = field(default_factory=list)
    buffer_capacity: int = 10
    processing_time: int = 0  # Time per batch in steps
    current_progress: int = 0  # Current processing progress
    malfunction_probability: float = 0.0  # Chance of malfunction
    wear_level: float = 0.0  # 0.0 ~ 1.0, affects quality
    random: Optional[np.random.RandomState] = None

    def can_accept_input(self) -> bool:
        """Check if station can accept more input."""
        return len(self.input_buffer) < self.buffer_capacity

    def can_provide_output(self) -> bool:
        """Check if station has output available."""
        return len(self.output_buffer) > 0

    def add_input(self, item: Item) -> bool:
        """Add item to input buffer."""
        if not self.can_accept_input():
            return False
        self.input_buffer.append(item)
        return True

    def take_output(self) -> Optional[Item]:
        """Take item from output buffer."""
        if not self.can_provide_output():
            return None
        return self.output_buffer.pop(0)

    def process(self) -> None:
        """Process items (override in subclasses)."""
        if self.status == StationStatus.ERROR or self.status == StationStatus.DOWN:
            return

        if len(self.input_buffer) > 0 and self.status == StationStatus.IDLE:
            self.status = StationStatus.BUSY
            self.current_progress = 0

        if self.status == StationStatus.BUSY:
            self.current_progress += 1
            if self.current_progress >= self.processing_time:
                self._complete_processing()

    def _complete_processing(self) -> None:
        """Complete the processing (override in subclasses)."""
        if len(self.input_buffer) > 0:
            item = self.input_buffer.pop(0)
            # Quality degradation based on wear
            item.quality *= (1.0 - self.wear_level * 0.1)
            self.output_buffer.append(item)
        self.status = StationStatus.IDLE
        self.current_progress = 0

    def check_malfunction(self) -> bool:
        """Check if station malfunctions."""
        if self.random is not None and self.random.random() < self.malfunction_probability:
            self.status = StationStatus.ERROR
            return True
        return False

    def repair(self) -> None:
        """Repair the station."""
        self.status = StationStatus.IDLE
        self.wear_level = max(0.0, self.wear_level - 0.2)

    def get_state_dict(self) -> dict:
        """Get station state as dictionary."""
        return {
            "id": self.station_id,
            "type": self.station_type.value,
            "position": self.position,
            "status": self.status.value,
            "input_count": len(self.input_buffer),
            "output_count": len(self.output_buffer),
            "progress": self.current_progress,
            "max_progress": self.processing_time,
            "wear_level": self.wear_level,
        }


@dataclass
class Storage(Station):
    """Storage station for raw materials and finished products."""

    inventory: dict[ItemType, int] = field(default_factory=dict)
    capacity: int = 1000

    def __post_init__(self) -> None:
        self.station_type = StationType.STORAGE
        self.processing_time = 1  # Instant

    def add_to_inventory(self, item_type: ItemType, quantity: int) -> None:
        """Add items to inventory."""
        if item_type not in self.inventory:
            self.inventory[item_type] = 0
        self.inventory[item_type] += quantity

    def get_from_inventory(self, item_type: ItemType, quantity: int = 1) -> Optional[Item]:
        """Get item from inventory."""
        if item_type in self.inventory and self.inventory[item_type] >= quantity:
            self.inventory[item_type] -= quantity
            return Item(item_type=item_type, quantity=quantity)
        return None

    def process(self) -> None:
        """Storage doesn't process, just stores."""
        pass


@dataclass
class Washer(Station):
    """Washing station for vegetables and meats."""

    def __post_init__(self) -> None:
        self.station_type = StationType.WASHER
        self.processing_time = 10  # 1 minute
        self.malfunction_probability = 0.001


@dataclass
class Cutter(Station):
    """Cutting station for slicing vegetables and meats."""

    blade_wear: float = 0.0  # 0.0 ~ 1.0

    def __post_init__(self) -> None:
        self.station_type = StationType.CUTTER
        self.processing_time = 12  # 2 minutes
        self.malfunction_probability = 0.005

    def _complete_processing(self) -> None:
        """Complete processing with blade wear consideration."""
        if len(self.input_buffer) > 0:
            item = self.input_buffer.pop(0)
            # Quality affected by blade wear
            item.quality *= (1.0 - self.blade_wear * 0.2)
            item.processed = True
            self.output_buffer.append(item)
            # Increase blade wear
            self.blade_wear = min(1.0, self.blade_wear + 0.001)
        self.status = StationStatus.IDLE
        self.current_progress = 0

    def replace_blade(self) -> None:
        """Replace the blade."""
        self.blade_wear = 0.0
        self.wear_level = 0.0


@dataclass
class Cooker(Station):
    """Cooking station for mixing and cooking."""

    batch_size: int = 20
    temperature: float = 180.0  # Celsius
    optimal_temp: float = 180.0

    def __post_init__(self) -> None:
        self.station_type = StationType.COOKER
        self.processing_time = 24  # 4 minutes
        self.malfunction_probability = 0.003

    def _complete_processing(self) -> None:
        """Complete cooking with temperature consideration."""
        batch = []
        while len(self.input_buffer) > 0 and len(batch) < self.batch_size:
            batch.append(self.input_buffer.pop(0))

        if len(batch) > 0:
            # Temperature affects quality
            temp_factor = 1.0 - abs(self.temperature - self.optimal_temp) / 100.0
            temp_factor = max(0.5, min(1.0, temp_factor))

            # Create cooked item
            cooked_item = Item(
                item_type=ItemType.COOKED_PASTA,  # Generic for now
                quantity=len(batch),
                processed=True,
                quality=sum(item.quality for item in batch) / len(batch) * temp_factor,
            )
            self.output_buffer.append(cooked_item)

        self.status = StationStatus.IDLE
        self.current_progress = 0


@dataclass
class Plating(Station):
    """Plating station for assembling dishes."""

    vibration_level: float = 0.0  # 0.0 ~ 1.0

    def __post_init__(self) -> None:
        self.station_type = StationType.PLATING
        self.processing_time = 6  # 1 minute
        self.malfunction_probability = 0.002

    def _complete_processing(self) -> None:
        """Complete plating with vibration consideration."""
        if len(self.input_buffer) > 0:
            item = self.input_buffer.pop(0)
            # Vibration affects quality
            item.quality *= (1.0 - self.vibration_level * 0.15)
            item.processed = True
            self.output_buffer.append(item)
        self.status = StationStatus.IDLE
        self.current_progress = 0


@dataclass
class Sealing(Station):
    """Sealing station for packaging."""

    pressure: float = 100.0  # kPa
    optimal_pressure: float = 100.0

    def __post_init__(self) -> None:
        self.station_type = StationType.SEALING
        self.processing_time = 6  # 1 minute
        self.malfunction_probability = 0.002

    def _complete_processing(self) -> None:
        """Complete sealing with pressure consideration."""
        if len(self.input_buffer) > 0:
            item = self.input_buffer.pop(0)
            # Pressure affects seal quality
            pressure_factor = 1.0 - abs(self.pressure - self.optimal_pressure) / 50.0
            pressure_factor = max(0.7, min(1.0, pressure_factor))
            item.quality *= pressure_factor
            item.metadata["sealed"] = True
            self.output_buffer.append(item)
        self.status = StationStatus.IDLE
        self.current_progress = 0


@dataclass
class VisionQA(Station):
    """Vision QA station for quality inspection."""

    defect_threshold: float = 0.7  # Items below this are defective

    def __post_init__(self) -> None:
        self.station_type = StationType.VISION_QA
        self.processing_time = 3  # 30 seconds
        self.malfunction_probability = 0.001

    def _complete_processing(self) -> None:
        """Complete QA inspection."""
        if len(self.input_buffer) > 0:
            item = self.input_buffer.pop(0)
            # Check quality
            if item.quality < self.defect_threshold:
                item.item_type = ItemType.DEFECTIVE
                item.metadata["defective"] = True
            self.output_buffer.append(item)
        self.status = StationStatus.IDLE
        self.current_progress = 0
