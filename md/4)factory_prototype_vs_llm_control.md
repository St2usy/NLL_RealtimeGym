# Factory 프로토타입 vs LLM 제어

## 질문: factory_basic.py는 LLM reasoning 없이 단순히 turn마다 station이 작동하는 것인가?

**답변: 맞습니다!** 👍

---

## 현재 `factory_basic.py`의 동작 방식

```python
env.step("produce_ricotta_salad")  # 제품 생성만 명령
env.step("continue")                # 이후는 자동 진행
env.step("continue")                # LLM reasoning 없음
```

### 현재 상태 (프로토타입)

#### 1. 자동 워크플로우 (`_auto_workflow()`)
- 스테이션 간 제품 이동이 **자동**
- Storage 완료 → Washer로 자동 이동
- Washer 완료 → Cutter로 자동 이동
- Cutter 완료 → 다음 스테이션으로 자동 이동
- ... 끝까지 자동

#### 2. 로봇은 Idle
- 로봇팔 20개, 물류 로봇 24개 모두 `idle` 상태
- 실제로 아무 일도 안 함
- 단순히 위치만 추적

#### 3. 단순 액션만 가능
- `produce_X`: 제품 생성
- `maintain_cutter_X`: 유지보수
- `continue`: 계속 진행

---

## 향후 상위 에이전트가 제어할 내용 (LLM Reasoning)

### 1. 부품 설계 에이전트 (Product Design Agent)

**현재 (자동)**:
```python
# 제품이 자동으로 라인 0으로 배정됨
env.step("produce_ricotta_salad")
→ Storage[0]에 자동 추가
```

**향후 (LLM 제어)**:
```python
# LLM이 상황을 분석하고 결정
LLM Reasoning:
"현재 라인 0은 Cutter에 3개 제품이 대기 중이고,
라인 1은 Washer에 1개만 있네.
리코타 샐러드는 라인 1로 보내는 게 효율적이겠다."

Action: assign_product_to_line(salad, line=1)
```

**더 복잡한 시나리오**:
```python
LLM Reasoning:
"지금 볶음밥 20개 주문이 들어왔는데,
Cooker의 batch_size가 30이니까 한 번에 조리 가능하다.
하지만 Cutter[0]의 blade_sharpness가 0.3이라 고장 위험이 있다.
라인 1의 Cutter를 사용하되, 유지보수를 먼저 예약해야겠다."

Action:
1. assign_product_to_line(rice, line=1)
2. schedule_maintenance(cutter_0, time="+30min")
3. adjust_batch_size(cooker_0, size=30)
```

---

### 2. 설비 관리 에이전트 (Facility Management Agent)

**현재 (수동)**:
```python
# 사용자가 직접 유지보수 명령
env.step("maintain_cutter_0")
```

**향후 (LLM 제어)**:
```python
LLM Reasoning:
"Cutter[0]의 blade_sharpness가 0.3으로 떨어졌다.
failure_probability가 0.007 (0.7%)로 증가했다.
현재 큐에 2개 제품이 있으니 처리 후 유지보수하자.
예상 시간: 4 스텝 후"

Action:
1. monitor_equipment_status()
2. schedule_maintenance(cutter_0, after_queue_empty=True)
3. notify_robot_coordinator("cutter_0 will be down in 4 steps")
```

**예지보전 시나리오**:
```python
LLM Reasoning:
"과거 데이터를 보니 Sealing[1]의 압력이 0.85 이하로 떨어지면
불량률이 5% → 12%로 증가했다.
현재 압력이 0.87이니 선제적으로 조정하자."

Action: adjust_sealing_pressure(sealing_1, pressure=0.95)
```

---

### 3. 로봇 협동 에이전트 (Robot Coordination Agent)

**현재 (Idle)**:
```python
# 로봇들은 아무 것도 안 함
for robot in robot_arms:
    robot.status == "idle"  # 계속 idle
```

**향후 (LLM 제어)**:
```python
LLM Reasoning:
"Washer[0]에서 세척이 완료되었다.
물류 로봇 3번이 가장 가까운 위치(5, 3)에 있고,
Cutter[0]까지의 경로는 (5,3) → (4,5) → (3,6)이다.
로봇 7번은 (8,5)에 있어서 충돌 가능성이 있으니 대기시키자."

Action:
1. assign_task(logistics_robot_3, "pick", station=washer_0)
2. assign_task(logistics_robot_3, "move", target=(3,6))
3. assign_task(logistics_robot_3, "drop", station=cutter_0)
4. assign_task(robot_arm_5, "operate", station=cutter_0)
5. hold_position(logistics_robot_7, duration=3)
```

**충돌 회피 시나리오**:
```python
LLM Reasoning:
"로봇 3번과 로봇 12번이 모두 (5,8) 위치로 이동 중이다.
2 스텝 후 충돌할 것으로 예상된다.
로봇 12번의 우선순위가 더 높으니 (긴급 주문 처리 중)
로봇 3번을 우회 경로로 보내자."

Action:
1. update_path(robot_3, new_path=[(5,6), (6,7), (6,8)])
2. continue_path(robot_12)
```

---

### 4. 품질 검사 에이전트 (Quality Assurance Agent)

**현재 (자동)**:
```python
# VisionQA가 자동으로 불량품 제거
if item.defective:
    reject()  # 자동 폐기
```

**향후 (LLM 제어)**:
```python
LLM Reasoning:
"최근 10개 제품 중 2개가 불량으로 판정되었다.
불량률이 20%로 임계치(5%)를 초과했다.
원인 분석:
1. Cutter[0]의 blade_sharpness: 0.35 → 절단 불량 가능
2. Sealing[0]의 pressure: 0.82 → 밀봉 불량 가능

설비 관리 에이전트에게 Cutter 유지보수 요청하고,
Sealing 압력을 즉시 조정하자."

Action:
1. analyze_defect_pattern()
2. request_maintenance(cutter_0, priority="high")
3. adjust_parameter(sealing_0, "pressure", value=0.95)
4. increase_inspection_frequency(vision_qa_0, multiplier=2)
```

**품질 기준 조정 시나리오**:
```python
LLM Reasoning:
"프리미엄 제품 주문이 들어왔다.
품질 기준을 더 엄격하게 적용해야 한다.
중량 허용 오차: ±5% → ±2%
외관 검사 민감도: 0.8 → 0.95"

Action:
1. update_qa_standards(vision_qa_0, weight_tolerance=0.02)
2. update_qa_standards(vision_qa_0, appearance_sensitivity=0.95)
3. notify_all_agents("premium_mode_enabled")
```

---

## 비교표: 현재 vs 향후

| 항목 | 현재 (프로토타입) | 향후 (LLM 제어) |
|------|------------------|----------------|
| **워크플로우** | ✅ 자동 (`_auto_workflow()`) | 🤖 부품 설계 에이전트가 결정 |
| **라인 배정** | ❌ 항상 라인 0 | 🤖 부하 분산 최적화 |
| **로봇 제어** | ❌ Idle (아무 것도 안 함) | 🤖 로봇 협동 에이전트가 스케줄링 |
| **경로 계획** | ❌ 없음 | 🤖 충돌 회피, 최단 경로 |
| **유지보수** | ⚠️ 수동 명령 (`maintain_cutter_X`) | 🤖 설비 관리 에이전트가 시점 결정 |
| **예지보전** | ❌ 없음 | 🤖 마모도 예측, 선제 조치 |
| **품질 관리** | ✅ 자동 (불량품 자동 제거) | 🤖 품질 검사 에이전트가 기준 조정 |
| **불량 원인 분석** | ❌ 없음 | 🤖 패턴 분석, 근본 원인 해결 |
| **의사결정** | ❌ 없음 | ✅ **LLM reasoning** |
| **상황 인식** | ❌ 없음 | ✅ 전체 시스템 상태 파악 |
| **최적화** | ❌ 없음 | ✅ 실시간 최적화 |

---

## 실행 흐름 비교

### 현재 (프로토타입)

```
1. env.step("produce_ricotta_salad")
   → WorkItem 생성 → Storage[0] 자동 추가

2. env.step("continue")
   → Storage 처리 (자동)
   → Washer로 자동 이동

3. env.step("continue")
   → Washer 처리 (자동)
   → Cutter로 자동 이동

... (자동 반복)

N. 제품 완성 → 보상 +10점
```

**특징**:
- ❌ 의사결정 없음
- ❌ 상황 판단 없음
- ✅ 단순 시뮬레이션만 가능

---

### 향후 (LLM 제어)

```
1. 주문 접수: "샐러드 5개, 볶음밥 3개 긴급 주문"

2. [부품 설계 에이전트]
   LLM Reasoning:
   "볶음밥이 긴급이니 우선 처리하자.
   라인 0은 Cooker가 비어있고, 라인 1은 샐러드 처리 중.
   볶음밥 → 라인 0, 샐러드 → 라인 1로 배정"

   Action:
   - assign_to_line(rice, 0)
   - assign_to_line(salad, 1)

3. [로봇 협동 에이전트]
   LLM Reasoning:
   "Storage → Washer 운반이 필요하다.
   로봇 3, 5, 7이 가장 가깝다.
   로봇 3은 배터리 20%라 제외.
   로봇 5 할당."

   Action:
   - assign_task(robot_5, "pick_and_deliver")
   - monitor_battery_levels()

4. [설비 관리 에이전트]
   (백그라운드 모니터링)
   LLM Reasoning:
   "Cutter[0] blade_sharpness 0.4로 감소.
   현재 작업 완료 후 유지보수 예약"

   Action:
   - schedule_maintenance(cutter_0, "+20steps")

5. env.step() × N
   (각 스텝마다 에이전트들이 상황 판단 및 조치)

6. [품질 검사 에이전트]
   LLM Reasoning:
   "불량률 증가 감지. Cutter 마모가 원인.
   즉시 유지보수 요청"

   Action:
   - request_urgent_maintenance(cutter_0)
   - adjust_production_speed(line_0, -20%)

7. 생산 완료
   - KPI 분석
   - 개선점 도출
   - 다음 주문 최적화
```

**특징**:
- ✅ 실시간 의사결정
- ✅ 상황별 최적화
- ✅ 문제 예측 및 선제 대응
- ✅ 다중 에이전트 협업

---

## 코드 비교

### 현재: 자동 워크플로우

```python
def _auto_workflow(self) -> None:
    """자동으로 다음 스테이션으로 이동"""
    for station_type in workflow_order:
        for station in self.stations[station_type]:
            while len(station.output_buffer) > 0:
                item = station.pickup_output()

                # 다음 스테이션 자동 결정
                recipe = RECIPES[item.product_type]
                item.current_step += 1
                next_station_type = recipe.workflow[item.current_step]

                # 자동으로 같은 라인의 다음 스테이션에 추가
                line_idx = self.stations[station_type].index(station)
                next_station = self.stations[next_station_type][line_idx]
                next_station.add_to_queue(item)
```

---

### 향후: LLM 기반 의사결정

```python
def step(self, action: str):
    """LLM 에이전트들이 상황을 파악하고 결정"""

    # 1. 현재 상황 관찰
    observation = self.get_full_observation()

    # 2. 부품 설계 에이전트 추론
    design_agent_prompt = f"""
    현재 공장 상태:
    - 라인 0: Cutter에 3개 대기, Cooker 사용 중
    - 라인 1: Washer에 1개 대기, Cooker 비어있음
    - 새 주문: 볶음밥 5개 (긴급)

    최적의 라인 배정을 결정하세요.
    """
    design_decision = llm_reasoning(design_agent_prompt)

    # 3. 로봇 협동 에이전트 추론
    robot_agent_prompt = f"""
    Washer[0]에서 작업 완료:
    - 로봇 3: 위치 (5,3), 배터리 85%
    - 로봇 7: 위치 (8,5), 배터리 20%
    - 로봇 12: 위치 (10,2), 배터리 95%, 긴급 작업 중

    Cutter[0]로 운반할 로봇을 선택하고 경로를 계획하세요.
    """
    robot_decision = llm_reasoning(robot_agent_prompt)

    # 4. 설비 관리 에이전트 추론
    facility_agent_prompt = f"""
    설비 상태:
    - Cutter[0]: blade_sharpness 0.35, failure_prob 0.65%
    - Cutter[1]: blade_sharpness 0.78, failure_prob 0.22%
    - Sealing[0]: pressure 0.82, 최근 불량률 8%

    유지보수 우선순위를 정하고 조치 시점을 결정하세요.
    """
    facility_decision = llm_reasoning(facility_agent_prompt)

    # 5. 품질 검사 에이전트 추론
    qa_agent_prompt = f"""
    최근 10개 제품:
    - 8개 합격
    - 2개 불량 (Cutter[0]에서 처리된 제품)

    원인을 분석하고 대응 방안을 제시하세요.
    """
    qa_decision = llm_reasoning(qa_agent_prompt)

    # 6. 결정 사항 실행
    self.execute_decisions(
        design_decision,
        robot_decision,
        facility_decision,
        qa_decision
    )
```

---

## 요약

### ✅ 현재 상태 (프로토타입)

**구현된 것**:
- ✅ 공정 환경 (Factory Environment)
- ✅ 스테이션 시뮬레이션
- ✅ 로봇 에이전트 구조
- ✅ 제품 워크플로우
- ✅ KPI 추적

**자동화된 것**:
- ✅ 워크플로우 (스테이션 간 자동 이동)
- ✅ 품질 검사 (불량품 자동 제거)

**없는 것**:
- ❌ LLM reasoning
- ❌ 상위 에이전트
- ❌ 의사결정 로직
- ❌ 최적화

---

### 🚀 다음 단계 (LLM 제어)

**구현할 것**:
- 🤖 상위 에이전트 4개 (부품 설계, 설비 관리, 로봇 협동, 품질 검사)
- 🤖 LLM reasoning 통합
- 🤖 실시간 의사결정
- 🤖 다중 에이전트 협업
- 🤖 최적화 알고리즘

**기대 효과**:
- ✨ 상황별 최적 판단
- ✨ 문제 예측 및 선제 대응
- ✨ 실시간 라인 밸런싱
- ✨ 자동 고장 예방
- ✨ 품질 자동 개선

---

## 결론

**현재**: Turn마다 station이 자동으로 작동하는 **시뮬레이션 플랫폼** ✅

**목표**: LLM이 실시간으로 판단하고 제어하는 **지능형 무인공장** 🤖

이 환경은 LLM 에이전트들이 **"언제, 어디로, 어떻게"** 제품을 생산할지 실시간으로 reasoning하고 결정할 수 있는 플랫폼입니다! 🏭
