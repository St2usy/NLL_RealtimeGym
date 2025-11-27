"""PartDesign agent prompts for factory environment."""

from pathlib import Path
from typing import Any

import yaml

# Load prompt templates from YAML
_TEMPLATE_FILE = Path(__file__).parent / "part_design.yaml"

with open(_TEMPLATE_FILE, "r", encoding="utf-8") as f:
    _TEMPLATES = yaml.safe_load(f)

# Export prompt templates as module constants
SYSTEM_PROMPT = _TEMPLATES["system_prompt"]
PLANNING_GUIDE = _TEMPLATES["planning_guide"]
OUTPUT_FORMAT = _TEMPLATES["output_format"]
ACTION_FORMAT = _TEMPLATES["action_format"]

# Action constants
ALL_ACTIONS = "JSON"
DEFAULT_ACTION = '{"action": "skip"}'


def state_to_description(state_for_llm: dict[str, Any], mode: str = "reactive") -> str:
    """Convert factory state to natural language description for part design agent.

    Args:
        state_for_llm: Dictionary containing factory state
            - product_request: Product type and quantity to produce
            - stations: Dict of station states (availability, capacity, queue)
            - robots: Robot availability statistics
            - maintenance_risk: Risk scores from maintenance agent
            - quality_metrics: Recent defect rates from quality agent
        mode: Agent mode (only "reactive" supported)

    Returns:
        Formatted prompt string for LLM
    """
    product_request = state_for_llm.get("product_request", {})
    stations = state_for_llm.get("stations", {})
    robots = state_for_llm.get("robots", {})
    maintenance_risk = state_for_llm.get("maintenance_risk", {})
    quality_metrics = state_for_llm.get("quality_metrics", {})

    # Build state description
    description = "**Production Request:**\n"
    description += f"- Product: {product_request.get('product_type', 'N/A')}\n"
    description += f"- Quantity: {product_request.get('quantity', 0)}\n"
    description += f"- Priority: {product_request.get('priority', 'normal')}\n\n"

    # Station availability
    description += "**Station Status:**\n"
    description += "| Line | Station | Status | Capacity | Queue | Risk |\n"
    description += "|------|---------|--------|----------|-------|------|\n"
    for station_type, station_list in stations.items():
        for i, station in enumerate(station_list):
            line = f"Line {i}"
            status = station.get("status", "unknown")
            capacity = station.get("capacity", "N/A")
            queue_size = station.get("queue_size", 0)
            risk = maintenance_risk.get(f"{station_type}_{i}", "Low")
            description += (
                f"| {line} | {station_type} | {status} | "
                f"{capacity} | {queue_size} | {risk} |\n"
            )
    description += "\n"

    # Robot availability
    description += "**Robot Availability:**\n"
    description += f"- Total robots: {robots.get('total', 44)}\n"
    description += f"- Idle robots: {robots.get('idle', 0)} ({robots.get('idle_ratio', 0):.1%})\n"
    description += f"- Robot arms idle: {robots.get('arms_idle', 0)}\n"
    description += f"- Logistics idle: {robots.get('logistics_idle', 0)}\n\n"

    # Quality metrics
    description += "**Recent Quality Metrics:**\n"
    for product_type, metrics in quality_metrics.items():
        description += f"- {product_type}: Defect rate {metrics.get('defect_rate', 0):.1%}\n"
    description += "\n"

    # Assemble full prompt
    full_prompt = (
        SYSTEM_PROMPT
        + "\n\n"
        + PLANNING_GUIDE
        + "\n\n"
        + description
        + "\n"
        + OUTPUT_FORMAT
        + "\n"
        + ACTION_FORMAT
    )

    return full_prompt
