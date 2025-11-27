"""MaintenanceAgent for Factory Environment."""

import json
import re
from typing import Any, Optional

from ..base import BaseAgent, extract_boxed


class MaintenanceAgent(BaseAgent):
    """
    Equipment health monitoring and predictive maintenance agent.

    Monitors station health, predicts maintenance needs, and provides
    risk assessments to other agents for production planning.
    """

    def __init__(
        self,
        prompts: Any,  # noqa: ANN401
        file: str,
        time_unit: str,
        model1_config: str,
        internal_budget: int,
    ) -> None:
        """
        Initialize Maintenance agent.

        Args:
            prompts: Prompt module (factory.maintenance)
            file: Log file path
            time_unit: "token" or "seconds"
            model1_config: Path to model config YAML
            internal_budget: Token/time budget
        """
        super().__init__(prompts, file, time_unit)
        self.config_model1(model1_config, internal_budget)

        # Store last assessment
        self.last_assessment: dict[str, Any] = {}

    def truncate_logs(self) -> None:
        """Truncate logs (required by BaseAgent interface)."""
        return

    def think(self, timeout: Optional[float] = None) -> dict[str, Any]:
        """
        Assess equipment health and generate maintenance recommendations.

        Args:
            timeout: Time/token budget for thinking

        Returns:
            Dictionary containing maintenance assessment
            Example: {
                "station_risk_scores": {"Washer_0": "Low", "Cooker_0": "High"},
                "maintenance_recommendations": [...],
                "predicted_failures": [...],
                "overall_fleet_health": 0.78,
                "notes": "..."
            }
        """
        assert self.current_observation is not None and timeout is not None

        budget = timeout
        observation = self.current_observation

        # Convert state to prompt
        prompt = self.prompts.state_to_description(
            observation["state"], mode="reactive"
        )

        messages = [{"role": "user", "content": prompt}]

        # Get LLM response
        text, token_num = self.reactive_inference(messages, budget)

        # Parse JSON from boxed content
        assessment = self._parse_maintenance_assessment(text)

        # Store for logging
        self.last_assessment = assessment

        # Log if enabled
        if self.log_thinking:
            self.logs["plan"].append("N/A")
            self.logs["model1_prompt"].append(messages[-1]["content"])
            self.logs["model1_response"].append(text)
        self.logs["model1_token_num"].append(token_num)

        return assessment

    def _parse_maintenance_assessment(self, llm_response: str) -> dict[str, Any]:
        """
        Parse maintenance assessment from LLM response.

        Args:
            llm_response: Raw LLM text output

        Returns:
            Dictionary of maintenance assessment, or default if parsing fails
        """
        # Extract content from \boxed{}
        boxed_content = extract_boxed(llm_response)

        if not boxed_content:
            print("[MaintenanceAgent] Warning: No boxed content found in LLM response")
            return self._default_assessment()

        try:
            # Clean JSON string
            json_str = boxed_content.strip()
            json_str = re.sub(r"^```json\s*", "", json_str)
            json_str = re.sub(r"^```\s*", "", json_str)
            json_str = re.sub(r"\s*```$", "", json_str)

            assessment = json.loads(json_str)

            # Validate structure
            if not isinstance(assessment, dict):
                print(f"[MaintenanceAgent] Warning: Parsed JSON is not a dict: {type(assessment)}")
                return self._default_assessment()

            # Validate required fields
            required_fields = ["station_risk_scores"]
            for field in required_fields:
                if field not in assessment:
                    print(f"[MaintenanceAgent] Warning: Missing required field '{field}'")
                    return self._default_assessment()

            return assessment

        except json.JSONDecodeError as e:
            print(f"[MaintenanceAgent] Error: Failed to parse JSON: {e}")
            print(f"[MaintenanceAgent] Content was: {boxed_content[:200]}")
            return self._default_assessment()

    def _default_assessment(self) -> dict[str, Any]:
        """Return a safe default maintenance assessment."""
        return {
            "station_risk_scores": {},
            "maintenance_recommendations": [],
            "predicted_failures": [],
            "overall_fleet_health": 1.0,
            "notes": "Default assessment - LLM parsing failed, assuming all equipment healthy"
        }

    def act(self) -> dict[str, Any]:
        """
        Return the maintenance assessment decided in think().

        Returns:
            Dictionary of maintenance assessment
        """
        return self.last_assessment
