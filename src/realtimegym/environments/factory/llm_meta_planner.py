"""
LLM-based Meta Planner Agent for Factory Environment.

This agent uses Large Language Models for high-level strategic planning and coordination.
It extends the BaseAgent class to use LLM reasoning for decision-making.
"""

import json
from typing import Any, NoReturn, Optional

from realtimegym.agents.base import BaseAgent

from .meta_planner import MetaPlannerAgent as RuleBasedMetaPlanner


class LLMMetaPlannerAgent(BaseAgent):
    """
    LLM-based Meta Planner Agent.

    This agent uses LLM reasoning to:
    - Analyze global factory state
    - Set strategic objectives
    - Coordinate other agents
    - Adapt strategy based on conditions
    """

    def __init__(self, prompts: Any, file: str, time_unit: str = "token") -> None:
        super().__init__(prompts, file, time_unit)
        # Rule-based agent for analysis
        self.rule_based_agent = RuleBasedMetaPlanner()
        self.last_decision = None
        self.decision_history = []

    def think(self, timeout: Optional[float] = None) -> NoReturn:
        """
        Use LLM to make strategic planning decisions.

        Args:
            timeout: Time/token budget for thinking
        """
        if self.current_observation is None:
            return

        # Get rule-based analysis as context
        state = self.current_observation.get("state", {})
        self.rule_based_agent.observe(state)
        rule_based_decision = self.rule_based_agent.decide()

        # Build prompt for LLM
        prompt = self._build_meta_planner_prompt(state, rule_based_decision)

        # Call LLM
        messages = [
            {"role": "system", "content": self.prompts.META_PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        budget = timeout if timeout else self.internal_budget

        # Use reactive inference for decision making
        response_text, token_count = self.reactive_inference(messages, budget)

        # Parse LLM response
        decision = self._parse_meta_planner_response(response_text, rule_based_decision)
        self.last_decision = decision
        self.decision_history.append(decision)

        # Store for logging
        if self.log_thinking:
            self.logs["meta_planner_prompt"].append(prompt)
            self.logs["meta_planner_response"].append(response_text)
            self.logs["meta_planner_token_num"].append(token_count)

    def get_decision(self) -> dict[str, Any]:
        """Get the last decision made by the agent."""
        return self.last_decision if self.last_decision else {}

    def _build_meta_planner_prompt(
        self, state: dict[str, Any], rule_based_decision: dict[str, Any]
    ) -> str:
        """Build prompt for LLM meta planner."""
        # Extract key metrics
        turn = state.get("turn", 0)
        max_turns = state.get("max_turns", 1000)
        completed = state.get("completed_products", 0)
        target = state.get("target_products", 10)
        defective = state.get("defective_products", 0)
        collisions = state.get("collision_count", 0)

        # Get performance assessment from rule-based
        perf = rule_based_decision.get("performance_assessment", {})
        critical_actions = rule_based_decision.get("critical_actions", [])
        objectives = rule_based_decision.get("objectives", [])

        prompt = f"""# Factory Strategic Planning Decision

## Current State
- Turn: {turn}/{max_turns} ({turn/max_turns*100:.1f}% elapsed)
- Production: {completed}/{target} products ({completed/target*100:.1f}% complete)
- Defective: {defective} products
- Collisions: {collisions}

## Performance Metrics
- Overall Status: {perf.get('overall_status', 'unknown').upper()}
- Production Progress: {perf.get('production_progress', 0)*100:.1f}%
- Quality Performance: {perf.get('quality_performance', 0)*100:.1f}%
- Resource Efficiency: {perf.get('efficiency', 0)*100:.1f}%
- Bottleneck Count: {perf.get('bottleneck_count', 0)}
- Collision Rate: {perf.get('collision_rate', 0)*100:.3f}%

## Rule-Based Analysis
### Current Objectives:
"""
        for obj in objectives[:5]:
            prompt += f"- [Priority {obj['priority']}] {obj['description']}\n"

        if critical_actions:
            prompt += "\n### Critical Actions Identified:\n"
            for action in critical_actions[:3]:
                prompt += f"- {action['action']}: {action['reason']}\n"

        prompt += """

## Your Task
As the Meta Planner, analyze the current situation and provide strategic guidance:

1. **Situation Assessment**: What is the current state? What are the main challenges?

2. **Strategic Priorities**: What should be the top 3 priorities right now?

3. **Agent Coordination**: What specific actions should each agent focus on?
   - Product Design Agent
   - Facility Management Agent
   - Robot Coordination Agent
   - Quality Inspection Agent
   - Design Agent

4. **Risk Assessment**: What are the main risks to completing the production target?

5. **Recommended Actions**: What immediate actions should be taken?

Provide your response in JSON format:
```json
{
    "situation_assessment": "brief analysis",
    "strategic_priorities": ["priority1", "priority2", "priority3"],
    "agent_coordination": {
        "product_design": ["action1", "action2"],
        "facility_management": ["action1"],
        "robot_coordination": ["action1", "action2"],
        "quality_inspection": ["action1"],
        "design_agent": ["action1"]
    },
    "risks": ["risk1", "risk2"],
    "immediate_actions": ["action1", "action2"]
}
```
"""
        return prompt

    def _parse_meta_planner_response(
        self, response_text: str, fallback_decision: dict[str, Any]
    ) -> dict[str, Any]:
        """Parse LLM response for meta planner decision."""
        try:
            # Try to extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                llm_decision = json.loads(json_text)

                # Merge with rule-based decision
                decision = fallback_decision.copy()
                decision["llm_analysis"] = llm_decision
                decision["situation_assessment"] = llm_decision.get("situation_assessment", "")
                decision["strategic_priorities"] = llm_decision.get("strategic_priorities", [])
                decision["risks"] = llm_decision.get("risks", [])
                decision["immediate_actions"] = llm_decision.get("immediate_actions", [])

                return decision
            else:
                # No JSON found, use fallback
                fallback_decision["llm_analysis"] = {"raw_response": response_text}
                return fallback_decision

        except Exception as e:
            print(f"Error parsing meta planner response: {e}")
            fallback_decision["llm_analysis"] = {
                "error": str(e),
                "raw_response": response_text
            }
            return fallback_decision


# Prompt templates
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
