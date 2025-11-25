# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Realtime Reasoning Gym** is an evaluation framework for testing language agents under real-time constraints. Unlike traditional OpenAI Gym environments, this framework enforces strict time budgets (seconds) or token budgets (LLM decoding tokens) to simulate real-world pressure scenarios.

The framework provides three real-time games (Freeway, Snake, Overcooked) with three cognitive load levels each (v0=Easy, v1=Medium, v2=Hard).

## Installation & Setup

```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Set up API keys in .env (see .env.example for template)
```

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/realtimegym --cov-report=term-missing --cov-report=html

# Run specific test categories
pytest tests/test_environments.py
pytest tests/test_agents.py

# Skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration
```

### Code Quality
```bash
# Run pre-commit hooks manually
pre-commit run --all-files

# Type checking
uv run ty check

# Linting and formatting (via pre-commit)
# - Ruff linter with auto-fix
# - Ruff formatter
# - ty type checker
```

### Running Evaluations
```bash
# Detailed configuration
agile_eval --time_unit token \
    --time_pressure 8192 \
    --internal_budget 4096 \
    --game freeway \
    --cognitive_load E \
    --mode agile \
    --reactive-model-config configs/example-deepseek-v3.2-reactive.yaml \
    --planning-model-config configs/example-deepseek-v3.2-planning.yaml \
    --seed_num 1 --repeat_times 1

# Compact configuration using settings
agile_eval --time_unit token \
    --settings freeway_H_8192_agile_4096 \
    --reactive-model-config configs/example-deepseek-v3.2-reactive.yaml \
    --planning-model-config configs/example-deepseek-v3.2-planning.yaml \
    --seed_num 8 --repeat_times 1
```

## Code Architecture

### Core Design Pattern

The framework implements a **three-phase interaction pattern** for real-time reasoning:

1. **observe()**: Agent receives observation from environment
2. **think(timeout)**: Agent processes information within budget constraints (tokens or seconds)
3. **act()**: Agent returns action or None for default action

This differs from traditional Gym's single-step `action = agent.act(obs)` by explicitly separating observation and bounded thinking phases.

### Key Components

#### 1. Environment Registry System (src/realtimegym/__init__.py)
- Central `_REGISTRY` maps environment IDs (e.g., "Freeway-v2") to (game_module, cognitive_load)
- `make(env_id, seed, render)` factory function creates environments
- Cognitive load levels embedded in version suffix: v0=Easy, v1=Medium, v2=Hard
- Returns tuple: `(env, actual_seed, renderer)`

#### 2. Agent Architecture (src/realtimegym/agents/)

**BaseAgent** (base.py) provides:
- Dual-model support: `model1` (reactive) and `model2` (planning)
- Token budget tracking via streaming or batch inference
- Environment variable resolution for API keys using `${VAR_NAME}` syntax
- Logging system with `log_thinking` flag (disabled for time-based budgets)
- `extract_boxed()` utility for parsing `\boxed{action}` format from LLM responses

**Three Agent Types:**
- **ReactiveAgent**: Single-model, generates responses within bounded time/token budget
- **PlanningAgent**: Single-model, comprehensive planning without reactive execution
- **AgileThinker**: Dual-model hybrid
  - Planning model runs in background (streaming)
  - Reactive model consumes planning output + current observation
  - Requires tokenizer for token-based budgets to decode partial outputs

#### 3. Time Pressure Implementation

**Token Budget** (`time_unit="token"`):
- Tracks completion tokens from API responses
- For planning agents: uses tokenizer to decode partial outputs incrementally
- Accumulates budget across turns using `gen_accum` counter
- Flushes decoded text when budget allows

**Time Budget** (`time_unit="seconds"`):
- Uses streaming APIs with wall-clock time measurement
- Planning agents: background thread with `planning_queue` and `planning_done` event
- Reactive agents: streams until timeout, then sleeps remaining time
- `log_thinking` disabled to avoid timing interference

#### 4. Environment Base Class (src/realtimegym/environments/base.py)

**BaseEnv** provides:
- `set_seed(seed)`: Initialize numpy RandomState
- `reset()`: Returns `(obs, done)` tuple
- `step(action)`: Returns `(obs, done, reward, reset)` tuple
- `observe()`: Returns observation dict with structure:
  ```python
  {
      "state_string": str,  # Human-readable game state
      "game_turn": int,     # Current turn number
      "state": dict         # Game-specific detailed state
  }
  ```
- `state_string()`: Visualization for logging
- `state_builder()`: Structured state for agent prompts

#### 5. Prompt System (src/realtimegym/prompts/)

Each game has:
- **Python module** (`freeway.py`, `snake.py`, `overcooked.py`): Contains `state_to_description()` function
- **YAML template** (`freeway.yaml`, etc.): Stores prompt strings as module constants
- **Module constants**: `ALL_ACTIONS`, `DEFAULT_ACTION`

`state_to_description(state, mode)` returns:
- String for `mode="reactive"` or `mode="planning"`
- Dict with both keys for `mode="agile"`

Prompt loading (agile_eval.py):
- Reads `configs/example-prompts.yaml` for game-to-module mapping
- Uses `_load_prompt_module()` to import via dotted module name or file path
- Supports both package imports and file paths for backward compatibility

#### 6. Evaluation Pipeline (src/realtimegym/agile_eval.py)

- Uses `ProcessPoolExecutor` for parallel evaluation across seeds
- Loads prompt modules dynamically via `_load_prompt_module()`
- Model configs are YAML files with structure:
  ```yaml
  model: "model-name"
  url: "https://api.provider.com"  # optional
  api_key: "${ENV_VAR_NAME}"
  inference_parameters:
    temperature: 0.7
    max_tokens: 1000
  tokenizer: "hf-model-id"  # required for AgileThinker with token budgets
  ```

### Special Considerations

#### Gemini API Exception
The codebase includes special handling for Gemini models where `completion_tokens` doesn't include thinking tokens. Uses `total_tokens - prompt_tokens` instead (see base.py:207-213).

#### Third-Party Code
`src/realtimegym/environments/overcooked_new/` contains vendored code from [Overcooked-AI](https://github.com/HumanCompatibleAI/overcooked_ai). This directory is excluded from type checking and linting (see pyproject.toml). See `THIRD_PARTY_NOTICE.md` for details.

#### Pre-commit Hooks
The project uses:
- Ruff for linting and formatting
- ty for type checking (via `uv run ty check`)
- Standard hooks (trailing-whitespace, end-of-file-fixer, check-yaml, etc.)

Pre-commit runs `uv run ty check` which excludes third-party and legacy code.

## Adding New Environments

1. Create environment class in `src/realtimegym/environments/` inheriting from `BaseEnv`
2. Implement required methods: `set_seed()`, `reset()`, `step()`, `state_string()`, `state_builder()`
3. Create `setup_env(seed, cognitive_load, save_trajectory_gifs)` function
4. Register in `_REGISTRY` in `src/realtimegym/__init__.py`
5. Create prompt module in `src/realtimegym/prompts/` with:
   - `state_to_description(state, mode)` function
   - `ALL_ACTIONS` and `DEFAULT_ACTION` constants
   - Optional YAML template file for prompt strings
6. Add mapping to `configs/example-prompts.yaml`

## Key Implementation Details

### Agent Think() Budget Semantics
- `timeout` parameter represents TOTAL budget for the turn
- For reactive agents: entire budget used for single inference
- For planning agents: budget consumed incrementally across turns until generation completes
- For agile agents: split between planning (timeout - internal_budget) and reactive (internal_budget)

### Boxed Action Format
LLM responses must end with `\boxed{ACTION}` format where ACTION is from `ALL_ACTIONS`. The framework:
- Extracts last `\boxed{}` occurrence via `extract_boxed()`
- Filters non-action characters using regex
- Falls back to `DEFAULT_ACTION` if parsing fails
- For reasoning models, wraps reasoning_content in `<think>...</think>` tags

### Observation Flow
1. Environment produces observation via `env.observe()`
2. Agent stores via `agent.observe(observation)`
3. Agent accesses stored observation in `agent.think()` via `self.current_observation`
4. This enables asynchronous thinking patterns where observation and decision are decoupled

### Logging Structure
Logs are pandas DataFrames with columns:
- `render`: state_string at each step
- `action`: action taken
- `reward`: reward received
- `plan`: planning output (if applicable)
- `model1_prompt`, `model1_response`, `model1_token_num`: reactive model logs
- `model2_prompt`, `model2_response`, `model2_token_num`: planning model logs

Saved to CSV via `agent.log(reward, reset)` after each step.
