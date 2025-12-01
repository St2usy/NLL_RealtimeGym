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
screen = pygame.display.set_mode((renderer.width, renderer.height + 150))
pygame.display.set_caption("Factory Simulation - Salad Production")
clock = pygame.time.Clock()

# Font for messages
font = pygame.font.Font(None, 24)


def start_production_batch():
    """Start a new production batch by creating initial items."""
    if env.completed_products >= env.target_products:
        return False

    # Add items to all washers that have space
    added = False
    for station in env.stations:
        if station.station_type.value == "Washer" and len(station.input_buffer) < 3:
            # Create lettuce item to start production
            item = Item(
                item_type=ItemType.LETTUCE,
                quantity=1,
                quality=1.0,
                processed=False
            )
            station.input_buffer.append(item)
            added = True

    return added


def auto_transport_items():
    """Automatically transport items between stations."""
    # Simple rule: transport to next station type in sequence
    station_sequence = ["Washer", "Cutter", "Plating", "Sealing", "VisionQA", "Storage"]

    # For salad recipe, we skip Cooker (no cooking needed)
    for station in env.stations:
        if station.station_type.value == "Storage":
            continue

        # If station has output, find next station
        while len(station.output_buffer) > 0:
            try:
                current_idx = station_sequence.index(station.station_type.value)
                if current_idx < len(station_sequence) - 1:
                    next_type = station_sequence[current_idx + 1]

                    # Find next station of this type with space
                    next_station = None
                    for s in env.stations:
                        if s.station_type.value == next_type and len(s.input_buffer) < s.buffer_capacity:
                            # For storage, only use output storage (bottom one)
                            if next_type == "Storage" and s.position[0] != 15:
                                continue
                            next_station = s
                            break

                    # Transport item
                    if next_station:
                        item = station.output_buffer.pop(0)
                        next_station.input_buffer.append(item)
                    else:
                        break  # No space, stop processing this station
                else:
                    break
            except ValueError:
                break


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
            # Start production every 5 steps to keep pipeline full
            if step_count % 5 == 0:
                start_production_batch()

            # Step environment first (processes stations)
            obs, done, reward, reset = env.step("WAIT")
            step_count += 1

            # Auto transport between stations after processing
            auto_transport_items()

            # Check for completed items in final storage
            for station in env.stations:
                if station.station_type.value == "Storage" and station.position[0] == 15:
                    # Move items from input buffer to completed
                    while len(station.input_buffer) > 0:
                        item = station.input_buffer.pop(0)
                        if item.item_type != ItemType.DEFECTIVE:
                            env.completed_products += 1
                            print(f"Product completed! Total: {env.completed_products}/{env.target_products}")
                        else:
                            env.defective_products += 1
                            print(f"Defective product detected! Total defects: {env.defective_products}")

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

    # Station status summary
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

    # Controls info
    controls_text = font.render(
        "SPACE: Speed Up | DOWN: Slow Down | P: Pause | ESC: Quit",
        True,
        (100, 100, 100)
    )
    screen.blit(controls_text, (bar_x, status_y + 50))

    pygame.display.flip()
    clock.tick(30)  # 30 FPS

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
