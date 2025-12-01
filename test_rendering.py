"""Test image rendering."""

import pygame
import realtimegym
from realtimegym.environments.factory.items import Item, ItemType

# Create environment
print("Creating Factory environment...")
env, seed, renderer = realtimegym.make("Factory-v0", seed=0, render=True)

# Reset environment
obs, done = env.reset()

# Check loaded images
print("\n=== Loaded Images ===")
for key, img in renderer.images.items():
    if img is not None:
        print(f"OK {key}: {img.get_size()}")
    else:
        print(f"FAIL {key}: NOT LOADED")

# Add test items
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

# Setup window
pygame.init()
screen = pygame.display.set_mode((renderer.width, renderer.height))
pygame.display.set_caption("Image Rendering Test")
clock = pygame.time.Clock()

print("\n=== Rendering Test ===")
print("Press ESC to close")

# Run for a few frames
running = True
frames = 0
while running and frames < 100:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # Step environment
    if frames % 10 == 0:
        obs, done, reward, reset = env.step("WAIT")

    # Render
    frame = renderer.render(env)
    screen.blit(frame, (0, 0))
    pygame.display.flip()
    clock.tick(30)
    frames += 1

pygame.quit()
print("\nRendering test completed")
