"""Coordinator agent prompts for factory environment."""

from pathlib import Path
from typing import Any

import yaml

# Load prompt templates from YAML
_TEMPLATE_FILE = Path(__file__).parent / "coordinator.yaml"

with open(_TEMPLATE_FILE, "r", encoding="utf-8") as f:
    _TEMPLATES = yaml.safe_load(f)

# Export prompt templates as module constants
SYSTEM_PROMPT = _TEMPLATES["system_prompt"]
TASK_ASSIGNMENT_GUIDE = _TEMPLATES["task_assignment_guide"]
OUTPUT_FORMAT = _TEMPLATES["output_format"]
ACTION_FORMAT = _TEMPLATES["action_format"]

# Action constants (JSON output expected)
ALL_ACTIONS = "JSON"  # Coordinator outputs JSON task assignments
DEFAULT_ACTION = '{"action": "continue"}'  # Default: continue current operations


def state_to_description(state_for_llm: dict[str, Any], mode: str = "reactive") -> str:
    """Convert factory state to natural language description for coordinator.

    Args:
        state_for_llm: Dictionary containing factory state
            - game_turn: Current simulation step
            - production_queue: List of products to produce
            - stations: Dict of station states
            - robots: Dict of robot states
            - kpis: Current KPI metrics
        mode: Agent mode (only "reactive" supported for coordinator)

    Returns:
        Formatted prompt string for LLM
    """
    game_turn = state_for_llm["game_turn"]
    production_queue = state_for_llm.get("production_queue", [])
    stations = state_for_llm.get("stations", {})
    robots = state_for_llm.get("robots", {})
    kpis = state_for_llm.get("kpis", {})

    # Build state description
    description = f"**Current Turn:** {game_turn}\n\n"

    # Production queue
    description += "**Production Queue:**\n"
    if production_queue:
        for product_type, quantity in production_queue:
            description += f"- {product_type}: {quantity} units\n"
    else:
        description += "- No products scheduled\n"
    description += "\n"

    # Station status
    description += "**Station Status:**\n"
    description += "| Line | Station | Status | Queue | Current Item |\n"
    description += "|------|---------|--------|-------|-------------|\n"
    for station_type, station_list in stations.items():
        for i, station in enumerate(station_list):
            line = f"Line {i}"
            status = station.get("status", "idle")
            queue_size = station.get("queue_size", 0)
            current_item = station.get("current_item", "None")
            description += f"| {line} | {station_type} | {status} | {queue_size} | {current_item} |\n"
    description += "\n"

    # Robot status
    description += "**Robot Status:**\n"
    description += "| Robot ID | Type | Position | Status | Current Task | Queue |\n"
    description += "|----------|------|----------|--------|--------------|-------|\n"
    for robot_id, robot in robots.items():
        robot_type = robot.get("type", "unknown")
        position = robot.get("position", (0, 0))
        status = robot.get("status", "idle")
        has_task = "Yes" if robot.get("has_task") else "No"
        queue_size = robot.get("queue_size", 0)
        description += (
            f"| {robot_id} | {robot_type} | {position} | "
            f"{status} | {has_task} | {queue_size} |\n"
        )
    description += "\n"

    # KPIs
    description += "**KPIs:**\n"
    description += f"- Production completed: {kpis.get('production', 0)}\n"
    description += f"- In progress: {kpis.get('in_progress', 0)}\n"
    description += f"- Robot idle ratio: {kpis.get('robot_idle_ratio', 0):.1%}\n"
    description += f"- Station idle ratio: {kpis.get('station_idle_ratio', 0):.1%}\n"
    description += "\n"

    # Assemble full prompt
    full_prompt = (
        SYSTEM_PROMPT
        + "\n\n"
        + TASK_ASSIGNMENT_GUIDE
        + "\n\n"
        + description
        + "\n"
        + OUTPUT_FORMAT
        + "\n"
        + ACTION_FORMAT
    )

    return full_prompt
