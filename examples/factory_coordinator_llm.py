"""
Factory Environment with LLM-based CoordinatorAgent
====================================================

This example demonstrates the complete integration of:
- FactoryEnv (multi-agent unmanned factory simulation)
- CoordinatorAgent (LLM-based high-level decision maker)
- Rule-based sub-agents (RobotArm and Logistics)

Requirements:
1. Set up API key in .env file
2. Install dependencies: pip install -e .
3. Run: python examples/factory_coordinator_llm.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from realtimegym.agents.factory import CoordinatorAgent
from realtimegym.environments.factory import FactoryEnv
from realtimegym.prompts.factory import coordinator as coordinator_prompts


def run_factory_with_coordinator(
    model_config: str = "configs/example-claude-coordinator.yaml",
    num_steps: int = 50,
    time_budget: int = 2000,  # tokens per step
):
    """
    Run factory simulation with LLM-based coordinator.

    Args:
        model_config: Path to model configuration file
        num_steps: Number of simulation steps to run
        time_budget: Token budget per step for coordinator
    """
    print("=" * 80)
    print("FACTORY ENVIRONMENT WITH LLM COORDINATOR")
    print("=" * 80)

    # 1. Create environment
    print("\n[1/5] Initializing Factory Environment...")
    env = FactoryEnv()
    env.set_seed(42)
    obs, done = env.reset()

    print(f"    ✓ Environment ready")
    print(f"      - Grid: {env.width}×{env.height}")
    print(f"      - Production lines: {env.num_lines}")
    print(f"      - Robot arms: {len(env.robot_arms)}")
    print(f"      - Logistics robots: {len(env.logistics_robots)}")
    print(f"      - Production queue: {env.production_queue}")

    # 2. Create coordinator agent
    print(f"\n[2/5] Initializing CoordinatorAgent...")
    print(f"    Model config: {model_config}")

    try:
        coordinator = CoordinatorAgent(
            prompts=coordinator_prompts,
            file="logs/factory_coordinator.csv",
            time_unit="token",
            model1_config=model_config,
            internal_budget=time_budget,
        )
        print(f"    ✓ Coordinator agent initialized")
        print(f"      - Model: {coordinator.model1}")
        print(f"      - Token budget per step: {time_budget}")

    except Exception as e:
        print(f"    ✗ Failed to initialize coordinator: {e}")
        print(f"\n    Make sure you have:")
        print(f"      1. Copied .env.example to .env")
        print(f"      2. Added your API key to .env")
        print(f"      3. Selected the correct model config file")
        return

    # 3. Spawn initial product
    print(f"\n[3/5] Starting production...")
    # Spawn a salad to produce
    work_item = env._spawn_product("ricotta_salad")
    env.stations["Storage"][0].add_to_queue(work_item)
    env.products_in_progress.append(work_item)
    print(f"    ✓ Added 1 Ricotta Salad to production queue")

    # 4. Run simulation loop
    print(f"\n[4/5] Running simulation for {num_steps} steps...")
    print("    " + "-" * 70)

    total_rewards = 0
    products_completed = 0

    for step in range(num_steps):
        # Coordinator observes environment
        obs = env.observe()
        coordinator.observe(obs)

        # Coordinator decides task assignments
        task_assignments = coordinator.think(timeout=time_budget)

        # Execute step with coordinator's decisions
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
    print("\n[5/5] Simulation Complete!")
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

    print("\n    Log file saved to: logs/factory_coordinator.csv")

    print("\n" + "=" * 80)
    print("DONE!")
    print("=" * 80)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run factory simulation with LLM coordinator"
    )
    parser.add_argument(
        "--model-config",
        type=str,
        default="configs/example-gpt4o-coordinator.yaml",
        help="Path to model configuration file",
    )
    parser.add_argument(
        "--steps", type=int, default=50, help="Number of simulation steps"
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=2000,
        help="Token budget per step for coordinator",
    )

    args = parser.parse_args()

    run_factory_with_coordinator(
        model_config=args.model_config,
        num_steps=args.steps,
        time_budget=args.budget,
    )


if __name__ == "__main__":
    main()
