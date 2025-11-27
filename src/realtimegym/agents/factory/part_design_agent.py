"""PartDesign Agent for Factory Environment."""

import json
import re
from typing import Any, Optional

from ..base import BaseAgent, extract_boxed


class PartDesignAgent(BaseAgent):
    """
    High-level part design agent for production planning.

    Converts product requests into executable production plans including:
    - Production route selection
    - Batch size determination
    - Robot allocation per station
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
        Initialize PartDesign agent.

        Args:
            prompts: Prompt module (factory.part_design)
            file: Log file path
            time_unit: "token" or "seconds"
            model1_config: Path to model config YAML
            internal_budget: Token/time budget
        """
        super().__init__(prompts, file, time_unit)
        self.config_model1(model1_config, internal_budget)

        # Store last production plan
        self.last_plan: dict[str, Any] = {}

    def truncate_logs(self) -> None:
        """Truncate logs (required by BaseAgent interface)."""
        return

    def think(self, timeout: Optional[float] = None) -> dict[str, Any]:
        """
        Create production plan based on current factory state.

        Args:
            timeout: Time/token budget for thinking

        Returns:
            Dictionary containing production plan
            Example: {
                "product_type": "ricotta_salad",
                "route": ["Storage", "Washer", "Cutter", ...],
                "batch_size": 5,
                "robot_allocation": {...}
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
        production_plan = self._parse_production_plan(text)

        # Store for logging
        self.last_plan = production_plan

        # Log if enabled
        if self.log_thinking:
            self.logs["plan"].append("N/A")
            self.logs["model1_prompt"].append(messages[-1]["content"])
            self.logs["model1_response"].append(text)
        self.logs["model1_token_num"].append(token_num)

        return production_plan

    def _parse_production_plan(self, llm_response: str) -> dict[str, Any]:
        """
        Parse production plan from LLM response.

        Args:
            llm_response: Raw LLM text output

        Returns:
            Dictionary of production plan, or default plan if parsing fails
        """
        # Extract content from \boxed{}
        boxed_content = extract_boxed(llm_response)

        if not boxed_content:
            print("[PartDesignAgent] Warning: No boxed content found in LLM response")
            return self._default_plan()

        try:
            # Clean JSON string
            json_str = boxed_content.strip()
            json_str = re.sub(r"^```json\s*", "", json_str)
            json_str = re.sub(r"^```\s*", "", json_str)
            json_str = re.sub(r"\s*```$", "", json_str)

            plan = json.loads(json_str)

            # Validate structure
            if not isinstance(plan, dict):
                print(f"[PartDesignAgent] Warning: Parsed JSON is not a dict: {type(plan)}")
                return self._default_plan()

            # Validate required fields
            required_fields = ["product_type", "route", "batch_size"]
            for field in required_fields:
                if field not in plan:
                    print(f"[PartDesignAgent] Warning: Missing required field '{field}'")
                    return self._default_plan()

            return plan

        except json.JSONDecodeError as e:
            print(f"[PartDesignAgent] Error: Failed to parse JSON: {e}")
            print(f"[PartDesignAgent] Content was: {boxed_content[:200]}")
            return self._default_plan()

    def _default_plan(self) -> dict[str, Any]:
        """Return a safe default production plan."""
        return {
            "product_type": "unknown",
            "quantity": 1,
            "production_line": 0,
            "route": ["Storage", "Washer", "Cutter", "Plating", "Sealing", "VisionQA", "FinalStorage"],
            "batch_size": 1,
            "num_batches": 1,
            "estimated_time": 100,
            "robot_allocation": {},
            "notes": "Default plan - LLM parsing failed"
        }

    def act(self) -> dict[str, Any]:
        """
        Return the production plan decided in think().

        Returns:
            Dictionary of production plan
        """
        return self.last_plan
