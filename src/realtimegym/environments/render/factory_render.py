"""Renderer for Factory environment."""

import os
from typing import Any

import pygame

# Image paths from public folder
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "public")


class FactoryRender:
    """Renderer for Factory environment using pygame."""

    def __init__(self, cell_size: int = 40) -> None:
        pygame.init()
        self.cell_size = cell_size
        self.grid_height = 20
        self.grid_width = 30
        self.width = self.grid_width * cell_size
        self.height = self.grid_height * cell_size
        self.screen = pygame.Surface((self.width, self.height))

        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GRAY = (200, 200, 200)
        self.LIGHT_GRAY = (240, 240, 240)
        self.DARK_GRAY = (100, 100, 100)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.ORANGE = (255, 165, 0)
        self.PURPLE = (128, 0, 128)

        # Load images
        self._load_images()

    def _load_images(self) -> None:
        """Load station images from public folder."""
        self.images: dict[str, Any] = {}

        image_files = {
            "storage": "storage.png",
            "washer": "washer.png",
            "cutter": "cutter.png",
            "cooker": "cooker.png",
            "plating": "plating.png",
            "sealing": "sealing.png",
            "visionqa": "visionQA.png",  # Match lowercase key
            "robot_arm": "robot_arm.png",
            "logistic": "logistic.png",
            "logistic_on": "logistic_on.png",
            "salad": "salad.png",
            "pasta": "pasta.png",
            "rice": "rice.png",
            "object": "object.png",
            "garbage_can": "garbage_can.png",
            "fire_extinguisher": "fire_extinguisher.png",
            "dish_container": "dish_container.png",
        }

        for key, filename in image_files.items():
            path = os.path.join(PUBLIC_DIR, filename)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path)
                    # Scale to cell size
                    img = pygame.transform.scale(img, (self.cell_size - 4, self.cell_size - 4))
                    self.images[key] = img
                except Exception as e:
                    print(f"Failed to load image {filename}: {e}")
                    self.images[key] = None
            else:
                print(f"Image not found: {path}")
                self.images[key] = None

    def render(self, env: Any) -> pygame.Surface:
        """Render the factory environment."""
        # Fill background
        self.screen.fill(self.LIGHT_GRAY)

        # Draw grid lines
        for row in range(self.grid_height + 1):
            y = row * self.cell_size
            pygame.draw.line(self.screen, self.GRAY, (0, y), (self.width, y), 1)

        for col in range(self.grid_width + 1):
            x = col * self.cell_size
            pygame.draw.line(self.screen, self.GRAY, (x, 0), (x, self.height), 1)

        # Draw line separator (middle vertical line between columns 14 and 15)
        separator_x = 15 * self.cell_size
        pygame.draw.line(self.screen, self.DARK_GRAY, (separator_x, 0), (separator_x, self.height), 3)

        # Draw line labels
        font = pygame.font.Font(None, 28)
        line1_text = font.render("LINE 1", True, self.DARK_GRAY)
        line2_text = font.render("LINE 2", True, self.DARK_GRAY)
        self.screen.blit(line1_text, (5 * self.cell_size, 2))
        self.screen.blit(line2_text, (20 * self.cell_size, 2))

        # Draw stations
        for station in env.stations:
            row, col = station.position
            x = col * self.cell_size
            y = row * self.cell_size

            # Draw station cell background
            status_color = self._get_status_color(station.status.value)
            pygame.draw.rect(
                self.screen,
                status_color,
                (x + 1, y + 1, self.cell_size - 2, self.cell_size - 2),
            )

            # Draw station image
            station_type = station.station_type.value.lower()
            if station_type in self.images and self.images[station_type]:
                self.screen.blit(self.images[station_type], (x + 2, y + 2))
            else:
                # Draw text as fallback
                font = pygame.font.Font(None, 20)
                text = font.render(station_type[:4], True, self.BLACK)
                text_rect = text.get_rect(center=(x + self.cell_size // 2, y + self.cell_size // 2))
                self.screen.blit(text, text_rect)

            # Draw progress bar if busy
            if station.status.value == "Busy" and station.processing_time > 0:
                progress = station.current_progress / station.processing_time
                bar_width = int((self.cell_size - 8) * progress)
                pygame.draw.rect(
                    self.screen,
                    self.GREEN,
                    (x + 4, y + self.cell_size - 8, bar_width, 4),
                )

        # Draw robot arms
        for robot in env.robot_arms:
            row, col = robot.position
            x = col * self.cell_size + self.cell_size // 4
            y = row * self.cell_size + self.cell_size // 4
            size = self.cell_size // 2

            if robot.status.value == "Operating":
                color = self.ORANGE
            elif robot.status.value == "Error":
                color = self.RED
            else:
                color = self.BLUE

            pygame.draw.circle(self.screen, color, (x + size // 2, y + size // 2), size // 3)

        # Draw logistic robots
        for robot in env.logistic_robots:
            row, col = robot.position
            size = 16  # Increased size for better visibility
            x = col * self.cell_size + (self.cell_size - size) // 2
            y = row * self.cell_size + (self.cell_size - size) // 2

            # Reserve robots shown in gray
            if not robot.is_active:
                pygame.draw.rect(self.screen, (150, 150, 150), (x, y, size, size))
                # Draw small "R" for reserve
                font = pygame.font.Font(None, 12)
                text = font.render("R", True, self.WHITE)
                text_rect = text.get_rect(center=(x + size // 2, y + size // 2))
                self.screen.blit(text, text_rect)
            elif robot.carrying_item:
                # Draw with item
                if "logistic_on" in self.images and self.images["logistic_on"]:
                    img = pygame.transform.scale(self.images["logistic_on"], (size, size))
                    self.screen.blit(img, (x, y))
                else:
                    pygame.draw.rect(self.screen, self.YELLOW, (x, y, size, size))
            else:
                # Draw empty
                if "logistic" in self.images and self.images["logistic"]:
                    img = pygame.transform.scale(self.images["logistic"], (size, size))
                    self.screen.blit(img, (x, y))
                else:
                    pygame.draw.rect(self.screen, self.GREEN, (x, y, size, size))

        # Draw info text
        font = pygame.font.Font(None, 24)
        info_text = f"Turn: {env.game_turn} | Completed: {env.completed_products}/{env.target_products} | Defects: {env.defective_products}"
        text = font.render(info_text, True, self.BLACK)
        # Draw on white background
        text_rect = text.get_rect()
        text_rect.topleft = (5, 5)
        pygame.draw.rect(self.screen, self.WHITE, text_rect.inflate(10, 5))
        self.screen.blit(text, text_rect)

        return self.screen.copy()

    def _get_status_color(self, status: str) -> tuple[int, int, int]:
        """Get color for station status."""
        if status == "Idle":
            return self.WHITE
        elif status == "Busy":
            return (200, 255, 200)  # Light green
        elif status == "Waiting":
            return (255, 255, 200)  # Light yellow
        elif status == "Error":
            return (255, 200, 200)  # Light red
        elif status == "Down":
            return self.DARK_GRAY
        else:
            return self.LIGHT_GRAY
