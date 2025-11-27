"""Coordinator Agent for Factory Environment."""

import json
import re
from typing import Any, Optional

from ..base import BaseAgent, extract_boxed


class CoordinatorAgent(BaseAgent):
    """
    High-level coordinator agent that assigns tasks to sub-agents (robots).

    Uses LLM to make decisions about task allocation based on factory state.
    Outputs JSON format task assignments for logistics and robot arm agents.
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
        Initialize coordinator agent.

        Args:
            prompts: Prompt module (factory.coordinator)
            file: Log file path
            time_unit: "token" or "seconds"
            model1_config: Path to model config YAML
            internal_budget: Token/time budget
        """
        super().__init__(prompts, file, time_unit)
        self.config_model1(model1_config, internal_budget)

        # Store last task assignments
        self.last_assignments: dict[str, dict] = {}

    def truncate_logs(self) -> None:
        """Truncate logs (required by BaseAgent interface)."""
        return

    def think(self, timeout: Optional[float] = None) -> dict[str, dict]:
        """
        Decide task assignments for all robots based on current factory state.

        Args:
            timeout: Time/token budget for thinking

        Returns:
            Dictionary mapping robot_id to task dict
            Example: {
                "logistics_0": {"type": "pick_and_deliver", "from": "Storage", "to": "Washer"},
                "robot_arm_washer_0": {"type": "operate_station", "station": "Washer"}
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
        task_assignments = self._parse_task_assignments(text)

        # Store for logging
        self.last_assignments = task_assignments

        # Log if enabled
        if self.log_thinking:
            self.logs["plan"].append("N/A")
            self.logs["model1_prompt"].append(messages[-1]["content"])
            self.logs["model1_response"].append(text)
        self.logs["model1_token_num"].append(token_num)

        return task_assignments

    def _parse_task_assignments(self, llm_response: str) -> dict[str, dict]:
        """
        Parse task assignments from LLM response.

        Extracts JSON from \\boxed{...} format and validates structure.

        Args:
            llm_response: Raw LLM text output

        Returns:
            Dictionary of task assignments, or empty dict if parsing fails
        """
        # Extract content from \boxed{}
        boxed_content = extract_boxed(llm_response)

        if not boxed_content:
            print("[CoordinatorAgent] Warning: No boxed content found in LLM response")
            return {}

        try:
            # Try to parse as JSON
            # Remove any markdown code blocks if present
            json_str = boxed_content.strip()
            json_str = re.sub(r"^```json\s*", "", json_str)
            json_str = re.sub(r"^```\s*", "", json_str)
            json_str = re.sub(r"\s*```$", "", json_str)

            assignments = json.loads(json_str)

            # Validate structure
            if not isinstance(assignments, dict):
                print(
                    f"[CoordinatorAgent] Warning: Parsed JSON is not a dict: {type(assignments)}"
                )
                return {}

            # Validate each task
            for robot_id, task in assignments.items():
                if not isinstance(task, dict):
                    print(
                        f"[CoordinatorAgent] Warning: Task for {robot_id} is not a dict"
                    )
                    return {}
                if "type" not in task:
                    print(
                        f"[CoordinatorAgent] Warning: Task for {robot_id} missing 'type' field"
                    )
                    return {}

            return assignments

        except json.JSONDecodeError as e:
            print(
                f"[CoordinatorAgent] Error: Failed to parse JSON from boxed content: {e}"
            )
            print(f"[CoordinatorAgent] Boxed content was: {boxed_content[:200]}")
            return {}

    def act(self) -> dict[str, dict]:
        """
        Return the task assignments decided in think().

        Returns:
            Dictionary of task assignments
        """
        return self.last_assignments
