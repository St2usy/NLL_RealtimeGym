"""QualityAgent prompts for factory environment."""

from pathlib import Path
from typing import Any

import yaml

# Load prompt templates from YAML
_TEMPLATE_FILE = Path(__file__).parent / "quality.yaml"

with open(_TEMPLATE_FILE, "r", encoding="utf-8") as f:
    _TEMPLATES = yaml.safe_load(f)

# Export prompt templates as module constants
SYSTEM_PROMPT = _TEMPLATES["system_prompt"]
QUALITY_ANALYSIS_GUIDE = _TEMPLATES["quality_analysis_guide"]
OUTPUT_FORMAT = _TEMPLATES["output_format"]
ACTION_FORMAT = _TEMPLATES["action_format"]

# Action constants
ALL_ACTIONS = "JSON"
DEFAULT_ACTION = '{"quality_metrics": {"overall_defect_rate": 0.0}, "recommendations": [], "notes": "No quality issues detected"}'


def state_to_description(state_for_llm: dict[str, Any], mode: str = "reactive") -> str:
    """Convert factory state to natural language description for quality agent.

    Args:
        state_for_llm: Dictionary containing factory state
            - inspection_results: Recent VisionQA inspection outcomes
            - production_history: Products produced with quality outcomes
            - defect_logs: Detailed defect records
            - station_parameters: Current process parameters
            - workload_metrics: Robot utilization, queue lengths
        mode: Agent mode (only "reactive" supported)

    Returns:
        Formatted prompt string for LLM
    """
    inspection_results = state_for_llm.get("inspection_results", [])
    production_history = state_for_llm.get("production_history", [])
    defect_logs = state_for_llm.get("defect_logs", [])
    station_parameters = state_for_llm.get("station_parameters", {})
    workload_metrics = state_for_llm.get("workload_metrics", {})

    # Build inspection results table
    description = "**Recent Inspection Results (Last 50 products):**\n"
    description += "| Product ID | Type | Line | Inspected At | Result | Defect Type | Severity |\n"
    description += "|------------|------|------|--------------|--------|-------------|----------|\n"

    for result in inspection_results[-50:]:
        product_id = result.get("product_id", "N/A")
        product_type = result.get("product_type", "unknown")
        line = result.get("production_line", "N/A")
        time = result.get("inspection_time", 0)
        outcome = result.get("result", "pass")
        defect_type = result.get("defect_type", "none")
        severity = result.get("severity", "-")

        description += (
            f"| {product_id} | {product_type} | Line {line} | "
            f"Turn {time} | {outcome} | {defect_type} | {severity} |\n"
        )
    description += "\n"

    # Quality summary by product type
    description += "**Quality Summary by Product Type:**\n"
    product_stats: dict[str, dict[str, int]] = {}
    for result in inspection_results:
        ptype = result.get("product_type", "unknown")
        outcome = result.get("result", "pass")
        if ptype not in product_stats:
            product_stats[ptype] = {"total": 0, "passed": 0, "failed": 0}
        product_stats[ptype]["total"] += 1
        if outcome == "pass":
            product_stats[ptype]["passed"] += 1
        else:
            product_stats[ptype]["failed"] += 1

    for ptype, stats in product_stats.items():
        total = stats["total"]
        failed = stats["failed"]
        defect_rate = failed / total if total > 0 else 0.0
        description += f"- {ptype}: {failed}/{total} defects ({defect_rate:.1%})\n"
    description += "\n"

    # Defect type distribution
    description += "**Defect Type Distribution:**\n"
    defect_counts: dict[str, int] = {}
    for defect in defect_logs:
        dtype = defect.get("defect_type", "unknown")
        defect_counts[dtype] = defect_counts.get(dtype, 0) + 1

    for dtype, count in sorted(defect_counts.items(), key=lambda x: x[1], reverse=True):
        description += f"- {dtype}: {count} occurrences\n"
    description += "\n"

    # Current process parameters
    description += "**Current Process Parameters:**\n"
    for station, params in station_parameters.items():
        description += f"- {station}:\n"
        for param_name, value in params.items():
            description += f"  - {param_name}: {value}\n"
    description += "\n"

    # Workload context
    description += "**Production Context:**\n"
    robot_idle = workload_metrics.get("robot_idle_ratio", 0)
    station_idle = workload_metrics.get("station_idle_ratio", 0)
    avg_queue = workload_metrics.get("avg_queue_length", 0)
    description += f"- Robot idle ratio: {robot_idle:.1%}\n"
    description += f"- Station idle ratio: {station_idle:.1%}\n"
    description += f"- Average queue length: {avg_queue:.1f}\n"
    description += "\n"

    # Assemble full prompt
    full_prompt = (
        SYSTEM_PROMPT
        + "\n\n"
        + QUALITY_ANALYSIS_GUIDE
        + "\n\n"
        + description
        + "\n"
        + OUTPUT_FORMAT
        + "\n"
        + ACTION_FORMAT
    )

    return full_prompt
