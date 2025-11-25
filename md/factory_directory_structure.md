# Factory 디렉토리 구조 설명

`src\realtimegym\environments\factory` 디렉토리는 무인 식품 공장 시뮬레이션 환경을 구현한 모듈입니다.

## 📁 디렉토리 구조

```
factory/
├── __init__.py          # 환경 등록 및 진입점
├── factory_env.py       # 메인 환경 클래스 (FactoryEnv)
├── stations.py          # 스테이션 클래스들
├── agents.py            # 로봇 에이전트 클래스들
├── recipes.py           # 제품 레시피 정의
└── README.md            # 사용 문서
```

---

## 📄 각 파일 설명

### 1. `__init__.py` (진입점)

```python
# 환경 등록 및 setup 함수
setup_env(seed, cognitive_load, save_trajectory_gifs)
```

- **역할**: Factory 환경을 RealtimeGym에 등록
- **seed_mapping**: Easy(v0), Medium(v1), Hard(v2) 난이도별 시드 매핑
- `realtimegym.make("Factory-v0")` 호출 시 이 파일을 통해 환경 생성

---

### 2. `recipes.py` (제품 레시피)

**Recipe 데이터클래스**:
```python
@dataclass
class Recipe:
    name: str                          # 제품명
    ingredients: list[str]             # 재료 목록
    workflow: list[str]                # 공정 순서 (스테이션 이름)
    processing_times: dict[str, int]   # 각 스테이션 처리 시간
```

**3가지 제품**:

#### 1. RICOTTA_SALAD (리코타치즈 샐러드)
- **재료**: 양상추, 로메인, 새싹잎, 방울토마토, 리코타치즈, 견과류, 발사믹 소스
- **워크플로우**: Storage → Washer → Cutter → Plating → Sealing → VisionQA → FinalStorage
- **총 처리 시간**: 12 스텝

#### 2. SHRIMP_FRIED_RICE (새우 볶음밥)
- **재료**: 밥, 새우, 대파, 당근, 양파, 식용유, 굴소스
- **워크플로우**: Storage → Washer → Cutter → **Cooker** → Plating → Sealing → VisionQA → FinalStorage
- **총 처리 시간**: 17 스텝 (조리 시간 5 스텝)

#### 3. TOMATO_PASTA (토마토 파스타)
- **재료**: 파스타면, 토마토, 양파, 마늘, 올리브오일, 설탕, 소금, 토마토 소스
- **워크플로우**: Storage → Washer → Cutter → **Cooker** → Plating → Sealing → VisionQA → FinalStorage
- **총 처리 시간**: 18 스텝 (조리 시간 6 스텝)

---

### 3. `stations.py` (스테이션 클래스)

**WorkItem 데이터클래스**:
```python
@dataclass
class WorkItem:
    product_type: str      # 제품 종류
    product_id: int        # 제품 고유 ID
    current_step: int      # 현재 공정 단계
    time_remaining: int    # 남은 처리 시간
    ingredients: list[str] # 재료 목록
```

**Station 베이스 클래스**:
```python
class Station:
    - name: 스테이션 이름
    - position: (x, y) 그리드 위치
    - status: IDLE/PROCESSING/WAITING_PICKUP/ERROR/MAINTENANCE
    - queue: 대기 중인 작업 목록
    - current_work: 현재 처리 중인 작업
    - output_buffer: 완료된 작업 (픽업 대기)
    - wear_level: 마모도 (0.0~1.0)
```

**7개 스테이션 구현**:

#### 1. Storage (입고/보관)
- 원재료와 완제품 저장
- `is_final`: FinalStorage 여부
- `inventory`: 재고 관리

#### 2. Washer (세척)
- 채소, 육류 세척
- 처리 시간: 2 스텝 (고정)

#### 3. Cutter (절단)
- 야채/육류 절단, 슬라이싱
- **칼날 마모 시뮬레이션**:
  - `blade_sharpness`: 0.0~1.0
  - 사용할수록 마모 → 고장 확률 증가
- 유지보수 가능 (`maintain_cutter_X` 액션)

#### 4. Cooker (조리/배합)
- 볶기, 데우기, 소스 조리
- `batch_size`: 30인분 (한 번에 20~30인분 조리 가능)
- `temperature`: 온도 파라미터

#### 5. Plating (조립/플레이팅)
- 용기에 밥/재료/토핑 담기
- 처리 시간: 3 스텝

#### 6. Sealing (밀봉/포장)
- 밀봉, 패킹, 라벨링
- **불량 발생 메커니즘**:
  - `pressure`: 압력 파라미터
  - 압력이 낮거나 마모도가 높으면 불량 발생
  - 불량품은 `defective=True` 마킹

#### 7. VisionQA (품질 검사)
- 카메라 기반 중량/외관 검사
- **불량 자동 제거**:
  - `defective=True`인 제품 감지
  - 자동으로 폐기 (output_buffer에 추가 안함)
  - `rejected_count` 카운팅
- `defect_rate` 계산

---

### 4. `agents.py` (로봇 에이전트)

**Robot 베이스 클래스**:
```python
class Robot:
    - robot_id: 로봇 고유 ID
    - position: (x, y) 그리드 위치
    - status: IDLE/MOVING/OPERATING/ERROR
    - current_task: 현재 작업
    - task_queue: 작업 대기열
    - total_moves: 총 이동 횟수
    - idle_steps: 유휴 시간
```

**Task 데이터클래스**:
```python
@dataclass
class Task:
    task_type: str                        # "move", "operate", "pick", "drop"
    target_position: tuple[int, int]      # 목표 위치
    target_station: str                   # 목표 스테이션
    work_item: WorkItem                   # 작업 아이템
```

**2가지 로봇 타입**:

#### 1. RobotArm (로봇팔) - 20개
- 각 스테이션에 배치
  - Washer 2개, Cutter 2개, Cooker 2개, Plating 2개 (라인당)
  - Sealing 1개, VisionQA 1개 (라인당)
  - 총: (2+2+2+2+1+1) × 2라인 = 20개
- **역할**: 이동 + 공정 작업 수행
- `assigned_station`: 할당된 스테이션
- `operation_time_remaining`: 작업 남은 시간
- Operate 작업: 2 스텝 소요

#### 2. LogisticsRobot (물류 로봇) - 24개
- 각 라인에 12개씩 분산 배치
- **역할**: 이동 + 재료/제품 운반
- `carrying`: 물건을 들고 있는지 여부
- `carried_item`: 현재 운반 중인 아이템
- Pick/Drop 작업 수행

---

### 5. `factory_env.py` (메인 환경)

**FactoryEnv 클래스** (BaseEnv 상속):

```python
class FactoryEnv(BaseEnv):
    # 그리드 설정
    width = 30, height = 16
    num_lines = 2  # 2개 생산 라인

    # 구성 요소
    stations: dict[str, list[Station]]     # 스테이션들
    robot_arms: list[RobotArm]             # 로봇팔 20개
    logistics_robots: list[LogisticsRobot] # 물류 로봇 24개

    # 생산 추적
    products_in_progress: list[WorkItem]   # 진행 중인 제품
    completed_products: list[WorkItem]     # 완성된 제품

    # KPI
    total_production: int                  # 총 생산량
    total_lead_time: int                   # 총 리드 타임
    rejected_products: int                 # 불량품 수
    collision_count: int                   # 충돌 횟수
```

**주요 메서드**:

#### 1. `reset()`: 환경 초기화
- 스테이션 배치 (`_setup_stations()`)
- 로봇 배치 (`_setup_robots()`)
- 생산 스케줄 초기화

#### 2. `step(action)`: 1 스텝 실행
- 액션 처리:
  - `produce_X`: 제품 생산 시작
  - `maintain_cutter_X`: 설비 유지보수
  - `continue`: 현재 작업 계속
- 모든 스테이션 처리 (`station.process_step()`)
- **워크플로우 자동화** (`_auto_workflow()`)
- 모든 로봇 업데이트
- 완성품 수집 및 보상 계산

#### 3. `_auto_workflow()`: 프로토타입 자동화
- 각 스테이션의 output_buffer 확인
- 완료된 아이템을 다음 스테이션으로 이동
- `current_step` 증가, `time_remaining` 설정
- 같은 라인의 다음 스테이션에 추가

#### 4. `state_string()`: 텍스트 시각화
- 생산 통계 (진행 중/완료/불량)
- 스테이션 상태 (라인별)
- 로봇 통계 (유휴/바쁨)

#### 5. `state_builder()`: 구조화된 상태
- 모든 스테이션 상태
- 모든 로봇 상태
- KPI 지표들

**보상 시스템**:
```python
reward = completed_products × 10    # 완성품당 +10점
       - rejected_products × 5      # 불량품당 -5점
```

---

## 🎮 실행 흐름 예시

### 1. 제품 생산 명령
```python
env.step("produce_ricotta_salad")
```
→ WorkItem 생성 → Storage[0].queue에 추가

### 2. 자동 워크플로우
- **Storage 처리 완료** (1 스텝)
  - → Washer로 자동 이동
- **Washer 처리 완료** (2 스텝)
  - → Cutter로 자동 이동
- **Cutter 처리 완료** (2 스텝)
  - → Plating으로 자동 이동 (Cooker 스킵, 샐러드는 조리 안함)
- **Plating 처리 완료** (3 스텝)
  - → Sealing으로 자동 이동
- **Sealing 처리 완료** (2 스텝)
  - → VisionQA로 자동 이동
- **VisionQA 통과** (1 스텝)
  - → FinalStorage 도착

### 3. 완성
- FinalStorage.output_buffer에서 픽업
- `completed_products`에 추가
- 보상 +10점

---

## 🔑 핵심 특징

### 1. 실제 공장 시뮬레이션
- 2개 독립 생산 라인
- 제품별 다른 워크플로우 (샐러드는 Cooker 없음)
- 스테이션별 처리 시간

### 2. 물리적 특성 시뮬레이션
- 칼날 마모 (Cutter)
- 압력/온도 파라미터 (Sealing, Cooker)
- 불량 발생 메커니즘

### 3. 품질 관리
- 자동 품질 검사
- 불량품 자동 제거
- 불량률 추적

### 4. 프로토타입 자동화
- 현재는 워크플로우 자동 실행
- 향후 상위 에이전트(LLM)가 제어할 예정

---

## 📊 구성 요소 통계

| 항목 | 개수 | 설명 |
|------|------|------|
| 생산 라인 | 2 | 독립적으로 운영 |
| 스테이션 종류 | 8 | Storage, Washer, Cutter, Cooker, Plating, Sealing, VisionQA, FinalStorage |
| 스테이션 총 개수 | 16 | 각 스테이션 × 2라인 |
| 로봇팔 | 20 | 스테이션 작업 수행 |
| 물류 로봇 | 24 | 재료/제품 운반 |
| 제품 종류 | 3 | 샐러드, 볶음밥, 파스타 |

---

## 🎯 설계 목적

이 환경은 **상위 에이전트 4개**(부품 설계, 설비 관리, 로봇 협동, 품질 검사)가 LLM reasoning을 통해 제어할 플랫폼 역할을 합니다.

현재는 **프로토타입**으로 워크플로우가 자동화되어 있지만, 향후 LLM이 모든 의사결정을 실시간으로 수행하도록 확장할 예정입니다. 🏭
