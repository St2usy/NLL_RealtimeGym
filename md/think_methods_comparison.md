# 세 가지 에이전트의 `think()` 메서드 비교 분석

## 📊 전체 비교표

| 특징 | ReactiveAgent | PlanningAgent | AgileThinker |
|------|--------------|---------------|--------------|
| **사용 모델** | model1 (reactive) | model2 (planning) | model1 + model2 (hybrid) |
| **추론 방식** | 즉시 반응 | 장기 계획 | 계획 + 반응 결합 |
| **코드 라인** | 19줄 (간단) | 35줄 (중간) | 37줄 (복잡) |
| **프롬프트 모드** | `"reactive"` | `"planning"` | `"agile"` (dict) |
| **예산 사용** | 전체를 reactive에 사용 | 전체를 planning에 사용 | planning + reactive 분할 |
| **계획 생성** | ❌ 없음 | ✅ `\boxed{}` 액션 시퀀스 | ✅ 텍스트 가이던스 |
| **계획 재사용** | ❌ | ✅ 여러 턴에 걸쳐 사용 | ✅ reactive에 전달 |

---

## 1️⃣ ReactiveAgent.think() - 즉시 반응 전략

**위치**: `src/realtimegym/agents/reactive.py:22-40`

```python
def think(self, timeout: Optional[float] = None) -> None:
    assert self.current_observation is not None and timeout is not None
    budget = timeout
    observation = self.current_observation
    prompt_gen = self.prompts.state_to_description(
        observation["state"], mode="reactive"
    )
    messages = [{"role": "user", "content": prompt_gen}]
    text, token_num = self.reactive_inference(messages, budget)
    self.action = re.sub(
        r"[^" + self.prompts.ALL_ACTIONS + "]", "", extract_boxed(text)
    )
    if self.action == "":
        self.action = self.prompts.DEFAULT_ACTION
    if self.log_thinking:
        self.logs["plan"].append("N/A")
        self.logs["model1_prompt"].append(messages[-1]["content"])
        self.logs["model1_response"].append(text)
    self.logs["model1_token_num"].append(token_num)
```

### 핵심 특징

**🎯 단순하고 빠른 의사결정**
- 현재 관찰만 보고 즉시 액션 결정
- 장기 계획 없이 반사적으로 대응
- 가장 짧고 단순한 코드

### 단계별 분석

#### Step 1: 입력 검증 (Line 23)
```python
assert self.current_observation is not None and timeout is not None
```
**Python 문법: `assert` 문**
- 조건이 `False`면 `AssertionError` 발생
- 디버깅용, 프로덕션에서는 비활성화 가능
- **논리 연산자 `and`**: 두 조건 모두 `True`여야 통과

#### Step 2: 프롬프트 생성 (Line 26-28)
```python
prompt_gen = self.prompts.state_to_description(
    observation["state"], mode="reactive"
)
messages = [{"role": "user", "content": prompt_gen}]
```
**Python 문법: 리스트와 딕셔너리**
- `[...]`: 리스트 리터럴 (순서 있는 컬렉션)
- `{...}`: 딕셔너리 리터럴 (키-값 쌍)
- OpenAI API 형식: `[{"role": "user", "content": "..."}]`

#### Step 3: 추론 실행 (Line 30)
```python
text, token_num = self.reactive_inference(messages, budget)
```
**Python 문법: 튜플 언패킹 (Tuple Unpacking)**
- 함수가 여러 값을 반환할 때 사용
- `reactive_inference()`는 `(text, token_num)` 튜플 반환
- 좌변의 변수에 순서대로 할당

#### Step 4: 액션 추출 (Line 31-35)
```python
self.action = re.sub(
    r"[^" + self.prompts.ALL_ACTIONS + "]", "", extract_boxed(text)
)
if self.action == "":
    self.action = self.prompts.DEFAULT_ACTION
```
**정규표현식 (Regex)**
- `re.sub(pattern, replacement, string)`: 패턴 매칭되는 부분을 replacement로 치환
- `r"[^...]"`: raw string (역슬래시 이스케이프 불필요)
- `[^ABC]`: 문자 클래스 부정 (A, B, C가 아닌 모든 문자)
- 예: `ALL_ACTIONS="UDLR"`이면 `[^UDLR]`는 U, D, L, R 외의 모든 문자 제거

**동작 예시:**
```python
text = "I should go up. \\boxed{UUU}"
extract_boxed(text) → "UUU"
re.sub(r"[^UDLR]", "", "UUU") → "UUU"
```

---

## 2️⃣ PlanningAgent.think() - 장기 계획 전략

**위치**: `src/realtimegym/agents/planning.py:30-64`

```python
def think(self, timeout: Optional[float] = None) -> None:
    assert timeout is not None and self.current_observation is not None
    budget = timeout

    observation = self.current_observation
    game_turn = observation["game_turn"]
    prompt_gen = self.prompts.state_to_description(
        observation["state"], mode="planning"
    )

    prompt = ""
    if self.gen_text == "":  # check whether the last generation is finished
        messages = [{"role": "user", "content": prompt_gen}]
        prompt = messages[-1]["content"]
    else:
        messages = []

    text, token_num, turn = self.planning_inference(messages, budget, game_turn)
    temp = extract_boxed(text)
    if temp != "":
        self.plan = re.sub(r"[^" + self.prompts.ALL_ACTIONS + "]", "", temp)
        if self.skip_action:
            self.plan = (
                self.plan[observation["game_turn"] - turn :]
                if len(self.plan) > observation["game_turn"] - turn
                else ""
            )

    if self.log_thinking:
        self.logs["plan"].append(self.plan)
        self.logs["model2_prompt"].append(prompt)
        self.logs["model2_response"].append(text)
    self.logs["model2_token_num"].append(token_num)
    self.action = self.plan[0] if self.plan != "" else self.prompts.DEFAULT_ACTION
    self.plan = self.plan[1:] if self.plan != "" else ""
```

### 핵심 특징

**🎯 여러 턴에 걸친 장기 계획**
- 한 번 생성한 계획을 여러 턴에서 재사용
- `self.plan`에 액션 시퀀스 저장 (예: "UUUDDLR")
- 매 턴마다 첫 글자만 사용하고 나머지는 다음 턴으로

### 단계별 분석

#### Step 1: 계획 생성 지속 여부 확인 (Line 41-46)
```python
prompt = ""
if self.gen_text == "":  # check whether the last generation is finished
    messages = [{"role": "user", "content": prompt_gen}]
    prompt = messages[-1]["content"]
else:
    messages = []
```
**핵심 개념: 스트리밍 생성**
- `self.gen_text`: 현재 생성 중인 텍스트 버퍼
- **비어있음 (`""`)**: 새 계획 시작 → 프롬프트 전달
- **비어있지 않음**: 이전 계획 계속 생성 중 → 빈 메시지

**Python 문법: 조건 표현식**
- `if 조건: ... else: ...`: 조건에 따라 다른 코드 실행

#### Step 2: Planning 추론 (Line 48)
```python
text, token_num, turn = self.planning_inference(messages, budget, game_turn)
```
**3개 값 언패킹**
- `text`: 생성된 계획 텍스트
- `token_num`: 사용한 토큰 수
- `turn`: 계획이 시작된 턴 번호

#### Step 3: 액션 시퀀스 추출 (Line 49-56)
```python
temp = extract_boxed(text)
if temp != "":
    self.plan = re.sub(r"[^" + self.prompts.ALL_ACTIONS + "]", "", temp)
    if self.skip_action:
        self.plan = (
            self.plan[observation["game_turn"] - turn :]
            if len(self.plan) > observation["game_turn"] - turn
            else ""
        )
```
**Python 문법: 삼항 연산자 (Ternary Operator)**
```python
값 = A if 조건 else B
```
- 조건이 `True`면 `A`, `False`면 `B`
- 한 줄로 if-else 표현

**skip_action 로직:**
```python
# 턴3에서 "UUUDDLR" 계획 생성
# 현재 턴5라면:
game_turn = 5, turn = 3
skip_count = 5 - 3 = 2
self.plan = "UUUDDLR"[2:] = "UDDLR"  # 앞 2개 건너뛰기
```

**Python 문법: 슬라이싱 (Slicing)**
```python
string[start:end]     # start부터 end-1까지
string[2:]            # 인덱스 2부터 끝까지
string[:5]            # 처음부터 인덱스 4까지
string[1:]            # 첫 글자 제거
```

#### Step 4: 현재 액션 선택 (Line 63-64)
```python
self.action = self.plan[0] if self.plan != "" else self.prompts.DEFAULT_ACTION
self.plan = self.plan[1:] if self.plan != "" else ""
```
**동작:**
1. 계획의 첫 글자를 현재 액션으로
2. 계획에서 첫 글자 제거 (다음 턴을 위해)

**예시:**
```python
self.plan = "UUUDD"
self.action = "U"       # 첫 글자
self.plan = "UUDD"      # 나머지
```

---

## 3️⃣ AgileThinker.think() - 하이브리드 전략

**위치**: `src/realtimegym/agents/agile.py:33-69`

```python
def think(self, timeout: Optional[float] = None) -> None:
    assert self.current_observation is not None and timeout is not None
    budget = timeout
    observation = self.current_observation
    self.state_string = observation["state_string"]
    game_turn = observation["game_turn"]
    prompt_gen = self.prompts.state_to_description(
        observation["state"], mode="agile"
    )
    prompt = ""
    if self.gen_text == "":  # check whether the last generation is finished
        messages = [{"role": "user", "content": prompt_gen["planning"]}]
        prompt = messages[-1]["content"]
    else:
        messages = []
    text, token_num, turn = self.planning_inference(messages, budget, game_turn)
    self.plan = f"""**Guidance from a Previous Thinking Model:** Turn \\( t_1 = {turn} \\)\n{text}"""
    if self.log_thinking:
        self.logs["plan"].append(self.plan)
        self.logs["model2_prompt"].append(prompt)
        self.logs["model2_response"].append(text)
    self.logs["model2_token_num"].append(token_num)

    prompt = prompt_gen["reactive"]
    if self.plan is not None:
        lines = self.plan.split("\n")
        for line in lines:
            prompt += f"> {line.strip()}\n"
    messages = [{"role": "user", "content": prompt}]
    text, token_num = self.reactive_inference(messages, self.internal_budget)
    self.action = re.sub(
        r"[^" + self.prompts.ALL_ACTIONS + "]", "", extract_boxed(text)
    )
    if self.log_thinking:
        self.logs["model1_prompt"].append(prompt)
        self.logs["model1_response"].append(text)
    self.logs["model1_token_num"].append(token_num)
```

### 핵심 특징

**🎯 두 모델의 협업**
- **Phase 1**: Planning 모델이 백그라운드에서 가이던스 생성
- **Phase 2**: Reactive 모델이 가이던스 + 현재 관찰로 최종 결정
- 장기 전략 + 즉각 대응의 장점 결합

### 단계별 분석

#### Phase 1: Planning (Line 39-54)

```python
prompt_gen = self.prompts.state_to_description(
    observation["state"], mode="agile"
)
```
**Python 문법: 딕셔너리 반환**
```python
# prompt_gen은 딕셔너리:
{
    "planning": "장기 계획용 프롬프트...",
    "reactive": "즉각 반응용 프롬프트..."
}
```

```python
messages = [{"role": "user", "content": prompt_gen["planning"]}]
```
- `prompt_gen["planning"]`: 딕셔너리 키로 값 접근

```python
self.plan = f"""**Guidance from a Previous Thinking Model:** Turn \\( t_1 = {turn} \\)\n{text}"""
```
**Python 문법: f-string (포맷 문자열)**
- `f"..."`: 중괄호 `{}` 안의 변수를 자동으로 문자열로 변환
- `\\(`: 백슬래시 이스케이프 (LaTeX 수식용)
- `\n`: 줄바꿈 문자
- 삼중 따옴표 `"""..."""`: 여러 줄 문자열

**예시:**
```python
turn = 5
text = "Move up to avoid cars"
result = f"**Guidance:** Turn \\( t_1 = {turn} \\)\n{text}"
# 출력:
# **Guidance:** Turn \( t_1 = 5 \)
# Move up to avoid cars
```

#### Phase 2: Reactive (Line 56-69)

```python
prompt = prompt_gen["reactive"]
if self.plan is not None:
    lines = self.plan.split("\n")
    for line in lines:
        prompt += f"> {line.strip()}\n"
```
**Python 문법: 문자열 메서드**
- `.split("\n")`: 줄바꿈으로 분리하여 리스트 반환
- `.strip()`: 앞뒤 공백 제거
- `+=`: 문자열 연결 (concatenation)

**Python 문법: for 루프**
```python
for 변수 in 컬렉션:
    # 각 요소에 대해 반복
```

**동작 예시:**
```python
self.plan = "Line1\nLine2\nLine3"
lines = ["Line1", "Line2", "Line3"]
prompt = "Initial: "
# 반복:
prompt += "> Line1\n"  # "Initial: > Line1\n"
prompt += "> Line2\n"  # "Initial: > Line1\n> Line2\n"
prompt += "> Line3\n"  # "Initial: > Line1\n> Line2\n> Line3\n"
```
**결과**: Planning 출력을 인용 형식(`>`)으로 Reactive 프롬프트에 추가

```python
text, token_num = self.reactive_inference(messages, self.internal_budget)
```
- `self.internal_budget`: Reactive 모델 전용 예산
- `timeout - internal_budget`: Planning 모델이 사용

---

## 🔄 세 에이전트의 실행 흐름 비교

### ReactiveAgent
```
관찰 → Reactive 추론 (전체 budget) → 액션 추출 → 종료
```

### PlanningAgent
```
턴1: 관찰 → Planning 시작 → 계획[0] 사용 → 계획[1:] 저장
턴2: 관찰 → Planning 계속 → 계획[0] 사용 → 계획[1:] 저장
턴3: Planning 완료 → 계획 시퀀스 생성 ("UUUDD")
턴4: 저장된 계획[0] 사용 ("U")
턴5: 저장된 계획[0] 사용 ("U")
...
```

### AgileThinker
```
관찰 → [Planning 시작 (백그라운드)]
     ↓
     Planning 출력 (부분) → Reactive에 전달
     ↓
     Reactive 추론 (internal_budget) → 최종 액션
```

---

## 📈 예산(Budget) 사용 비교

### 토큰 기반 (time_unit="token")

| 에이전트 | 총 예산 8192 토큰 | Planning | Reactive |
|---------|----------------|----------|----------|
| ReactiveAgent | 8192 | ❌ 0 | ✅ 8192 |
| PlanningAgent | 8192 | ✅ 8192 | ❌ 0 |
| AgileThinker | 8192 | ✅ 4096 | ✅ 4096 |

### 시간 기반 (time_unit="seconds")

| 에이전트 | 총 예산 10초 | Planning | Reactive |
|---------|------------|----------|----------|
| ReactiveAgent | 10초 | ❌ 0초 | ✅ 10초 |
| PlanningAgent | 10초 | ✅ 10초 | ❌ 0초 |
| AgileThinker | 10초 | ✅ 6초 | ✅ 4초 |

---

## 🧠 핵심 Python 문법 정리

### 1. **튜플 언패킹 (Tuple Unpacking)**
```python
text, token_num = function()  # 2개
text, token_num, turn = function()  # 3개
```

### 2. **조건 표현식 (Ternary Operator)**
```python
value = A if condition else B
```

### 3. **정규표현식 (Regular Expression)**
```python
re.sub(pattern, replacement, string)  # 치환
r"..."  # raw string (이스케이프 불필요)
[^ABC]  # ABC가 아닌 문자
```

### 4. **슬라이싱 (Slicing)**
```python
string[0]     # 첫 글자
string[1:]    # 첫 글자 제외한 나머지
string[n:]    # n번째 인덱스부터
```

### 5. **f-string (포맷 문자열)**
```python
f"Value: {variable}"
f"Calc: {x + y}"
```

### 6. **딕셔너리 접근**
```python
dict = {"key1": "value1", "key2": "value2"}
dict["key1"]  # "value1"
```

### 7. **문자열 메서드**
```python
string.split("\n")   # 분리 → 리스트
string.strip()       # 공백 제거
string += "text"     # 문자열 추가
```

---

## 💡 전략적 차이점 요약

| 측면 | ReactiveAgent | PlanningAgent | AgileThinker |
|------|--------------|---------------|--------------|
| **적합한 상황** | 빠른 반응 필요 | 복잡한 장기 전략 | 균형 잡힌 접근 |
| **강점** | 단순, 빠름 | 일관된 장기 계획 | 유연성, 적응성 |
| **약점** | 근시안적 | 변화 대응 느림 | 복잡성, 비용 높음 |
| **코드 복잡도** | ⭐ 낮음 | ⭐⭐ 중간 | ⭐⭐⭐ 높음 |
| **계산 비용** | 💰 낮음 | 💰💰 중간 | 💰💰💰 높음 |

---

## 📝 실제 사용 예시

### ReactiveAgent 실행
```bash
agile_eval --time_unit token \
    --time_pressure 8192 \
    --game freeway \
    --cognitive_load E \
    --mode reactive \
    --reactive-model-config configs/example-deepseek-v3.2-reactive.yaml \
    --seed_num 1 --repeat_times 1
```

### PlanningAgent 실행
```bash
agile_eval --time_unit token \
    --time_pressure 8192 \
    --game freeway \
    --cognitive_load E \
    --mode planning \
    --planning-model-config configs/example-deepseek-v3.2-planning.yaml \
    --seed_num 1 --repeat_times 1
```

### AgileThinker 실행
```bash
agile_eval --time_unit token \
    --time_pressure 8192 \
    --internal_budget 4096 \
    --game freeway \
    --cognitive_load E \
    --mode agile \
    --reactive-model-config configs/example-deepseek-v3.2-reactive.yaml \
    --planning-model-config configs/example-deepseek-v3.2-planning.yaml \
    --seed_num 1 --repeat_times 1
```
