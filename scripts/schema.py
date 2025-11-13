from pydantic import BaseModel, Field
from typing import List, Optional


class Ingredient(BaseModel):
    name: str = Field(description="Name of the ingredient.")
    quantity: str = Field(description="Quantity of the ingredient, including units.")


class Recipe(BaseModel):
    recipe_name: str = Field(description="The name of the recipe.")
    prep_time_minutes: Optional[int] = Field(
        description="Optional time in minutes to prepare the recipe."
    )
    ingredients: List[Ingredient]
    instructions: List[str]
