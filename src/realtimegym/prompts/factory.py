"""Factory game prompts - Python logic for state-to-description conversion."""

from typing import Any, Optional, Union

# Module-level constants
ALL_ACTIONS = "WAIT|MAINTAIN|INSPECT|SCHEDULE"
DEFAULT_ACTION = "WAIT"

# Prompt templates
REACTIVE_PROMPT = """You are operating an unmanned food production factory.
Make quick decisions to keep the factory running efficiently.

Available actions:
- WAIT: Do nothing this turn
- MAINTAIN: Schedule maintenance for a failing station
- INSPECT: Inspect product quality
- SCHEDULE: Adjust robot task priorities

Current state will be provided below. Respond with your action in \\boxed{ACTION} format.
"""

PLANNING_PROMPT = """You are the strategic coordinator of an unmanned food production factory.
Analyze the current state and plan long-term strategies for optimization.

Your goals:
1. Maximize production volume
2. Minimize defect rate
3. Optimize robot utilization
4. Prevent equipment failures

Think step by step about:
- Current bottlenecks in the production line
- Predictive maintenance needs
- Resource allocation
- Quality control measures

Provide your analysis and recommendations.
"""


def state_to_description(
    state_for_llm: dict[str, Any], mode: Optional[str] = None
) -> Union[str, dict[str, str]]:
    """
    Convert game state to natural language description.

    Args:
        state_for_llm: Dictionary containing the factory state
        mode: Agent mode - "reactive", "planning", or "agile"

    Returns:
        String description for reactive/planning modes, or dict with both for agile mode
    """
    # Extract state information
    turn = state_for_llm.get("turn", 0)
    max_turns = state_for_llm.get("max_turns", 1000)
    completed = state_for_llm.get("completed_products", 0)
    target = state_for_llm.get("target_products", 0)
    defective = state_for_llm.get("defective_products", 0)
    stations = state_for_llm.get("stations", [])
    robot_arms_idle = state_for_llm.get("robot_arms_count", 0)
    logistic_idle = state_for_llm.get("logistic_robots_count", 0)
    collisions = state_for_llm.get("collision_count", 0)

    # Build state description
    state_desc = f"""
=== Factory Status (Turn {turn}/{max_turns}) ===

Production Progress:
- Completed Products: {completed}/{target}
- Defective Products: {defective}
- Quality Rate: {(completed / max(1, completed + defective) * 100):.1f}%

Robot Status:
- Idle Robot Arms: {robot_arms_idle}
- Idle Logistic Robots: {logistic_idle}
- Total Collisions: {collisions}

Station Status:
"""

    # Add station information
    for station in stations[:10]:  # Show first 10 stations
        station_type = station.get("type", "Unknown")
        status = station.get("status", "Unknown")
        input_count = station.get("input_count", 0)
        output_count = station.get("output_count", 0)
        progress = station.get("progress", 0)
        max_progress = station.get("max_progress", 1)
        wear = station.get("wear_level", 0.0)

        state_desc += f"\n{station_type} (ID {station.get('id', 0)}): {status}"
        state_desc += f" | In:{input_count} Out:{output_count}"
        if status == "Busy":
            state_desc += f" | Progress:{progress}/{max_progress}"
        if wear > 0.3:
            state_desc += f" | Wear:{wear:.2f} ⚠"

    # Add performance metrics
    state_desc += f"\n\nKey Metrics:"
    state_desc += f"\n- Production Rate: {(completed / max(1, turn)) * 100:.2f} products/100 turns"
    state_desc += f"\n- Robot Utilization: {((20 - robot_arms_idle) / 20 * 100):.1f}% (arms)"
    if defective > 0:
        state_desc += f"\n- Defect Rate: {(defective / (completed + defective) * 100):.1f}% ⚠"

    # Mode-specific formatting
    if mode == "reactive":
        return REACTIVE_PROMPT + "\n" + state_desc

    elif mode == "planning":
        return PLANNING_PROMPT + "\n" + state_desc

    elif mode == "agile":
        return {
            "reactive": REACTIVE_PROMPT + "\n" + state_desc,
            "planning": PLANNING_PROMPT + "\n" + state_desc,
        }

    else:
        # Default to reactive
        return REACTIVE_PROMPT + "\n" + state_desc
