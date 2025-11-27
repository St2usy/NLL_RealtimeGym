"""Image-based visualization renderer for Factory environment using PNG assets."""

from pathlib import Path
from typing import TYPE_CHECKING
from PIL import Image, ImageDraw, ImageFont
import io

if TYPE_CHECKING:
    from .factory_env import FactoryEnv


class FactoryImageRenderer:
    """Renderer for visualizing factory environment using PNG images."""

    def __init__(self, env: "FactoryEnv", assets_dir: str | Path = "public"):
        self.env = env
        self.assets_dir = Path(assets_dir)

        # Grid settings
        self.cell_size = 48  # pixels per grid cell
        self.grid_width = env.width
        self.grid_height = env.height

        # Calculate canvas size
        self.canvas_width = self.grid_width * self.cell_size
        self.canvas_height = self.grid_height * self.cell_size + 100  # +100 for status bar

        # Load all PNG assets
        self.images = self._load_images()

        # Track work items for visualization
        self.work_item_positions = {}  # work_item_id -> (x, y, current_station_type)

        # Animation frames
        self.frames = []

    def _load_images(self) -> dict:
        """Load all PNG assets from the assets directory."""
        images = {}

        # Station images
        station_files = {
            "Storage": "storage.png",
            "Washer": "washer.png",
            "Cutter": "cutter.png",
            "Cooker": "cooker.png",
            "Plating": "plating.png",
            "Sealing": "sealing.png",
            "VisionQA": "visionQA.png",
            "FinalStorage": "storage.png",
        }

        for station_type, filename in station_files.items():
            path = self.assets_dir / filename
            if path.exists():
                img = Image.open(path).convert("RGBA")
                # Resize to fit in cell
                img = img.resize((self.cell_size - 4, self.cell_size - 4), Image.Resampling.LANCZOS)
                images[station_type] = img

        # Robot images
        robot_files = {
            "robot_arm": "robot_arm.png",
            "logistics": "logistic.png",
            "logistics_carrying": "logistic_on.png",
        }

        for robot_type, filename in robot_files.items():
            path = self.assets_dir / filename
            if path.exists():
                img = Image.open(path).convert("RGBA")
                # Resize to smaller size for robots
                img = img.resize((int(self.cell_size * 0.6), int(self.cell_size * 0.6)), Image.Resampling.LANCZOS)
                images[robot_type] = img

        # Work item image
        object_path = self.assets_dir / "object.png"
        if object_path.exists():
            img = Image.open(object_path).convert("RGBA")
            img = img.resize((int(self.cell_size * 0.5), int(self.cell_size * 0.5)), Image.Resampling.LANCZOS)
            images["object"] = img

        # Product images
        product_files = {
            "ricotta_salad": "salad.png",
            "shrimp_fried_rice": "rice.png",
            "tomato_pasta": "pasta.png",
        }

        for product_type, filename in product_files.items():
            path = self.assets_dir / filename
            if path.exists():
                img = Image.open(path).convert("RGBA")
                img = img.resize((int(self.cell_size * 0.4), int(self.cell_size * 0.4)), Image.Resampling.LANCZOS)
                images[product_type] = img

        # Sub-station images
        substation_files = {
            "dish_container": "dish_container.png",
            "garbage_can": "garbage_can.png",
        }

        for substation_type, filename in substation_files.items():
            path = self.assets_dir / filename
            if path.exists():
                img = Image.open(path).convert("RGBA")
                img = img.resize((int(self.cell_size * 0.7), int(self.cell_size * 0.7)), Image.Resampling.LANCZOS)
                images[substation_type] = img

        return images

    def _grid_to_pixel(self, x: int, y: int) -> tuple[int, int]:
        """Convert grid coordinates to pixel coordinates (top-left of cell)."""
        return (x * self.cell_size, y * self.cell_size)

    def _grid_to_pixel_center(self, x: int, y: int) -> tuple[int, int]:
        """Convert grid coordinates to pixel coordinates (center of cell)."""
        return (
            x * self.cell_size + self.cell_size // 2,
            y * self.cell_size + self.cell_size // 2
        )

    def render_frame(self) -> Image.Image:
        """Render current state of factory as a PIL Image."""
        # Create base canvas
        canvas = Image.new("RGB", (self.canvas_width, self.canvas_height), color="white")
        draw = ImageDraw.Draw(canvas)

        # Draw grid lines
        for x in range(self.grid_width + 1):
            px = x * self.cell_size
            draw.line([(px, 0), (px, self.grid_height * self.cell_size)], fill="lightgray", width=1)

        for y in range(self.grid_height + 1):
            py = y * self.cell_size
            draw.line([(0, py), (self.grid_width * self.cell_size, py)], fill="lightgray", width=1)

        # Draw production line separators
        line_width = self.grid_width // self.env.num_lines
        for i in range(1, self.env.num_lines):
            x_sep = i * line_width * self.cell_size
            draw.line([(x_sep, 0), (x_sep, self.grid_height * self.cell_size)],
                     fill="darkgray", width=3)

        # Draw stations
        self._draw_stations(canvas, draw)

        # Draw sub-stations (dish_container, garbage_can)
        self._draw_substations(canvas, draw)

        # Draw work items in stations
        self._draw_work_items(canvas, draw)

        # Draw robots
        self._draw_robots(canvas, draw)

        # Draw status bar
        self._draw_status_bar(canvas, draw)

        return canvas

    def _draw_stations(self, canvas: Image.Image, draw: ImageDraw.Draw):
        """Draw all stations on the canvas."""
        for station_type, station_list in self.env.stations.items():
            for station in station_list:
                x, y = station.position
                px, py = self._grid_to_pixel(x, y)

                # Draw station background based on status
                status_colors = {
                    "idle": "#F0F0F0",
                    "processing": "#C8E6C9",
                    "waiting_pickup": "#FFF9C4",
                    "error": "#FFCDD2",
                    "maintenance": "#E0E0E0",
                }
                bg_color = status_colors.get(station.status.value, "#F0F0F0")
                draw.rectangle([px + 2, py + 2, px + self.cell_size - 2, py + self.cell_size - 2],
                             fill=bg_color, outline="black", width=2)

                # Draw station image
                if station_type in self.images:
                    img = self.images[station_type]
                    # Center the image in the cell
                    img_x = px + (self.cell_size - img.width) // 2
                    img_y = py + (self.cell_size - img.height) // 2
                    canvas.paste(img, (img_x, img_y), img)

                # Draw queue indicator
                if len(station.queue) > 0:
                    queue_text = f"Q:{len(station.queue)}"
                    draw.text((px + 4, py + 4), queue_text, fill="blue", font=None)

                # Draw output buffer indicator
                if len(station.output_buffer) > 0:
                    output_text = f"O:{len(station.output_buffer)}"
                    draw.text((px + 4, py + self.cell_size - 14), output_text, fill="green", font=None)

    def _draw_substations(self, canvas: Image.Image, draw: ImageDraw.Draw):
        """Draw sub-stations (dish_container, garbage_can)."""
        # Draw dish_containers for Plating stations
        if "Plating" in self.env.stations:
            for station in self.env.stations["Plating"]:
                if hasattr(station, "dish_container_positions"):
                    for container_x, container_y in station.dish_container_positions:
                        px_center, py_center = self._grid_to_pixel_center(container_x, container_y)

                        if "dish_container" in self.images:
                            # Use PNG image
                            img = self.images["dish_container"]
                            img_x = px_center - img.width // 2
                            img_y = py_center - img.height // 2
                            canvas.paste(img, (img_x, img_y), img)
                        else:
                            # Fallback: colored rectangle
                            px, py = self._grid_to_pixel(container_x, container_y)
                            draw.rectangle(
                                [px + 8, py + 8, px + self.cell_size - 8, py + self.cell_size - 8],
                                fill="#ADD8E6",
                                outline="#4682B4",
                                width=2
                            )

        # Draw garbage_cans for VisionQA stations
        if "VisionQA" in self.env.stations:
            for station in self.env.stations["VisionQA"]:
                if hasattr(station, "garbage_can_positions"):
                    for gc_x, gc_y in station.garbage_can_positions:
                        px_center, py_center = self._grid_to_pixel_center(gc_x, gc_y)

                        if "garbage_can" in self.images:
                            # Use PNG image
                            img = self.images["garbage_can"]
                            img_x = px_center - img.width // 2
                            img_y = py_center - img.height // 2
                            canvas.paste(img, (img_x, img_y), img)
                        else:
                            # Fallback: colored rectangle
                            px, py = self._grid_to_pixel(gc_x, gc_y)
                            draw.rectangle(
                                [px + 8, py + 8, px + self.cell_size - 8, py + self.cell_size - 8],
                                fill="#808080",
                                outline="#404040",
                                width=2
                            )

    def _draw_work_items(self, canvas: Image.Image, draw: ImageDraw.Draw):
        """Draw work items being processed in stations."""
        for station_type, station_list in self.env.stations.items():
            for station in station_list:
                x, y = station.position

                # Draw current work item being processed
                if station.current_work is not None:
                    work_item = station.current_work

                    # Draw product-specific image if available, otherwise use generic object
                    img_key = work_item.product_type if work_item.product_type in self.images else "object"
                    if img_key in self.images:
                        img = self.images[img_key]
                        px_center, py_center = self._grid_to_pixel_center(x, y)
                        img_x = px_center - img.width // 2
                        img_y = py_center - img.height // 2
                        canvas.paste(img, (img_x, img_y), img)

                    # Track position for animation
                    self.work_item_positions[work_item.product_id] = (x, y, station_type)

    def _draw_robots(self, canvas: Image.Image, draw: ImageDraw.Draw):
        """Draw all robots on the canvas."""
        # Draw robot arms
        for robot in self.env.robot_arms:
            x, y = robot.position
            px_center, py_center = self._grid_to_pixel_center(x, y)

            if "robot_arm" in self.images:
                img = self.images["robot_arm"]
                img_x = px_center - img.width // 2
                img_y = py_center - img.height // 2
                canvas.paste(img, (img_x, img_y), img)
            else:
                # Fallback: draw circle
                draw.ellipse([px_center - 10, py_center - 10, px_center + 10, py_center + 10],
                           fill="red", outline="darkred", width=2)

        # Draw logistics robots
        for robot in self.env.logistics_robots:
            x, y = robot.position
            px_center, py_center = self._grid_to_pixel_center(x, y)

            # Use different image based on carrying status
            img_key = "logistics_carrying" if robot.carrying else "logistics"

            if img_key in self.images:
                img = self.images[img_key]
                img_x = px_center - img.width // 2
                img_y = py_center - img.height // 2
                canvas.paste(img, (img_x, img_y), img)
            else:
                # Fallback: draw square
                color = "green" if robot.carrying else "cyan"
                draw.rectangle([px_center - 8, py_center - 8, px_center + 8, py_center + 8],
                             fill=color, outline="black", width=2)

    def _draw_status_bar(self, canvas: Image.Image, draw: ImageDraw.Draw):
        """Draw status bar at the bottom."""
        status_y = self.grid_height * self.cell_size

        # Background for status bar
        draw.rectangle([0, status_y, self.canvas_width, self.canvas_height],
                      fill="lightblue", outline="black", width=2)

        # Status text
        status_text = [
            f"Turn: {self.env.game_turn}",
            f"In Progress: {len(self.env.products_in_progress)}",
            f"Completed: {len(self.env.completed_products)}",
            f"Rejected: {self.env.rejected_products}",
            f"Reward: {self.env.reward:.1f}",
        ]

        text_x = 10
        text_y = status_y + 10

        for line in status_text:
            draw.text((text_x, text_y), line, fill="black", font=None)
            text_y += 20

    def capture_frame(self):
        """Capture current state as a frame for animation."""
        frame = self.render_frame()
        self.frames.append(frame)

    def save_gif(self, filepath: str, duration: int = 500, loop: int = 0):
        """Save captured frames as an animated GIF.

        Args:
            filepath: Output path for the GIF file
            duration: Duration of each frame in milliseconds
            loop: Number of times to loop (0 = infinite)
        """
        if not self.frames:
            print("No frames to save!")
            return

        # Save as GIF
        self.frames[0].save(
            filepath,
            save_all=True,
            append_images=self.frames[1:],
            duration=duration,
            loop=loop,
            optimize=False
        )
        print(f"GIF saved to {filepath} ({len(self.frames)} frames)")

    def save_frame(self, filepath: str):
        """Save current state as a single PNG image."""
        frame = self.render_frame()
        frame.save(filepath)
        print(f"Frame saved to {filepath}")

    def clear_frames(self):
        """Clear all captured frames."""
        self.frames = []

    def create_animation(
        self,
        num_steps: int = 100,
        actions: list[str] | None = None,
        output_path: str = "factory_animation.gif",
        frame_duration: int = 300,
        products_per_cycle: int = 3
    ):
        """Create an animation of factory operation.

        Args:
            num_steps: Number of simulation steps to run
            actions: List of actions to execute (if None, uses auto actions)
            output_path: Path to save the GIF
            frame_duration: Duration of each frame in milliseconds
            products_per_cycle: Number of products to spawn per cycle
        """
        print(f"Creating animation with {num_steps} steps...")

        # Reset and capture initial state
        self.env.reset()
        self.capture_frame()

        # Prepare actions
        if actions is None:
            # Auto-generate actions: spawn products periodically
            actions = []
            product_types = ["ricotta_salad", "shrimp_fried_rice", "tomato_pasta"]

            for step in range(num_steps):
                # Spawn products every 5 steps, cycling through types
                if step % 5 == 0 and step < 50:  # Spawn for first 50 steps
                    product_idx = (step // 5) % len(product_types)
                    actions.append(f"produce_{product_types[product_idx]}")
                else:
                    actions.append("continue")

        # Run simulation and capture frames
        for step in range(min(num_steps, len(actions))):
            action = actions[step]

            # Step environment
            obs, done, reward, reset = self.env.step(action)

            # Capture frame every step
            self.capture_frame()

            if step % 10 == 0:
                print(f"  Step {step}/{num_steps}: {action}, Reward: {reward:.1f}")

            if done:
                break

        # Save as GIF
        print(f"Saving animation...")
        self.save_gif(output_path, duration=frame_duration)

        return output_path
