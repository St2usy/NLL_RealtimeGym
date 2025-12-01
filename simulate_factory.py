"""Visualize Factory environment simulation with automatic production."""

import sys
import time

import pygame

import realtimegym
from realtimegym.environments.factory import RecipeType
from realtimegym.environments.factory.items import Item, ItemType

# Create environment
print("Creating Factory environment...")
env, seed, renderer = realtimegym.make("Factory-v0", seed=0, render=True)

# Reset environment
obs, done = env.reset()
print(f"Environment initialized. Target: {env.target_products} products")

# Setup pygame window
pygame.init()
screen = pygame.display.set_mode((renderer.width, renderer.height + 230))  # Increased for ingredient info
pygame.display.set_caption(f"Factory Simulation - {env.current_recipe.value.upper()} Production")
clock = pygame.time.Clock()

# Font for messages
font = pygame.font.Font(None, 24)


def start_production_batch():
    """Start a new production batch with ALL required recipe ingredients."""
    if env.completed_products >= env.target_products:
        return False

    # Get current recipe ingredients
    from realtimegym.environments.factory import RECIPES
    recipe = RECIPES[env.current_recipe]
    required_ingredients = recipe.ingredients

    added = False

    # For each production line, add a complete set of ingredients to Washer
    for station in env.stations:
        if station.station_type.value == "Washer" and len(station.input_buffer) < 2:
            # Add ALL required ingredients for one batch
            for ingredient in required_ingredients:
                item = Item(
                    item_type=ingredient,
                    quantity=1,
                    quality=1.0,
                    processed=False,
                    line=station.line
                )
                station.input_buffer.append(item)
                added = True

            # Only add to one washer per call to control production rate
            break

    return added


# Logistic robots now handle transport automatically via environment
# No manual transport needed


# Main simulation loop
running = True
step_count = 0
production_started = False

print("\nStarting simulation...")
print("Press SPACE to speed up, ESC to quit\n")

speed = 1  # Steps per frame
paused = False

while running and not done:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                speed = min(speed * 2, 32)
                print(f"Speed: {speed}x")
            elif event.key == pygame.K_DOWN:
                speed = max(speed // 2, 1)
                print(f"Speed: {speed}x")
            elif event.key == pygame.K_p:
                paused = not paused
                print("Paused" if paused else "Resumed")

    if not paused:
        for _ in range(speed):
            # Start production every 20 steps to allow ingredients to combine
            # (need time for all 6 ingredients to reach Plating)
            if step_count % 20 == 0:
                start_production_batch()

            # Step environment (processes stations and robots)
            obs, done, reward, reset = env.step("WAIT")
            step_count += 1

            # Check for completed items in final storage
            for station in env.stations:
                if station.station_type.value == "Storage" and station.position[0] == 19:
                    # Move items from input buffer to completed
                    while len(station.input_buffer) > 0:
                        item = station.input_buffer.pop(0)
                        if item.item_type != ItemType.DEFECTIVE:
                            env.completed_products += 1
                            print(f"[Line {item.line}] Product completed! Total: {env.completed_products}/{env.target_products}")
                        else:
                            env.defective_products += 1
                            print(f"[Line {item.line}] Defective product! Total defects: {env.defective_products}")

            if done:
                break

    # Render
    frame = renderer.render(env)
    screen.blit(frame, (0, 0))

    # Draw additional info
    info_y = renderer.height + 10

    # Progress bar
    progress = env.completed_products / env.target_products
    bar_width = 600
    bar_height = 30
    bar_x = 50
    bar_y = info_y + 10

    pygame.draw.rect(screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, int(bar_width * progress), bar_height))
    pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 2)

    # Progress text
    progress_text = font.render(
        f"Progress: {env.completed_products}/{env.target_products} ({progress*100:.1f}%)",
        True,
        (0, 0, 0)
    )
    screen.blit(progress_text, (bar_x + bar_width + 20, bar_y + 5))

    # Quality info
    total = env.completed_products + env.defective_products
    quality_rate = (env.completed_products / total * 100) if total > 0 else 100
    quality_text = font.render(
        f"Quality: {quality_rate:.1f}% | Defects: {env.defective_products} | Speed: {speed}x",
        True,
        (0, 0, 0)
    )
    screen.blit(quality_text, (bar_x, bar_y + 40))

    # Station status summary with ingredient tracking
    station_types = ["Washer", "Cutter", "Plating", "Sealing", "VisionQA"]
    status_y = bar_y + 65
    small_font = pygame.font.Font(None, 18)

    for i, st_type in enumerate(station_types):
        stations_of_type = [s for s in env.stations if s.station_type.value == st_type]
        if stations_of_type:
            busy_count = sum(1 for s in stations_of_type if s.status.value == "Busy")
            in_count = sum(len(s.input_buffer) for s in stations_of_type)
            out_count = sum(len(s.output_buffer) for s in stations_of_type)

            status = f"{st_type}: {busy_count}/{len(stations_of_type)} busy | In:{in_count} Out:{out_count}"
            color = (0, 150, 0) if busy_count > 0 else (100, 100, 100)
            text = small_font.render(status, True, color)
            screen.blit(text, (bar_x + (i % 3) * 300, status_y + (i // 3) * 20))

    # Show Plating station ingredient details (recipe combination info)
    plating_y = status_y + 45
    from realtimegym.environments.factory import RECIPES
    recipe = RECIPES[env.current_recipe]

    # Recipe info
    recipe_text = font.render(f"Recipe: {env.current_recipe.value.upper()}", True, (50, 50, 150))
    screen.blit(recipe_text, (bar_x, plating_y))

    # Show required ingredients
    ingredients_text = small_font.render(
        f"Required: {', '.join([ing.value for ing in recipe.ingredients])}",
        True,
        (80, 80, 80)
    )
    screen.blit(ingredients_text, (bar_x, plating_y + 25))

    # Show Plating station ingredient status
    plating_stations = [s for s in env.stations if s.station_type.value == "Plating"]
    if plating_stations:
        plating = plating_stations[0]
        available_types = [item.item_type for item in plating.input_buffer]
        has_all = all(ing in available_types for ing in recipe.ingredients)

        status_color = (0, 150, 0) if has_all else (150, 100, 0)
        status_msg = "Ready to combine!" if has_all else f"Waiting ({len(plating.input_buffer)}/{len(recipe.ingredients)} ingredients)"

        plating_status = small_font.render(
            f"Plating Status: {status_msg}",
            True,
            status_color
        )
        screen.blit(plating_status, (bar_x, plating_y + 45))

    # Controls info
    controls_text = font.render(
        "SPACE: Speed Up | DOWN: Slow Down | P: Pause | ESC: Quit",
        True,
        (100, 100, 100)
    )
    screen.blit(controls_text, (bar_x, plating_y + 70))

    pygame.display.flip()
    clock.tick(10)  # 10 FPS (slower = lower number)

# Final results
print("\n" + "="*50)
print("SIMULATION COMPLETE")
print("="*50)
print(f"Total Steps: {step_count}")
print(f"Completed Products: {env.completed_products}/{env.target_products}")
print(f"Defective Products: {env.defective_products}")
total = env.completed_products + env.defective_products
if total > 0:
    print(f"Quality Rate: {env.completed_products/total*100:.1f}%")
print(f"Final Reward: {env.reward:.2f}")
print("="*50)

# Wait a bit before closing
time.sleep(2)
pygame.quit()
sys.exit()
