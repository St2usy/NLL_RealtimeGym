"""
Meta Planner Agent for Factory Environment.

This agent performs high-level strategic planning and coordination across all other agents.
It analyzes global factory state, sets objectives, and orchestrates other specialized agents.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class StrategicObjective:
    """Represents a strategic objective for the factory."""

    objective_id: str
    description: str
    priority: int  # 1-10, higher is more important
    target_metrics: dict[str, float]
    deadline_turn: Optional[int] = None
    status: str = "active"  # active, completed, failed


@dataclass
class AgentCoordinationPlan:
    """Coordination plan for all upper-level agents."""

    product_design_priorities: list[str] = field(default_factory=list)
    facility_management_priorities: list[str] = field(default_factory=list)
    robot_coordination_priorities: list[str] = field(default_factory=list)
    quality_inspection_priorities: list[str] = field(default_factory=list)
    design_agent_priorities: list[str] = field(default_factory=list)


@dataclass
class MetaPlannerAgent:
    """
    Meta Planner Agent - Highest level strategic planning and coordination.

    This agent:
    1. Analyzes global factory state and performance metrics
    2. Sets strategic objectives and priorities
    3. Coordinates all other upper-level agents (ProductDesign, FacilityManagement,
       RobotCoordination, QualityInspection, DesignAgent)
    4. Monitors progress toward objectives
    5. Adapts strategy based on changing conditions

    Input:
    - Complete factory state (all stations, robots, products)
    - Historical performance data
    - Current objectives and their progress
    - Reports from all other upper agents

    Output:
    - Strategic objectives for current planning horizon
    - Priority assignments for each agent
    - Resource allocation recommendations
    - Coordination directives for inter-agent collaboration
    """

    agent_id: str = "meta_planner"
    observations: dict[str, Any] = field(default_factory=dict)
    objectives: list[StrategicObjective] = field(default_factory=list)
    coordination_plan: AgentCoordinationPlan = field(default_factory=AgentCoordinationPlan)
    planning_horizon: int = 100  # Number of turns to plan ahead
    current_turn: int = 0

    def observe(self, state: dict[str, Any]) -> None:
        """
        Receive comprehensive state observations from the entire factory.

        Args:
            state: Complete factory state including:
                - stations: List of all station states
                - robots: Robot arm and logistic robot states
                - production_metrics: Completed/defective products, throughput
                - resource_utilization: Station utilization rates
                - quality_metrics: Defect rates, inspection results
                - coordination_metrics: Collision counts, idle times
        """
        self.current_turn = state.get("turn", 0)
        self.observations = {
            "turn": state.get("turn", 0),
            "max_turns": state.get("max_turns", 1000),
            "completed_products": state.get("completed_products", 0),
            "target_products": state.get("target_products", 10),
            "defective_products": state.get("defective_products", 0),
            "stations": state.get("stations", []),
            "robot_arms_idle": state.get("robot_arms_count", 0),
            "logistic_robots_idle": state.get("logistic_robots_count", 0),
            "collision_count": state.get("collision_count", 0),
            # Calculate derived metrics
            "production_rate": self._calculate_production_rate(state),
            "quality_rate": self._calculate_quality_rate(state),
            "resource_utilization": self._calculate_resource_utilization(state),
            "bottleneck_stations": self._identify_bottlenecks(state),
        }

    def _calculate_production_rate(self, state: dict[str, Any]) -> float:
        """Calculate current production rate (products per turn)."""
        turn = state.get("turn", 1)
        completed = state.get("completed_products", 0)
        return completed / max(1, turn)

    def _calculate_quality_rate(self, state: dict[str, Any]) -> float:
        """Calculate quality rate (non-defective ratio)."""
        completed = state.get("completed_products", 0)
        defective = state.get("defective_products", 0)
        total = completed + defective
        return completed / max(1, total)

    def _calculate_resource_utilization(self, state: dict[str, Any]) -> float:
        """Calculate overall resource utilization rate."""
        stations = state.get("stations", [])
        if not stations:
            return 0.0

        busy_count = sum(
            1 for s in stations if s.get("status") in ["Busy", "Processing"]
        )
        return busy_count / len(stations)

    def _identify_bottlenecks(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        """Identify bottleneck stations based on buffer occupancy and status."""
        stations = state.get("stations", [])
        bottlenecks = []

        for station in stations:
            input_buffer_size = station.get("input_buffer_size", 5)
            input_buffer_occupancy = len(station.get("input_buffer", []))
            output_buffer_occupancy = len(station.get("output_buffer", []))

            # Station is a bottleneck if output buffer is consistently full
            if output_buffer_occupancy >= input_buffer_size * 0.8:
                bottlenecks.append({
                    "station_id": station.get("station_id"),
                    "station_type": station.get("station_type"),
                    "line": station.get("line"),
                    "output_occupancy": output_buffer_occupancy,
                    "severity": output_buffer_occupancy / input_buffer_size,
                })

        return sorted(bottlenecks, key=lambda x: x["severity"], reverse=True)

    def decide(self) -> dict[str, Any]:
        """
        Make high-level strategic decisions and coordinate all agents.

        Returns:
            Dictionary with strategic decisions:
            - objectives: List of StrategicObjective instances
            - coordination_plan: AgentCoordinationPlan instance
            - critical_actions: Immediate actions needed
            - resource_allocation: Resource distribution recommendations
            - performance_assessment: Current performance vs. targets
        """
        # Update objectives based on current state
        self._update_objectives()

        # Create coordination plan for all agents
        self._create_coordination_plan()

        # Assess current performance
        performance = self._assess_performance()

        # Identify critical actions needed immediately
        critical_actions = self._identify_critical_actions()

        # Generate resource allocation recommendations
        resource_allocation = self._plan_resource_allocation()

        return {
            "objectives": [
                {
                    "id": obj.objective_id,
                    "description": obj.description,
                    "priority": obj.priority,
                    "target_metrics": obj.target_metrics,
                    "status": obj.status,
                }
                for obj in self.objectives
            ],
            "coordination_plan": {
                "product_design": self.coordination_plan.product_design_priorities,
                "facility_management": self.coordination_plan.facility_management_priorities,
                "robot_coordination": self.coordination_plan.robot_coordination_priorities,
                "quality_inspection": self.coordination_plan.quality_inspection_priorities,
                "design_agent": self.coordination_plan.design_agent_priorities,
            },
            "critical_actions": critical_actions,
            "resource_allocation": resource_allocation,
            "performance_assessment": performance,
        }

    def _update_objectives(self) -> None:
        """Update strategic objectives based on current state."""
        # Clear completed objectives
        self.objectives = [
            obj for obj in self.objectives
            if obj.status == "active" and (
                obj.deadline_turn is None or obj.deadline_turn > self.current_turn
            )
        ]

        # Add new objectives based on current state
        progress_rate = self.observations["completed_products"] / max(
            1, self.observations["target_products"]
        )

        # Objective 1: Meet production target
        if not any(obj.objective_id == "production_target" for obj in self.objectives):
            self.objectives.append(
                StrategicObjective(
                    objective_id="production_target",
                    description="Meet production target within deadline",
                    priority=10,
                    target_metrics={
                        "completed_products": self.observations["target_products"],
                        "min_quality_rate": 0.9,
                    },
                    deadline_turn=self.observations["max_turns"],
                )
            )

        # Objective 2: Maintain quality if defect rate is high
        quality_rate = self.observations["quality_rate"]
        if quality_rate < 0.85 and not any(
            obj.objective_id == "improve_quality" for obj in self.objectives
        ):
            self.objectives.append(
                StrategicObjective(
                    objective_id="improve_quality",
                    description="Improve product quality rate",
                    priority=8,
                    target_metrics={"quality_rate": 0.9},
                )
            )

        # Objective 3: Resolve bottlenecks if identified
        if self.observations["bottleneck_stations"] and not any(
            obj.objective_id == "resolve_bottlenecks" for obj in self.objectives
        ):
            self.objectives.append(
                StrategicObjective(
                    objective_id="resolve_bottlenecks",
                    description="Resolve production bottlenecks",
                    priority=7,
                    target_metrics={"max_buffer_occupancy": 0.6},
                )
            )

        # Objective 4: Reduce collisions if high
        if self.observations["collision_count"] > 5 and not any(
            obj.objective_id == "reduce_collisions" for obj in self.objectives
        ):
            self.objectives.append(
                StrategicObjective(
                    objective_id="reduce_collisions",
                    description="Reduce robot collision count",
                    priority=6,
                    target_metrics={"collision_count": 2},
                )
            )

    def _create_coordination_plan(self) -> None:
        """Create coordination plan for all agents based on objectives."""
        self.coordination_plan = AgentCoordinationPlan()

        for obj in sorted(self.objectives, key=lambda x: x.priority, reverse=True):
            if obj.objective_id == "production_target":
                self.coordination_plan.product_design_priorities.append(
                    "optimize_routing_for_throughput"
                )
                self.coordination_plan.robot_coordination_priorities.append(
                    "maximize_robot_utilization"
                )
                self.coordination_plan.design_agent_priorities.append(
                    "optimize_line_configuration"
                )

            elif obj.objective_id == "improve_quality":
                self.coordination_plan.quality_inspection_priorities.append(
                    "increase_inspection_rigor"
                )
                self.coordination_plan.facility_management_priorities.append(
                    "monitor_equipment_performance"
                )
                self.coordination_plan.design_agent_priorities.append(
                    "analyze_quality_failure_modes"
                )

            elif obj.objective_id == "resolve_bottlenecks":
                self.coordination_plan.product_design_priorities.append(
                    "balance_workload_distribution"
                )
                self.coordination_plan.robot_coordination_priorities.append(
                    "prioritize_bottleneck_stations"
                )
                self.coordination_plan.design_agent_priorities.append(
                    "recommend_capacity_adjustments"
                )

            elif obj.objective_id == "reduce_collisions":
                self.coordination_plan.robot_coordination_priorities.append(
                    "improve_path_planning"
                )
                self.coordination_plan.design_agent_priorities.append(
                    "optimize_robot_placement"
                )

    def _identify_critical_actions(self) -> list[dict[str, Any]]:
        """Identify critical actions needed immediately."""
        critical_actions = []

        # Critical: Production far behind schedule
        turns_remaining = self.observations["max_turns"] - self.observations["turn"]
        products_remaining = (
            self.observations["target_products"] - self.observations["completed_products"]
        )
        required_rate = products_remaining / max(1, turns_remaining)
        current_rate = self.observations["production_rate"]

        if current_rate < required_rate * 0.8:
            critical_actions.append({
                "action": "accelerate_production",
                "urgency": "high",
                "reason": f"Current rate {current_rate:.3f} below required {required_rate:.3f}",
                "target_agents": ["product_design", "robot_coordination"],
            })

        # Critical: Quality rate very low
        if self.observations["quality_rate"] < 0.7:
            critical_actions.append({
                "action": "emergency_quality_control",
                "urgency": "critical",
                "reason": f"Quality rate {self.observations['quality_rate']:.2f} critically low",
                "target_agents": ["quality_inspection", "facility_management"],
            })

        # Critical: Severe bottlenecks
        if self.observations["bottleneck_stations"]:
            for bottleneck in self.observations["bottleneck_stations"][:2]:
                if bottleneck["severity"] > 0.9:
                    critical_actions.append({
                        "action": "resolve_bottleneck",
                        "urgency": "high",
                        "reason": f"Station {bottleneck['station_type']} severely blocked",
                        "target_agents": ["robot_coordination", "design_agent"],
                        "target_station": bottleneck["station_id"],
                    })

        return critical_actions

    def _plan_resource_allocation(self) -> dict[str, Any]:
        """Plan resource allocation across the factory."""
        return {
            "robot_allocation": self._allocate_robots(),
            "station_priorities": self._prioritize_stations(),
            "buffer_management": self._plan_buffer_management(),
        }

    def _allocate_robots(self) -> dict[str, Any]:
        """Allocate robot resources based on priorities."""
        bottleneck_lines = set()
        for bottleneck in self.observations["bottleneck_stations"]:
            bottleneck_lines.add(bottleneck["line"])

        return {
            "prioritize_lines": list(bottleneck_lines),
            "activate_reserve_robots": len(self.observations["bottleneck_stations"]) > 3,
            "idle_robot_threshold": 0.2,  # Alert if >20% robots idle
        }

    def _prioritize_stations(self) -> list[dict[str, Any]]:
        """Prioritize stations for resource allocation."""
        priorities = []

        # Prioritize bottleneck stations
        for bottleneck in self.observations["bottleneck_stations"]:
            priorities.append({
                "station_id": bottleneck["station_id"],
                "priority": "high",
                "reason": "bottleneck",
            })

        return priorities

    def _plan_buffer_management(self) -> dict[str, Any]:
        """Plan buffer management strategies."""
        return {
            "increase_buffers": [
                b["station_id"] for b in self.observations["bottleneck_stations"]
                if b["severity"] > 0.8
            ],
            "target_occupancy": 0.7,  # Target 70% buffer occupancy
        }

    def _assess_performance(self) -> dict[str, Any]:
        """Assess current performance against targets."""
        return {
            "production_progress": (
                self.observations["completed_products"]
                / max(1, self.observations["target_products"])
            ),
            "quality_performance": self.observations["quality_rate"],
            "efficiency": self.observations["resource_utilization"],
            "bottleneck_count": len(self.observations["bottleneck_stations"]),
            "collision_rate": (
                self.observations["collision_count"]
                / max(1, self.observations["turn"])
            ),
            "overall_status": self._calculate_overall_status(),
        }

    def _calculate_overall_status(self) -> str:
        """Calculate overall factory status."""
        production_ok = (
            self.observations["completed_products"]
            / max(1, self.observations["target_products"])
        ) > 0.5
        quality_ok = self.observations["quality_rate"] > 0.8

        if production_ok and quality_ok:
            return "excellent"
        elif production_ok or quality_ok:
            return "acceptable"
        else:
            return "critical"
