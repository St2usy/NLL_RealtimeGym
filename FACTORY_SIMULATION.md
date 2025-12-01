# Factory Environment 시각화 가이드

## 시뮬레이션 실행 방법

```bash
python simulate_factory.py
```

## 화면 설명

### 메인 뷰 (그리드)
- **16×30 그리드**: 공장 레이아웃
- **스테이션 셀**: 색상으로 상태 표시
  - 흰색: Idle (대기 중)
  - 연한 초록색: Busy (작업 중)
  - 연한 노란색: Waiting (자재 대기)
  - 연한 빨간색: Error (오류)
  - 회색: Down (고장)

- **진행 바**: 작업 중인 스테이션 하단에 초록색 진행 바 표시
- **로봇**: 스테이션 위의 작은 원형/사각형
  - 파란색 원: 대기 중인 RobotArm
  - 주황색 원: 작업 중인 RobotArm
  - 초록색 사각형: 빈 LogisticRobot
  - 노란색 사각형: 아이템을 운반 중인 LogisticRobot

### 정보 패널 (하단)
- **진행 상황 바**: 전체 생산 진행도
- **품질 정보**: 품질률, 불량품 수, 시뮬레이션 속도
- **스테이션 상태**: 각 스테이션 타입별 작업 현황
  - busy 카운트: 작업 중인 스테이션 수
  - In: 입력 버퍼의 아이템 수
  - Out: 출력 버퍼의 아이템 수

## 조작 방법

| 키 | 기능 |
|---|---|
| **SPACE** | 시뮬레이션 속도 증가 (1x → 2x → 4x → 8x → 16x → 32x) |
| **DOWN** | 시뮬레이션 속도 감소 |
| **P** | 일시정지 / 재개 |
| **ESC** | 시뮬레이션 종료 |

## 생산 과정 (Salad Recipe)

```
[Storage] → [Washer] → [Cutter] → [Plating] → [Sealing] → [VisionQA] → [Storage]
   ↓           10초       12초        6초        6초         3초          ↓
원자재                                                                  완제품
(상추)                                                                  (샐러드)
```

## 자동 생산 로직

시뮬레이션은 완전 자동으로 작동합니다:

1. **자재 투입**: 5스텝마다 Washer에 상추 투입
2. **스테이션 처리**: 각 스테이션이 자동으로 아이템 처리
3. **자동 운반**: 스테이션 간 아이템 자동 이동
4. **품질 검사**: VisionQA에서 품질 70% 미만은 불량품 처리
5. **완제품 수집**: 최종 Storage에 도달한 제품 카운트

## 성능 지표 (KPI)

- **생산량**: 완성된 제품 수 / 목표 제품 수
- **품질률**: (완성품 / (완성품 + 불량품)) × 100%
- **최종 보상**:
  - 완성품 1개당: +10점
  - 품질률: +100점 (최대)
  - 스테이션 고장: -5점/회

## 난이도별 목표

- **Easy (v0)**: 10개 제품 생산
- **Medium (v1)**: 25개 제품 생산
- **Hard (v2)**: 50개 제품 생산

## 커스터마이징

`simulate_factory.py`를 수정하여:

- 생산 속도 조절: `start_production_batch()` 호출 빈도 변경
- 다른 레시피 사용: ItemType 변경
- 시각화 속도: `clock.tick(30)` 값 조절 (FPS)
- 초기 속도: `speed = 1` 값 변경

## 예제 출력

```
Creating Factory environment...
Environment initialized. Target: 10 products

Starting simulation...
Press SPACE to speed up, ESC to quit

Product completed! Total: 1/10
Product completed! Total: 2/10
Product completed! Total: 3/10
...

==================================================
SIMULATION COMPLETE
==================================================
Total Steps: 1000
Completed Products: 10/10
Defective Products: 1
Quality Rate: 90.9%
Final Reward: 190.91
==================================================
```

## 문제 해결

### pygame 창이 열리지 않는 경우
```bash
pip install pygame
```

### 시뮬레이션이 너무 느린 경우
- SPACE 키를 눌러 속도 증가
- 또는 코드에서 `speed = 8` 등으로 초기 속도 설정

### 제품이 생산되지 않는 경우
- 콘솔 출력 확인: "Added lettuce to Washer" 메시지 확인
- 스테이션 상태 확인: 하단 패널에서 In/Out 버퍼 확인
