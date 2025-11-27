# Factory Multi-Agent System

This document describes the hierarchical multi-agent architecture for the unmanned food factory environment.

## Architecture Overview

```
                    Product Request
                          │
                          ▼
                 ┌─────────────────┐
                 │ PartDesignAgent │  🧠 Production Planning
                 │  (부품설계 에이전트)  │
                 └─────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │Maintenance   │ │ QualityAgent │ │ Coordinator  │
  │Agent         │ │ (품질검사)    │ │ Agent        │
  │(설비관리)     │ │              │ │ (로봇조정)    │
  └──────────────┘ └──────────────┘ └──────────────┘
        │                 │                 │
        └─────────────────┴─────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Lower Agents   │  🤖 Execution
                 │  (Rule-based)   │
                 │                 │
                 │ • RobotArm (20) │
                 │ • Logistics(24) │
                 └─────────────────┘
```

## Agent Responsibilities

### 1. PartDesignAgent (부품설계 에이전트)

**Role:** High-level production planning

**Inputs:**
- Product requests (type, quantity, priority)
- Station availability and capacity
- Robot availability statistics
- Maintenance risk scores (from MaintenanceAgent)
- Quality metrics (from QualityAgent)

**Outputs:**
```python
{
    "product_type": "ricotta_salad",
    "quantity": 10,
    "production_line": 0,
    "route": ["Storage", "Washer", "Cutter", "Plating", "Sealing", "VisionQA"],
    "batch_size": 5,
    "num_batches": 2,
    "estimated_time": 120,
    "robot_allocation": {
        "Washer": {"robot_arms": 1, "logistics": 2},
        "Cutter": {"robot_arms": 1, "logistics": 1},
        # ...
    },
    "notes": "Using Line 0, avoiding Cooker (not needed for salad)"
}
```

**Decision Factors:**
- Recipe requirements (which stations needed)
- Station health and availability
- Equipment maintenance risk
- Recent quality metrics
- Robot capacity and workload

**Files:**
- `src/realtimegym/agents/factory/part_design_agent.py`
- `src/realtimegym/prompts/factory/part_design.py`
- `src/realtimegym/prompts/factory/part_design.yaml`

---

### 2. MaintenanceAgent (설비관리 에이전트)

**Role:** Equipment health monitoring and predictive maintenance

**Inputs:**
- Station operation counts
- Last maintenance timestamps
- Error logs and fault history
- Sensor data (temperature, vibration, timing)

**Outputs:**
```python
{
    "station_risk_scores": {
        "Washer_0": "Low",
        "Cutter_0": "Medium",
        "Cooker_0": "High",
        "Sealing_1": "Critical"
    },
    "maintenance_recommendations": [
        {
            "station": "Sealing_1",
            "urgency": "immediate",
            "reason": "850 operations since last maintenance",
            "estimated_downtime": 30
        }
    ],
    "predicted_failures": [
        {
            "station": "Cutter_1",
            "probability": 0.35,
            "timeframe": "48_hours",
            "impact": "Medium production disruption"
        }
    ],
    "overall_fleet_health": 0.78,
    "notes": "Cooker approaching maintenance window..."
}
```

**Risk Scoring:**
- **Low:** < 50% of maintenance interval, no errors
- **Medium:** 50-75% of interval, minor anomalies
- **High:** > 75% of interval, or 3+ errors in last 10 ops
- **Critical:** Immediate maintenance required, degradation detected

**Coordination:**
- Provides risk scores to **PartDesignAgent** for route planning
- Alerts **CoordinatorAgent** when stations need shutdown
- Informs **QualityAgent** of equipment wear that may affect quality

**Files:**
- `src/realtimegym/agents/factory/maintenance_agent.py`
- `src/realtimegym/prompts/factory/maintenance.py`
- `src/realtimegym/prompts/factory/maintenance.yaml`

---

### 3. QualityAgent (품질검사 에이전트)

**Role:** Quality control and defect analysis

**Inputs:**
- Vision QA inspection results
- Production history with quality outcomes
- Defect logs (type, severity, frequency)
- Station process parameters
- Workload metrics (robot utilization)

**Outputs:**
```python
{
    "quality_metrics": {
        "overall_defect_rate": 0.023,  # 2.3%
        "by_product": {
            "ricotta_salad": 0.015,
            "shrimp_fried_rice": 0.032,
            "tomato_pasta": 0.021
        },
        "by_line": {
            "line_0": 0.018,
            "line_1": 0.028
        },
        "recent_trend": "degrading"
    },
    "defect_analysis": {
        "top_defect_types": [
            {"type": "portion", "count": 12, "percentage": 0.4},
            {"type": "appearance", "count": 8, "percentage": 0.27}
        ],
        "patterns_detected": [
            {
                "pattern": "systematic",
                "description": "Portion defects on Line 1 Plating",
                "severity": "medium"
            }
        ]
    },
    "root_causes": [
        {
            "defect_type": "portion",
            "suspected_cause": "Plating_1 calibration drift",
            "evidence": "Under-filling by ~15%",
            "confidence": 0.85
        }
    ],
    "recommendations": [
        {
            "action": "adjust_parameter",
            "target": "Plating_1",
            "parameter": "portion_size",
            "current_value": 200,
            "recommended_value": 230
        }
    ],
    "alerts": [
        {
            "severity": "warning",
            "message": "Shrimp Fried Rice defect rate (3.2%) approaching threshold (5%)"
        }
    ]
}
```

**Defect Categories:**
- **Appearance:** Color, presentation, plating
- **Portion:** Under/over-filled, missing ingredients
- **Contamination:** Foreign objects, cross-contamination
- **Packaging:** Seal defects, label errors
- **Temperature:** Out of safe range

**Coordination:**
- Provides quality metrics to **PartDesignAgent** for planning
- Requests maintenance from **MaintenanceAgent** for equipment issues
- Recommends parameter adjustments to **CoordinatorAgent**

**Files:**
- `src/realtimegym/agents/factory/quality_agent.py`
- `src/realtimegym/prompts/factory/quality.py`
- `src/realtimegym/prompts/factory/quality.yaml`

---

### 4. CoordinatorAgent (로봇조정 에이전트)

**Role:** Real-time robot task assignment and execution control

**Inputs:**
- Current factory state (all stations, robots, queues)
- Production plan (from PartDesignAgent)
- Equipment status (from MaintenanceAgent)
- Quality recommendations (from QualityAgent)

**Outputs:**
```python
{
    "logistics_0": {
        "task_type": "pick_and_deliver",
        "from_location": [3, 5],
        "to_location": [8, 10],
        "priority": 5,
        "item": "ricotta_salad_batch_1"
    },
    "arm_0": {
        "task_type": "operate_station",
        "station_name": "Washer",
        "operation": "wash",
        "duration": 10
    },
    "logistics_5": {
        "task_type": "wait",
        "reason": "No items ready for pickup"
    }
    # ... (task for each of 44 robots)
}
```

**Task Types:**
- **pick_and_deliver:** Move items between stations (logistics robots)
- **operate_station:** Perform station operations (robot arms)
- **wait:** Idle until needed

**Decision Making:**
- Assigns tasks based on current production state
- Prioritizes items based on production plan
- Balances workload across robots
- Avoids assigning tasks to high-risk stations

**Files:**
- `src/realtimegym/agents/factory/coordinator_agent.py`
- `src/realtimegym/prompts/factory/coordinator.py`
- `src/realtimegym/prompts/factory/coordinator.yaml`

---

## Multi-Agent Coordination Flow

### Phase 1: Production Planning (Step 0)

```
PartDesignAgent receives product request
    ↓
Analyzes: station capacity, robot availability, maintenance risk, quality history
    ↓
Generates: route, batch size, robot allocation plan
    ↓
Shares plan with other agents
```

### Phase 2: Equipment Monitoring (Every 10 steps)

```
MaintenanceAgent assesses all stations
    ↓
Analyzes: operation counts, time since maintenance, error patterns
    ↓
Generates: risk scores, maintenance recommendations, failure predictions
    ↓
Updates PartDesignAgent and CoordinatorAgent on high-risk equipment
```

### Phase 3: Quality Monitoring (Every 15 steps)

```
QualityAgent analyzes inspection results
    ↓
Detects: defect patterns, root causes, systematic issues
    ↓
Generates: quality metrics, parameter recommendations, alerts
    ↓
Provides feedback to PartDesignAgent and CoordinatorAgent
```

### Phase 4: Task Execution (Every step)

```
CoordinatorAgent observes current state
    ↓
Considers: production plan, maintenance risks, quality recommendations
    ↓
Assigns tasks to all 44 robots
    ↓
Environment executes tasks
    ↓
Repeat
```

---

## Running the Multi-Agent System

### Basic Usage

```bash
python examples/factory_multi_agent_integration.py \
    --model-config configs/example-claude-coordinator.yaml \
    --steps 100 \
    --budget 2000
```

### With Different Models

```bash
# GPT-4o (balanced cost/performance)
python examples/factory_multi_agent_integration.py \
    --model-config configs/example-gpt4o-coordinator.yaml

# DeepSeek (lowest cost)
python examples/factory_multi_agent_integration.py \
    --model-config configs/example-deepseek-coordinator.yaml

# Claude (highest performance)
python examples/factory_multi_agent_integration.py \
    --model-config configs/example-claude-coordinator.yaml
```

---

## Inter-Agent Communication

The agents communicate by sharing structured information:

### PartDesignAgent → Maintenance/Quality Agents
- **Query:** "What are the risk scores for Cooker_0 and Cutter_1?"
- **Response:** Included in state dict when PartDesign makes decisions

### MaintenanceAgent → PartDesignAgent
- **Signal:** "Cooker_0 has High maintenance risk"
- **Impact:** PartDesign may choose alternative route or delay production

### QualityAgent → PartDesignAgent
- **Signal:** "Shrimp Fried Rice defect rate is 3.2%"
- **Impact:** PartDesign may adjust batch sizes or change parameters

### All Upper Agents → CoordinatorAgent
- **Plan:** Production route and batch sizes
- **Constraints:** Avoid high-risk stations, implement quality adjustments
- **Execution:** Coordinator follows plan while respecting constraints

---

## Configuration

### Model Configuration (YAML)

All agents use the same model config format:

```yaml
# configs/example-claude-coordinator.yaml
model: claude-sonnet-4
api_key: ${ANTHROPIC_API_KEY}
inference_parameters:
  temperature: 0.3
  max_tokens: 2000
```

### Token Budget

Each agent gets a token budget per decision:
- **PartDesignAgent:** 2000 tokens (complex planning)
- **MaintenanceAgent:** 2000 tokens (analytical assessment)
- **QualityAgent:** 2000 tokens (defect analysis)
- **CoordinatorAgent:** 2000 tokens (task assignment)

Total budget per full cycle: ~8000 tokens (when all agents run)

---

## Logging and Monitoring

Each agent saves detailed logs:

```
logs/
├── part_design_agent.csv      # Production plans
├── maintenance_agent.csv      # Equipment assessments
├── quality_agent.csv          # Defect analyses
└── coordinator_agent.csv      # Task assignments
```

Log columns:
- `render`: Environment state
- `action`: Agent decision
- `reward`: Environment reward
- `model1_prompt`: Input to LLM
- `model1_response`: LLM output
- `model1_token_num`: Tokens used

---

## Extension Points

### Adding New Upper Agents

1. Create agent class inheriting from `BaseAgent`
2. Implement `think()` method with LLM inference
3. Create prompt module (`.py` + `.yaml`)
4. Add to `src/realtimegym/agents/factory/__init__.py`
5. Integrate in coordination loop

### Adding New Station Types

1. Define station class in `factory_env.py`
2. Add to `RECIPES` dict with processing requirements
3. Update PartDesign prompts with new station
4. Update Maintenance prompts with maintenance intervals

### Customizing Decision Logic

Edit YAML prompt files to adjust:
- Risk scoring criteria
- Quality thresholds
- Planning priorities
- Task assignment strategies

---

## Performance Considerations

### Token Costs

Approximate tokens per 100-step simulation:
- PartDesignAgent: 1 call × 2000 = 2,000 tokens
- MaintenanceAgent: 10 calls × 2000 = 20,000 tokens
- QualityAgent: 7 calls × 2000 = 14,000 tokens
- CoordinatorAgent: 100 calls × 2000 = 200,000 tokens

**Total: ~236,000 tokens per 100 steps**

### Optimization Strategies

1. **Reduce Coordinator Frequency:** Call every N steps instead of every step
2. **Cache Repeated Decisions:** Reuse task assignments when state unchanged
3. **Use Smaller Models:** DeepSeek for coordinator, Claude for planning
4. **Batch Decisions:** Plan multiple steps ahead

---

## Troubleshooting

### Agent Not Making Decisions

Check:
1. API key set in `.env` file
2. Model config path correct
3. Token budget sufficient (minimum 1000)
4. LLM response contains `\boxed{...}` format

### JSON Parsing Errors

- Agents expect JSON in `\boxed{}` format
- Check prompt templates follow format requirements
- Increase temperature if LLM produces malformed JSON

### High Token Usage

- Reduce state information passed to agents
- Use shorter prompt templates
- Decrease decision frequency for monitoring agents
- Consider using smaller models for routine decisions

---

## References

- **PDF Specification:** `public/env_specification.pdf` (pages 5, 17-22)
- **CoordinatorAgent Documentation:** `FACTORY_COORDINATOR_SUMMARY.md`
- **BaseAgent Implementation:** `src/realtimegym/agents/base.py`
- **Factory Environment:** `src/realtimegym/environments/factory/`
