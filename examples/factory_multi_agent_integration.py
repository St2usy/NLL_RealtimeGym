"""
Factory Environment with Multi-Agent Integration
=================================================

This example demonstrates the complete hierarchical multi-agent system:

**Upper Agents (LLM-based):**
1. PartDesignAgent: Production planning (route, batch size, robot allocation)
2. MaintenanceAgent: Equipment health monitoring and predictive maintenance
3. QualityAgent: Defect analysis and process parameter recommendations
4. CoordinatorAgent: Robot task assignment and execution control

**Architecture:**
```
                    Product Request
                          │
                          ▼
                 PartDesignAgent
                 (Production Plan)
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
  MaintenanceAgent   QualityAgent    CoordinatorAgent
  (Equipment Risk)   (Defect Rate)   (Task Assignment)
        │                 │                 │
        └─────────────────┴─────────────────┘
                          │
                          ▼
                   Lower Agents
            (RobotArm + Logistics Robots)
```

Requirements:
1. Set up API keys in .env file
2. Install dependencies: pip install -e .
3. Run: python examples/factory_multi_agent_integration.py
"""

import sys
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from realtimegym.agents.factory import (
    CoordinatorAgent,
    MaintenanceAgent,
    PartDesignAgent,
    QualityAgent,
)
from realtimegym.environments.factory import FactoryEnv
from realtimegym.prompts.factory import (
    coordinator as coordinator_prompts,
    maintenance as maintenance_prompts,
    part_design as part_design_prompts,
    quality as quality_prompts,
)


def run_multi_agent_factory(
    model_config: str = "configs/example-claude-coordinator.yaml",
    num_steps: int = 100,
    time_budget: int = 2000,  # tokens per step per agent
):
    """
    Run factory simulation with full hierarchical multi-agent system.

    Args:
        model_config: Path to model configuration file (used for all agents)
        num_steps: Number of simulation steps to run
        time_budget: Token budget per step for each agent
    """
    print("=" * 80)
    print("FACTORY MULTI-AGENT INTEGRATION")
    print("=" * 80)

    # 1. Create environment
    print("\n[1/6] Initializing Factory Environment...")
    env = FactoryEnv()
    env.set_seed(42)
    obs, done = env.reset()

    print(f"    ✓ Environment ready")
    print(f"      - Grid: {env.width}×{env.height}")
    print(f"      - Production lines: {env.num_lines}")
    print(f"      - Robot arms: {len(env.robot_arms)}")
    print(f"      - Logistics robots: {len(env.logistics_robots)}")

    # 2. Initialize all upper agents
    print(f"\n[2/6] Initializing Upper Agents...")
    print(f"    Model config: {model_config}")
    print(f"    Token budget per agent: {time_budget}")

    try:
        # PartDesign Agent - Production planning
        part_design_agent = PartDesignAgent(
            prompts=part_design_prompts,
            file="logs/part_design_agent.csv",
            time_unit="token",
            model1_config=model_config,
            internal_budget=time_budget,
        )
        print(f"    ✓ PartDesignAgent initialized")

        # Maintenance Agent - Equipment health
        maintenance_agent = MaintenanceAgent(
            prompts=maintenance_prompts,
            file="logs/maintenance_agent.csv",
            time_unit="token",
            model1_config=model_config,
            internal_budget=time_budget,
        )
        print(f"    ✓ MaintenanceAgent initialized")

        # Quality Agent - Defect analysis
        quality_agent = QualityAgent(
            prompts=quality_prompts,
            file="logs/quality_agent.csv",
            time_unit="token",
            model1_config=model_config,
            internal_budget=time_budget,
        )
        print(f"    ✓ QualityAgent initialized")

        # Coordinator Agent - Task execution
        coordinator_agent = CoordinatorAgent(
            prompts=coordinator_prompts,
            file="logs/coordinator_agent.csv",
            time_unit="token",
            model1_config=model_config,
            internal_budget=time_budget,
        )
        print(f"    ✓ CoordinatorAgent initialized")

    except Exception as e:
        print(f"    ✗ Failed to initialize agents: {e}")
        print(f"\n    Make sure you have:")
        print(f"      1. Copied .env.example to .env")
        print(f"      2. Added your API key to .env")
        print(f"      3. Selected the correct model config file")
        return

    # 3. Create initial production request
    print(f"\n[3/6] Setting up initial production scenario...")

    # Mock product request for PartDesign agent
    product_request = {
        "product_type": "ricotta_salad",
        "quantity": 10,
        "priority": "high"
    }

    # Spawn initial product in environment
    work_item = env._spawn_product("ricotta_salad")
    env.stations["Storage"][0].add_to_queue(work_item)
    env.products_in_progress.append(work_item)
    print(f"    ✓ Production request: {product_request['quantity']} × {product_request['product_type']}")

    # 4. Run multi-agent decision loop
    print(f"\n[4/6] Running multi-agent coordination loop for {num_steps} steps...")
    print("    " + "-" * 70)

    total_rewards = 0
    products_completed = 0

    # Decision cycle: Plan → Monitor → Coordinate → Execute
    for step in range(num_steps):
        # Get current environment state
        obs = env.observe()
        env_state = obs["state"]

        # ─────────────────────────────────────────────────────────────────
        # PHASE 1: Production Planning (PartDesign Agent)
        # ─────────────────────────────────────────────────────────────────
        if step == 0:  # Run planning at start
            print(f"\n    Step {step+1}: [Phase 1] PartDesignAgent creating production plan...")

            # Build state for PartDesign agent
            part_design_state = _build_part_design_state(env_state, product_request)
            part_design_agent.observe({"state": part_design_state, "game_turn": step, "state_string": ""})

            production_plan = part_design_agent.think(timeout=time_budget)
            print(f"              → Plan: {production_plan.get('batch_size', 'N/A')} items per batch, "
                  f"{len(production_plan.get('route', []))} stations")

        # ─────────────────────────────────────────────────────────────────
        # PHASE 2: Equipment Health Monitoring (Maintenance Agent)
        # ─────────────────────────────────────────────────────────────────
        if step % 10 == 0:  # Run every 10 steps
            print(f"\n    Step {step+1}: [Phase 2] MaintenanceAgent assessing equipment...")

            maintenance_state = _build_maintenance_state(env_state, step)
            maintenance_agent.observe({"state": maintenance_state, "game_turn": step, "state_string": ""})

            maintenance_assessment = maintenance_agent.think(timeout=time_budget)
            high_risk_stations = [
                k for k, v in maintenance_assessment.get("station_risk_scores", {}).items()
                if v in ["High", "Critical"]
            ]
            if high_risk_stations:
                print(f"              → High risk stations: {', '.join(high_risk_stations)}")
            else:
                print(f"              → All equipment healthy")

        # ─────────────────────────────────────────────────────────────────
        # PHASE 3: Quality Monitoring (Quality Agent)
        # ─────────────────────────────────────────────────────────────────
        if step % 15 == 0 and step > 0:  # Run every 15 steps after initial production
            print(f"\n    Step {step+1}: [Phase 3] QualityAgent analyzing defects...")

            quality_state = _build_quality_state(env_state, step)
            quality_agent.observe({"state": quality_state, "game_turn": step, "state_string": ""})

            quality_analysis = quality_agent.think(timeout=time_budget)
            defect_rate = quality_analysis.get("quality_metrics", {}).get("overall_defect_rate", 0.0)
            print(f"              → Overall defect rate: {defect_rate:.1%}")

            alerts = quality_analysis.get("alerts", [])
            if alerts:
                print(f"              → Alerts: {len(alerts)} quality issues detected")

        # ─────────────────────────────────────────────────────────────────
        # PHASE 4: Task Coordination (Coordinator Agent)
        # ─────────────────────────────────────────────────────────────────
        coordinator_agent.observe(obs)
        task_assignments = coordinator_agent.think(timeout=time_budget)

        # Execute step with coordinator's task assignments
        obs, done, reward, reset = env.step(task_assignments)

        total_rewards += reward

        # Track production
        if reward > 0:
            products_completed += 1
            print(f"    Step {step+1:3d}: 🎉 Product completed! Reward: {reward}")

        # Print periodic status
        if (step + 1) % 10 == 0:
            kpis = obs["state"]["kpis"]
            print(
                f"    Step {step+1:3d}: Production={kpis['production']}, "
                f"InProgress={kpis['in_progress']}, "
                f"RobotIdle={kpis['robot_idle_ratio']:.1%}"
            )

        if done:
            print(f"    Simulation terminated at step {step+1}")
            break

    # 5. Final statistics
    print("\n[5/6] Simulation Complete!")
    print("    " + "-" * 70)

    final_state = env.state_builder()
    kpis = final_state["kpis"]

    print(f"\n    Final Statistics:")
    print(f"      Total Steps:         {env.game_turn}")
    print(f"      Total Reward:        {total_rewards}")
    print(f"      Products Completed:  {kpis['production']}")
    print(f"      Products Rejected:   {kpis['rejected']}")
    print(f"      In Progress:         {kpis['in_progress']}")
    print(f"      Defect Rate:         {kpis['defect_rate']:.1%}")
    print(f"      Avg Lead Time:       {kpis['avg_lead_time']:.1f} steps")
    print(f"      Robot Idle Ratio:    {kpis['robot_idle_ratio']:.1%}")
    print(f"      Station Idle Ratio:  {kpis['station_idle_ratio']:.1%}")

    # 6. Agent coordination summary
    print("\n[6/6] Agent Logs Saved:")
    print("    - logs/part_design_agent.csv")
    print("    - logs/maintenance_agent.csv")
    print("    - logs/quality_agent.csv")
    print("    - logs/coordinator_agent.csv")

    print("\n" + "=" * 80)
    print("DONE!")
    print("=" * 80)


def _build_part_design_state(env_state: dict[str, Any], product_request: dict[str, Any]) -> dict[str, Any]:
    """Build state dict for PartDesign agent."""
    return {
        "product_request": product_request,
        "stations": env_state.get("stations", {}),
        "robots": env_state.get("robots", {}),
        "maintenance_risk": {},  # Would come from MaintenanceAgent in real system
        "quality_metrics": {}    # Would come from QualityAgent in real system
    }


def _build_maintenance_state(env_state: dict[str, Any], current_time: int) -> dict[str, Any]:
    """Build state dict for Maintenance agent."""
    stations = env_state.get("stations", {})

    # Mock maintenance history (in real system, would be tracked)
    maintenance_history = {}
    for station_type, station_list in stations.items():
        for i, _ in enumerate(station_list):
            station_key = f"{station_type}_{i}"
            maintenance_history[station_key] = 0  # Last maintained at turn 0

    return {
        "stations": stations,
        "maintenance_history": maintenance_history,
        "error_logs": [],  # Would be populated from station error tracking
        "sensor_data": {},
        "current_time": current_time
    }


def _build_quality_state(env_state: dict[str, Any], current_time: int) -> dict[str, Any]:
    """Build state dict for Quality agent."""
    # Mock inspection results (in real system, would come from VisionQA station)
    inspection_results = []

    # In real implementation, would get actual inspection data from environment
    # For now, return mock structure
    return {
        "inspection_results": inspection_results,
        "production_history": [],
        "defect_logs": [],
        "station_parameters": {},
        "workload_metrics": env_state.get("robots", {})
    }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run factory with hierarchical multi-agent system"
    )
    parser.add_argument(
        "--model-config",
        type=str,
        default="configs/example-claude-coordinator.yaml",
        help="Path to model configuration file",
    )
    parser.add_argument(
        "--steps", type=int, default=100, help="Number of simulation steps"
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=2000,
        help="Token budget per step per agent",
    )

    args = parser.parse_args()

    run_multi_agent_factory(
        model_config=args.model_config,
        num_steps=args.steps,
        time_budget=args.budget,
    )


if __name__ == "__main__":
    main()
