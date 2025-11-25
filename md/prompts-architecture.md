# Prompts 아키텍처: Agent와 게임 지식의 분리

## 핵심 통찰

> "Agent는 '어떻게 생각할지'를 알고, Prompts는 '무엇을 생각할지'를 알려준다."

환경마다 agents가 하는 세부 역할이 다르지만, agents들이 환경마다 정의되어 있지 않은 이유는 **실질적인 명령이 prompts를 활용한 명령이기 때문**입니다.

---

## 설계 원리: 관심사의 분리 (Separation of Concerns)

```
┌─────────────────────────────────────────┐
│         Agent (범용 엔진)                │
│  "HOW to think" (어떻게 생각할 것인가)    │
│                                          │
│  - LLM API 호출                          │
│  - 토큰/시간 관리                        │
│  - 응답 파싱 (extract_boxed)            │
│  - Reactive vs Planning vs Agile 전략   │
└────────────┬────────────────────────────┘
             │ 의존성 주입 (Dependency Injection)
             │ prompts 모듈을 받아옴
             ↓
┌─────────────────────────────────────────┐
│        Prompts (게임별 지식)             │
│  "WHAT to think about" (무엇을)          │
│                                          │
│  - 게임 규칙 설명                        │
│  - 상태 → 자연어 변환                    │
│  - ALL_ACTIONS, DEFAULT_ACTION          │
│  - Freeway vs Snake vs Overcooked       │
└─────────────────────────────────────────┘
```

---

## 코드 증거

### 1. Agent 생성 시 prompts를 주입받음

**agile_eval.py:99-122**
```python
params = {
    "prompts": _load_prompt_module(prompt_config[args.game]),  # 게임별 prompts
    "file": file,
    "time_unit": args.time_unit,
}

if args.mode == "reactive":
    agent = ReactiveAgent(**params)      # 같은 클래스
elif args.mode == "planning":
    agent = PlanningAgent(**params)      # 같은 클래스
elif args.mode == "agile":
    agent = AgileThinker(**params)       # 같은 클래스
```

**모든 게임에 동일한 Agent 클래스 사용!**

---

### 2. Agent는 prompts를 통해서만 게임을 "봄"

**ReactiveAgent.think() (reactive.py:26-35)**
```python
def think(self, timeout: Optional[float] = None) -> None:
    observation = self.current_observation

    # ✅ prompts에게 "상태를 어떻게 설명해?" 물어봄
    prompt_gen = self.prompts.state_to_description(
        observation["state"], mode="reactive"
    )

    # LLM에게 프롬프트 전달
    messages = [{"role": "user", "content": prompt_gen}]
    text, token_num = self.reactive_inference(messages, budget)

    # ✅ prompts에게 "어떤 액션이 유효해?" 물어봄
    self.action = re.sub(
        r"[^" + self.prompts.ALL_ACTIONS + "]", "", extract_boxed(text)
    )

    # ✅ prompts에게 "기본 액션은 뭐야?" 물어봄
    if self.action == "":
        self.action = self.prompts.DEFAULT_ACTION
```

**Agent는 게임 로직을 전혀 모릅니다!**

---

### 3. Prompts가 제공하는 인터페이스

모든 prompts 모듈은 다음 계약(contract)을 준수합니다:

```python
# 필수 상수
ALL_ACTIONS: str           # "UDS" (Freeway) or "LRUD" (Snake)
DEFAULT_ACTION: str        # "U" or "S"

# 필수 함수
def state_to_description(state: dict, mode: str) -> str | dict:
    """게임 상태를 LLM이 이해할 수 있는 자연어로 변환"""
    pass
```

**게임별 차이는 여기에만 존재합니다!**

---

## 실제 예시

### Freeway 실행 시

```python
# 1. Freeway prompts 로드
freeway_prompts = import_module("realtimegym.prompts.freeway")
# freeway_prompts.ALL_ACTIONS = "UDS"
# freeway_prompts.DEFAULT_ACTION = "U"

# 2. Agent에 주입
agent = ReactiveAgent(prompts=freeway_prompts, ...)

# 3. Agent 실행
agent.observe(observation)
agent.think(timeout=8192)
# → freeway_prompts.state_to_description() 호출
# → "Player at (0,3), cars at..." 프롬프트 생성
# → LLM이 "U" 반환
# → freeway_prompts.ALL_ACTIONS로 검증
```

### Snake로 바꾸면?

```python
# 1. Snake prompts 로드
snake_prompts = import_module("realtimegym.prompts.snake")
# snake_prompts.ALL_ACTIONS = "LRUD"  # ← 다름!
# snake_prompts.DEFAULT_ACTION = "S"   # ← 다름!

# 2. 똑같은 Agent 클래스에 주입
agent = ReactiveAgent(prompts=snake_prompts, ...)

# 3. Agent 실행 (코드 동일!)
agent.observe(observation)
agent.think(timeout=8192)
# → snake_prompts.state_to_description() 호출  # ← 다른 함수!
# → "Snake head at (5,5), food at..." 프롬프트 생성
# → LLM이 "L" 반환
# → snake_prompts.ALL_ACTIONS로 검증
```

**Agent 코드는 한 줄도 바꾸지 않음!**

---

## Prompts 폴더 구조

```
prompts/
├── __init__.py
├── freeway.py        ← Python 로직
├── freeway.yaml      ← 프롬프트 템플릿
├── snake.py          ← Python 로직
├── snake.yaml        ← 프롬프트 템플릿
├── overcooked.py     ← Python 로직
└── overcooked.yaml   ← 프롬프트 템플릿
```

각 게임마다 **2개의 파일**이 쌍을 이룹니다:
- **`.py` 파일**: 상태 변환 로직 (코드)
- **`.yaml` 파일**: 프롬프트 텍스트 (템플릿)

---

## Python 파일 (`.py`)의 구조

### 1. 필수 상수 정의
```python
ALL_ACTIONS = "UDS"      # Freeway: Up, Down, Stay
DEFAULT_ACTION = "U"     # 시간 내 결정 못하면 사용할 기본 액션
```

### 2. YAML 템플릿 로드
```python
_TEMPLATE_FILE = Path(__file__).parent / "freeway.yaml"
with open(_TEMPLATE_FILE, "r") as f:
    _TEMPLATES = yaml.safe_load(f)

# 템플릿을 모듈 변수로 export
SLOW_AGENT_PROMPT = _TEMPLATES["slow_agent_prompt"]      # Planning용
FAST_AGENT_PROMPT = _TEMPLATES["fast_agent_prompt"]      # Reactive용
ACTION_FORMAT_PROMPT = _TEMPLATES["action_format_prompt"]
CONCLUSION_FORMAT_PROMPT = _TEMPLATES["conclusion_format_prompt"]
```

### 3. 핵심 함수: `state_to_description()`
```python
def state_to_description(state_for_llm: dict, mode: str) -> str | dict:
    """
    게임 상태 딕셔너리를 에이전트 타입에 맞는 프롬프트로 변환

    Args:
        state_for_llm: 게임 상태 정보
        mode: "reactive", "planning", "agile" 중 하나

    Returns:
        - reactive/planning: 완성된 프롬프트 문자열
        - agile: {"planning": ..., "reactive": ...} 딕셔너리
    """
```

---

## YAML 파일 (`.yaml`)의 구조

**4가지 프롬프트 타입:**

1. **`slow_agent_prompt`**: Planning 에이전트용 (전략 수립)
   - 여러 턴을 내다보고 계획 수립
   - 게임 역학 상세 설명
   - 최적 경로 탐색 지시

2. **`fast_agent_prompt`**: Reactive 에이전트용 (즉각 반응)
   - 현재 상태만 고려
   - 단일 액션 결정
   - 이전 계획 참고 (옵션)

3. **`action_format_prompt`**: Planning 출력 형식
   ```
   \boxed{
   Turn t_1: a_{t_1}
   Turn t_1 + 1: a_{t_1 + 1}
   ...
   }
   ```

4. **`conclusion_format_prompt`**: Agile 출력 형식
   - 액션 시퀀스 + 전략 요약

---

## 에이전트별 프롬프트 조합

### ReactiveAgent (빠른 반응)
```python
if mode == "reactive":
    return FAST_AGENT_PROMPT + model1_description
```
→ 현재 상태만 보고 **1턴의 액션** 결정

### PlanningAgent (전략 계획)
```python
elif mode == "planning":
    return SLOW_AGENT_PROMPT + ACTION_FORMAT_PROMPT + model2_description
```
→ 여러 턴을 내다보고 **액션 시퀀스** 생성

### AgileThinker (하이브리드)
```python
elif mode == "agile":
    return {
        "planning": SLOW_AGENT_PROMPT + CONCLUSION_FORMAT_PROMPT + model2_description,
        "reactive": FAST_AGENT_PROMPT + model1_description
    }
```
→ Planning 모델의 전략 + Reactive 모델의 실시간 결정

---

## 작동 흐름: Freeway 예시

### 1. 환경이 생성한 게임 상태
```python
state = {
    "game_turn": 5,
    "player_states": 3,  # y 좌표
    "car_states": [
        [1, 2, "right", 1, 3],  # [레인, 머리, 방향, 속도, 길이]
        [2, 5, "left", 2, 4],
        ...
    ]
}
```

### 2. Python이 표 형식으로 변환
```python
description = """
**Player Position:** ( (0, 3) )
**Car State**:
| Freeway k | Cars (head h, tail τ, direction d, speed s) |
|-----------|---------------------------------------------|
| 1         | (2, 5, right, 1), ...                       |
| 2         | (5, 1, left, 2)                             |
"""
```

### 3. 최종 프롬프트 조합
```
[FAST_AGENT_PROMPT]
You are a player in a freeway game...
### 1. Game Dynamics:
...
### 3. Task (Turn t_0):
Choose one action...

[상태 정보]
**Current Turn:** t_0 = 5
**Player Position:** (0, 3)
**Car State:**
| Freeway k | Cars ... |
...
```

---

## 설계의 장점

### ✅ 1. 코드 재사용
- 3개 Agent 클래스 × 3개 게임 = 9개 조합
- 새 게임 추가 시 prompts 모듈만 작성
- Agent는 수정 불필요

### ✅ 2. 역할 분리
```
AI 연구자    → Agent 알고리즘 개선
게임 디자이너 → Prompts 작성/튜닝
```

### ✅ 3. 테스트 용이
```python
# Mock prompts로 Agent 단위 테스트
mock_prompts = Mock()
mock_prompts.ALL_ACTIONS = "ABC"
mock_prompts.state_to_description = lambda s, m: "test prompt"
agent = ReactiveAgent(prompts=mock_prompts, ...)
```

### ✅ 4. 프롬프트 엔지니어링 실험
- Agent 코드 건드리지 않고 prompts만 수정
- 다양한 프롬프트 전략 A/B 테스트
- 게임 규칙 설명 방식 실험

### ✅ 5. Python + YAML 분리

**Python (`.py`)**
- 게임 상태 → 텍스트 변환 로직
- 동적 데이터 처리 (위치, 턴 수 등)
- 복잡한 조건 분기

**YAML (`.yaml`)**
- 고정된 프롬프트 템플릿
- 게임 규칙 설명
- 수정이 쉬움 (코드 몰라도 프롬프트 수정 가능)

---

## 디자인 패턴 분석

### Strategy Pattern + Dependency Injection

```python
# Strategy Pattern: 게임별 전략을 캡슐화
class FreewayPrompts:
    def state_to_description(...): ...

class SnakePrompts:
    def state_to_description(...): ...

# Dependency Injection: 런타임에 전략 주입
agent = ReactiveAgent(prompts=chosen_prompts)
```

이것은 **"Tell, Don't Ask"** 원칙의 완벽한 구현입니다:
- Agent가 게임에게 "너 무슨 게임이야?"라고 묻지 않음
- 대신 Prompts가 "이렇게 해석해"라고 알려줌

---

## 게임별 차이점

| 게임 | ALL_ACTIONS | DEFAULT_ACTION | 특징 |
|------|------------|----------------|------|
| **Freeway** | `"UDS"` | `"U"` | 수학적 수식 (좌표 계산, 충돌 판정) |
| **Snake** | `"LRUD"` | `"S"` | 음식 수명, 꼬리 추적, 역방향 금지 |
| **Overcooked** | `"LRUDIS"` | `"S"` | 복잡한 레시피, 아이템 상호작용 |

각 게임은 **고유한 게임 역학**을 자연어로 상세히 설명합니다.

---

## 비교표: Agent vs Prompts

| 요소 | 역할 | 게임별 차이 | 파일 위치 |
|------|------|------------|-----------|
| **Agent** | LLM 추론 엔진<br>- API 호출<br>- 토큰 관리<br>- 전략 실행 | ❌ 없음 (범용) | `src/realtimegym/agents/` |
| **Prompts** | 게임 지식 제공자<br>- 규칙 설명<br>- 상태 변환<br>- 액션 정의 | ✅ 있음 (게임마다 다름) | `src/realtimegym/prompts/` |

---

## 핵심 요약

`prompts/` 폴더는 **LLM 에이전트의 눈과 귀** 역할입니다:

1. 게임 상태를 자연어로 번역
2. 에이전트 타입에 맞는 지시사항 제공
3. 출력 형식 지정
4. 게임 규칙과 전략 가이드 제공

이를 통해 LLM이 숫자와 배열 대신 **"플레이어는 (0,3) 위치에 있고, 1번 레인에는 오른쪽으로 움직이는 차가..."** 같은 맥락을 이해하고 추론할 수 있게 됩니다.

**Agent는 게임을 모르고, Prompts가 게임을 알려줍니다.**
