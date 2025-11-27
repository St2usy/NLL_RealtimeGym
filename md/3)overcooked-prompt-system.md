# Overcooked 프롬프트 시스템 상세 가이드

## 목차
1. [개요](#개요)
2. [파일 구조](#파일-구조)
3. [Overcooked 환경 구조](#overcooked-환경-구조)
4. [상태 업데이트 메커니즘](#상태-업데이트-메커니즘)
5. [프롬프트 생성 로직](#프롬프트-생성-로직)
6. [실행 흐름](#실행-흐름)

---

## 개요

Overcooked 환경은 **2인 협동 요리 게임**으로, LLM 에이전트(Alice)와 스크립트 에이전트(Bob)가 협력하여 수프를 조리하고 서빙하는 실시간 추론 평가 환경입니다.

### 핵심 특징
- **협동 작업**: 재료 수집, 조리, 서빙의 분업 필요
- **실시간 제약**: 100턴 제한, 토큰/시간 예산 제약
- **복잡한 상호작용**: 6가지 액션과 7가지 타일 타입
- **동적 상태**: 플레이어 위치, 냄비 조리 상태, 행동 히스토리 등

---

## 파일 구조

### 1. `src/realtimegym/prompts/overcooked.py`

**역할**: 게임 상태를 자연어 프롬프트로 변환하는 로직

```python
# 모듈 상수
ALL_ACTIONS = "UDLRIS"  # Up, Down, Left, Right, Interact, Stay
DEFAULT_ACTION = "S"     # 기본 액션: Stay

# 핵심 함수
def state_to_description(state_for_llm: dict, mode: str) -> Union[str, dict]:
    """
    Args:
        state_for_llm: 구조화된 게임 상태 딕셔너리
        mode: "reactive" | "planning" | "agile"

    Returns:
        mode에 따라 프롬프트 문자열 또는 딕셔너리 반환
    """
```

**주요 기능**:
- 레이아웃 정보 추출 (Kitchen Counter, Dispensers, Pots 등)
- 레시피 정보 자연어 변환
- 플레이어 상태 (위치, 방향, 소지 아이템, 히스토리) 추출
- 냄비/카운터 상태 텍스트 생성
- 모드별 프롬프트 조합

### 2. `src/realtimegym/prompts/overcooked.yaml`

**역할**: 프롬프트 템플릿 저장소

| 템플릿 | 용도 | 주요 내용 |
|--------|------|-----------|
| `slow_agent_prompt` | Planning 모델 시스템 프롬프트 | 게임 규칙, 협력 전략, H턴 계획 수립 |
| `action_format_prompt` | Planning 출력 형식 | 다중 턴 액션 시퀀스 형식 |
| `conclusion_format_prompt` | Agile Planning 출력 형식 | 액션 시퀀스 + 전략 요약 |
| `fast_agent_prompt` | Reactive 모델 시스템 프롬프트 | 즉각 액션 결정, Planning 참고 활용 |
| `game_state_prompt` | 현재 게임 상태 템플릿 | 레이아웃, 플레이어, 냄비 상태 등 |

---

## Overcooked 환경 구조

### 게임 그리드 (2D 타일 맵)

```
[Example Layout: cc_easy]

T  X  X  X  X  O
   P        P
S              S
   P        P
D  X  X  X  X  O
```

| 타일 타입 | 기호 | 설명 | 상호작용 |
|----------|------|------|----------|
| Empty Tile | (공백) | 이동 가능한 빈 공간 | 플레이어 이동 |
| Kitchen Counter | `X` | 임시 아이템 보관 | 아이템 배치/픽업 |
| Tomato Dispenser | `T` | 토마토 디스펜서 | 토마토 획득 (무한) |
| Onion Dispenser | `O` | 양파 디스펜서 | 양파 획득 (무한) |
| Plate Dispenser | `D` | 접시 디스펜서 | 깨끗한 접시 획득 (무한) |
| Pot | `P` | 조리 냄비 | 재료 추가/수프 담기 |
| Serving Counter | `S` | 서빙 카운터 | 완성된 수프 서빙 |

### 플레이어

- **Alice (Player 0)**: LLM 제어 에이전트
  - 역할: 전략적 의사결정
  - 설정: `agent0_policy_name = "script:LLM"`

- **Bob (Player 1)**: 스크립트 에이전트
  - 역할: 규칙 기반 협력 파트너
  - 전략: `put_onion_everywhere` - 양파를 계속 냄비에 넣음

### 액션 시스템

#### 6가지 액션

```python
U - Up:       (x, y+1) 이동 + 위쪽 방향 전환
D - Down:     (x, y-1) 이동 + 아래쪽 방향 전환
L - Left:     (x-1, y) 이동 + 왼쪽 방향 전환
R - Right:    (x+1, y) 이동 + 오른쪽 방향 전환
I - Interact: 상호작용 (아래 참조)
S - Stay:     제자리 대기 (아무것도 안 함)
```

#### Interact (I) 액션 상세

**실행 조건**:
1. 플레이어가 **빈 타일**에 서 있어야 함
2. 상호작용할 타일을 **향하고 있어야 함** (orientation)

**타일별 효과**:

| 타일 | 조건 | 효과 |
|------|------|------|
| **Dispenser** | 빈손 | 해당 아이템 획득 (tomato/onion/dish) |
| **Pot** | 재료 들고 있음 + 냄비 미만 | 재료 추가 (3개 차면 자동 조리 시작) |
| **Pot** | 접시 들고 있음 + 수프 완성됨 | 수프를 접시에 담기 |
| **Serving Counter** | 수프 담긴 접시 들고 있음 | 서빙 완료 → 보상 획득 |
| **Kitchen Counter** | 빈손 + 카운터에 아이템 있음 | 아이템 픽업 |
| **Kitchen Counter** | 아이템 들고 있음 + 카운터 비어있음 | 아이템 배치 |

#### 제약 사항

- ❌ 플레이어는 **한 번에 하나의 아이템**만 소지 가능
- ❌ 플레이어끼리 **통과 불가** (같은 타일에 있을 수 없음)
- ❌ 비어있지 않은 타일로 **이동 불가**
- ✅ 인접한 타일을 향해야만 상호작용 가능

### 레시피 시스템

```python
# 예시 레시피
{
    "ingredients": ["onion", "onion", "tomato"],  # 필요 재료
    "value": 20,                                  # 보상 점수
    "time": 20                                    # 조리 시간 (턴)
}
```

**조리 메커니즘**:
1. 냄비에 재료 3개 투입 → 자동으로 조리 시작
2. `cook_time` 만큼 턴이 경과하면 완성
3. 재료가 레시피와 일치하지 않으면:
   - 조리 시간: 20턴 (기본값)
   - 보상: 0점

---

## 상태 업데이트 메커니즘

### 전체 상태 구조

```python
state_for_llm = {
    # ========== 정적 정보 (게임 시작 시 고정) ==========
    "layout": {
        "X": [(2, 3), (3, 3), ...],  # Kitchen Counter 위치 리스트
        "T": [(1, 5)],                # Tomato Dispenser 위치
        "O": [(6, 5), (6, 1)],        # Onion Dispenser 위치
        "D": [(1, 1)],                # Plate Dispenser 위치
        "P": [(2, 2), (2, 4), ...],   # Pot 위치
        "S": [(1, 3), (6, 3)]         # Serving Counter 위치
    },

    # ========== 주문 정보 (게임 내내 유지) ==========
    "all_orders": [
        {
            "ingredients": ["onion", "onion", "onion"],
            "value": 20,
            "time": 20
        },
        {
            "ingredients": ["onion", "onion", "tomato"],
            "value": 25,
            "time": 25
        }
    ],

    # ========== 동적 정보 (매 턴 업데이트) ==========
    "game_turn": 15,  # 현재 턴 번호 (0~100)

    "history": [
        ["I", "R", "I", "U", "I"],  # Alice 최근 5개 액션 (최신이 마지막)
        ["U", "I", "D", "I", "S"]   # Bob 최근 5개 액션
    ],

    "state": {
        "players": [
            {  # Alice (player 0)
                "position": (3, 2),           # 현재 위치
                "orientation": (1, 0),        # 방향 벡터 (R)
                "held_object": {
                    "name": "onion",
                    "position": (3, 2)
                }  # 또는 None (빈손)
            },
            {  # Bob (player 1)
                "position": (5, 2),
                "orientation": (0, 1),        # 방향 벡터 (U)
                "held_object": {
                    "name": "dish",
                    "position": (5, 2)
                }
            }
        ],

        "objects": [  # 냄비 수프 + 카운터 위 아이템
            {
                "name": "soup",
                "position": (4, 3),           # Pot 위치
                "_ingredients": [
                    {"name": "onion", "position": (4, 3)},
                    {"name": "onion", "position": (4, 3)}
                ],
                "cooking_tick": 5,            # 현재까지 조리된 턴
                "cook_time": 20,              # 필요한 총 조리 시간
                "is_idle": False,             # 조리 시작 전?
                "is_cooking": True,           # 조리 중?
                "is_ready": False             # 조리 완료?
            },
            {
                "name": "dish",               # Kitchen Counter 위 접시
                "position": (2, 3)
            }
        ]
    }
}
```

### 방향 매핑

```python
orientation_to_char_mapping = {
    (0, 1):  "U",  # Up
    (0, -1): "D",  # Down
    (-1, 0): "L",  # Left
    (1, 0):  "R"   # Right
}
```

### 상태 변화 시나리오 예시

#### Scenario 1: 양파 디스펜서에서 양파 획득

**초기 상태 (Turn 10)**:
```python
Alice: position=(2, 5), orientation=(1, 0), held_object=None
```

**액션**: `action = "I"` (오른쪽 Onion Dispenser를 향해 Interact)

**업데이트된 상태 (Turn 11)**:
```python
game_turn: 10 → 11
Alice.held_object: None → {"name": "onion", "position": (2, 5)}
history[0]: [...] → [..., "I"]
```

---

#### Scenario 2: 냄비에 재료 추가 및 조리 시작

**초기 상태 (Turn 15)**:
```python
Alice: position=(3, 2), held_object={"name": "onion"}
Pot (4, 3): {
    "_ingredients": [onion, onion],  # 2개만 있음
    "is_idle": True,
    "is_cooking": False
}
```

**액션**: `action = "I"` (Pot를 향해 Interact)

**업데이트된 상태 (Turn 16)**:
```python
game_turn: 15 → 16
Alice.held_object: {"name": "onion"} → None
Pot._ingredients: [onion, onion] → [onion, onion, onion]  # 3개 차서 조리 시작
Pot.is_idle: True → False
Pot.is_cooking: False → True
Pot.cooking_tick: 0 → 0
history[0]: [...] → [..., "I"]
```

---

#### Scenario 3: 조리 완료 (자동 업데이트)

**Turn 36 (20턴 경과 후)**:
```python
# 플레이어 액션 없이 자동 업데이트
Pot.cooking_tick: 19 → 20
Pot.is_cooking: True → False
Pot.is_ready: False → True
```

---

#### Scenario 4: 수프 담기

**초기 상태 (Turn 37)**:
```python
Alice: position=(3, 3), held_object={"name": "dish"}
Pot (4, 3): {
    "_ingredients": [onion, onion, onion],
    "is_ready": True
}
```

**액션**: `action = "I"` (Pot를 향해 Interact)

**업데이트된 상태 (Turn 38)**:
```python
game_turn: 37 → 38
Alice.held_object: {"name": "dish"} → {"name": "soup"}
objects: Pot soup 제거됨
history[0]: [...] → [..., "I"]
```

---

#### Scenario 5: 서빙 및 보상 획득

**초기 상태 (Turn 40)**:
```python
Alice: position=(1, 3), held_object={"name": "soup"}
reward: 0
```

**액션**: `action = "I"` (Serving Counter를 향해 Interact)

**업데이트된 상태 (Turn 41)**:
```python
game_turn: 40 → 41
Alice.held_object: {"name": "soup"} → None
reward: 0 → 20  # 레시피 보상 획득!
history[0]: [...] → [..., "I"]
```

---

## 프롬프트 생성 로직

### `state_to_description()` 함수 흐름

#### Phase 1: 데이터 추출 및 변환 (44-128줄)

##### 1. 레이아웃 정보 추출
```python
kitchen_counters = state_for_llm["layout"]["X"]
tomatoes = state_for_llm["layout"]["T"]
onions = state_for_llm["layout"]["O"]
plates = state_for_llm["layout"]["D"]
pots = state_for_llm["layout"]["P"]
serving_counters = state_for_llm["layout"]["S"]
```

##### 2. 레시피 정보 텍스트 변환
```python
# 입력: all_orders
# 출력 예시:
"""
Recipe 1: 3 onions, 0 tomatoes; reward: 20; time to cook: 20 turns
Recipe 2: 2 onions, 1 tomatoes; reward: 25; time to cook: 25 turns
"""
```

##### 3. 플레이어 상태 추출
```python
for i in range(2):  # Alice, Bob
    position[i] = player["position"]           # (x, y)
    orientation[i] = "U" | "D" | "L" | "R"     # 방향 문자

    # 소지 아이템 변환
    if held_object is None:
        held_object[i] = "nothing"
    elif held_object["name"] == "dish":
        held_object[i] = "clean plate"
    elif held_object["name"] == "soup":
        held_object[i] = "soup in plate"
    else:
        held_object[i] = "one onion" | "one tomato"

    # 히스토리 (최근 5개)
    history[i] = "I, R, I, U, I" | "No action history"
```

##### 4. 냄비 상태 텍스트 생성
```python
# 출력 예시:
pot_state = {
    (4, 3): "Pot on (4, 3): contains 2 onions and 1 tomatoes; Cooked for 5 turns, still need 15 turns to finish.",
    (6, 5): "Pot on (6, 5): contains nothing; Pot is not full thus cooking hasn't started yet.",
    (2, 2): "Pot on (2, 2): contains 3 onions and 0 tomatoes; Ready to serve."
}

text_pot_state = "\n".join(pot_state.values())
# 냄비가 모두 비어있으면: "All pots are empty."
```

##### 5. 주방 카운터 상태 텍스트 생성
```python
# 출력 예시:
kitchen_counter_state = {
    (2, 3): "Kitchen Counter on (2, 3): contains a clean plate; "
}

text_kitchen_counter_state = "\n".join(kitchen_counter_state.values())
# 카운터가 모두 비어있으면: "All kitchen counters are empty."
```

---

#### Phase 2: 프롬프트 조합 (130-183줄)

##### Mode 1: `reactive` (Reactive Agent)

**코드**:
```python
return FAST_AGENT_PROMPT + model1_description
```

**구성**:
```
[FAST_AGENT_PROMPT]
  - 역할: Alice가 Bob과 협력하여 즉각 액션 결정
  - 입력: 현재 게임 상태 + Planning 모델의 과거 계획 (참고용)
  - 게임 규칙 설명
  - 출력 형식: \boxed{a_{t_0}}

[model1_description] (GAME_STATE_PROMPT 템플릿 적용)
  - Game Turn: t_0 = {현재턴}
  - Tile Types: Kitchen Counter, Dispensers, Pots, Serving Counter
  - Recipe Information
  - Player Information (Alice & Bob)
  - Non-empty Kitchen Counter 상태
  - Non-empty Pot 상태
```

**출력 예시**:
```
Help Alice collaborate with Bob in *Overcooked* to maximize...
...
Game Turn: t_0 = 15

Player Information:
- You (Alice)
    - Position: (3, 2)
    - Orientation: R
    - Holding: one onion
    - Action History: I, R, I, U, I

- Teammate (Bob)
    - Position: (5, 2)
    - Orientation: U
    - Holding: clean plate
    - Action History: U, I, D, I, S

Non-empty Pot State:
Pot on (4, 3): contains 2 onions and 0 tomatoes; Cooked for 5 turns, still need 15 turns to finish.

Your answer: \boxed{a_{t_0}}
```

---

##### Mode 2: `planning` (Planning Agent)

**코드**:
```python
return SLOW_AGENT_PROMPT + ACTION_FORMAT_PROMPT + model2_description
```

**구성**:
```
[SLOW_AGENT_PROMPT]
  - 역할: H턴에 걸친 액션 시퀀스 계획
  - 최적화 목표: 총 보상 최대화
  - 협력 전략, 조율, 의사결정

[ACTION_FORMAT_PROMPT]
  - 출력 형식:
    \boxed{
    Turn t_1: a_{t_1}
    Turn t_1 + 1: a_{t_1 + 1}
    ...
    }

[model2_description] (GAME_STATE_PROMPT 템플릿 적용)
  - Game Turn: t_1 = {현재턴}
  - (나머지는 reactive와 동일)
```

**출력 예시**:
```
Help Alice collaborate with Bob in *Overcooked* to maximize...
Plan a sequence of actions {a_{t_1 + t}} for Alice over next H turns...

\boxed{
Turn 15: I
Turn 16: D
Turn 17: L
Turn 18: I
Turn 19: R
...
}
```

---

##### Mode 3: `agile` (Agile Agent - 하이브리드)

**코드**:
```python
return {
    "planning": SLOW_AGENT_PROMPT + CONCLUSION_FORMAT_PROMPT + model2_description,
    "reactive": FAST_AGENT_PROMPT + model1_description
}
```

**Planning 프롬프트**:
```
[SLOW_AGENT_PROMPT]
  - (위와 동일)

[CONCLUSION_FORMAT_PROMPT]
  - 출력 형식:
    (1) Action Sequence:
      \boxed{Turn t_1: a_{t_1}\n...}

    (2) Main Thinking Conclusion:
      전략 요약 (1-2문장)

[model2_description]
  - Game Turn: t_1 = {현재턴}
  - (상태 정보)
```

**Reactive 프롬프트**:
```
[FAST_AGENT_PROMPT]
  - 입력: 현재 상태 + Planning 모델의 계획 (참고용)
  - Planning 출력을 "strategic reference"로 활용
  - 즉각 액션 결정

[model1_description]
  - Game Turn: t_0 = {현재턴}
  - (상태 정보)
```

**실행 흐름**:
1. Planning 모델이 백그라운드에서 전략 수립 + 액션 시퀀스 생성
2. Reactive 모델이 Planning 출력을 참고하여 즉각 액션 결정
3. Planning 모델은 계속 업데이트된 상태로 새 계획 생성

---

### 프롬프트 타임스탬프 차이

| 모델 | 시간 표기 | 의미 |
|------|----------|------|
| Planning | `t_1` | 계획을 **시작한 시점**의 턴 번호 |
| Reactive | `t_0` | **현재 즉시** 액션을 결정해야 하는 턴 번호 |

**예시**:
- Turn 10에서 Planning 시작 → `t_1 = 10`
- Turn 15에서 Reactive 액션 결정 → `t_0 = 15`
- Planning은 Turn 10 기준으로 생성한 계획을 제공
- Reactive는 Turn 15의 최신 상태를 보고 즉각 판단

---

## 실행 흐름

### 전체 게임 루프

```python
# agile_eval.py:150-161

# 1. 환경 초기화
obs, done = env.reset()
# → game_turn=0, reward=0, history=[[], []]

while not done:
    # 2. 관찰 단계
    agent.observe(obs)
    # → agent.current_observation = obs

    # 3. 추론 단계
    agent.think(timeout=args.time_pressure)
    # → state_to_description() 호출
    # → LLM 추론

    # 4. 액션 실행
    action = agent.act()
    # → extract_boxed() 파싱

    # 5. 환경 업데이트
    obs, done, reward, reset_flag = env.step(action)
    # → 상태 변화 적용

    # 6. 로깅
    agent.log(reward, reset_flag)
    # → CSV 파일에 기록
```

---

### 턴별 상태 업데이트 타임라인

```
┌─────────────────────────────────────────────────────────────┐
│ Turn 0: 게임 시작 (env.reset)                               │
├─────────────────────────────────────────────────────────────┤
│ game_turn = 0                                                │
│ reward = 0                                                   │
│ history = [[], []]                                           │
│ players: 초기 위치 배치                                      │
│ objects = []                                                 │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Turn 1: agent.think()                                        │
├─────────────────────────────────────────────────────────────┤
│ 1. state_to_description(obs, mode)                           │
│    → 프롬프트 생성 (t_0 = 1 또는 t_1 = 1)                    │
│                                                              │
│ 2. LLM 추론                                                  │
│    → Planning: 액션 시퀀스 생성                              │
│    → Reactive: 즉각 액션 결정                                │
│                                                              │
│ 3. agent.act()                                               │
│    → extract_boxed() 파싱                                    │
│    → action = "R"                                            │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Turn 1: env.step("R")                                        │
├─────────────────────────────────────────────────────────────┤
│ 상태 업데이트:                                               │
│ - game_turn: 0 → 1                                           │
│ - Alice.position: (2, 2) → (3, 2)                            │
│ - Alice.orientation: (0, 1) → (1, 0)  [U → R]                │
│ - history[0]: [] → ["R"]                                     │
│ - Bob도 동시에 액션 수행 (script agent)                      │
│ - history[1]: [] → ["U"]                                     │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Turn 2: agent.think()                                        │
├─────────────────────────────────────────────────────────────┤
│ 1. state_to_description(obs, mode)                           │
│    → 업데이트된 상태로 새 프롬프트 생성 (t_0 = 2)            │
│    → history에 최근 액션 포함: "R"                           │
│    → 변경된 위치/방향 반영                                   │
│                                                              │
│ 2. LLM 추론 → action = "I"                                   │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Turn 2: env.step("I")                                        │
├─────────────────────────────────────────────────────────────┤
│ 상태 업데이트:                                               │
│ - game_turn: 1 → 2                                           │
│ - Alice.held_object: None → {"name": "onion"}  [양파 획득]   │
│ - history[0]: ["R"] → ["R", "I"]                             │
│ - history[1]: ["U"] → ["U", "I"]                             │
└─────────────────────────────────────────────────────────────┘
                       ↓
                      ...
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Turn 15: 냄비에 3번째 재료 추가                              │
├─────────────────────────────────────────────────────────────┤
│ action = "I"                                                 │
│                                                              │
│ 상태 업데이트:                                               │
│ - Pot._ingredients: [o, o] → [o, o, o]  [3개 차서 조리 시작] │
│ - Pot.is_idle: True → False                                  │
│ - Pot.is_cooking: False → True                               │
│ - Pot.cooking_tick: 0 (시작)                                 │
│ - Alice.held_object: {"name": "onion"} → None                │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Turn 16~34: 조리 중 (자동 업데이트)                          │
├─────────────────────────────────────────────────────────────┤
│ 매 턴마다:                                                   │
│ - Pot.cooking_tick: 0 → 1 → 2 → ... → 19                     │
│ - Pot.is_cooking: True (계속 유지)                           │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Turn 35: 조리 완료 (자동)                                    │
├─────────────────────────────────────────────────────────────┤
│ - Pot.cooking_tick: 19 → 20                                  │
│ - Pot.is_cooking: True → False                               │
│ - Pot.is_ready: False → True  [수프 완성!]                   │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Turn 40: 수프 서빙                                           │
├─────────────────────────────────────────────────────────────┤
│ action = "I" (Serving Counter 앞에서)                        │
│                                                              │
│ 상태 업데이트:                                               │
│ - Alice.held_object: {"name": "soup"} → None                 │
│ - reward: 0 → 20  [레시피 보상 획득!]                        │
│ - history[0]: [...] → [..., "I"]                             │
└─────────────────────────────────────────────────────────────┘
                       ↓
                      ...
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Turn 100: 게임 종료                                          │
├─────────────────────────────────────────────────────────────┤
│ done = True                                                  │
│ 최종 reward 집계                                             │
│ 로그 CSV 파일 저장                                           │
└─────────────────────────────────────────────────────────────┘
```

---

### Agile Mode 실행 흐름

```
┌──────────────────────────────────────────────────────────────┐
│ Turn N: Agile Agent (듀얼 모델)                               │
└──────────────────────────────────────────────────────────────┘

Planning Model (백그라운드)          Reactive Model (메인 스레드)
─────────────────────────            ───────────────────────────
1. 상태 관찰 (t_1 = N)                1. 상태 관찰 (t_0 = N)

2. 프롬프트 생성:                     2. 프롬프트 생성:
   - SLOW_AGENT_PROMPT                   - FAST_AGENT_PROMPT
   - CONCLUSION_FORMAT_PROMPT            - 과거 Planning 출력 포함
   - model2_description                  - model1_description

3. LLM 추론 (스트리밍):               3. LLM 추론:
   ┌─────────────────┐                   - Planning 계획 참고
   │ Turn N: R       │                   - 현재 상태 기반
   │ Turn N+1: I     │                   - 즉각 액션 결정
   │ Turn N+2: D     │
   │ ...             │ ────────참고──→ 4. 액션 결정: action = "I"
   │                 │
   │ Conclusion:     │                5. 액션 실행
   │ "Get onion      │                   env.step("I")
   │  and add to pot"│
   └─────────────────┘

4. 토큰 예산 소진 시                  6. 다음 턴 대기
   또는 완료 시까지 계속
```

**핵심 포인트**:
- Planning: 백그라운드에서 전략적 계획 수립
- Reactive: Planning 출력을 "참고"하되, 현재 상태에 맞춰 즉각 결정
- 토큰 예산 분할: `time_pressure - internal_budget` (Planning) + `internal_budget` (Reactive)

---

## 프롬프트 모드 비교 요약

| 특성 | Reactive | Planning | Agile |
|------|----------|----------|-------|
| **모델 수** | 1개 (Reactive) | 1개 (Planning) | 2개 (Planning + Reactive) |
| **시간 표기** | `t_0` (현재) | `t_1` (계획 시작) | `t_1` (Planning), `t_0` (Reactive) |
| **출력 형식** | 단일 액션 | 액션 시퀀스 | 시퀀스 + 전략 요약 (Planning)<br>단일 액션 (Reactive) |
| **전략** | 즉각 반응 | 장기 계획 | 하이브리드 (계획 참고 + 즉각 대응) |
| **예산 사용** | 전체 예산 | 전체 예산 | 분할 (Planning + Reactive) |
| **프롬프트** | `FAST_AGENT_PROMPT` | `SLOW_AGENT_PROMPT`<br>`ACTION_FORMAT_PROMPT` | `SLOW_AGENT_PROMPT`<br>`CONCLUSION_FORMAT_PROMPT`<br>`FAST_AGENT_PROMPT` |

---

## 실행 예시

### 명령어

```bash
agile_eval --time_unit token \
    --time_pressure 8192 \
    --internal_budget 4096 \
    --game overcooked \
    --cognitive_load E \
    --mode agile \
    --reactive-model-config configs/example-gemini-2.5-pro-reactive.yaml \
    --planning-model-config configs/example-gemini-2.5-pro-planning.yaml \
    --seed_num 1 \
    --repeat_times 1 \
    --save_trajectory_gifs
```

### 난이도별 레이아웃

| cognitive_load | 레이아웃 이름 | 설명 |
|----------------|-------------|------|
| `E` (Easy) | `cc_easy` | 단순한 구조, 넓은 이동 공간 |
| `M` (Medium) | `cc_hard` | 복잡한 구조, 좁은 통로 |
| `H` (Hard) | `cc_insane` | 매우 복잡, 높은 조율 필요 |

### 출력

- **로그 파일**: `{log_dir}/overcooked-E-agile-token-8192-4096_seed{N}_rep{M}.csv`
- **GIF 파일**: `{log_dir}/overcooked-E-agile-token-8192-4096_seed{N}_rep{M}.gif`

**로그 내용**:
- `render`: 각 턴의 state_string
- `action`: Alice가 수행한 액션
- `reward`: 누적 보상
- `plan`: Planning 모델 출력
- `model1_prompt`, `model1_response`, `model1_token_num`: Reactive 모델 로그
- `model2_prompt`, `model2_response`, `model2_token_num`: Planning 모델 로그

---

## 요약

Overcooked 프롬프트 시스템은 복잡한 협동 작업을 실시간 제약 하에서 수행하도록 설계된 평가 프레임워크입니다.

**핵심 요소**:
1. **구조화된 상태 표현**: 레이아웃, 플레이어, 오브젝트, 히스토리
2. **자연어 변환**: Python 로직으로 게임 상태를 프롬프트로 변환
3. **모드별 프롬프트**: Reactive (즉각), Planning (장기), Agile (하이브리드)
4. **실시간 업데이트**: 매 턴마다 동적 상태 변화 반영
5. **협력 메커니즘**: LLM과 스크립트 에이전트의 조율

이 시스템을 통해 LLM의 **실시간 추론 능력**, **협력 전략**, **동적 환경 적응력**을 평가할 수 있습니다.
