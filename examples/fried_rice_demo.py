"""
볶음밥 시뮬레이션 데모

이 시뮬레이션은 다음을 보여줍니다:
- Logistics 로봇이 실제로 물건을 픽업하고 다음 station으로 운반
- 로봇의 이동속도: 1 step당 1 grid
- 완전한 생산 워크플로우: Storage → Washer → Cutter → Cooker → Plating → Sealing → VisionQA → FinalStorage
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the custom environment from the main simulation
exec(open(Path(__file__).parent / "fried_rice_100_simulation.py", encoding='utf-8').read().split("def run_fried_rice_simulation")[0])


def run_fried_rice_demo(quantity=30):
    """Run fried rice production demo."""
    print("=" * 70)
    print(f"Fried Rice Production Simulation - {quantity} units")
    print("=" * 70)
    print("\nKey Features:")
    print("  - Logistics robots physically transport items between stations")
    print("  - Movement speed: 1 grid per step")
    print(f"  - Target: {quantity} fried rice")
    print("  - 2 parallel production lines")
    print("=" * 70)

    # Create environment
    print("\n1. Creating Factory environment...")
    env = FriedRiceFactoryEnv()
    env.set_seed(42)
    env.reset()

    # Production parameters
    spawn_interval = 10  # Slower spawn to avoid bottleneck
    max_steps = 3000

    spawned_count = 0

    print(f"\n2. Starting production (max {max_steps} steps)...")
    print(f"   Target quantity: {quantity}")
    print(f"   Spawn interval: every {spawn_interval} steps")
    print(f"   Number of robots: {len(env.logistics_robots)}\n")

    for step in range(max_steps):
        # Spawn fried rice
        if step % spawn_interval == 0 and spawned_count < quantity:
            action = "produce_shrimp_fried_rice"
            spawned_count += 1
        else:
            action = "continue"

        obs, done, reward, reset = env.step(action)

        # 진행상황 출력 (25 step마다)
        if step % 25 == 0:
            in_progress = len(env.products_in_progress)
            completed = len(env.completed_products)
            rejected = env.rejected_products
            carrying = sum(1 for r in env.logistics_robots if r.carrying)

            # 각 station의 아이템 수 계산
            items_in_stations = {}
            for station_type, station_list in env.stations.items():
                count = sum(len(s.queue) + len(s.output_buffer) + (1 if s.current_work else 0)
                           for s in station_list)
                if count > 0:
                    items_in_stations[station_type] = count

            print(f"Step {step:4d}: Spawned={spawned_count:2d}/{quantity}, " +
                  f"InProgress={in_progress:2d}, Carrying={carrying:2d}, " +
                  f"Done={completed:2d}, Rejected={rejected}")

            # Print station status (brief)
            if items_in_stations:
                station_str = ", ".join([f"{k}:{v}" for k, v in list(items_in_stations.items())[:3]])
                print(f"         Stations: {station_str}")

        # Check if all products are completed
        if (spawned_count >= quantity and
            len(env.completed_products) + env.rejected_products >= quantity):
            print(f"\n   [OK] All {quantity} items processed at step {step}!")
            break

        if done:
            break

    # Final statistics
    print("\n3. Production Complete!")
    print("=" * 70)
    print(f"Final Statistics:")
    print(f"  Total spawned: {spawned_count}")
    print(f"  Completed: {len(env.completed_products)}")
    print(f"  Rejected (QA failed): {env.rejected_products}")
    print(f"  Still in progress: {len(env.products_in_progress)}")

    if env.total_production > 0:
        avg_lead_time = env.total_lead_time / env.total_production
        print(f"  Average production time: {avg_lead_time:.1f} steps")

    # Robot statistics
    total_moves = sum(r.total_moves for r in env.logistics_robots)
    total_tasks = sum(r.total_tasks_completed for r in env.logistics_robots)
    print(f"\nLogistics Robot Statistics:")
    print(f"  Total robots: {len(env.logistics_robots)}")
    print(f"  Total moves: {total_moves} grids")
    print(f"  Total tasks completed: {total_tasks}")
    print(f"  Average moves per robot: {total_moves / len(env.logistics_robots):.1f} grids")

    success_rate = (len(env.completed_products) / spawned_count * 100) if spawned_count > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}% ({len(env.completed_products)}/{spawned_count})")
    print("=" * 70)


if __name__ == "__main__":
    # 30개로 완전한 데모 실행
    run_fried_rice_demo(quantity=30)
