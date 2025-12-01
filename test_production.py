"""Test full production cycle."""

import realtimegym
from realtimegym.environments.factory.items import Item, ItemType

# Create environment
print("Creating Factory environment...")
env, seed, renderer = realtimegym.make("Factory-v0", seed=0, render=False)

# Reset environment
obs, done = env.reset()
print(f"Target: {env.target_products} products")
print(f"Total robots: {len(env.logistic_robots)}")
print(f"Active robots: {len([r for r in env.logistic_robots if r.is_active])}")
print(f"Reserve robots: {len([r for r in env.logistic_robots if not r.is_active])}")

# Debug: show robot positions and segments
print("\n=== Robot Configuration ===")
for r in env.logistic_robots[:4]:  # Show first 4
    print(f"Robot {r.robot_id}: pos={r.position}, segment={r.assigned_segment}, active={r.is_active}")

# Debug: show station positions
print("\n=== Station Positions (Line 1) ===")
for s in [s for s in env.stations if s.line == 1]:
    print(f"{s.station_type.value}: row={s.position[0]}, col={s.position[1]}")
print()

# Production helper
def start_production_batch():
    """Add items to washers."""
    added = 0
    for station in env.stations:
        if station.station_type.value == "Washer" and len(station.input_buffer) < 5:
            item = Item(
                item_type=ItemType.LETTUCE,
                quantity=1,
                quality=1.0,
                processed=False,
                line=station.line
            )
            station.input_buffer.append(item)
            added += 1
    return added

# Run simulation
print("Running production simulation...")
step_count = 0
last_completed = 0
debug_interval = 100

while not done and step_count < 1000:
    # Add items every 3 steps
    if step_count % 3 == 0:
        start_production_batch()

    # Step environment
    obs, done, reward, reset = env.step("WAIT")
    step_count += 1

    # Check for completed products
    for station in env.stations:
        if station.station_type.value == "Storage" and station.position[0] == 19:
            while len(station.input_buffer) > 0:
                item = station.input_buffer.pop(0)
                if item.item_type != ItemType.DEFECTIVE:
                    env.completed_products += 1
                else:
                    env.defective_products += 1

    # Debug output every 100 steps
    if step_count % debug_interval == 0:
        washers = [s for s in env.stations if s.station_type.value == "Washer"]
        cutters = [s for s in env.stations if s.station_type.value == "Cutter"]
        platings = [s for s in env.stations if s.station_type.value == "Plating"]
        sealings = [s for s in env.stations if s.station_type.value == "Sealing"]
        visionqas = [s for s in env.stations if s.station_type.value == "VisionQA"]
        storages = [s for s in env.stations if s.station_type.value == "Storage" and s.position[0] == 19]
        print(f"\nStep {step_count}:")
        for w in washers[:1]:
            print(f"  Washer L{w.line}: in={len(w.input_buffer)}, out={len(w.output_buffer)}")
        for c in cutters[:2]:
            print(f"  Cutter L{c.line}: in={len(c.input_buffer)}, out={len(c.output_buffer)}")
        for p in platings[:1]:
            print(f"  Plating L{p.line}: in={len(p.input_buffer)}, out={len(p.output_buffer)}")
        for s in sealings[:1]:
            print(f"  Sealing L{s.line}: in={len(s.input_buffer)}, out={len(s.output_buffer)}")
        for v in visionqas[:1]:
            print(f"  VisionQA L{v.line}: in={len(v.input_buffer)}, out={len(v.output_buffer)}")
        for st in storages[:1]:
            print(f"  Storage(out) L{st.line}: in={len(st.input_buffer)}")

        # Check robots for each segment
        for seg_name, seg in [("Sealing->VisionQA", ("Sealing", "VisionQA")), ("VisionQA->Storage", ("VisionQA", "Storage"))]:
            seg_robots = [r for r in env.logistic_robots if r.assigned_segment == seg and r.is_active]
            print(f"  {seg_name} robots (active): {len(seg_robots)}")
            if seg_robots:
                r = seg_robots[0]
                print(f"    Robot {r.robot_id} pos={r.position}: {r.status.value}, carrying={r.carrying_item is not None}")

    # Report progress
    if env.completed_products > last_completed:
        print(f"Step {step_count}: Completed {env.completed_products}/{env.target_products}")
        last_completed = env.completed_products

    # Check if target reached
    if env.completed_products >= env.target_products:
        print(f"\nTarget reached at step {step_count}!")
        break

print(f"\n=== Final Results ===")
print(f"Steps: {step_count}")
print(f"Completed: {env.completed_products}/{env.target_products}")
print(f"Defective: {env.defective_products}")
total = env.completed_products + env.defective_products
if total > 0:
    print(f"Quality Rate: {env.completed_products/total*100:.1f}%")
else:
    print("Quality Rate: N/A (no products)")

# Check robot status
idle_robots = [r for r in env.logistic_robots if r.status.value == "Idle"]
home_robots = [r for r in idle_robots if r.home_position and r.position == r.home_position]
print(f"\nRobots at home: {len(home_robots)}/{len(env.logistic_robots)}")
