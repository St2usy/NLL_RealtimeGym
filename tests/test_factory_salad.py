"""Test script for factory environment with CoordinatorAgent - Salad production scenario."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from realtimegym.agents.factory import CoordinatorAgent
from realtimegym.environments.factory import FactoryEnv
from realtimegym.prompts.factory import coordinator as coordinator_prompts


def test_coordinator_integration():
    """Test basic integration between FactoryEnv and CoordinatorAgent."""
    print("=" * 80)
    print("Factory Environment + CoordinatorAgent Integration Test")
    print("=" * 80)

    # Create environment
    env = FactoryEnv()
    env.set_seed(42)
    obs, done = env.reset()

    print("\n[1] Environment initialized")
    print(f"    - Grid size: {env.width}x{env.height}")
    print(f"    - Robot arms: {len(env.robot_arms)}")
    print(f"    - Logistics robots: {len(env.logistics_robots)}")
    print(f"    - Total robots: {len(env.robot_lookup)}")

    # Create coordinator agent
    print("\n[2] Creating CoordinatorAgent...")
    print("    Note: This requires a model config file and API key")
    print("    Skipping agent creation for now (requires API credentials)")

    # For now, manually test with a simple task assignment
    print("\n[3] Testing manual task assignment (simulating coordinator)")

    # Simulate coordinator output: assign some tasks
    test_task_assignments = {
        "logistics_0": {
            "type": "pick_and_deliver",
            "from": "Storage",
            "to": "Washer",
            "item": "lettuce",
        },
        "logistics_1": {
            "type": "wait",
        },
        "robot_arm_washer_0": {
            "type": "operate_station",
            "station": "Washer",
        },
    }

    print(f"\n    Task assignments: {test_task_assignments}")

    # Execute step with coordinator mode
    obs, done, reward, reset = env.step(test_task_assignments)

    print(f"\n[4] Step executed")
    print(f"    - Game turn: {obs['game_turn']}")
    print(f"    - Reward: {reward}")
    print(f"    - Done: {done}")

    # Check robot states
    print("\n[5] Robot states after task assignment:")
    for robot_name in ["logistics_0", "logistics_1", "robot_arm_washer_0"]:
        if robot_name in env.robot_lookup:
            robot = env.robot_lookup[robot_name]
            print(
                f"    - {robot_name}: status={robot.status.value}, "
                f"queue={len(robot.task_queue)}, position={robot.position}"
            )

    # Run a few more steps
    print("\n[6] Running 5 more steps...")
    for i in range(5):
        # Continue with empty task assignments
        obs, done, reward, reset = env.step({})
        print(f"    Step {i+2}: turn={obs['game_turn']}, reward={reward}")

    print("\n[7] Final state:")
    print(env.state_string())

    print("\n" + "=" * 80)
    print("Test completed successfully!")
    print("=" * 80)


def test_state_observation():
    """Test that observation format is correct for coordinator."""
    print("\n" + "=" * 80)
    print("Testing Observation Format")
    print("=" * 80)

    env = FactoryEnv()
    env.set_seed(42)
    obs, done = env.reset()

    print("\n[1] Observation keys:")
    for key in obs.keys():
        print(f"    - {key}")

    print("\n[2] State keys:")
    for key in obs["state"].keys():
        print(f"    - {key}")

    print("\n[3] Sample robot states (first 3):")
    robot_names = list(obs["state"]["robots"].keys())[:3]
    for robot_name in robot_names:
        robot_state = obs["state"]["robots"][robot_name]
        print(f"    {robot_name}:")
        for k, v in robot_state.items():
            print(f"        {k}: {v}")

    print("\n[4] Sample station states:")
    for station_type in ["Storage", "Washer"]:
        stations = obs["state"]["stations"][station_type]
        print(f"    {station_type} (Line 0): {stations[0]}")

    print("\n" + "=" * 80)
    print("Observation format test completed!")
    print("=" * 80)


def test_legacy_mode():
    """Test that legacy string action mode still works."""
    print("\n" + "=" * 80)
    print("Testing Legacy String Action Mode")
    print("=" * 80)

    env = FactoryEnv()
    env.set_seed(42)
    obs, done = env.reset()

    print("\n[1] Testing produce action...")
    obs, done, reward, reset = env.step("produce_ricotta_salad")

    print(f"    - Products in progress: {len(env.products_in_progress)}")
    print(f"    - Reward: {reward}")

    print("\n[2] Running continue action for 10 steps...")
    for i in range(10):
        obs, done, reward, reset = env.step("continue")
        if reward > 0:
            print(f"    Step {i+1}: Produced product! Reward={reward}")

    print(f"\n[3] Final stats:")
    print(f"    - Total production: {env.total_production}")
    print(f"    - Products in progress: {len(env.products_in_progress)}")
    print(f"    - Completed: {len(env.completed_products)}")

    print("\n" + "=" * 80)
    print("Legacy mode test completed!")
    print("=" * 80)


if __name__ == "__main__":
    # Run tests
    test_state_observation()
    test_coordinator_integration()
    test_legacy_mode()

    print("\n\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Create model config file (configs/example-coordinator.yaml)")
    print("2. Set up API keys in .env file")
    print("3. Test with actual CoordinatorAgent and LLM")
    print("4. Implement A* pathfinding for better robot movement")
