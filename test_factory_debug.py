"""Debug factory environment."""

import realtimegym
from realtimegym.environments.factory.items import Item, ItemType

# Create environment
print("Creating Factory environment...")
env, seed, renderer = realtimegym.make("Factory-v0", seed=0, render=False)

# Reset environment
obs, done = env.reset()
print(f"Environment initialized. Target: {env.target_products} products\n")

# Print station configuration
print("=== Station Configuration ===")
for station in env.stations:
    print(f"Station {station.station_id}: {station.station_type.value} at {station.position}, Line {station.line}")

print(f"\nTotal stations: {len(env.stations)}")
print(f"Robot arms: {len(env.robot_arms)}")
print(f"Logistic robots: {len(env.logistic_robots)}")

# Print robot configuration
print("\n=== Logistic Robot Configuration ===")
line1_robots = [r for r in env.logistic_robots if r.line == 1]
line2_robots = [r for r in env.logistic_robots if r.line == 2]
print(f"Line 1 robots: {len(line1_robots)}")
print(f"Line 2 robots: {len(line2_robots)}")

# Add test items to washers
print("\n=== Adding Test Items ===")
for station in env.stations:
    if station.station_type.value == "Washer":
        item = Item(
            item_type=ItemType.LETTUCE,
            quantity=1,
            quality=1.0,
            processed=False,
            line=station.line
        )
        station.input_buffer.append(item)
        print(f"Added item to Washer at {station.position}, Line {station.line}")

# Run simulation for a few steps
print("\n=== Running Simulation ===")
for step in range(300):
    obs, done, reward, reset = env.step("WAIT")

    # Check station status every 10 steps
    if step % 10 == 0:
        print(f"\n--- Step {step} ---")
        for station in env.stations:
            if len(station.input_buffer) > 0 or len(station.output_buffer) > 0 or station.station_type.value in ["VisionQA", "Storage"]:
                print(f"  {station.station_type.value} (Line {station.line}, ID={station.station_id}): "
                      f"Status={station.status.value}, In={len(station.input_buffer)}, Out={len(station.output_buffer)}")

        # Check robot tasks
        busy_robots = [r for r in env.logistic_robots if r.status.value != "Idle"]
        idle_robots = [r for r in env.logistic_robots if r.status.value == "Idle"]
        line2_busy = [r for r in busy_robots if r.line == 2]
        print(f"  Active robots: {len(busy_robots)}, Idle robots: {len(idle_robots)}")
        print(f"    Line 1 idle: {len([r for r in idle_robots if r.line == 1])}, Line 2 idle: {len([r for r in idle_robots if r.line == 2])}")
        if len(busy_robots) > 0:
            for r in busy_robots[:3]:  # Show first 3
                print(f"    Robot {r.robot_id} (Line {r.line}): {r.status.value}, "
                      f"carrying={r.carrying_item is not None}, tasks={len(r.task_queue)}")
        if len(line2_busy) > 0 and step == 100:
            print(f"  Line 2 busy robots:")
            for r in line2_busy[:5]:
                print(f"    Robot {r.robot_id}: status={r.status.value}, carrying={r.carrying_item}, "
                      f"tasks={len(r.task_queue)}, position={r.position}, path_len={len(r.path)}")

    # Check for completed products
    for station in env.stations:
        if station.station_type.value == "Storage" and station.position[0] == 15:
            while len(station.input_buffer) > 0:
                item = station.input_buffer.pop(0)
                if item.item_type != ItemType.DEFECTIVE:
                    env.completed_products += 1
                    print(f"\n*** Product completed! Line {item.line}, Total: {env.completed_products} ***")
                else:
                    env.defective_products += 1

    if env.completed_products >= 2:  # Stop after 2 products
        break

print(f"\n=== Final Results ===")
print(f"Completed: {env.completed_products}/{env.target_products}")
print(f"Defective: {env.defective_products}")
print(f"Steps: {step + 1}")
