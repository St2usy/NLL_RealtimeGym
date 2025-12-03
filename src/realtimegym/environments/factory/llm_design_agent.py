"""
LLM-based Design Agent for Factory Environment.

This agent uses Large Language Models for production system design and optimization.
It extends the BaseAgent class to use LLM reasoning for design decisions.
"""

import json
from typing import Any, NoReturn, Optional

from realtimegym.agents.base import BaseAgent

from .design_agent import DesignAgent as RuleBasedDesignAgent


class LLMDesignAgent(BaseAgent):
    """
    LLM-based Design Agent.

    This agent uses LLM reasoning to:
    - Analyze production system capacity
    - Identify design-level inefficiencies
    - Recommend structural improvements
    - Plan capacity adjustments
    """

    def __init__(self, prompts: Any, file: str, time_unit: str = "token") -> None:
        super().__init__(prompts, file, time_unit)
        # Rule-based agent for analysis
        self.rule_based_agent = RuleBasedDesignAgent()
        self.last_decision = None
        self.decision_history = []

    def think(self, timeout: Optional[float] = None) -> NoReturn:
        """
        Use LLM to make design decisions.

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
        prompt = self._build_design_agent_prompt(state, rule_based_decision)

        # Call LLM
        messages = [
            {"role": "system", "content": self.prompts.DESIGN_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        budget = timeout if timeout else self.internal_budget

        # Use reactive inference for decision making
        response_text, token_count = self.reactive_inference(messages, budget)

        # Parse LLM response
        decision = self._parse_design_agent_response(response_text, rule_based_decision)
        self.last_decision = decision
        self.decision_history.append(decision)

        # Store for logging
        if self.log_thinking:
            self.logs["design_agent_prompt"].append(prompt)
            self.logs["design_agent_response"].append(response_text)
            self.logs["design_agent_token_num"].append(token_count)

    def get_decision(self) -> dict[str, Any]:
        """Get the last decision made by the agent."""
        return self.last_decision if self.last_decision else {}

    def _build_design_agent_prompt(
        self, state: dict[str, Any], rule_based_decision: dict[str, Any]
    ) -> str:
        """Build prompt for LLM design agent."""
        # Extract key info
        turn = state.get("turn", 0)
        completed = state.get("completed_products", 0)
        target = state.get("target_products", 10)

        # Get analysis from rule-based
        capacity_analysis = rule_based_decision.get("capacity_analysis", [])
        system_metrics = rule_based_decision.get("system_metrics", {})
        config_recs = rule_based_decision.get("configuration_recommendations", [])
        opt_priorities = rule_based_decision.get("optimization_priorities", [])

        prompt = f"""# Factory System Design Analysis

## Current State
- Turn: {turn}
- Production: {completed}/{target} products
- Grid: 20x30, 2 production lines

## System Metrics
- Line Balance: {system_metrics.get('line_balance', 0)*100:.1f}%
- Average Utilization: {system_metrics.get('average_utilization', 0)*100:.1f}%
- Capacity Efficiency: {system_metrics.get('capacity_efficiency', 0)*100:.1f}%
- Bottleneck Count: {system_metrics.get('bottleneck_count', 0)}
- Line 1 Utilization: {system_metrics.get('line1_utilization', 0)*100:.1f}%
- Line 2 Utilization: {system_metrics.get('line2_utilization', 0)*100:.1f}%

## Capacity Analysis (Bottlenecks)
"""
        bottlenecks = [a for a in capacity_analysis if a.get("is_bottleneck", False)]
        if bottlenecks:
            for bn in bottlenecks[:5]:
                prompt += f"""- Station {bn['station_id']} ({bn['station_type']}, Line {bn['line']}):
  - Utilization: {bn['utilization_rate']*100:.0f}%
  - Current Throughput: {bn['current_throughput']:.2f} items/100 turns
  - Max Capacity: {bn['max_capacity']:.2f} items/100 turns
"""
        else:
            prompt += "- No critical bottlenecks detected\n"

        prompt += "\n## Rule-Based Recommendations\n"
        for rec in config_recs[:3]:
            prompt += f"""- [{rec['priority']}] {rec['description']}
  - Expected Improvement: {rec['expected_improvement']}
  - Feasibility: {rec['feasibility']*100:.0f}%
"""

        prompt += "\n## Optimization Priorities\n"
        for opt in opt_priorities[:3]:
            prompt += f"{opt['priority']}. {opt['optimization']}: {opt['description']}\n"

        prompt += """

## Your Task
As the Design Agent, provide expert analysis and recommendations:

1. **System Assessment**: Evaluate the current production system design. What are the strengths and weaknesses?

2. **Bottleneck Analysis**: Are the identified bottlenecks correct? What is causing them?

3. **Design Recommendations**: What design changes would have the highest impact?
   - Station configuration (add/remove/relocate)
   - Buffer size adjustments
   - Robot allocation
   - Line balancing strategies

4. **Implementation Priority**: What should be implemented first, second, third?

5. **Expected Impact**: What improvements can we expect from your recommendations?

Provide your response in JSON format:
```json
{
    "system_assessment": "brief evaluation of design",
    "bottleneck_analysis": {
        "root_causes": ["cause1", "cause2"],
        "critical_stations": [station_ids]
    },
    "design_recommendations": [
        {
            "recommendation": "description",
            "rationale": "why this helps",
            "priority": 1-10,
            "expected_impact": {
                "throughput_increase": 0.2,
                "utilization_improvement": 0.15
            }
        }
    ],
    "implementation_plan": [
        {"step": 1, "action": "description"},
        {"step": 2, "action": "description"}
    ],
    "expected_overall_improvement": "summary of benefits"
}
```
"""
        return prompt

    def _parse_design_agent_response(
        self, response_text: str, fallback_decision: dict[str, Any]
    ) -> dict[str, Any]:
        """Parse LLM response for design agent decision."""
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
                decision["system_assessment"] = llm_decision.get("system_assessment", "")
                decision["bottleneck_analysis"] = llm_decision.get("bottleneck_analysis", {})
                decision["design_recommendations"] = llm_decision.get("design_recommendations", [])
                decision["implementation_plan"] = llm_decision.get("implementation_plan", [])
                decision["expected_improvement"] = llm_decision.get("expected_overall_improvement", "")

                return decision
            else:
                # No JSON found, use fallback
                fallback_decision["llm_analysis"] = {"raw_response": response_text}
                return fallback_decision

        except Exception as e:
            print(f"Error parsing design agent response: {e}")
            fallback_decision["llm_analysis"] = {
                "error": str(e),
                "raw_response": response_text
            }
            return fallback_decision


# Prompt templates
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
