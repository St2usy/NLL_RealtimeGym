"""Test to check if agents behave differently per station."""

import realtimegym


def test_agents_by_station():
    """Check if robot agents are differentiated by station."""
    print("=" * 80)
    print("Testing: Do agents behave differently per station?")
    print("=" * 80)

    # Create environment
    env, seed, _ = realtimegym.make("Factory-v0", seed=0)
    env.reset()

    print("\n1. Robot Arms Setup:")
    print("-" * 80)

    # Group robot arms by assigned station
    arms_by_station = {}
    for arm in env.robot_arms:
        station = arm.assigned_station
        if station not in arms_by_station:
            arms_by_station[station] = []
        arms_by_station[station].append(arm)

    for station, arms in sorted(arms_by_station.items()):
        print(f"\n{station}:")
        for arm in arms:
            print(f"  - Robot {arm.robot_id}: position={arm.position}, "
                  f"status={arm.status.value}")

    print("\n" + "-" * 80)
    print(f"Total Robot Arms: {len(env.robot_arms)}")
    print(f"Stations with Arms: {list(arms_by_station.keys())}")

    print("\n2. Logistics Robots Setup:")
    print("-" * 80)
    print(f"Total Logistics Robots: {len(env.logistics_robots)}")
    for i, robot in enumerate(env.logistics_robots[:6]):  # Show first 6
        print(f"  - Robot {robot.robot_id}: position={robot.position}, "
              f"status={robot.status.value}")
    print(f"  ... (showing 6 of {len(env.logistics_robots)})")

    print("\n3. Testing: Are agents station-specific?")
    print("-" * 80)

    # Check if each station type has dedicated arms
    expected_stations = ["Washer", "Cutter", "Cooker", "Plating", "Sealing", "VisionQA"]
    for station in expected_stations:
        count = len(arms_by_station.get(station, []))
        print(f"  {station:12s}: {count} robot arms")

    print("\n4. Testing: Do agents have different positions?")
    print("-" * 80)

    # Check if arms in same station have different positions
    for station, arms in sorted(arms_by_station.items()):
        positions = [arm.position for arm in arms]
        unique_positions = len(set(positions))
        print(f"  {station:12s}: {len(positions)} arms, {unique_positions} unique positions")

    print("\n5. Running simulation to check if agents remain idle:")
    print("-" * 80)

    # Run a few steps
    env.step("produce_ricotta_salad")

    for step in range(10):
        env.step("continue")

    # Check agent states after simulation
    print("\n  After 10 steps:")
    print(f"    Total arms idle: {sum(1 for r in env.robot_arms if r.status.value == 'idle')}/{len(env.robot_arms)}")
    print(f"    Total logistics idle: {sum(1 for r in env.logistics_robots if r.status.value == 'idle')}/{len(env.logistics_robots)}")

    # Check if any robot has moved or operated
    moved_arms = [r for r in env.robot_arms if r.total_moves > 0]
    operated_arms = [r for r in env.robot_arms if r.total_tasks_completed > 0]
    moved_logistics = [r for r in env.logistics_robots if r.total_moves > 0]

    print(f"\n    Moved robot arms: {len(moved_arms)}")
    print(f"    Operated robot arms: {len(operated_arms)}")
    print(f"    Moved logistics robots: {len(moved_logistics)}")

    print("\n6. Conclusion:")
    print("-" * 80)

    if len(set([arm.assigned_station for arm in env.robot_arms])) > 1:
        print("  ✅ YES: Robot arms ARE assigned to different stations")
    else:
        print("  ❌ NO: All robot arms assigned to same station")

    if len(moved_arms) > 0 or len(moved_logistics) > 0:
        print("  ⚠️  Some agents ARE moving (not idle)")
    else:
        print("  ❌ NO: All agents remain IDLE (no tasks assigned)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_agents_by_station()
