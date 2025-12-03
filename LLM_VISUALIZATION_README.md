# LLM-Based Agents Visualization

## Overview

`visualize_factory_with_llm_agents.py` - Factory 환경에서 **LLM 기반 에이전트**가 실시간으로 전략적 결정을 내리는 모습을 시각화합니다.

## Features

### 🤖 LLM AI 에이전트

**MetaPlannerAgent (전략 기획)**:
- 실시간 상황 평가
- AI 기반 전략적 우선순위 설정
- 다중 에이전트 조정
- 위험 식별 및 즉각 조치 권장

**DesignAgent (시스템 설계)**:
- 생산 시스템 평가
- 병목 현상 근본 원인 분석
- AI 기반 설계 권장사항
- 구현 계획 수립

### 🎮 시각화 특징

**메인 화면**:
- 20x30 공장 그리드
- 2개 생산 라인
- 스테이션 및 로봇 실시간 표시
- 제품 생산 과정 애니메이션

**AI 컨트롤 패널** (우측):
- LLM 활성화 상태 표시
- Meta Planner AI 분석
  - 상황 평가 (실시간)
  - AI 전략적 우선순위
  - AI 권장 조치
- Design Agent AI 분석
  - 시스템 평가
  - AI 설계 조언 (근거 포함)
- 스테이션 상태 모니터링

## Setup

### 1. API 키 설정 (LLM 사용)

`.env` 파일 생성:

```bash
# OpenAI GPT-4 사용
OPENAI_API_KEY=sk-your-openai-key-here

# 또는 DeepSeek V3 사용 (더 저렴)
DEEPSEEK_API_KEY=your-deepseek-key-here
```

### 2. 모델 설정 (선택 사항)

기본적으로 `configs/example-meta-planner.yaml` 사용 (GPT-4o)

다른 모델 사용하려면 설정 파일 수정:

```yaml
# configs/example-meta-planner.yaml
model: "gpt-4o-mini"  # 더 저렴한 모델
api_key: "${OPENAI_API_KEY}"
inference_parameters:
  temperature: 0.7
  max_tokens: 1500  # 토큰 예산
```

## Usage

### 기본 실행

```bash
python visualize_factory_with_llm_agents.py
```

**API 키가 없으면**: 규칙 기반 fallback 모드로 자동 전환
**API 키가 있으면**: LLM AI 모드로 실행

### 조작법

| 키 | 동작 |
|----|------|
| **SPACE** | 속도 증가 (1x → 2x → 4x → 8x → 16x → 32x) |
| **DOWN** | 속도 감소 |
| **P** | 일시정지/재개 |
| **ESC** | 종료 및 최종 AI 분석 표시 |

## What You'll See

### LLM AI 모드 (API 키 설정 시)

**시작 메시지**:
```
Creating Factory environment with LLM-based intelligent agents...
Initializing LLM agents...
[OK] MetaPlannerAgent configured with LLM (GPT-4o)
[OK] DesignAgent configured with LLM (GPT-4o)
[INFO] LLM agents active - decisions will be powered by AI!
```

**화면 표시**:
```
┌────────────────────────────────┬─────────────────────┐
│                                │  AI AGENT CONTROL   │
│     Factory Grid (20x30)       │  Powered by LLMs    │
│   [생산 라인 애니메이션]          │                     │
│                                │  META PLANNER       │
│   스테이션: Washer, Cutter...   │  Status: EXCELLENT  │
│   로봇: 이동 및 작업             │  [AI]               │
│   제품: 생산 과정                │  Assessment: ...    │
│                                │  AI Strategic:      │
│                                │    • Priority 1     │
│                                │    • Priority 2     │
│                                │  AI Recommendations:│
│                                │    → Action 1       │
│                                │                     │
│                                │  DESIGN AGENT       │
│                                │  Line Balance: 95%  │
│                                │  [AI]               │
│                                │  AI Design Advice:  │
├────────────────────────────────┤    • Recommendation │
│ Progress: [========>   ] 80%  │      ↳ Rationale    │
└────────────────────────────────┴─────────────────────┘
```

**실시간 AI 분석 출력**:
```
[Step 20] Meta Planner AI: Current production is proceeding well with...
[Step 20] Design Agent AI: The system shows good line balance but could...
[OK] [Line 1] Product #1 completed at step 112
[Step 40] Meta Planner AI: Maintain current strategy while monitoring...
[Step 40] Design Agent AI: Consider increasing buffer capacity at...
```

### Fallback 모드 (API 키 없을 시)

**시작 메시지**:
```
[INFO] MetaPlannerAgent using rule-based fallback: ...
[INFO] DesignAgent using rule-based fallback: ...
[INFO] Using rule-based fallback - set API keys in .env for LLM mode
```

**화면 표시**:
- 규칙 기반 메트릭 및 권장사항 표시
- "[AI]" 아이콘 없음
- 상단에 "Rule-based fallback mode" 표시

## Performance & Cost

### Agent Update Frequency

기본 설정: **20 스텝마다 LLM 호출**

```python
agent_update_interval = 20  # Update every 20 steps
```

이유:
- API 비용 최적화
- 전략적 결정은 매 스텝마다 필요하지 않음
- 빠른 시뮬레이션 속도 유지

### Cost Estimation

**GPT-4o 사용 시**:
- 에이전트 업데이트당: ~$0.045
- 400 스텝 시뮬레이션: 20회 업데이트 = ~$0.90
- 1000 스텝 시뮬레이션: 50회 업데이트 = ~$2.25

**GPT-4o-mini 사용 시** (10배 저렴):
- 400 스텝: ~$0.09
- 1000 스텝: ~$0.23

**DeepSeek V3 사용 시** (20배 저렴):
- 400 스텝: ~$0.045
- 1000 스텝: ~$0.11

### Cost Optimization

#### 1. Update Interval 조정

```python
# 스크립트에서 수정
agent_update_interval = 50  # 50스텝마다 (비용 60% 감소)
```

#### 2. 저렴한 모델 사용

```yaml
# configs/example-meta-planner.yaml
model: "gpt-4o-mini"  # 또는 "deepseek-chat"
```

#### 3. 토큰 예산 감소

```python
meta_planner.config_model1("config.yaml", internal_budget=1000)  # 1500 → 1000
```

## AI Decision Examples

### Meta Planner AI 출력

**상황 평가**:
```
"Current production is behind schedule due to insufficient material
flow. Line 1 is operating at 80% capacity while Line 2 is at 60%."
```

**전략적 우선순위**:
```
1. "Accelerate production rate on both lines"
2. "Balance workload between Line 1 and Line 2"
3. "Monitor quality metrics to prevent defects"
```

**즉각 조치**:
```
→ "Activate reserve robots to increase throughput"
→ "Adjust batch sizes to optimize station utilization"
```

### Design Agent AI 출력

**시스템 평가**:
```
"The production system has good line balance (95%) but shows
underutilized capacity at early stages (Washer/Cutter)."
```

**설계 조언**:
```
• "Increase buffer size at Washer stations"
  ↳ "Prevents starvation during peak demand periods"

• "Add parallel Cutter station on Line 1"
  ↳ "Reduces bottleneck and improves throughput by 20%"
```

## Comparison: LLM vs Rule-Based

| 특징 | Rule-Based | LLM AI |
|------|-----------|--------|
| 분석 속도 | 즉각적 | 1-3초 |
| 인사이트 | 정량적 메트릭 | 정성적 이해 + 정량적 |
| 적응력 | 고정된 규칙 | 상황에 따라 적응 |
| 설명력 | 수치만 | 자연어 근거 제공 |
| 비용 | 무료 | API 비용 발생 |
| 신뢰성 | 100% 안정 | 99% 안정 (API 의존) |

**권장**: LLM AI 모드로 실행하여 인텔리전트한 분석 경험!

## Troubleshooting

### "Environment variable 'OPENAI_API_KEY' not found"

**해결**: `.env` 파일 생성
```bash
echo "OPENAI_API_KEY=sk-your-key" > .env
```

### LLM 분석이 화면에 표시되지 않음

**원인**: API 키 미설정 또는 잘못된 키

**확인**:
```bash
cat .env  # API 키 확인
```

**해결**: 올바른 API 키 설정

### "Error parsing meta planner response"

**정상 동작**: LLM이 JSON 외에 추가 텍스트 생성

**처리**: 자동으로 fallback 처리됨, 걱정 불필요

### 시뮬레이션이 느림

**원인**: LLM API 호출 시간

**해결**:
1. `agent_update_interval` 증가 (20 → 50)
2. 더 빠른 모델 사용 (gpt-4o-mini)
3. 토큰 예산 감소

### 비용이 너무 높음

**해결**:
1. Update interval 증가
2. DeepSeek V3 사용 (20배 저렴)
3. 토큰 예산 감소
4. 짧은 시뮬레이션 실행

## Final Statistics Example

```
======================================================================
                         SIMULATION COMPLETE
======================================================================

Production Statistics:
  Total Steps: 385
  Completed Products: 10/10
  Defective Products: 0
  Quality Rate: 100.0%
  Final Reward: 200.00

----------------------------------------------------------------------
                      FINAL AI AGENT ANALYSIS
----------------------------------------------------------------------

Meta Planner Final Assessment:
  AI Assessment: Production completed successfully with excellent
                 quality. Both production lines operated efficiently
                 with minimal resource waste.
  AI Priorities:
    - Maintain current operational parameters for future runs
    - Continue monitoring quality metrics
    - Optimize robot allocation for next batch

Design Agent Final Analysis:
  AI Assessment: The system achieved good line balance (70%) with
                 room for improvement in early-stage utilization.
  AI Recommendations:
    - Increase Washer input buffers to 8-10 items
    - Consider adding parallel Cutter at Line 2
    - Optimize robot paths to reduce collisions

======================================================================
LLM AI was active during this simulation!
Decisions were powered by Large Language Models.
======================================================================
```

## Files Created

- **Script**: `visualize_factory_with_llm_agents.py` (612 lines)
- **Logs**:
  - `logs/llm_meta_planner.csv` (decisions log)
  - `logs/llm_design_agent.csv` (decisions log)

## Advanced Usage

### Multiple Runs for Comparison

```bash
# Run 1: LLM mode
OPENAI_API_KEY=sk-... python visualize_factory_with_llm_agents.py

# Run 2: Rule-based mode (rename .env temporarily)
mv .env .env.backup
python visualize_factory_with_llm_agents.py
mv .env.backup .env

# Compare logs
python -c "
import pandas as pd
llm = pd.read_csv('logs/llm_meta_planner.csv')
print('LLM decisions:', len(llm))
print(llm[['meta_planner_response']].head())
"
```

### Custom Model Configuration

```python
# Edit script to use different models
meta_planner.config_model1(
    "configs/example-deepseek-meta-planner.yaml",  # DeepSeek V3
    internal_budget=1500
)
```

### Real-time Decision Monitoring

```python
# Add after meta_planner.think()
decision = meta_planner.get_decision()
if "llm_analysis" in decision:
    with open("realtime_decisions.txt", "a") as f:
        f.write(f"Step {step_count}: {decision['llm_analysis']}\n")
```

## See Also

- `LLM_AGENTS_GUIDE.md` - Complete LLM agent usage guide
- `LLM_AGENTS_SUMMARY.md` - Implementation summary
- `test_llm_upper_agents.py` - Testing script
- `configs/` - Model configuration files

## Tips

1. **First Run**: Start without API key to see rule-based mode
2. **LLM Test**: Add API key and watch AI decisions
3. **Cost Control**: Increase update interval for longer runs
4. **Model Choice**: Use DeepSeek for cost-effective AI
5. **Analysis**: Check logs for detailed AI reasoning

Enjoy watching AI agents make intelligent decisions in real-time! 🤖✨
