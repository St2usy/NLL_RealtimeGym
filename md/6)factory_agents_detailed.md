# Factory Agents 상세 설명 (agents.py)

## 파일 개요

`src/realtimegym/environments/factory/agents.py`는 공장 환경에서 작동하는 로봇 에이전트들을 정의한 파일입니다.

---

## 📊 클래스 구조

```
Robot (베이스 클래스)
├── RobotArm (로봇팔)
└── LogisticsRobot (물류 로봇)

AgentStatus (Enum)
Task (데이터클래스)
```

---

## 1. AgentStatus (Enum)

로봇의 작동 상태를 나타내는 열거형

```python
class AgentStatus(Enum):
    IDLE = "idle"           # 유휴 상태
    MOVING = "moving"       # 이동 중
    OPERATING = "operating" # 작업 수행 중
    ERROR = "error"         # 에러 상태
```

---

## 2. Task (데이터클래스)

로봇에게 할당되는 작업을 정의

```python
@dataclass
class Task:
    task_type: str                        # "move", "operate", "pick", "drop"
    target_position: tuple[int, int]      # 목표 위치 (x, y)
    target_station: str                   # 목표 스테이션 이름
    work_item: WorkItem                   # 작업 대상 아이템
```

### Task 타입

| task_type | 설명 | 사용 로봇 |
|-----------|------|-----------|
| `move` | 특정 위치로 이동 | Robot (공통) |
| `operate` | 스테이션에서 작업 수행 | RobotArm 전용 |
| `pick` | 아이템 픽업 | LogisticsRobot 전용 |
| `drop` | 아이템 내려놓기 | LogisticsRobot 전용 |

---

## 3. Robot (베이스 클래스)

모든 로봇의 공통 기능을 정의하는 베이스 클래스

### 속성 (Attributes)

```python
# 기본 정보
self.robot_id: int                    # 로봇 고유 ID (0-43)
self.position: tuple[int, int]        # 현재 위치 (x, y)
self.robot_type: str                  # "arm" 또는 "logistics"
self.status: AgentStatus              # 현재 상태

# 작업 관리
self.current_task: Task | None        # 현재 수행 중인 작업
self.task_queue: list[Task]           # 대기 중인 작업 (최대 5개)
self.error_flag: bool                 # 에러 발생 여부

# 통계
self.total_moves: int                 # 총 이동 횟수
self.total_tasks_completed: int       # 완료한 작업 수
self.idle_steps: int                  # 유휴 시간 (스텝 단위)
```

### 주요 메서드

#### `assign_task(task: Task) -> bool`
작업을 로봇에게 할당

```python
def assign_task(self, task: Task) -> bool:
    if len(self.task_queue) < 5:  # 최대 5개까지만 큐에 추가
        self.task_queue.append(task)
        return True
    return False
```

- **반환값**: 성공 시 `True`, 큐가 가득 찬 경우 `False`
- **큐 제한**: 최대 5개 작업까지만 대기 가능

#### `move_towards(target: tuple[int, int]) -> None`
목표 위치를 향해 한 칸 이동 (Manhattan Distance)

```python
def move_towards(self, target: tuple[int, int]) -> None:
    x, y = self.position
    tx, ty = target

    # 우선순위: x축 → y축
    if x < tx:
        x += 1      # 오른쪽으로
    elif x > tx:
        x -= 1      # 왼쪽으로
    elif y < ty:
        y += 1      # 아래로
    elif y > ty:
        y -= 1      # 위로

    self.position = (x, y)
    self.total_moves += 1
```

**이동 방식**:
- **한 번에 한 칸씩** 이동 (대각선 이동 불가)
- **x축 우선**: x 좌표를 먼저 맞춘 후 y 좌표 조정
- **Manhattan Distance**: |x1-x2| + |y1-y2|

**예시**:
```
현재 위치: (2, 3)
목표 위치: (5, 7)

이동 경로:
(2,3) → (3,3) → (4,3) → (5,3) → (5,4) → (5,5) → (5,6) → (5,7)
총 7 스텝 소요
```

#### `is_at_position(target: tuple[int, int]) -> bool`
목표 위치에 도착했는지 확인

```python
def is_at_position(self, target: tuple[int, int]) -> bool:
    return self.position == target
```

#### `step() -> None`
**매 턴마다 호출되는 핵심 메서드**

```python
def step(self) -> None:
    # 1. 새 작업 시작
    if self.current_task is None and len(self.task_queue) > 0:
        self.current_task = self.task_queue.pop(0)  # FIFO
        self.status = AgentStatus.MOVING

    # 2. 현재 작업 실행
    if self.current_task is not None:
        if self.current_task.task_type == "move":
            if not self.is_at_position(self.current_task.target_position):
                self.move_towards(self.current_task.target_position)
                self.status = AgentStatus.MOVING
            else:
                self.complete_task()  # 도착 완료
    else:
        # 3. 작업 없으면 IDLE
        self.status = AgentStatus.IDLE
        self.idle_steps += 1
```

**동작 흐름**:
1. `task_queue`에서 작업 하나를 꺼내 `current_task`로 설정
2. 작업 타입에 따라 실행
3. 작업 완료 시 `complete_task()` 호출
4. 작업이 없으면 `IDLE` 상태로 대기

#### `complete_task() -> None`
현재 작업 완료 처리

```python
def complete_task(self) -> None:
    self.current_task = None
    self.total_tasks_completed += 1
    self.status = AgentStatus.IDLE
```

#### `get_state() -> dict`
로봇의 현재 상태를 딕셔너리로 반환

```python
def get_state(self) -> dict:
    return {
        "robot_id": self.robot_id,
        "type": self.robot_type,
        "position": self.position,
        "status": self.status.value,
        "has_task": self.current_task is not None,
        "queue_size": len(self.task_queue),
        "error": self.error_flag,
        "total_moves": self.total_moves,
        "total_tasks": self.total_tasks_completed,
        "idle_steps": self.idle_steps,
    }
```

---

## 4. RobotArm (로봇팔)

스테이션에 고정 배치되어 공정 작업을 수행하는 로봇

### 추가 속성

```python
self.assigned_station: str            # 할당된 스테이션 (예: "Washer", "Cutter")
self.operation_time_remaining: int    # 작업 남은 시간 (스텝 단위)
```

### `step()` 메서드 (오버라이드)

```python
def step(self) -> None:
    # 1. 작업 진행 중인 경우
    if self.status == AgentStatus.OPERATING:
        self.operation_time_remaining -= 1
        if self.operation_time_remaining <= 0:
            self.complete_task()
        return  # 작업 중에는 다른 일 불가

    # 2. 새 작업 시작
    if self.current_task is None and len(self.task_queue) > 0:
        self.current_task = self.task_queue.pop(0)

    # 3. 작업 실행
    if self.current_task is not None:
        if self.current_task.task_type == "operate":
            self.status = AgentStatus.OPERATING
            self.operation_time_remaining = 2  # 2 스텝 소요
        elif self.current_task.task_type == "move":
            if not self.is_at_position(self.current_task.target_position):
                self.move_towards(self.current_task.target_position)
                self.status = AgentStatus.MOVING
            else:
                self.complete_task()
    else:
        self.status = AgentStatus.IDLE
        self.idle_steps += 1
```

### 주요 차이점

| 항목 | Robot (베이스) | RobotArm |
|------|---------------|----------|
| **작업 타입** | move만 가능 | move + **operate** |
| **작업 시간** | 즉시 | operate는 **2 스텝** 소요 |
| **상태** | IDLE, MOVING, ERROR | + **OPERATING** |
| **고정 배치** | 아니오 | **예** (assigned_station) |

### 작업 흐름 예시

```python
# 1. Washer에서 작업 명령
task = Task(task_type="operate", target_station="Washer")
robot_arm.assign_task(task)

# 2. Step 1: 작업 시작
robot_arm.step()
# status: OPERATING, operation_time_remaining: 2

# 3. Step 2: 작업 진행
robot_arm.step()
# status: OPERATING, operation_time_remaining: 1

# 4. Step 3: 작업 완료
robot_arm.step()
# status: IDLE, total_tasks_completed: 1
```

---

## 5. LogisticsRobot (물류 로봇)

스테이션 간 재료/제품을 운반하는 로봇

### 추가 속성

```python
self.carrying: bool                   # 물건을 들고 있는지 여부
self.carried_item: WorkItem | None    # 현재 운반 중인 아이템
```

### `step()` 메서드 (오버라이드)

```python
def step(self) -> None:
    # 1. 새 작업 시작
    if self.current_task is None and len(self.task_queue) > 0:
        self.current_task = self.task_queue.pop(0)

    # 2. 작업 실행
    if self.current_task is not None:
        if self.current_task.task_type == "move":
            if not self.is_at_position(self.current_task.target_position):
                self.move_towards(self.current_task.target_position)
                self.status = AgentStatus.MOVING
            else:
                self.complete_task()

        elif self.current_task.task_type == "pick":
            if self.current_task.work_item and not self.carrying:
                self.carried_item = self.current_task.work_item
                self.carrying = True
                self.complete_task()

        elif self.current_task.task_type == "drop":
            if self.carrying:
                self.carried_item = None
                self.carrying = False
                self.complete_task()
    else:
        self.status = AgentStatus.IDLE
        self.idle_steps += 1
```

### 주요 차이점

| 항목 | Robot (베이스) | LogisticsRobot |
|------|---------------|----------------|
| **작업 타입** | move만 가능 | move + **pick** + **drop** |
| **운반 기능** | 없음 | **있음** (carrying, carried_item) |
| **고정 배치** | 아니오 | **아니오** (자유 이동) |

### 작업 흐름 예시

```python
# Storage → Washer로 재료 운반

# 1. Storage로 이동
task1 = Task(task_type="move", target_position=(1, 1))
robot.assign_task(task1)

# 2. 아이템 픽업
task2 = Task(task_type="pick", work_item=salad_item)
robot.assign_task(task2)

# 3. Washer로 이동
task3 = Task(task_type="move", target_position=(3, 3))
robot.assign_task(task3)

# 4. 아이템 드롭
task4 = Task(task_type="drop")
robot.assign_task(task4)

# Step마다 순차적으로 실행
for _ in range(10):
    robot.step()
```

---

## 📊 현재 환경에서의 Agent 배치

### 테스트 결과 분석

```bash
python test_agents_by_station.py
```

### 1. Robot Arms 배치

**총 20개**: 각 station마다 2-4개씩 배치

| Station | 개수 | 위치 (라인 0) | 위치 (라인 1) |
|---------|------|--------------|--------------|
| **Washer** | 4 | (2,3), (2,4) | (17,3), (17,4) |
| **Cutter** | 4 | (2,6), (2,7) | (17,6), (17,7) |
| **Cooker** | 4 | (2,9), (2,10) | (17,9), (17,10) |
| **Plating** | 4 | (2,11), (2,12) | (17,11), (17,12) |
| **Sealing** | 2 | (4,13) | (19,13) |
| **VisionQA** | 2 | (6,13) | (21,13) |

**특징**:
- ✅ **각 station마다 전용 robot arm 할당됨**
- ✅ **2개 라인에 대칭적으로 배치됨**
- ✅ **각 arm은 고유한 위치를 가짐** (겹치지 않음)
- ✅ **assigned_station 속성으로 구분됨**

### 2. Logistics Robots 배치

**총 24개**: 각 라인에 12개씩 분산 배치

| 라인 | 개수 | 위치 범위 |
|------|------|-----------|
| 라인 0 | 12 | x=5, y=2~13 |
| 라인 1 | 12 | x=20, y=2~13 |

**특징**:
- ✅ **라인을 따라 균등 배치**
- ✅ **각 로봇은 고유한 위치를 가짐**
- ❌ **특정 station에 할당되지 않음** (자유 이동 가능)

---

## ⚠️ 현재 프로토타입의 한계

### 테스트 결과: 모든 Agent가 IDLE 상태

```
After 10 steps:
  Total arms idle: 20/20
  Total logistics idle: 24/24

  Moved robot arms: 0
  Operated robot arms: 0
  Moved logistics robots: 0
```

### 문제점

#### 1. **Task 할당이 없음**
```python
# factory_env.py의 step() 메서드
for robot in self.robot_arms:
    robot.step()  # 호출은 되지만 task_queue가 비어있음
```

**원인**:
- `assign_task()` 메서드가 호출되지 않음
- 로봇들의 `task_queue`가 항상 빈 상태
- 따라서 `step()` 내부에서 항상 IDLE 상태로 유지

#### 2. **워크플로우가 자동화되어 로봇 불필요**
```python
# _auto_workflow() 메서드가 모든 걸 처리
def _auto_workflow(self) -> None:
    for station in self.stations[station_type]:
        while len(station.output_buffer) > 0:
            item = station.pickup_output()
            # 직접 다음 스테이션에 추가 (로봇 없이)
            next_station.add_to_queue(item)
```

**원인**:
- 스테이션 간 이동이 자동으로 처리됨
- 로봇이 실제로 운반할 필요가 없음

#### 3. **Station 작업도 자동화됨**
```python
# Station.process_step()이 자동으로 처리
def process_step(self, random_state) -> None:
    if self.current_work is not None:
        self.current_work.time_remaining -= 1
        # 로봇 없이 자동으로 처리
```

**원인**:
- 로봇팔이 작업을 시작하지 않아도 스테이션이 자동 처리
- `RobotArm.operate()` 기능이 사용되지 않음

---

## 🎯 Agent가 실제로 동작하려면?

### 필요한 변경사항

#### 1. **워크플로우에서 로봇 할당**

**현재 (자동)**:
```python
# _auto_workflow()에서 직접 이동
next_station.add_to_queue(item)
```

**변경 후 (로봇 사용)**:
```python
# 물류 로봇에게 운반 작업 할당
available_robot = self._find_nearest_logistics_robot(current_station.position)
if available_robot:
    # 1. 현재 스테이션으로 이동
    available_robot.assign_task(Task(
        task_type="move",
        target_position=current_station.position
    ))
    # 2. 아이템 픽업
    available_robot.assign_task(Task(
        task_type="pick",
        work_item=item
    ))
    # 3. 다음 스테이션으로 이동
    available_robot.assign_task(Task(
        task_type="move",
        target_position=next_station.position
    ))
    # 4. 아이템 드롭
    available_robot.assign_task(Task(
        task_type="drop"
    ))
```

#### 2. **Station 작업에 로봇팔 필요**

**현재 (자동)**:
```python
# Station이 자동으로 처리
station.process_step(random_state)
```

**변경 후 (로봇 필요)**:
```python
# 스테이션에서 작업이 필요할 때
if station.queue and not station.current_work:
    # 해당 스테이션의 로봇팔 찾기
    assigned_arms = [r for r in self.robot_arms
                     if r.assigned_station == station.name]

    # 유휴 로봇팔에게 작업 할당
    idle_arm = next((r for r in assigned_arms if r.status == AgentStatus.IDLE), None)
    if idle_arm:
        idle_arm.assign_task(Task(
            task_type="operate",
            target_station=station.name
        ))
        # 로봇이 operate를 완료해야 station.start_processing() 호출
```

#### 3. **Robot Coordinator Agent 구현**

```python
class RobotCoordinatorAgent:
    """로봇 협동 에이전트 (향후 LLM 기반)"""

    def schedule_logistics(self, from_station, to_station, item):
        """물류 로봇 스케줄링"""
        # 가장 가까운 로봇 찾기
        robot = self._find_nearest_robot(from_station.position)

        # 충돌 회피 경로 계획
        path = self._plan_collision_free_path(
            robot.position,
            to_station.position
        )

        # 작업 할당
        self._assign_transport_tasks(robot, from_station, to_station, item, path)

    def schedule_operation(self, station):
        """로봇팔 작업 스케줄링"""
        # 해당 스테이션의 로봇팔 찾기
        arms = self._get_assigned_arms(station)

        # 우선순위에 따라 로봇팔 선택
        selected_arm = self._select_by_priority(arms)

        # 작업 할당
        selected_arm.assign_task(Task(task_type="operate"))
```

---

## 📊 정리: Station마다 Agent가 다른가?

### ✅ 설계상으로는 YES

| 항목 | 현재 상태 |
|------|----------|
| **RobotArm 배치** | ✅ 각 station마다 전용 arm 할당됨 |
| **위치 분리** | ✅ 각 arm은 고유한 위치를 가짐 |
| **assigned_station** | ✅ 각 arm은 담당 station이 명확함 |
| **LogisticsRobot 배치** | ✅ 라인별로 균등 분산 배치됨 |

### ❌ 동작상으로는 NO

| 항목 | 현재 상태 |
|------|----------|
| **Task 할당** | ❌ 아무도 작업을 할당하지 않음 |
| **실제 이동** | ❌ 모든 로봇이 제자리 (total_moves=0) |
| **실제 작업** | ❌ 모든 로봇이 idle (total_tasks_completed=0) |
| **Station 의존** | ❌ Station이 로봇 없이 자동 처리됨 |

---

## 결론

### 현재 상태

**Agent 구조**:
- ✅ **완벽하게 구현됨**: 클래스, 메서드, 속성 모두 잘 정의됨
- ✅ **Station마다 구분됨**: RobotArm은 각 station에 전용 배치
- ✅ **Task 시스템 준비됨**: assign_task, task_queue 모두 작동 가능

**실제 동작**:
- ❌ **사용되지 않음**: 모든 agent가 idle 상태
- ❌ **자동화로 대체됨**: `_auto_workflow()`가 모든 걸 처리
- ❌ **Task 할당 없음**: 아무도 `assign_task()`를 호출하지 않음

### 향후 작업

**상위 에이전트가 구현되면**:
1. **로봇 협동 에이전트**가 `assign_task()` 호출
2. **물류 로봇**이 station 간 운반 수행
3. **로봇팔**이 실제 공정 작업 수행
4. `_auto_workflow()` 제거 또는 수정

**그러면**:
- ✅ Agent들이 실제로 움직임 (total_moves > 0)
- ✅ 작업 수행 (total_tasks_completed > 0)
- ✅ Station마다 다른 동작 수행
- ✅ 실시간 스케줄링 및 최적화 가능

---

## 코드 요약

```python
# 현재: 모든 agent idle
for robot in self.robot_arms:
    robot.step()  # task_queue가 비어있어서 항상 idle

# 향후: agent가 실제 작업
for robot in self.robot_arms:
    if robot.status == AgentStatus.IDLE:
        # 로봇 협동 에이전트가 작업 할당
        coordinator.assign_work_to_robot(robot)
    robot.step()  # task를 실행
```

현재는 **프레임워크는 완벽하지만 사용되지 않는 상태**입니다! 🤖💤
