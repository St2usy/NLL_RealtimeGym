# Factory Recipe System - 구현 요약

## 📋 완료된 작업

### 1. **Plating 스테이션 - 재료 조합 로직**
- ✅ 레시피에 정의된 모든 재료가 input_buffer에 있는지 확인
- ✅ 재료가 모두 있으면 소비하고 완제품 1개 생성
- ✅ 재료가 부족하면 대기 (처리하지 않음)

**구현 위치**: `src/realtimegym/environments/factory/stations.py`

```python
class Plating(Station):
    def _has_required_ingredients(self, required_ingredients):
        """모든 재료가 있는지 확인"""

    def _consume_ingredients(self, required_ingredients):
        """재료를 소비하고 반환"""

    def _complete_processing(self):
        """재료가 모두 있으면 SALAD/PASTA_DISH/RICE_DISH 생성"""
```

### 2. **Cooker 스테이션 - 재료 조리 로직**
- ✅ 동일한 재료 확인 및 소비 로직
- ✅ 온도 기반 품질 계산
- ✅ 레시피에 따라 PASTA_DISH 또는 RICE_DISH 생성

**구현 위치**: `src/realtimegym/environments/factory/stations.py`

```python
class Cooker(Station):
    def _has_required_ingredients(self, required_ingredients):
        """모든 재료가 있는지 확인"""

    def _consume_ingredients(self, required_ingredients):
        """재료를 소비하고 반환"""

    def _complete_processing(self):
        """재료가 모두 있으면 요리 생성"""
```

### 3. **레시피 자동 할당**
- ✅ Factory 환경 reset() 시 현재 레시피를 Cooker/Plating에 자동 전달
- ✅ Station.current_recipe 필드 추가

**구현 위치**: `src/realtimegym/environments/factory/__init__.py`

```python
def reset(self):
    # ...
    # Set recipe for stations that need it
    recipe = RECIPES[self.current_recipe]
    for station in self.stations:
        if station.station_type in [StationType.COOKER, StationType.PLATING]:
            station.current_recipe = recipe
```

### 4. **시각화 개선 (simulate_factory.py)**
- ✅ 레시피의 모든 재료를 Washer에 투입
- ✅ 현재 레시피 정보 표시
- ✅ 필요한 재료 목록 표시
- ✅ Plating 스테이션의 재료 조합 상태 실시간 표시

**주요 변경사항**:
```python
# Before: LETTUCE 하나만
item = Item(item_type=ItemType.LETTUCE, ...)

# After: 레시피의 모든 재료
for ingredient in recipe.ingredients:
    item = Item(item_type=ingredient, ...)
```

## 🧪 테스트 검증

### test_recipe_combination.py 결과

```
✅ TEST 1: Plating - SALAD 생성
   - 6가지 재료 → SALAD 1개
   - 품질: 1.00

✅ TEST 2: Cooker - PASTA_DISH 생성
   - 5가지 재료 → PASTA_DISH 1개
   - 품질: 1.00

✅ TEST 3: 불완전한 재료 처리
   - 3가지만 있으면 조합하지 않음
   - Input buffer에 그대로 유지
```

## 📊 레시피 정의

### SALAD (샐러드)
**필요 재료 (6가지)**:
- LETTUCE (양상추)
- ROMAINE (로메인)
- SPROUTS (새싹잎)
- CHERRY_TOMATO (방울토마토)
- RICOTTA (리코타치즈)
- NUTS (견과류)

**처리 경로**: Storage → Washer → Cutter → **Plating** → Sealing → VisionQA → Storage

### PASTA (토마토 파스타)
**필요 재료 (5가지)**:
- PASTA (파스타면)
- TOMATO (토마토)
- ONION (양파)
- GARLIC (마늘)
- OLIVE_OIL (올리브오일)

**처리 경로**: Storage → Washer → Cutter → **Cooker** → Plating → Sealing → VisionQA → Storage

### FRIED_RICE (새우 볶음밥)
**필요 재료 (7가지)**:
- RICE (밥)
- SHRIMP (새우)
- GREEN_ONION (대파)
- CARROT (당근)
- ONION_FRIED (양파)
- OIL (식용유)
- OYSTER_SAUCE (굴소스)

**처리 경로**: Storage → Washer → Cutter → **Cooker** → Plating → Sealing → VisionQA → Storage

## 🎮 실행 방법

### 1. 테스트 스크립트 실행
```bash
python test_recipe_combination.py
```

### 2. 시각화 시뮬레이션 실행
```bash
python simulate_factory.py
```

**키보드 컨트롤**:
- SPACE: 속도 증가
- DOWN: 속도 감소
- P: 일시정지
- ESC: 종료

## 📁 수정된 파일

1. **stations.py** (+130 lines)
   - Plating 클래스 재료 조합 로직
   - Cooker 클래스 재료 조합 로직
   - Station 베이스 클래스에 current_recipe 필드

2. **factory/__init__.py** (+5 lines)
   - reset() 메서드에서 레시피 자동 할당

3. **simulate_factory.py** (~50 lines modified)
   - start_production_batch() 재작성
   - 레시피 정보 시각화 추가
   - Plating 조합 상태 실시간 표시

4. **test_recipe_combination.py** (새 파일)
   - 재료 조합 로직 검증 테스트

## 🔍 작동 원리

```
┌─────────────────────────────────────────────────────┐
│ Factory Environment (SALAD Recipe)                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Washer Input Buffer]                             │
│   - LETTUCE      ✓                                 │
│   - ROMAINE      ✓                                 │
│   - SPROUTS      ✓                                 │
│   - CHERRY_TOMATO ✓                                │
│   - RICOTTA      ✓                                 │
│   - NUTS         ✓                                 │
│                                                     │
│          ↓ (Washer 처리)                            │
│          ↓ (LogisticRobot 운반)                     │
│          ↓                                          │
│                                                     │
│  [Cutter] → 절단 처리                               │
│          ↓ (LogisticRobot 운반)                     │
│          ↓                                          │
│                                                     │
│  [Plating Input Buffer]                            │
│   - LETTUCE (cut) ✓                                │
│   - ROMAINE (cut) ✓                                │
│   - SPROUTS (cut) ✓                                │
│   - CHERRY_TOMATO (cut) ✓                          │
│   - RICOTTA (cut) ✓                                │
│   - NUTS (cut) ✓                                   │
│                                                     │
│   ✅ All ingredients ready!                         │
│   🔄 Combining into SALAD...                        │
│                                                     │
│  [Plating Output Buffer]                           │
│   - SALAD ★                                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## ⚙️ 기술적 세부사항

### 재료 확인 알고리즘
```python
def _has_required_ingredients(self, required: list[ItemType]) -> bool:
    available = [item.item_type for item in self.input_buffer]
    for ingredient in required:
        if ingredient not in available:
            return False  # 하나라도 없으면 False
    return True  # 모두 있으면 True
```

### 재료 소비 알고리즘
```python
def _consume_ingredients(self, required: list[ItemType]) -> list[Item]:
    consumed = []
    for ingredient in required:
        for i, item in enumerate(self.input_buffer):
            if item.item_type == ingredient:
                consumed.append(self.input_buffer.pop(i))
                break  # 각 재료는 1개만 소비
    return consumed
```

### 품질 계산
```python
# 모든 재료의 평균 품질
avg_quality = sum(item.quality for item in ingredients) / len(ingredients)

# Plating: vibration 영향
avg_quality *= (1.0 - self.vibration_level * 0.15)

# Cooker: temperature 영향
temp_factor = 1.0 - abs(self.temperature - self.optimal_temp) / 100.0
avg_quality *= temp_factor
```

## 🎯 시각화에서 확인 가능한 것

1. **레시피 정보**
   - "Recipe: SALAD"
   - "Required: lettuce, romaine, sprouts, cherry_tomato, ricotta, nuts"

2. **재료 조합 상태**
   - "Waiting (3/6 ingredients)" - 재료 수집 중
   - "Ready to combine!" - 조합 준비 완료

3. **스테이션 가동 상태**
   - Washer: 2/2 busy | In:12 Out:0
   - Plating: 1/2 busy | In:6 Out:1

4. **생산 진행**
   - 진행 바: 3/10 (30%)
   - 품질률: 100%
   - 불량품: 0

## 📝 참고사항

- 레시피 정의는 `src/realtimegym/environments/factory/items.py`의 `RECIPES` 딕셔너리에 있습니다
- 각 레시피는 `Recipe` 클래스로 정의되어 있으며 ingredients, processing_steps, processing_time 등을 포함합니다
- Cooker는 PASTA와 FRIED_RICE만 처리 (둘 다 요리가 필요)
- Plating은 SALAD 처리 (요리 없이 조합만)
