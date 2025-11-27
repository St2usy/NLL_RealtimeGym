"""QualityAgent for Factory Environment."""

import json
import re
from typing import Any, Optional

from ..base import BaseAgent, extract_boxed


class QualityAgent(BaseAgent):
    """
    Quality control and defect analysis agent.

    Monitors inspection results, detects defect patterns, analyzes root causes,
    and recommends process parameter adjustments to improve quality.
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
        Initialize Quality agent.

        Args:
            prompts: Prompt module (factory.quality)
            file: Log file path
            time_unit: "token" or "seconds"
            model1_config: Path to model config YAML
            internal_budget: Token/time budget
        """
        super().__init__(prompts, file, time_unit)
        self.config_model1(model1_config, internal_budget)

        # Store last analysis
        self.last_analysis: dict[str, Any] = {}

    def truncate_logs(self) -> None:
        """Truncate logs (required by BaseAgent interface)."""
        return

    def think(self, timeout: Optional[float] = None) -> dict[str, Any]:
        """
        Analyze quality data and generate recommendations.

        Args:
            timeout: Time/token budget for thinking

        Returns:
            Dictionary containing quality analysis
            Example: {
                "quality_metrics": {
                    "overall_defect_rate": 0.023,
                    "by_product": {...}
                },
                "defect_analysis": {...},
                "root_causes": [...],
                "recommendations": [...],
                "alerts": [...],
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
        analysis = self._parse_quality_analysis(text)

        # Store for logging
        self.last_analysis = analysis

        # Log if enabled
        if self.log_thinking:
            self.logs["plan"].append("N/A")
            self.logs["model1_prompt"].append(messages[-1]["content"])
            self.logs["model1_response"].append(text)
        self.logs["model1_token_num"].append(token_num)

        return analysis

    def _parse_quality_analysis(self, llm_response: str) -> dict[str, Any]:
        """
        Parse quality analysis from LLM response.

        Args:
            llm_response: Raw LLM text output

        Returns:
            Dictionary of quality analysis, or default if parsing fails
        """
        # Extract content from \boxed{}
        boxed_content = extract_boxed(llm_response)

        if not boxed_content:
            print("[QualityAgent] Warning: No boxed content found in LLM response")
            return self._default_analysis()

        try:
            # Clean JSON string
            json_str = boxed_content.strip()
            json_str = re.sub(r"^```json\s*", "", json_str)
            json_str = re.sub(r"^```\s*", "", json_str)
            json_str = re.sub(r"\s*```$", "", json_str)

            analysis = json.loads(json_str)

            # Validate structure
            if not isinstance(analysis, dict):
                print(f"[QualityAgent] Warning: Parsed JSON is not a dict: {type(analysis)}")
                return self._default_analysis()

            # Validate required fields
            required_fields = ["quality_metrics"]
            for field in required_fields:
                if field not in analysis:
                    print(f"[QualityAgent] Warning: Missing required field '{field}'")
                    return self._default_analysis()

            return analysis

        except json.JSONDecodeError as e:
            print(f"[QualityAgent] Error: Failed to parse JSON: {e}")
            print(f"[QualityAgent] Content was: {boxed_content[:200]}")
            return self._default_analysis()

    def _default_analysis(self) -> dict[str, Any]:
        """Return a safe default quality analysis."""
        return {
            "quality_metrics": {
                "overall_defect_rate": 0.0,
                "by_product": {},
                "by_line": {},
                "recent_trend": "stable"
            },
            "defect_analysis": {
                "top_defect_types": [],
                "patterns_detected": []
            },
            "root_causes": [],
            "recommendations": [],
            "alerts": [],
            "notes": "Default analysis - LLM parsing failed, no quality data available"
        }

    def act(self) -> dict[str, Any]:
        """
        Return the quality analysis decided in think().

        Returns:
            Dictionary of quality analysis
        """
        return self.last_analysis
