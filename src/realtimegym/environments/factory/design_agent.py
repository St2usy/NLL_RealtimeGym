"""
Design Agent for Factory Environment.

This agent focuses on production system design, capacity planning,
and configuration optimization. It analyzes the production system
and recommends structural improvements.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CapacityAnalysis:
    """Analysis of station capacity and throughput."""

    station_id: int
    station_type: str
    line: int
    current_throughput: float
    max_capacity: float
    utilization_rate: float
    is_bottleneck: bool
    recommended_capacity: Optional[float] = None


@dataclass
class SystemConfiguration:
    """Recommended system configuration changes."""

    configuration_id: str
    description: str
    affected_components: list[str]
    expected_improvement: dict[str, float]
    implementation_priority: int  # 1-10
    feasibility: float  # 0-1


@dataclass
class DesignAgent:
    """
    Design Agent - Production system design and optimization.

    This agent:
    1. Analyzes production system configuration and capacity
    2. Identifies design-level inefficiencies and bottlenecks
    3. Recommends structural improvements (station placement, capacity, etc.)
    4. Evaluates alternative production line configurations
    5. Plans capacity adjustments and system reconfigurations
    6. Provides long-term optimization recommendations

    Input:
    - Factory layout and configuration
    - Station capacities and performance characteristics
    - Robot configuration and capabilities
    - Production requirements and constraints
    - Historical performance data
    - Current bottleneck analysis

    Output:
    - Capacity analysis for each station
    - System configuration recommendations
    - Production line optimization suggestions
    - Robot placement and allocation recommendations
    - Buffer size recommendations
    - Long-term improvement roadmap
    """

    agent_id: str = "design_agent"
    observations: dict[str, Any] = field(default_factory=dict)
    capacity_analyses: list[CapacityAnalysis] = field(default_factory=list)
    configuration_recommendations: list[SystemConfiguration] = field(default_factory=list)
    system_metrics: dict[str, float] = field(default_factory=dict)

    def observe(self, state: dict[str, Any]) -> None:
        """
        Receive state observations focusing on system design aspects.

        Args:
            state: Factory state including:
                - stations: Detailed station information
                - grid_size: Factory dimensions
                - robot counts and configurations
                - production metrics
                - bottleneck information
        """
        self.observations = {
            "stations": state.get("stations", []),
            "grid_size": state.get("grid_size", (20, 30)),
            "turn": state.get("turn", 0),
            "max_turns": state.get("max_turns", 1000),
            "completed_products": state.get("completed_products", 0),
            "target_products": state.get("target_products", 10),
            "defective_products": state.get("defective_products", 0),
            "robot_arms_idle": state.get("robot_arms_count", 0),
            "logistic_robots_idle": state.get("logistic_robots_count", 0),
            "collision_count": state.get("collision_count", 0),
        }

        # Perform capacity analysis
        self._analyze_capacity()

        # Calculate system-level metrics
        self._calculate_system_metrics()

    def _analyze_capacity(self) -> None:
        """Analyze capacity for each station."""
        self.capacity_analyses = []
        stations = self.observations["stations"]

        for station in stations:
            station_type = station.get("station_type", "Unknown")
            station_id = station.get("station_id", -1)
            line = station.get("line", 1)

            # Calculate throughput metrics
            input_buffer = station.get("input_buffer", [])
            output_buffer = station.get("output_buffer", [])
            input_buffer_size = station.get("input_buffer_size", 5)
            processing_time = station.get("processing_time", 10)

            # Current utilization
            input_occupancy = len(input_buffer) / max(1, input_buffer_size)
            output_occupancy = len(output_buffer) / max(1, input_buffer_size)
            status = station.get("status", "Idle")

            # Estimate throughput (items per 100 turns)
            if status == "Busy" or status == "Processing":
                current_throughput = 100.0 / max(1, processing_time)
            else:
                current_throughput = 0.0

            # Max theoretical capacity
            max_capacity = 100.0 / max(1, processing_time)

            # Utilization rate
            utilization = current_throughput / max(0.01, max_capacity)

            # Determine if bottleneck (high output occupancy or consistently busy)
            is_bottleneck = output_occupancy > 0.7 or (
                status in ["Busy", "Processing"] and input_occupancy > 0.8
            )

            # Recommend capacity increase for bottlenecks
            recommended_capacity = None
            if is_bottleneck:
                recommended_capacity = max_capacity * 1.5

            analysis = CapacityAnalysis(
                station_id=station_id,
                station_type=station_type,
                line=line,
                current_throughput=current_throughput,
                max_capacity=max_capacity,
                utilization_rate=utilization,
                is_bottleneck=is_bottleneck,
                recommended_capacity=recommended_capacity,
            )
            self.capacity_analyses.append(analysis)

    def _calculate_system_metrics(self) -> None:
        """Calculate system-level design metrics."""
        stations = self.observations["stations"]
        if not stations:
            self.system_metrics = {}
            return

        # Average utilization across all stations
        avg_utilization = sum(
            a.utilization_rate for a in self.capacity_analyses
        ) / max(1, len(self.capacity_analyses))

        # Bottleneck count
        bottleneck_count = sum(1 for a in self.capacity_analyses if a.is_bottleneck)

        # Line balance (variance in utilization between lines)
        line1_utilization = sum(
            a.utilization_rate for a in self.capacity_analyses if a.line == 1
        ) / max(1, sum(1 for a in self.capacity_analyses if a.line == 1))

        line2_utilization = sum(
            a.utilization_rate for a in self.capacity_analyses if a.line == 2
        ) / max(1, sum(1 for a in self.capacity_analyses if a.line == 2))

        line_balance = 1.0 - abs(line1_utilization - line2_utilization)

        # Capacity efficiency (how well capacity matches demand)
        total_capacity = sum(a.max_capacity for a in self.capacity_analyses)
        required_capacity = (
            self.observations["target_products"] * 100.0
            / max(1, self.observations["max_turns"])
        )
        capacity_efficiency = min(1.0, required_capacity / max(0.01, total_capacity))

        self.system_metrics = {
            "average_utilization": avg_utilization,
            "bottleneck_count": bottleneck_count,
            "line_balance": line_balance,
            "capacity_efficiency": capacity_efficiency,
            "line1_utilization": line1_utilization,
            "line2_utilization": line2_utilization,
        }

    def decide(self) -> dict[str, Any]:
        """
        Make design-level decisions and recommendations.

        Returns:
            Dictionary with design decisions:
            - capacity_analysis: List of capacity analyses per station
            - system_metrics: System-level performance metrics
            - configuration_recommendations: List of configuration changes
            - buffer_recommendations: Buffer size adjustments
            - robot_allocation_design: Robot placement recommendations
            - optimization_priorities: Prioritized list of improvements
        """
        # Generate configuration recommendations
        self._generate_configuration_recommendations()

        # Generate buffer recommendations
        buffer_recommendations = self._generate_buffer_recommendations()

        # Generate robot allocation design
        robot_allocation = self._design_robot_allocation()

        # Prioritize optimizations
        optimization_priorities = self._prioritize_optimizations()

        return {
            "capacity_analysis": [
                {
                    "station_id": a.station_id,
                    "station_type": a.station_type,
                    "line": a.line,
                    "current_throughput": a.current_throughput,
                    "max_capacity": a.max_capacity,
                    "utilization_rate": a.utilization_rate,
                    "is_bottleneck": a.is_bottleneck,
                    "recommended_capacity": a.recommended_capacity,
                }
                for a in self.capacity_analyses
            ],
            "system_metrics": self.system_metrics,
            "configuration_recommendations": [
                {
                    "id": c.configuration_id,
                    "description": c.description,
                    "affected_components": c.affected_components,
                    "expected_improvement": c.expected_improvement,
                    "priority": c.implementation_priority,
                    "feasibility": c.feasibility,
                }
                for c in self.configuration_recommendations
            ],
            "buffer_recommendations": buffer_recommendations,
            "robot_allocation_design": robot_allocation,
            "optimization_priorities": optimization_priorities,
        }

    def _generate_configuration_recommendations(self) -> None:
        """Generate system configuration recommendations."""
        self.configuration_recommendations = []

        # Recommendation 1: Add parallel stations at bottlenecks
        bottlenecks = [a for a in self.capacity_analyses if a.is_bottleneck]
        if bottlenecks:
            for bottleneck in bottlenecks[:3]:  # Top 3 bottlenecks
                config = SystemConfiguration(
                    configuration_id=f"add_parallel_station_{bottleneck.station_id}",
                    description=f"Add parallel {bottleneck.station_type} station at line {bottleneck.line}",
                    affected_components=[f"station_{bottleneck.station_id}"],
                    expected_improvement={
                        "throughput_increase": 0.4,
                        "utilization_reduction": 0.3,
                    },
                    implementation_priority=8,
                    feasibility=0.7,
                )
                self.configuration_recommendations.append(config)

        # Recommendation 2: Balance production lines
        line_balance = self.system_metrics.get("line_balance", 1.0)
        if line_balance < 0.8:
            config = SystemConfiguration(
                configuration_id="balance_production_lines",
                description="Rebalance workload between production lines",
                affected_components=["line1", "line2"],
                expected_improvement={
                    "line_balance": 0.2,
                    "overall_throughput": 0.15,
                },
                implementation_priority=7,
                feasibility=0.9,
            )
            self.configuration_recommendations.append(config)

        # Recommendation 3: Optimize robot count
        robot_idle_rate = (
            self.observations["logistic_robots_idle"]
            + self.observations["robot_arms_idle"]
        ) / max(1, 44)  # 20 arms + 24 logistic robots
        if robot_idle_rate > 0.3:
            config = SystemConfiguration(
                configuration_id="reduce_robot_count",
                description="Reduce number of robots to improve coordination",
                affected_components=["logistic_robots"],
                expected_improvement={
                    "collision_reduction": 0.25,
                    "coordination_efficiency": 0.2,
                },
                implementation_priority=5,
                feasibility=0.95,
            )
            self.configuration_recommendations.append(config)

        # Recommendation 4: Increase buffer sizes at critical points
        high_utilization_stations = [
            a for a in self.capacity_analyses if a.utilization_rate > 0.85
        ]
        if high_utilization_stations:
            config = SystemConfiguration(
                configuration_id="increase_critical_buffers",
                description="Increase buffer sizes at high-utilization stations",
                affected_components=[
                    f"station_{s.station_id}" for s in high_utilization_stations
                ],
                expected_improvement={
                    "buffer_utilization": 0.2,
                    "throughput_stability": 0.15,
                },
                implementation_priority=6,
                feasibility=1.0,
            )
            self.configuration_recommendations.append(config)

    def _generate_buffer_recommendations(self) -> dict[str, Any]:
        """Generate buffer size recommendations."""
        recommendations = {}

        for analysis in self.capacity_analyses:
            if analysis.is_bottleneck:
                # Increase buffer size before bottleneck stations
                recommendations[f"station_{analysis.station_id}_input"] = {
                    "current_size": 5,  # Default size
                    "recommended_size": 10,
                    "reason": "bottleneck_upstream_buffering",
                }

            if analysis.utilization_rate > 0.9:
                # Increase buffer size for highly utilized stations
                recommendations[f"station_{analysis.station_id}_output"] = {
                    "current_size": 5,
                    "recommended_size": 8,
                    "reason": "high_utilization_smoothing",
                }

        return recommendations

    def _design_robot_allocation(self) -> dict[str, Any]:
        """Design optimal robot allocation."""
        bottleneck_stations = [
            a.station_id for a in self.capacity_analyses if a.is_bottleneck
        ]

        # Analyze collision hotspots (simplified)
        collision_rate = self.observations["collision_count"] / max(
            1, self.observations["turn"]
        )

        return {
            "logistic_robot_allocation": {
                "line1": 12,
                "line2": 12,
                "reserve": 4 if len(bottleneck_stations) > 2 else 2,
            },
            "robot_arm_allocation": {
                "standard_stations": 1,
                "bottleneck_stations": 2,  # Consider adding arms at bottlenecks
            },
            "path_planning_strategy": (
                "conflict_avoidance" if collision_rate > 0.05 else "shortest_path"
            ),
            "priority_stations": bottleneck_stations,
        }

    def _prioritize_optimizations(self) -> list[dict[str, Any]]:
        """Prioritize optimization recommendations."""
        priorities = []

        # Priority 1: Critical bottlenecks
        critical_bottlenecks = [
            a for a in self.capacity_analyses
            if a.is_bottleneck and a.utilization_rate > 0.9
        ]
        if critical_bottlenecks:
            priorities.append({
                "priority": 1,
                "optimization": "resolve_critical_bottlenecks",
                "description": f"Resolve {len(critical_bottlenecks)} critical bottlenecks",
                "expected_impact": "high",
                "stations": [b.station_id for b in critical_bottlenecks],
            })

        # Priority 2: Line balancing
        if self.system_metrics.get("line_balance", 1.0) < 0.8:
            priorities.append({
                "priority": 2,
                "optimization": "balance_production_lines",
                "description": "Improve balance between production lines",
                "expected_impact": "medium",
            })

        # Priority 3: Buffer optimization
        priorities.append({
            "priority": 3,
            "optimization": "optimize_buffers",
            "description": "Adjust buffer sizes for better flow",
            "expected_impact": "medium",
        })

        # Priority 4: Robot coordination
        if self.observations["collision_count"] > 5:
            priorities.append({
                "priority": 4,
                "optimization": "improve_robot_coordination",
                "description": "Optimize robot paths and allocation",
                "expected_impact": "low-medium",
            })

        # Priority 5: Capacity planning
        if self.system_metrics.get("capacity_efficiency", 1.0) < 0.7:
            priorities.append({
                "priority": 5,
                "optimization": "increase_capacity",
                "description": "Add capacity to meet production targets",
                "expected_impact": "high",
            })

        return sorted(priorities, key=lambda x: x["priority"])
