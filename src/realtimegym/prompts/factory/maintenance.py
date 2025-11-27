"""MaintenanceAgent prompts for factory environment."""

from pathlib import Path
from typing import Any

import yaml

# Load prompt templates from YAML
_TEMPLATE_FILE = Path(__file__).parent / "maintenance.yaml"

with open(_TEMPLATE_FILE, "r", encoding="utf-8") as f:
    _TEMPLATES = yaml.safe_load(f)

# Export prompt templates as module constants
SYSTEM_PROMPT = _TEMPLATES["system_prompt"]
MAINTENANCE_GUIDE = _TEMPLATES["maintenance_guide"]
OUTPUT_FORMAT = _TEMPLATES["output_format"]
ACTION_FORMAT = _TEMPLATES["action_format"]

# Action constants
ALL_ACTIONS = "JSON"
DEFAULT_ACTION = '{"station_risk_scores": {}, "maintenance_recommendations": [], "notes": "No maintenance needed"}'


def state_to_description(state_for_llm: dict[str, Any], mode: str = "reactive") -> str:
    """Convert factory state to natural language description for maintenance agent.

    Args:
        state_for_llm: Dictionary containing factory state
            - stations: Dict of station states with operation counts, errors
            - maintenance_history: Last maintenance timestamps
            - error_logs: Recent error events
            - sensor_data: Temperature, vibration, timing metrics
        mode: Agent mode (only "reactive" supported)

    Returns:
        Formatted prompt string for LLM
    """
    stations = state_for_llm.get("stations", {})
    maintenance_history = state_for_llm.get("maintenance_history", {})
    error_logs = state_for_llm.get("error_logs", [])
    sensor_data = state_for_llm.get("sensor_data", {})
    current_time = state_for_llm.get("current_time", 0)

    # Build station health table
    description = "**Station Health Status:**\n"
    description += "| Station | Line | Operations | Last Maintenance | Time Since | Recent Errors | Status |\n"
    description += "|---------|------|------------|------------------|------------|---------------|--------|\n"

    for station_type, station_list in stations.items():
        for i, station in enumerate(station_list):
            station_key = f"{station_type}_{i}"
            ops_count = station.get("operation_count", 0)
            last_maint = maintenance_history.get(station_key, 0)
            time_since = current_time - last_maint
            recent_errors = sum(
                1 for err in error_logs if err.get("station") == station_key and err.get("time", 0) > current_time - 10
            )
            status = station.get("status", "OK")

            description += (
                f"| {station_type} | Line {i} | {ops_count} | "
                f"Turn {last_maint} | {time_since} turns | {recent_errors} | {status} |\n"
            )
    description += "\n"

    # Sensor data (if available)
    if sensor_data:
        description += "**Sensor Readings:**\n"
        for station_key, sensors in sensor_data.items():
            temp = sensors.get("temperature", "N/A")
            vib = sensors.get("vibration", "N/A")
            description += f"- {station_key}: Temp={temp}, Vibration={vib}\n"
        description += "\n"

    # Recent error log
    description += "**Recent Error Log (Last 10 turns):**\n"
    if error_logs:
        for err in error_logs[-10:]:
            station = err.get("station", "unknown")
            time = err.get("time", 0)
            msg = err.get("message", "")
            description += f"- Turn {time}: {station} - {msg}\n"
    else:
        description += "- No recent errors\n"
    description += "\n"

    # Maintenance recommendations criteria
    description += "**Maintenance Interval Guidelines:**\n"
    description += "- Cooker: 500 operations or 30 days\n"
    description += "- Cutter: 800 operations or 45 days\n"
    description += "- Washer: 1000 operations or 60 days\n"
    description += "- Plating: 600 operations or 40 days\n"
    description += "- Sealing: 700 operations or 50 days\n"
    description += "- VisionQA: 1500 operations or 90 days (sensor calibration)\n\n"

    # Assemble full prompt
    full_prompt = (
        SYSTEM_PROMPT
        + "\n\n"
        + MAINTENANCE_GUIDE
        + "\n\n"
        + description
        + "\n"
        + OUTPUT_FORMAT
        + "\n"
        + ACTION_FORMAT
    )

    return full_prompt
