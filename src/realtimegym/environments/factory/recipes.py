"""Product recipes and workflow definitions for the factory environment."""

from dataclasses import dataclass


@dataclass
class Recipe:
    """Product recipe definition."""

    name: str
    ingredients: list[str]
    workflow: list[str]  # Station names in order
    processing_times: dict[str, int]  # Station name -> processing time in steps


# Define the three products
RICOTTA_SALAD = Recipe(
    name="Ricotta Salad",
    ingredients=[
        "lettuce",
        "romaine",
        "sprouts",
        "cherry_tomato",
        "ricotta_cheese",
        "nuts",
        "balsamic_sauce",
    ],
    workflow=["Storage", "Washer", "Cutter", "Plating", "Sealing", "VisionQA", "FinalStorage"],
    processing_times={
        "Storage": 1,
        "Washer": 2,  # 1-2 steps (10-20 sec)
        "Cutter": 2,
        "Plating": 3,
        "Sealing": 2,
        "VisionQA": 1,
        "FinalStorage": 1,
    },
)

SHRIMP_FRIED_RICE = Recipe(
    name="Shrimp Fried Rice",
    ingredients=["rice", "shrimp", "green_onion", "carrot", "onion", "cooking_oil", "oyster_sauce"],
    workflow=["Storage", "Washer", "Cutter", "Cooker", "Plating", "Sealing", "VisionQA", "FinalStorage"],
    processing_times={
        "Storage": 1,
        "Washer": 2,
        "Cutter": 2,
        "Cooker": 5,  # Longer cooking time
        "Plating": 3,
        "Sealing": 2,
        "VisionQA": 1,
        "FinalStorage": 1,
    },
)

TOMATO_PASTA = Recipe(
    name="Tomato Pasta",
    ingredients=[
        "pasta",
        "tomato",
        "onion",
        "garlic",
        "olive_oil",
        "sugar",
        "salt",
        "tomato_sauce",
    ],
    workflow=["Storage", "Washer", "Cutter", "Cooker", "Plating", "Sealing", "VisionQA", "FinalStorage"],
    processing_times={
        "Storage": 1,
        "Washer": 2,
        "Cutter": 2,
        "Cooker": 6,  # Boiling pasta + sauce
        "Plating": 3,
        "Sealing": 2,
        "VisionQA": 1,
        "FinalStorage": 1,
    },
)

# All recipes
RECIPES = {
    "ricotta_salad": RICOTTA_SALAD,
    "shrimp_fried_rice": SHRIMP_FRIED_RICE,
    "tomato_pasta": TOMATO_PASTA,
}
