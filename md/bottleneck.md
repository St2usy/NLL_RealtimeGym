현재 SALAD 레시피 기준으로 생산 라인을 분석한 결과입니다.

� 현재 생산 라인 구조 (각 라인)

Storage → Washer(×1) → Cutter(×2) → Plating(×1) → Sealing(×1) → VisionQA(×1) → Storage
(즉시) 10 steps 12 steps 6 steps 6 steps 3 steps (즉시)

� 주요 병목 지점

1. Washer - 최대 병목 (10 steps, 단일 스테이션)

문제:

- 생산 라인의 입구 지점이면서 단일 스테이션
- 처리 시간: 10 steps/item
- 처리 용량: 6 items/minute (60 steps 기준)
- 모든 아이템이 여기를 거쳐야 함

영향:

- 2개 라인 × 1 Washer = 총 2개만 있어 전체 throughput 제한
- 최대 생산 속도: 12 items/minute (2 라인 합계)

2. Plating - 재료 수집 병목 (6개 재료 필요)

문제:

- SALAD 레시피는 6개 재료 필요:
  LETTUCE, ROMAINE, SPROUTS, CHERRY_TOMATO, RICOTTA, NUTS
- 각 재료가 별도로 Washer → Cutter를 거쳐 도착
- 6개 모두 모일 때까지 처리 시작 불가 (동기화 지연)
- 로봇이 한 번에 1개씩만 운반 → 6번의 물류 이동 필요

영향:
시간 분석:

- Washer: 10 steps × 6개 재료 = 60 steps (순차 처리)
- Cutter: 12 steps × 6개 재료 / 2개 병렬 = 36 steps
- 물류 이동: ~6-10 steps (거리에 따라)
- Plating 대기: 마지막 재료 도착까지 대기
  → 총 약 106+ steps per SALAD (이론적 최소값)

3. 물류 로봇 - 세그먼트별 불균등

문제:

- 총 24개 로봇 (라인당 12개)
  - 2개는 reserve (비활성)
  - 실제 작동: 라인당 10개
- 세그먼트 기반 할당:
  Washer→Cutter: ~4 robots
  Cutter→Plating: ~2 robots ← 병목!
  Plating→Sealing: ~2 robots
  Sealing→VisionQA: ~2 robots
  VisionQA→Storage: ~2 robots
- Cutter→Plating 구간이 가장 많은 물량 (6개 재료)

영향:

- Cutter→Plating 로봇이 부족하여 재료 운반 지연
- 로봇 이동 속도: 1 cell/step
- 평균 거리: ~5 cells → 5 steps × 왕복 = 10 steps overhead

4. Cutter - 상대적으로 양호

처리 시간: 12 steps/item
병렬도: 2개
Effective throughput: 6 steps/item = 10 items/minute

→ Washer보다 빠르므로 병목 아님

� 전체 생산 성능 분석

이론적 최대 throughput (2 라인 합계):
병목: Washer (10 steps/item × 2개 = 20 steps for 2 items)
최대 속도: 1000 steps / (10 steps/item) × 2 lines = 200 items

실제 성능 (SALAD 레시피):
1 SALAD = 6개 재료

- Washer bottleneck: 60 steps (6재료 × 10 steps)
- 물류 지연: ~20 steps
- 동기화 지연: ~10 steps
  → 약 90-110 steps per SALAD

1000 steps로 약 9-11 SALADs 생성 가능 (라인당)
→ 2 라인 합계: 18-22 SALADs

목표 (난이도별):

- Easy (v0): 10 SALADs ✓ 달성 가능
- Medium (v1): 25 SALADs ✗ 어려움
- Hard (v2): 50 SALADs ✗ 불가능

� 개선 방안

1. Washer 병렬화 (High Impact)

# 현재: 각 라인당 Washer 1개

# 제안: 각 라인당 Washer 2개

line1_stations.append(Washer(..., position=(3, 2), line=1))
line1_stations.append(Washer(..., position=(3, 4), line=1))

효과:

- Throughput 2배 증가: 12 → 24 items/minute
- SALAD 생산 시간: 90 steps → 45-55 steps
- Medium (25개) 목표 달성 가능

2. 재료 Batching 시스템 (Medium Impact)

현재 문제:

- 재료가 하나씩 순차적으로 도착
- Plating이 6개 모두 기다림

개선안:

# Cutter 이후에 "Preparation" 스테이션 추가

class Preparation(Station):
"""재료 사전 준비 스테이션"""
def process(self) -> None: # 6개 재료를 batch로 묶어서 output
if len(self.input_buffer) >= 6:
batch = self.input_buffer[:6]
combined = Item(
item_type=ItemType.SALAD_INGREDIENTS,
ingredients=batch
)
self.output_buffer.append(combined)

효과:

- Plating 대기 시간 제거
- 물류 로봇 효율성 향상 (1번 이동 vs 6번 이동)

3. 동적 로봇 재할당 (Low Impact, High Effort)

현재: 세그먼트 고정 할당
개선: 작업량에 따라 동적 할당

def \_rebalance_robots(self):
"""병목 구간에 로봇 추가 할당""" # Cutter→Plating 구간 혼잡도 체크
if cutter_output_count > threshold: # Reserve robot 활성화
for robot in self.logistic_robots:
if not robot.is_active and robot.line == 1:
robot.is_active = True
robot.assigned_segment = ("Cutter", "Plating")
break

효과:

- Cutter→Plating 구간 물류 속도 20-30% 향상

4. 버퍼 크기 최적화 (Low Impact)

현재: 대부분 10개
제안:

# Washer output buffer 증가 (재료 대기)

washer.buffer_capacity = 20

# Cutter output buffer 증가

cutter.buffer_capacity = 15

# Plating input buffer는 이미 10개 (충분)

효과:

- 버퍼 오버플로우로 인한 대기 감소
- 생산 흐름 안정성 향상

5. 병렬 생산 라인 간 밸런싱 (Medium Impact)

현재: 각 라인 독립적으로 작동
개선: 재료 공유 풀

# Line 1의 Washer가 idle이면 Line 2의 재료도 처리

def \_cross_line_balancing(self):
for line1_station in line1_washers:
if line1_station.status == IDLE and line1_station.can_accept_input(): # Line 2에서 대기 중인 재료 가져오기
for line2_storage in line2_storages:
if line2_storage.can_provide_output():
item = line2_storage.take_output()
line1_station.add_input(item)

효과:

- 유휴 시간 감소
- 전체 utilization 15-20% 향상

� 우선순위별 실행 계획

| 우선순위 | 개선 사항           | 구현 난이도 | 예상 효과           | 목표 달성   |
| -------- | ------------------- | ----------- | ------------------- | ----------- |
| 1        | Washer 병렬화 (2개) | 낮음        | +100% throughput    | Medium 달성 |
| 2        | 재료 Batching       | 중간        | -40% 물류 시간      | Hard 접근   |
| 3        | 동적 로봇 재할당    | 높음        | +20-30% 효율        | 안정성 향상 |
| 4        | 버퍼 크기 최적화    | 낮음        | +5-10% 안정성       | -           |
| 5        | 라인 간 밸런싱      | 중간        | +15-20% utilization | -           |

� 결론

현재 최대 병목: Washer (단일 스테이션, 10 steps)

가장 효과적인 해결책:

1. Washer를 2개로 증가 → Medium 난이도 달성 가능
2. 재료 Batching 시스템 → Hard 난이도 접근 가능
