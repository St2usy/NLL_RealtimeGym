"""Create a static diagram showing the logistics lane layout."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PIL import Image, ImageDraw, ImageFont


def create_lanes_diagram():
    """Create a clear diagram of the logistics lane system."""
    # Canvas size
    width = 1200
    height = 1600

    canvas = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(canvas)

    # Try to load a font, fallback to default if not available
    try:
        title_font = ImageFont.truetype("arial.ttf", 32)
        header_font = ImageFont.truetype("arial.ttf", 24)
        normal_font = ImageFont.truetype("arial.ttf", 18)
    except:
        title_font = None
        header_font = None
        normal_font = None

    # Title
    title = "Factory Logistics Lane System"
    draw.text((width//2 - 200, 30), title, fill="black", font=title_font)

    # Draw lanes
    lane_start_x = 150
    lane_width = 180
    lane_height = 1200
    lane_start_y = 150

    lane_colors = ["#FFE6E6", "#E6F3FF", "#E6FFE6", "#FFF9E6", "#F0E6FF"]
    lane_names = ["Lane 1 (x=2)", "Lane 2 (x=3)", "Lane 3 (x=4)", "Lane 4 (x=5)", "Lane 5 (x=6)"]

    # Draw each lane
    for i in range(5):
        x = lane_start_x + i * lane_width

        # Draw lane rectangle
        draw.rectangle(
            [x, lane_start_y, x + lane_width - 20, lane_start_y + lane_height],
            fill=lane_colors[i],
            outline="black",
            width=3
        )

        # Lane label
        draw.text((x + 10, lane_start_y + 10), lane_names[i], fill="black", font=header_font)

    # Station Y-positions (relative to lane_start_y)
    stations = {
        "Storage": 50,
        "Washer": 200,
        "Cutter": 400,
        "Cooker": 600,
        "Plating": 800,
        "Sealing": 900,
        "VisionQA": 1000,
        "FinalStorage": 1100,
    }

    # Draw stations on the right side
    station_x = lane_start_x + 5 * lane_width + 20
    draw.text((station_x, lane_start_y - 30), "Stations:", fill="black", font=header_font)

    for station_name, y_offset in stations.items():
        y = lane_start_y + y_offset
        # Draw station marker
        draw.rectangle([station_x, y - 10, station_x + 120, y + 20],
                      fill="#D0D0D0", outline="black", width=2)
        draw.text((station_x + 5, y - 5), station_name, fill="black", font=normal_font)

    # Draw logistics robots and their routes
    robots = [
        # (lane_idx, robot_id, start_station, end_station, color)
        (2, "ID=0", "Storage", "Washer", "blue"),
        (1, "ID=1", "Washer", "Cutter", "green"),
        (3, "ID=2", "Washer", "Cutter", "green"),
        (1, "ID=3", "Cutter", "Cooker", "orange"),
        (3, "ID=4", "Cutter", "Cooker", "orange"),
        (0, "ID=5", "Cooker", "FinalStorage", "red"),
        (4, "ID=6", "Cooker", "FinalStorage", "red"),
        (2, "ID=7", "VisionQA", "FinalStorage", "purple"),
    ]

    for lane_idx, robot_id, start_station, end_station, color in robots:
        x = lane_start_x + lane_idx * lane_width + lane_width//2 - 10

        start_y = lane_start_y + stations[start_station]
        end_y = lane_start_y + stations[end_station]

        # Draw route line
        draw.line([(x, start_y), (x, end_y)], fill=color, width=4)

        # Draw robot marker (circle)
        mid_y = (start_y + end_y) // 2
        draw.ellipse([x - 15, mid_y - 15, x + 15, mid_y + 15],
                    fill=color, outline="black", width=2)

        # Draw robot ID
        draw.text((x - 12, mid_y - 8), robot_id.split("=")[1], fill="white", font=normal_font)

        # Draw route text
        route_text = f"{robot_id}"
        text_y = mid_y + 25
        draw.text((x - 20, text_y), route_text, fill="black", font=normal_font)

    # Legend
    legend_y = lane_start_y + lane_height + 50
    draw.text((50, legend_y), "Legend:", fill="black", font=header_font)

    legend_items = [
        ("ID=0: Storage ↔ Washer (Lane 3)", "blue"),
        ("ID=1: Washer ↔ Cutter (Lane 2)", "green"),
        ("ID=2: Washer ↔ Cutter (Lane 4)", "green"),
        ("ID=3: Cutter ↔ Cooker (Lane 2)", "orange"),
        ("ID=4: Cutter ↔ Cooker (Lane 4)", "orange"),
        ("ID=5: Cooker → Lower Stations (Lane 1)", "red"),
        ("ID=6: Cooker → Lower Stations (Lane 5)", "red"),
        ("ID=7: VisionQA ↔ FinalStorage (Lane 3)", "purple"),
    ]

    legend_y += 40
    for i, (text, color) in enumerate(legend_items):
        y = legend_y + i * 30
        # Draw color box
        draw.rectangle([50, y, 80, y + 20], fill=color, outline="black", width=1)
        # Draw text
        draw.text((90, y), text, fill="black", font=normal_font)

    # Save diagram
    output_path = "factory_lanes_diagram.png"
    canvas.save(output_path)
    print(f"[OK] Lane diagram saved to: {output_path}")

    return output_path


if __name__ == "__main__":
    print("Creating logistics lane diagram...")
    output_path = create_lanes_diagram()
    print(f"[OK] Diagram created successfully!")
    print(f"[OK] This shows the 5 lanes and 8 logistics robots with their routes")
