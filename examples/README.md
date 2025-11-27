# RealtimeGym Examples

This directory contains example scripts demonstrating how to use RealtimeGym.

## Quick Start

All examples can be run directly with Python:

```bash
python examples/basic_usage.py
```

## Available Examples

### 1. `basic_usage.py` - Getting Started
The simplest example showing the core API loop:
- Creating an environment with `realtimegym.make()`
- Implementing a basic agent
- Running the observe → think → act loop

**Run:** `python examples/basic_usage.py`

### 2. `all_environments.py` - Environment Tour
Demonstrates all three environments (Freeway, Snake, Overcooked):
- How the same agent interface works across all environments
- Basic environment differences
- Handling different action spaces

**Run:** `python examples/all_environments.py`

### 3. `custom_agent.py` - Advanced Agent
Shows how to create a sophisticated agent:
- Maintaining observation history
- State management across steps
- Custom decision-making logic
- Collecting agent statistics

**Run:** `python examples/custom_agent.py`

### 4. `difficulty_levels.py` - Difficulty Comparison
Explores all difficulty levels (Easy, Medium, Hard):
- Testing v0, v1, v2 variants
- Comparing performance across difficulties
- Adaptive agent strategies

**Run:** `python examples/difficulty_levels.py`

### 5. `factory_basic.py` - Factory Environment (Prototype)
Demonstrates the unmanned factory environment:
- Multi-agent system with 44 robots (20 arms + 24 logistics)
- Production workflow for 3 food products
- Automated workflow management (prototype mode)
- KPI tracking (production, lead time, defect rate)

**Run:** `python examples/factory_basic.py`

### 6. `factory_coordinator_llm.py` - LLM-Based Coordinator (Advanced)
**NEW!** Shows the complete multi-agent factory with LLM control:
- CoordinatorAgent using GPT-4o/DeepSeek/Claude
- LLM decides task assignments for all 44 robots
- Real-time token-budgeted decision making
- Salad production scenario

**Prerequisites:**
1. Copy `.env.example` to `.env`
2. Add your API key (OPENAI_API_KEY, DEEPSEEK_API_KEY, or ANTHROPIC_API_KEY)

**Run:**
```bash
# Using GPT-4o (default)
python examples/factory_coordinator_llm.py

# Using DeepSeek (cost-effective)
python examples/factory_coordinator_llm.py --model-config configs/example-deepseek-coordinator.yaml

# Using Claude (high-performance)
python examples/factory_coordinator_llm.py --model-config configs/example-claude-coordinator.yaml

# Custom settings
python examples/factory_coordinator_llm.py --steps 100 --budget 4000
```

## The RealtimeGym API

All examples follow the standard API pattern:

```python
import realtimegym

# 1. Create environment
env, seed, renderer = realtimegym.make('Freeway-v0', seed=0, render=False)

# 2. Initialize agent
agent = MyAgent()
DEFAULT_ACTION = "S"

# 3. Reset environment
obs, done = env.reset()

# 4. Game loop
while not done:
    # Agent observes
    agent.observe(obs)

    # Agent thinks
    agent.think(timeout=8192)

    # Agent acts
    action = agent.act() or DEFAULT_ACTION

    # Environment steps
    obs, done, reward, reset = env.step(action)
```

## Environment IDs

Available environments:

| Environment | Easy | Medium | Hard |
|------------|------|--------|------|
| Freeway    | `Freeway-v0` | `Freeway-v1` | `Freeway-v2` |
| Snake      | `Snake-v0` | `Snake-v1` | `Snake-v2` |
| Overcooked | `Overcooked-v0` | `Overcooked-v1` | `Overcooked-v2` |
| Factory    | `Factory-v0` | `Factory-v1` | `Factory-v2` |

## Agent Interface

Your agent should implement three methods:

```python
class MyAgent:
    def observe(self, observation):
        """Receive observation (dict) from environment."""
        pass

    def think(self, timeout=None):
        """Process observation and decide action."""
        pass

    def act(self):
        """Return chosen action (str) or None for default."""
        pass
```

## Common Actions

- **Freeway**: `U` (up), `D` (down), `S` (stay)
- **Snake**: `U` (up), `D` (down), `L` (left), `R` (right), `S` (stay)
- **Overcooked**: `U`, `D`, `L`, `R`, `I` (interact), `S` (stay)

## Next Steps

1. Start with `basic_usage.py` to understand the fundamentals. See `basic_renderer.py` to understand how to automatically get visualization for game trajectory.
2. Explore `all_environments.py` to see environment differences
3. Study `custom_agent.py` to learn advanced agent patterns
4. Test `difficulty_levels.py` to understand difficulty scaling

For more information, see the main [README.md](../README.md) and [CONTRIBUTING.md](../CONTRIBUTING.md).
