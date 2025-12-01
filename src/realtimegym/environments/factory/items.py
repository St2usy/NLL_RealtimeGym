"""Item and Recipe definitions for Factory environment."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ItemType(Enum):
    """Types of items in the factory."""

    # Raw ingredients
    LETTUCE = "lettuce"  # 양상추
    ROMAINE = "romaine"  # 로메인
    SPROUTS = "sprouts"  # 새싹잎
    CHERRY_TOMATO = "cherry_tomato"  # 방울토마토
    RICOTTA = "ricotta"  # 리코타치즈
    NUTS = "nuts"  # 견과류
    BALSAMIC = "balsamic"  # 발사믹소스

    PASTA = "pasta"  # 파스타면
    TOMATO = "tomato"  # 토마토
    ONION = "onion"  # 양파
    GARLIC = "garlic"  # 마늘
    OLIVE_OIL = "olive_oil"  # 올리브오일
    SUGAR = "sugar"  # 설탕
    SALT = "salt"  # 소금

    RICE = "rice"  # 밥
    SHRIMP = "shrimp"  # 새우
    GREEN_ONION = "green_onion"  # 대파
    CARROT = "carrot"  # 당근
    ONION_FRIED = "onion_fried"  # 양파 (볶음용)
    OIL = "oil"  # 식용유
    OYSTER_SAUCE = "oyster_sauce"  # 굴소스

    # Processed items
    WASHED_VEGGIE = "washed_veggie"  # 세척된 채소
    CUT_VEGGIE = "cut_veggie"  # 절단된 채소
    COOKED_PASTA = "cooked_pasta"  # 조리된 파스타
    TOMATO_SAUCE = "tomato_sauce"  # 토마토 소스
    FRIED_RICE = "fried_rice"  # 볶음밥

    # Final products
    SALAD = "salad"  # 샐러드
    PASTA_DISH = "pasta_dish"  # 파스타 요리
    RICE_DISH = "rice_dish"  # 볶음밥 요리

    # Containers
    CONTAINER = "container"  # 용기
    SEALED_CONTAINER = "sealed_container"  # 밀봉된 용기

    # Special
    DEFECTIVE = "defective"  # 불량품


@dataclass
class Item:
    """Represents an item in the factory."""

    item_type: ItemType
    quantity: int = 1
    processed: bool = False
    quality: float = 1.0  # 0.0 ~ 1.0
    line: int = 1  # Production line (1 or 2)
    metadata: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"{self.item_type.value}(q={self.quantity}, qual={self.quality:.2f}, line={self.line})"


class RecipeType(Enum):
    """Types of recipes."""

    SALAD = "salad"  # 리코타치즈 샐러드
    PASTA = "pasta"  # 토마토 파스타
    FRIED_RICE = "fried_rice"  # 새우 볶음밥


@dataclass
class Recipe:
    """Recipe definition."""

    recipe_type: RecipeType
    ingredients: list[ItemType]
    processing_steps: list[str]  # Station names
    processing_time: dict[str, int]  # Station -> time in steps
    batch_size: int = 1  # How many can be made at once
    quality_threshold: float = 0.7  # Minimum quality to pass QA


# Recipe definitions
RECIPES: dict[RecipeType, Recipe] = {
    RecipeType.SALAD: Recipe(
        recipe_type=RecipeType.SALAD,
        ingredients=[
            ItemType.LETTUCE,
            ItemType.ROMAINE,
            ItemType.SPROUTS,
            ItemType.CHERRY_TOMATO,
            ItemType.RICOTTA,
            ItemType.NUTS,
        ],
        processing_steps=["Storage", "Washer", "Cutter", "Plating", "Sealing", "VisionQA", "Storage"],
        processing_time={
            "Washer": 10,  # 1 minute (10초 단위)
            "Cutter": 12,  # 2 minutes
            "Plating": 6,  # 1 minute
            "Sealing": 6,  # 1 minute
            "VisionQA": 3,  # 30 seconds
        },
        batch_size=10,
        quality_threshold=0.75,
    ),
    RecipeType.PASTA: Recipe(
        recipe_type=RecipeType.PASTA,
        ingredients=[
            ItemType.PASTA,
            ItemType.TOMATO,
            ItemType.ONION,
            ItemType.GARLIC,
            ItemType.OLIVE_OIL,
        ],
        processing_steps=["Storage", "Washer", "Cutter", "Cooker", "Plating", "Sealing", "VisionQA", "Storage"],
        processing_time={
            "Washer": 10,
            "Cutter": 12,
            "Cooker": 24,  # 4 minutes
            "Plating": 6,
            "Sealing": 6,
            "VisionQA": 3,
        },
        batch_size=15,
        quality_threshold=0.7,
    ),
    RecipeType.FRIED_RICE: Recipe(
        recipe_type=RecipeType.FRIED_RICE,
        ingredients=[
            ItemType.RICE,
            ItemType.SHRIMP,
            ItemType.GREEN_ONION,
            ItemType.CARROT,
            ItemType.ONION_FRIED,
            ItemType.OIL,
            ItemType.OYSTER_SAUCE,
        ],
        processing_steps=["Storage", "Washer", "Cutter", "Cooker", "Plating", "Sealing", "VisionQA", "Storage"],
        processing_time={
            "Washer": 10,
            "Cutter": 12,
            "Cooker": 30,  # 5 minutes
            "Plating": 6,
            "Sealing": 6,
            "VisionQA": 3,
        },
        batch_size=20,
        quality_threshold=0.7,
    ),
}
