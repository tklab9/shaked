from typing import Optional
from app.lib.dto.base_dto import Base


class RecipeDTO(Base):
    id: int
    name: str
    sub_id: int = 0
    difficulty_level: int
    kosher_type: int
    preparation_time: int
    preparation_method: str
    main_picture_url: str
    nutrifox_recipe_id: int
    create_at: int
    status: int
    sub_title: Optional[str] = None
    portion_num: Optional[int] = None
    nut_recommend: Optional[str] = None
    comment: Optional[str] = None
    main_picture: Optional[str] = None
    secondary_picture: Optional[str] = None
    nutrition_picture: Optional[str] = None
    calories_val: Optional[float] = None
    sodium_val: Optional[float] = None
    fat_val: Optional[float] = None
    protein_val: Optional[float] = None
    carbs_val: Optional[float] = None
    fiber_val: Optional[float] = None
    original_recipe: Optional[str] = None
    referral_id: Optional[int] = None
    clients_only: int = 0
    shopping_list_raw: Optional[str] = None
    hebrew_list: Optional[str] = None
    list_english: Optional[str] = None
    vegan: Optional[str] = None
    vegetarian: Optional[str] = None
    low_carb: Optional[str] = None
    high_protein: Optional[str] = None
    meal_type: Optional[str] = None
    dish_type: Optional[str] = None
    shopping_list_final: Optional[str] = None
    shopping_list_final_json: Optional[list[dict]] = None

    def __repr__(self):
        return (
            f"RecipeDTO(id={self.id}, name={self.name!r},"
            f"vegan={self.vegan}, vegetarian={self.vegetarian},"
            f"high_protein={self.high_protein}, low_carb={self.low_carb}"
            f"dish_type={self.dish_type}, meal_type={self.meal_type}"
        )