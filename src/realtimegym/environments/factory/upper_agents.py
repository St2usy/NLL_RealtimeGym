"""
Upper-level agent interfaces for Factory environment.

These are interfaces for LLM-based agents to interact with the environment.
The actual implementation will be done separately using LLM agents.

Six types of upper agents:
1. ProductDesignAgent: Route planning and batch size decisions
2. FacilityManagementAgent: Predictive maintenance and risk management
3. RobotCoordinationAgent: Robot scheduling and path planning
4. QualityInspectionAgent: Quality control and defect management
5. MetaPlannerAgent: High-level strategic planning and coordination
6. DesignAgent: Production system design and capacity optimization
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from .design_agent import DesignAgent
from .items import RecipeType
from .meta_planner import MetaPlannerAgent
from .stations import Station


@dataclass
class ProductDesignAgent:
    """
    Product Design Agent - Plans production routes and batch sizes.

    Input:
    - Product recipe (BOM + process steps)
    - Available equipment list
    - Equipment performance (capacity/processing speed)
    - Equipment availability status

    Output:
    - Process routing (Route Graph)
    - Batch size decisions
    - Required lower agent counts per station
    """

    agent_id: str = "product_design"
    observations: dict[str, Any] = field(default_factory=dict)

    def observe(self, state: dict[str, Any]) -> None:
        """Receive state observations."""
        self.observations = {
            "stations": state.get("stations", []),
            "recipe": state.get("current_recipe", None),
            "robot_availability": state.get("robot_arms_count", 0),
            "quality_metrics": state.get("defective_products", 0),
        }

    def decide(self) -> dict[str, Any]:
        """
        Make decisions about production routing.

        Returns:
            Dictionary with decisions:
            - route: List of station types to visit
            - batch_size: Items to process per batch
            - priority_stations: Stations needing more robots
        """
        # This will be implemented by LLM agent
        # For now, return a placeholder
        return {
            "route": ["Storage", "Washer", "Cutter", "Cooker", "Plating", "Sealing", "VisionQA", "Storage"],
            "batch_size": 20,
            "priority_stations": [],
        }


@dataclass
class FacilityManagementAgent:
    """
    Facility Management Agent - Handles predictive maintenance and risk.

    Input:
    - Sensor data from each equipment
    - Equipment wear level
    - Maintenance history
    - Current workload

    Output:
    - Maintenance schedule
    - Risk scores
    - Equipment replacement recommendations
    """

    agent_id: str = "facility_management"
    observations: dict[str, Any] = field(default_factory=dict)
    maintenance_schedule: dict[int, str] = field(default_factory=dict)  # station_id -> action

    def observe(self, state: dict[str, Any]) -> None:
        """Receive state observations."""
        self.observations = {
            "stations": state.get("stations", []),
            "malfunction_count": sum(
                1 for s in state.get("stations", []) if s.get("status") in ["Error", "Down"]
            ),
        }

    def decide(self) -> dict[str, Any]:
        """
        Make maintenance decisions.

        Returns:
            Dictionary with decisions:
            - schedule_maintenance: List of station IDs needing maintenance
            - risk_scores: Dict of station_id -> risk score (0-1)
            - urgent_repairs: List of critical station IDs
        """
        # This will be implemented by LLM agent
        return {
            "schedule_maintenance": [],
            "risk_scores": {},
            "urgent_repairs": [],
        }


@dataclass
class RobotCoordinationAgent:
    """
    Robot Coordination Agent - Schedules and coordinates all robots.

    Input:
    - States of all robot arms and logistic robots
    - Process routing (from ProductDesignAgent)
    - Station states
    - Map information

    Output:
    - Task assignments for each robot
    - Path planning for logistic robots
    - Conflict resolution
    """

    agent_id: str = "robot_coordination"
    observations: dict[str, Any] = field(default_factory=dict)

    def observe(self, state: dict[str, Any]) -> None:
        """Receive state observations."""
        self.observations = {
            "robot_arms_idle": state.get("robot_arms_count", 0),
            "logistic_robots_idle": state.get("logistic_robots_count", 0),
            "stations": state.get("stations", []),
            "collision_count": state.get("collision_count", 0),
        }

    def decide(self) -> dict[str, Any]:
        """
        Make robot coordination decisions.

        Returns:
            Dictionary with decisions:
            - robot_arm_tasks: List of (robot_id, task) tuples
            - logistic_tasks: List of (robot_id, source, destination) tuples
            - priority_adjustments: Dict of robot_id -> new priority
        """
        # This will be implemented by LLM agent
        return {
            "robot_arm_tasks": [],
            "logistic_tasks": [],
            "priority_adjustments": {},
        }


@dataclass
class QualityInspectionAgent:
    """
    Quality Inspection Agent - Manages quality control and defect handling.

    Input:
    - Vision inspection results
    - Product weight/appearance
    - Process conditions (temperature, time)
    - Recent defect rate

    Output:
    - Accept/reject decisions
    - Process parameter adjustments
    - Root cause analysis flags
    """

    agent_id: str = "quality_inspection"
    observations: dict[str, Any] = field(default_factory=dict)

    def observe(self, state: dict[str, Any]) -> None:
        """Receive state observations."""
        self.observations = {
            "completed_products": state.get("completed_products", 0),
            "defective_products": state.get("defective_products", 0),
            "stations": state.get("stations", []),
        }

    def decide(self) -> dict[str, Any]:
        """
        Make quality control decisions.

        Returns:
            Dictionary with decisions:
            - quality_threshold: New threshold for pass/fail (0-1)
            - parameter_adjustments: Dict of station_id -> parameter changes
            - defect_alerts: List of station IDs with quality issues
        """
        # This will be implemented by LLM agent
        # Calculate defect rate
        total = self.observations["completed_products"] + self.observations["defective_products"]
        defect_rate = self.observations["defective_products"] / max(1, total)

        return {
            "quality_threshold": 0.75 if defect_rate > 0.1 else 0.7,
            "parameter_adjustments": {},
            "defect_alerts": [],
        }


# Helper function to create all upper agents
def create_upper_agents() -> dict[str, Any]:
    """Create all upper-level agents."""
    return {
        "meta_planner": MetaPlannerAgent(),
        "design_agent": DesignAgent(),
        "product_design": ProductDesignAgent(),
        "facility_management": FacilityManagementAgent(),
        "robot_coordination": RobotCoordinationAgent(),
        "quality_inspection": QualityInspectionAgent(),
    }
