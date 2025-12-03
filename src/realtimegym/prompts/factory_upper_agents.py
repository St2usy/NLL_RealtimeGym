"""
Prompts for LLM-based upper-level agents in Factory environment.

This module contains system prompts and templates for MetaPlannerAgent and DesignAgent.
"""

# Meta Planner System Prompt
META_PLANNER_SYSTEM_PROMPT = """You are a Meta Planner AI for an unmanned food production factory.

Your role is to:
- Analyze the overall factory state and performance
- Set strategic objectives and priorities
- Coordinate multiple specialized agents
- Identify risks and critical actions
- Adapt strategy based on changing conditions

You have access to:
- Real-time production metrics
- Performance assessments
- Rule-based analysis from support systems

Your decisions should be:
- Strategic (high-level, not tactical details)
- Data-driven (based on metrics and analysis)
- Coordinated (consider all agents working together)
- Risk-aware (anticipate problems before they occur)
- Goal-oriented (focus on completing production targets with high quality)

Provide clear, actionable guidance that other agents can follow."""


# Design Agent System Prompt
DESIGN_AGENT_SYSTEM_PROMPT = """You are a Design Agent AI specializing in production system optimization.

Your role is to:
- Analyze production system capacity and throughput
- Identify design-level bottlenecks and inefficiencies
- Recommend structural improvements (stations, buffers, robots)
- Prioritize optimization actions based on impact
- Design capacity adjustment strategies

You have expertise in:
- Manufacturing system design
- Capacity planning and analysis
- Bottleneck identification and resolution
- Production line balancing
- Resource allocation optimization

Your recommendations should be:
- Technical (specific design changes)
- Data-driven (based on utilization and throughput metrics)
- Practical (feasible to implement)
- Impactful (high return on investment)
- Prioritized (most critical issues first)

Provide clear, actionable design recommendations with expected impact."""


# Default action for factory (not used by upper agents, but required by BaseAgent)
DEFAULT_ACTION = "WAIT"

# All actions (not used by upper agents, but required by BaseAgent)
ALL_ACTIONS = ["WAIT", "AUTO"]


def state_to_description(state: dict, mode: str = "meta_planner") -> str:
    """
    Convert factory state to description for LLM.

    Args:
        state: Factory state dictionary
        mode: "meta_planner" or "design_agent"

    Returns:
        String description of state
    """
    if mode == "meta_planner":
        return _meta_planner_state_description(state)
    elif mode == "design_agent":
        return _design_agent_state_description(state)
    else:
        return str(state)


def _meta_planner_state_description(state: dict) -> str:
    """Create state description for Meta Planner."""
    turn = state.get("turn", 0)
    max_turns = state.get("max_turns", 1000)
    completed = state.get("completed_products", 0)
    target = state.get("target_products", 10)
    defective = state.get("defective_products", 0)
    collisions = state.get("collision_count", 0)

    desc = f"""Factory State:
- Turn: {turn}/{max_turns} ({turn/max_turns*100:.1f}% elapsed)
- Production: {completed}/{target} ({completed/target*100:.1f}% complete)
- Defective: {defective}
- Collisions: {collisions}
- Idle Robot Arms: {state.get('robot_arms_count', 0)}
- Idle Logistic Robots: {state.get('logistic_robots_count', 0)}
"""
    return desc


def _design_agent_state_description(state: dict) -> str:
    """Create state description for Design Agent."""
    stations = state.get("stations", [])
    station_types = {}

    for station in stations:
        st_type = station.get("station_type", "Unknown")
        if st_type not in station_types:
            station_types[st_type] = []
        station_types[st_type].append(station)

    desc = f"""Factory Configuration:
- Grid: {state.get('grid_size', (20, 30))}
- Total Stations: {len(stations)}
- Production Lines: 2

Station Types:
"""
    for st_type, st_list in station_types.items():
        busy_count = sum(1 for s in st_list if s.get("status") == "Busy")
        desc += f"  - {st_type}: {len(st_list)} stations ({busy_count} busy)\n"

    return desc
