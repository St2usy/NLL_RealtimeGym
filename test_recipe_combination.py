"""Test recipe-based ingredient combination in Plating and Cooker stations."""

import realtimegym
from realtimegym.environments.factory import RecipeType
from realtimegym.environments.factory.items import RECIPES, Item, ItemType
from realtimegym.environments.factory.stations import StationType

# Create environment
print("Creating Factory environment...")
env, seed, renderer = realtimegym.make("Factory-v0", seed=0, render=False)
obs, done = env.reset()

print(f"\nCurrent Recipe: {env.current_recipe}")
print(f"Target Products: {env.target_products}")

# Get recipe details
recipe = RECIPES[env.current_recipe]
print(f"\nRecipe Type: {recipe.recipe_type}")
print(f"Required Ingredients: {[ing.value for ing in recipe.ingredients]}")
print(f"Processing Steps: {recipe.processing_steps}")

# Test 1: Plating Station with all ingredients
print("\n" + "="*70)
print("TEST 1: Plating Station - SALAD Recipe")
print("="*70)

plating_station = None
for station in env.stations:
    if station.station_type == StationType.PLATING and station.line == 1:
        plating_station = station
        break

if plating_station:
    print(f"\nPlating Station ID: {plating_station.station_id}")
    print(f"Current Recipe Set: {plating_station.current_recipe is not None}")

    if plating_station.current_recipe:
        print(f"Recipe Type: {plating_station.current_recipe.recipe_type}")
        print(f"Required Ingredients: {[ing.value for ing in plating_station.current_recipe.ingredients]}")

    # Add all required ingredients to plating station
    print("\nAdding required ingredients to Plating station...")
    for ingredient in recipe.ingredients:
        item = Item(
            item_type=ingredient,
            quantity=1,
            quality=1.0,
            processed=True,
            line=1
        )
        plating_station.input_buffer.append(item)
        print(f"  Added: {ingredient.value}")

    print(f"\nInput Buffer Count: {len(plating_station.input_buffer)}")
    print(f"Status: {plating_station.status.value}")

    # Trigger processing
    print("\nTriggering process...")
    plating_station.status = plating_station.status  # Ensure it starts

    # Simulate processing steps
    for step in range(plating_station.processing_time + 1):
        plating_station.process()
        if step == plating_station.processing_time:
            print(f"Step {step}: Processing complete")

    print(f"\nAfter processing:")
    print(f"  Input Buffer: {len(plating_station.input_buffer)} items")
    print(f"  Output Buffer: {len(plating_station.output_buffer)} items")

    if plating_station.output_buffer:
        output_item = plating_station.output_buffer[0]
        print(f"  Output Item Type: {output_item.item_type.value}")
        print(f"  Output Item Quality: {output_item.quality:.2f}")
        print(f"  Output Item Processed: {output_item.processed}")

        if output_item.item_type == ItemType.SALAD:
            print("\n[OK] SUCCESS: Salad was created from ingredients!")
        else:
            print(f"\n[FAIL] Expected SALAD but got {output_item.item_type.value}")
    else:
        print("\n[FAIL] No output item created")

# Test 2: Cooker Station with PASTA ingredients
print("\n" + "="*70)
print("TEST 2: Cooker Station - PASTA Recipe")
print("="*70)

# First, we need to test with pasta recipe
# For this test, let's manually set the recipe to PASTA
pasta_recipe = RECIPES[RecipeType.PASTA]
print(f"\nPASTA Recipe Ingredients: {[ing.value for ing in pasta_recipe.ingredients]}")

cooker_station = None
for station in env.stations:
    if station.station_type == StationType.COOKER and station.line == 1:
        cooker_station = station
        break

if cooker_station:
    # Set pasta recipe manually for this test
    cooker_station.current_recipe = pasta_recipe

    print(f"\nCooker Station ID: {cooker_station.station_id}")
    print(f"Recipe Set: {cooker_station.current_recipe.recipe_type}")

    # Add all required ingredients
    print("\nAdding required ingredients to Cooker station...")
    for ingredient in pasta_recipe.ingredients:
        item = Item(
            item_type=ingredient,
            quantity=1,
            quality=1.0,
            processed=True,
            line=1
        )
        cooker_station.input_buffer.append(item)
        print(f"  Added: {ingredient.value}")

    print(f"\nInput Buffer Count: {len(cooker_station.input_buffer)}")

    # Trigger processing
    print("\nTriggering process...")
    for step in range(cooker_station.processing_time + 1):
        cooker_station.process()
        if step == cooker_station.processing_time:
            print(f"Step {step}: Processing complete")

    print(f"\nAfter processing:")
    print(f"  Input Buffer: {len(cooker_station.input_buffer)} items")
    print(f"  Output Buffer: {len(cooker_station.output_buffer)} items")

    if cooker_station.output_buffer:
        output_item = cooker_station.output_buffer[0]
        print(f"  Output Item Type: {output_item.item_type.value}")
        print(f"  Output Item Quality: {output_item.quality:.2f}")
        print(f"  Output Item Processed: {output_item.processed}")

        if output_item.item_type == ItemType.PASTA_DISH:
            print("\n[OK] SUCCESS: Pasta dish was created from ingredients!")
        else:
            print(f"\n[FAIL] Expected PASTA_DISH but got {output_item.item_type.value}")
    else:
        print("\n[FAIL] No output item created")

# Test 3: Incomplete ingredients (should not process)
print("\n" + "="*70)
print("TEST 3: Plating Station - Incomplete Ingredients")
print("="*70)

plating_station2 = None
for station in env.stations:
    if station.station_type == StationType.PLATING and station.line == 2:
        plating_station2 = station
        break

if plating_station2:
    print(f"\nPlating Station ID: {plating_station2.station_id}")

    # Add only 3 out of 6 ingredients
    print("\nAdding ONLY 3 ingredients (incomplete)...")
    for ingredient in recipe.ingredients[:3]:
        item = Item(
            item_type=ingredient,
            quantity=1,
            quality=1.0,
            processed=True,
            line=2
        )
        plating_station2.input_buffer.append(item)
        print(f"  Added: {ingredient.value}")

    print(f"\nInput Buffer Count: {len(plating_station2.input_buffer)}")

    # Trigger processing
    print("\nTriggering process...")
    for step in range(plating_station2.processing_time + 1):
        plating_station2.process()

    print(f"\nAfter processing:")
    print(f"  Input Buffer: {len(plating_station2.input_buffer)} items (should remain 3)")
    print(f"  Output Buffer: {len(plating_station2.output_buffer)} items (should be 0)")

    if len(plating_station2.output_buffer) == 0 and len(plating_station2.input_buffer) == 3:
        print("\n[OK] SUCCESS: Did not process with incomplete ingredients!")
    else:
        print("\n[FAIL] Should not have processed incomplete ingredients")

print("\n" + "="*70)
print("All tests completed!")
print("="*70)
