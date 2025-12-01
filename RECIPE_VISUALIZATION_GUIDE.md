# Factory Recipe Visualization Guide

## 구현 완료 사항

### 1. 레시피 기반 재료 조합 시스템
- **Plating 스테이션**: 샐러드 레시피의 6가지 재료를 모아서 SALAD로 조합
- **Cooker 스테이션**: 파스타/볶음밥 레시피의 재료들을 모아서 PASTA_DISH/RICE_DISH로 조합

### 2. 시각화 개선 사항

#### simulate_factory.py 실행 시 표시되는 정보:

1. **레시피 정보**
   - 현재 생산 중인 레시피 (SALAD/PASTA/FRIED_RICE)
   - 필요한 재료 목록

2. **재료 조합 상태**
   - Plating 스테이션의 현재 재료 수
   - "Ready to combine!" - 모든 재료가 준비됨
   - "Waiting (3/6 ingredients)" - 재료 대기 중

3. **스테이션 상태**
   - 각 스테이션의 가동 상태 (Busy/Idle)
   - Input/Output 버퍼 아이템 수

## 사용 방법

### 실행
```bash
python simulate_factory.py
```

### 키보드 컨트롤
- **SPACE**: 속도 증가 (최대 32배속)
- **DOWN**: 속도 감소 (최소 1배속)
- **P**: 일시정지/재개
- **ESC**: 종료

## 작동 원리

### 샐러드 제조 과정 (SALAD Recipe)

```
1. Washer에 6가지 재료 투입:
   - LETTUCE (양상추)
   - ROMAINE (로메인)
   - SPROUTS (새싹잎)
   - CHERRY_TOMATO (방울토마토)
   - RICOTTA (리코타치즈)
   - NUTS (견과류)

2. Washer → Cutter:
   - LogisticRobot이 세척된 재료를 Cutter로 운반
   - Cutter에서 절단 처리

3. Cutter → Plating:
   - 절단된 6가지 재료가 모두 Plating으로 이동

4. Plating에서 조합:
   - 6가지 재료가 모두 모이면 자동으로 SALAD 1개 생성
   - 시각화에서 "Ready to combine!" 표시

5. Plating → Sealing → VisionQA → Storage:
   - 완성된 SALAD가 포장 및 검수를 거쳐 최종 Storage로

6. 완제품 카운트:
   - 최종 Storage에 도착하면 completed_products 증가
```

### 파스타 제조 과정 (PASTA Recipe)

```
1. Washer에 5가지 재료 투입:
   - PASTA, TOMATO, ONION, GARLIC, OLIVE_OIL

2. Washer → Cutter → Cooker:
   - 재료들이 절단 후 Cooker로 이동

3. Cooker에서 조합:
   - 5가지 재료가 모두 모이면 PASTA_DISH 1개 생성

4. Cooker → Plating → ... → Storage:
   - 완성된 요리가 최종 Storage로
```

## 주요 변경사항

### 파일: `simulate_factory.py`

#### Before (문제점)
```python
# LETTUCE 하나만 추가
item = Item(item_type=ItemType.LETTUCE, ...)
station.input_buffer.append(item)
```

#### After (수정)
```python
# 레시피의 모든 재료 추가
for ingredient in recipe.ingredients:
    item = Item(item_type=ingredient, ...)
    station.input_buffer.append(item)
```

#### 시각화 추가
```python
# 레시피 정보 표시
recipe_text = font.render(f"Recipe: {env.current_recipe.value.upper()}", ...)

# 필요 재료 목록
ingredients_text = small_font.render(
    f"Required: {', '.join([ing.value for ing in recipe.ingredients])}",
    ...
)

# Plating 조합 상태
if has_all:
    status_msg = "Ready to combine!"
else:
    status_msg = f"Waiting ({len(plating.input_buffer)}/{len(recipe.ingredients)} ingredients)"
```

## 테스트 결과

### test_recipe_combination.py 실행 결과

```
TEST 1: Plating Station - SALAD Recipe
[OK] SUCCESS: Salad was created from ingredients!
  - 6가지 재료 → SALAD 1개 생성 확인

TEST 2: Cooker Station - PASTA Recipe
[OK] SUCCESS: Pasta dish was created from ingredients!
  - 5가지 재료 → PASTA_DISH 1개 생성 확인

TEST 3: Incomplete Ingredients
[OK] SUCCESS: Did not process with incomplete ingredients!
  - 불완전한 재료는 조합하지 않음 확인
```

## 시각화에서 확인할 수 있는 것

1. **재료 이동 과정**
   - 여러 재료가 각 스테이션을 거쳐가는 모습
   - Input/Output 버퍼의 숫자 변화

2. **재료 조합 타이밍**
   - Plating의 "Waiting (3/6)" → "Waiting (6/6)" → "Ready to combine!"
   - 조합 후 SALAD가 Output 버퍼로 이동

3. **생산 진행률**
   - 진행 바로 완제품 수 확인
   - 품질률 및 불량품 수

## 알려진 제한사항

현재 Factory 환경은 아직 완전히 구현되지 않았습니다:

1. ⚠️ **로봇 동작**: LogisticRobot의 자동 운반이 완벽하지 않을 수 있음
2. ⚠️ **타이밍**: 재료들이 Plating에 동시에 도착하지 않을 수 있음
3. ⚠️ **생산 속도**: 실제 생산 완료까지 시간이 오래 걸릴 수 있음

하지만 **레시피 기반 재료 조합 로직 자체는 정상 작동**합니다! (test_recipe_combination.py로 검증)

## 다음 단계 개선 방향

1. Storage 스테이션이 자동으로 재료를 공급하도록 개선
2. LogisticRobot의 경로 최적화
3. 여러 제품을 동시에 생산할 수 있도록 병렬 처리 개선
