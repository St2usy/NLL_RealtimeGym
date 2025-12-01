"""Test Cooker station processing for PASTA recipe."""

import realtimegym
from realtimegym.environments.factory import RECIPES, RecipeType
from realtimegym.environments.factory.items import Item, ItemType
from realtimegym.environments.factory.stations import StationType

print("="*70)
print("COOKER STATION PROCESSING TEST - PASTA RECIPE")
print("="*70)

# Create environment
print("\n1. Creating Factory environment...")
env, seed, renderer = realtimegym.make("Factory-v0", seed=0, render=False)
obs, done = env.reset()

print(f"   Current Recipe: {env.current_recipe}")
print(f"   Target Products: {env.target_products}")

# Get PASTA recipe details
pasta_recipe = RECIPES[RecipeType.PASTA]
print(f"\n2. PASTA Recipe Details:")
print(f"   Recipe Type: {pasta_recipe.recipe_type}")
print(f"   Required Ingredients: {[ing.value for ing in pasta_recipe.ingredients]}")
print(f"   Processing Steps: {pasta_recipe.processing_steps}")
print(f"   Cooker Processing Time: {pasta_recipe.processing_time.get('Cooker', 'N/A')} steps")

# Find Cooker station
cooker_station = None
for station in env.stations:
    if station.station_type == StationType.COOKER and station.line == 1:
        cooker_station = station
        break

if not cooker_station:
    print("\n[ERROR] No Cooker station found!")
    exit(1)

print(f"\n3. Cooker Station Found:")
print(f"   Station ID: {cooker_station.station_id}")
print(f"   Position: {cooker_station.position}")
print(f"   Line: {cooker_station.line}")
print(f"   Current Recipe Set: {cooker_station.current_recipe is not None}")

if cooker_station.current_recipe:
    print(f"   Recipe Type: {cooker_station.current_recipe.recipe_type}")
    print(f"   Required Ingredients: {[ing.value for ing in cooker_station.current_recipe.ingredients]}")
else:
    print("\n   [WARNING] No recipe assigned to Cooker station!")

# Add all required ingredients to Cooker
print(f"\n4. Adding PASTA ingredients to Cooker station...")
for ingredient in pasta_recipe.ingredients:
    item = Item(
        item_type=ingredient,
        quantity=1,
        quality=1.0,
        processed=True,
        line=1
    )
    cooker_station.input_buffer.append(item)
    print(f"   [OK] Added: {ingredient.value}")

print(f"\n5. Before Processing:")
print(f"   Input Buffer Count: {len(cooker_station.input_buffer)}")
print(f"   Output Buffer Count: {len(cooker_station.output_buffer)}")
print(f"   Station Status: {cooker_station.status.value}")
print(f"   Current Progress: {cooker_station.current_progress}/{cooker_station.processing_time}")

# Check if Cooker can detect all ingredients
if cooker_station.current_recipe:
    has_all = cooker_station._has_required_ingredients(pasta_recipe.ingredients)
    print(f"   Has All Required Ingredients: {has_all}")

# Simulate processing
print(f"\n6. Simulating Cooker Processing...")
print(f"   Processing time required: {cooker_station.processing_time} steps")

step_count = 0
max_steps = cooker_station.processing_time + 5

while step_count < max_steps:
    cooker_station.process()
    step_count += 1

    # Print progress every 5 steps
    if step_count % 5 == 0 or cooker_station.status.value == "Idle":
        print(f"   Step {step_count:2d}: Status={cooker_station.status.value:8s} | "
              f"Progress={cooker_station.current_progress:2d}/{cooker_station.processing_time:2d} | "
              f"In={len(cooker_station.input_buffer)} Out={len(cooker_station.output_buffer)}")

    # Stop if processing completed
    if cooker_station.status.value == "Idle" and len(cooker_station.output_buffer) > 0:
        print(f"   [OK] Processing completed at step {step_count}")
        break

print(f"\n7. After Processing:")
print(f"   Input Buffer Count: {len(cooker_station.input_buffer)}")
print(f"   Output Buffer Count: {len(cooker_station.output_buffer)}")
print(f"   Station Status: {cooker_station.status.value}")

# Check output
print(f"\n8. Output Analysis:")
if len(cooker_station.output_buffer) > 0:
    output_item = cooker_station.output_buffer[0]
    print(f"   [OK] Output Item Created!")
    print(f"     - Type: {output_item.item_type.value}")
    print(f"     - Quantity: {output_item.quantity}")
    print(f"     - Quality: {output_item.quality:.2f}")
    print(f"     - Processed: {output_item.processed}")
    print(f"     - Line: {output_item.line}")

    if output_item.item_type == ItemType.PASTA_DISH:
        print(f"\n   [SUCCESS] PASTA_DISH was created from ingredients!")
    else:
        print(f"\n   [WARNING] Expected PASTA_DISH but got {output_item.item_type.value}")
else:
    print(f"   [FAIL] No output item created")
    print(f"   Input buffer still has {len(cooker_station.input_buffer)} items")

# Additional diagnostics
print(f"\n9. Diagnostics:")
print(f"   Recipe in Environment: {env.current_recipe}")
print(f"   Recipe in Cooker: {cooker_station.current_recipe.recipe_type if cooker_station.current_recipe else 'None'}")
print(f"   Temperature: {cooker_station.temperature}°C (optimal: {cooker_station.optimal_temp}°C)")
print(f"   Batch Size: {cooker_station.batch_size}")

# Test why it might not be processing
if cooker_station.current_recipe is None:
    print(f"\n   [ISSUE] Cooker has no recipe assigned!")
    print(f"      - This means _complete_processing will use fallback logic")
    print(f"      - It will create generic COOKED_PASTA instead of PASTA_DISH")

print("\n" + "="*70)
print("Test Complete")
print("="*70)
