# Factory Environment

무인 식품 공장 시뮬레이션 환경

## 개요

이 환경은 PDF 설계 문서(`public/env_specification.pdf`)를 기반으로 한 무인 공장 프로토타입입니다.

### 환경 사양

- **그리드 크기**: 16 × 30
- **생산 라인**: 2개
- **제품 종류**: 3개 (리코타치즈 샐러드, 새우 볶음밥, 토마토 파스타)
- **로봇 에이전트**: 44개
  - 로봇팔 20개 (각 스테이션에 배치)
  - 물류 로봇 24개 (재료 운반)

### 공정 단계

각 제품은 다음 단계를 거쳐 생산됩니다:

1. **Storage**: 원재료 입고
2. **Washer**: 세척 (1-2분)
3. **Cutter**: 절단/슬라이싱
4. **Cooker**: 조리/배합 (제품에 따라 다름)
5. **Plating**: 조립/플레이팅
6. **Sealing**: 밀봉/포장
7. **VisionQA**: 품질 검사
8. **FinalStorage**: 완제품 저장

## 사용 방법

### 기본 사용

```python
import realtimegym

# 환경 생성
env, seed, renderer = realtimegym.make("Factory-v0", seed=0)

# 환경 초기화
obs, done = env.reset()

# 제품 생산 명령
obs, done, reward, reset = env.step("produce_ricotta_salad")
obs, done, reward, reset = env.step("produce_shrimp_fried_rice")
obs, done, reward, reset = env.step("produce_tomato_pasta")

# 시뮬레이션 실행
for i in range(100):
    obs, done, reward, reset = env.step("continue")
    if reward > 0:
        print(f"Step {i}: Reward = {reward}")
```

### 사용 가능한 액션

- `produce_ricotta_salad`: 리코타치즈 샐러드 생산 시작
- `produce_shrimp_fried_rice`: 새우 볶음밥 생산 시작
- `produce_tomato_pasta`: 토마토 파스타 생산 시작
- `maintain_cutter_0`: 라인 0의 Cutter 유지보수
- `maintain_cutter_1`: 라인 1의 Cutter 유지보수
- `continue`: 현재 작업 계속

### KPI 지표

환경은 다음 KPI를 추적합니다:

```python
state = env.state_builder()
kpis = state['kpis']

# 사용 가능한 KPI
print(kpis['production'])          # 총 생산량
print(kpis['in_progress'])         # 진행 중인 제품 수
print(kpis['rejected'])            # 불량품 수
print(kpis['avg_lead_time'])       # 평균 리드 타임
print(kpis['station_idle_ratio'])  # 스테이션 유휴 비율
print(kpis['robot_idle_ratio'])    # 로봇 유휴 비율
print(kpis['defect_rate'])         # 불량률
```

## 구조

### Station 클래스

- `Storage`: 입고/출고 창고
- `Washer`: 세척 스테이션
- `Cutter`: 절단 스테이션 (칼날 마모도 시뮬레이션)
- `Cooker`: 조리 스테이션 (배치 크기, 온도 파라미터)
- `Plating`: 플레이팅 스테이션
- `Sealing`: 밀봉 스테이션 (압력 파라미터, 불량 발생 가능)
- `VisionQA`: 품질 검사 스테이션 (불량품 자동 제거)

### Agent 클래스

- `RobotArm`: 각 스테이션에 배치되어 공정 작업 수행
- `LogisticsRobot`: 스테이션 간 재료/제품 운반

## 난이도 레벨

- **v0 (Easy)**: 기본 난이도
- **v1 (Medium)**: 중간 난이도
- **v2 (Hard)**: 높은 난이도

## 프로토타입 제약사항

현재 버전은 **프로토타입**으로, 다음 기능이 자동화되어 있습니다:

1. **워크플로우 자동화**: 제품이 자동으로 스테이션 간 이동
2. **로봇 제어**: 로봇 에이전트는 현재 idle 상태

실제 운용 시에는 상위 에이전트(부품 설계, 설비 관리, 로봇 협동, 품질 검사)가 이러한 기능을 제어하게 됩니다.

## 파일 구조

```
factory/
├── __init__.py          # 환경 등록 및 setup_env 함수
├── factory_env.py       # 메인 환경 클래스
├── stations.py          # 스테이션 클래스들
├── agents.py            # 로봇 에이전트 클래스들
├── recipes.py           # 제품 레시피 정의
└── README.md            # 이 파일
```

## 향후 개발 계획

1. 상위 에이전트 통합 (부품 설계, 설비 관리, 로봇 협동, 품질 검사)
2. 로봇 경로 계획 및 충돌 회피
3. 실시간 스케줄링 최적화
4. 렌더링 시스템 (공장 시각화)
5. 더 복잡한 시나리오 (긴급 주문, 설비 고장 등)
