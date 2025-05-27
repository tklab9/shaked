import random
from collections import Counter
from typing import List, Dict, Optional
from collections import defaultdict
from difflib import SequenceMatcher
from app.api.dtos.recipes_dtos import RecipeDTO
from app.config.logger_settings import get_logger
from app.api.dtos.personal_food_menu_dtos import CreatePersonalFoodMenuDTO

logger = get_logger(__name__)


class PreparingDishes:
    CATEGORY_LIMITS = {
        "Starters": 7,
        "Main Dishes": 7,
        "Salads & Sides": 5,
        "Desserts & Snacks": 4,
        "Soups & Bowls": 4
    }
    CATEGORY_IMAGES = {
        "Starters": "🥘",
        "Main Dishes": "🍲",
        "Salads & Sides": "🥗",
        "Desserts & Snacks": "🍰",
        "Soups & Bowls": "🥣"
    }

    CATEGORY_PRIORITY = ["Main Dishes", "Starters", "Salads & Sides", "Soups & Bowls", "Desserts & Snacks"]
    CATEGORY_ANSWER_ORDER = ["Starters", "Salads & Sides", "Main Dishes", "Soups & Bowls", "Desserts & Snacks"]
    DESSERT_LIMIT = 5
    SIMILARITY_THRESHOLD = 0.7

    @classmethod
    def is_high_protein(cls, recipe: RecipeDTO) -> bool:
        return recipe.high_protein and recipe.high_protein.lower() in ["yes", "true"]

    @classmethod
    def is_low_carb(cls, recipe: RecipeDTO) -> bool:
        return recipe.low_carb and recipe.low_carb.lower() in ["yes", "true"]

    @classmethod
    def categorize_recipe(cls, recipe: RecipeDTO) -> Optional[str]:
        if recipe.dish_type in cls.CATEGORY_LIMITS:
            return recipe.dish_type
        return None

    @classmethod
    def compute_similarity(cls, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    @classmethod
    def remove_similar_dishes(cls, menu: Dict[str, List[RecipeDTO]], threshold: float = None):
        if threshold is None:
            threshold = cls.SIMILARITY_THRESHOLD

        for category, recipes in menu.items():
            unique_recipes = []
            for recipe in recipes:
                is_duplicate = any(cls.compute_similarity(recipe.name, r.name) >= threshold for r in unique_recipes)
                if not is_duplicate:
                    unique_recipes.append(recipe)
            menu[category] = unique_recipes

    @classmethod
    async def generate_menu(cls, recipes: List[RecipeDTO]) -> Dict[str, List[RecipeDTO]]:
        menu = defaultdict(list)
        used_ids = set()

        # Step 2: Add Low-Carb
        for category in cls.CATEGORY_LIMITS:
            low_carb_candidates = [r for r in recipes if cls.is_low_carb(r) and cls.categorize_recipe(r) == category and r.id not in used_ids]
            logger.info(f"Low-carb candidates for {category}, count: {len(low_carb_candidates)}, - {[p.id for p in low_carb_candidates]}")
            if low_carb_candidates:
                selected = random.choice(low_carb_candidates)
                menu[category].append(selected)
                used_ids.add(selected.id)

        # Step 3: Add High-Protein
        for category in cls.CATEGORY_LIMITS:
            needed = cls.CATEGORY_LIMITS[category] - len(menu[category])
            high_protein_candidates = [r for r in recipes if cls.is_high_protein(r) and cls.categorize_recipe(r) == category and r.id not in used_ids]
            logger.info(f"High-protein candidates for {category}, count: {len(high_protein_candidates)}, needed: {needed}, - {[p.id for p in high_protein_candidates]}")
            selected = random.sample(high_protein_candidates, min(needed, len(high_protein_candidates)))
            menu[category].extend(selected)
            used_ids.update(r.id for r in selected)

        # Step 4: Fill with other recipes
        for category in cls.CATEGORY_LIMITS:
            needed = cls.CATEGORY_LIMITS[category] - len(menu[category])
            other_candidates = [r for r in recipes if cls.categorize_recipe(r) == category and r.id not in used_ids]
            logger.info(f"Other candidates for {category}, count: {len(other_candidates)}, needed: {needed}, - {[p.id for p in other_candidates]}")
            selected = random.sample(other_candidates, min(needed, len(other_candidates)))
            menu[category].extend(selected)
            used_ids.update(r.id for r in selected)

        # Step 5 & 6: Enforce limits and prioritize
        for category in cls.CATEGORY_LIMITS:
            menu[category] = menu[category][:cls.CATEGORY_LIMITS[category]]
        
        if len(menu.get("Desserts & Snacks", [])) > cls.DESSERT_LIMIT:
            menu["Desserts & Snacks"] = menu["Desserts & Snacks"][:cls.DESSERT_LIMIT]

        logger.info(f"Menu after enforcing limits: {menu}")
        # Step 7: Remove Similar Dishes
        cls.remove_similar_dishes(menu)
        # Recalculate used_ids based on cleaned menu
        used_ids = {r.id for recipes in menu.values() for r in recipes}
        logger.info(f"Menu after removing similar dishes: {menu}")

        # Step 8: Ensure 27 dishes
        total_dishes = sum(len(v) for v in menu.values())
        if total_dishes < 27:
            deficit = 27 - total_dishes
            flat_list = [r for r in recipes if r.id not in used_ids]

            for category in cls.CATEGORY_PRIORITY:
                if category == "Desserts & Snacks":
                    current_count = len(menu[category])
                    if current_count >= cls.DESSERT_LIMIT:
                        continue
                    candidates = [r for r in flat_list if cls.categorize_recipe(r) == category]
                    max_to_add = min(deficit, cls.DESSERT_LIMIT - current_count, len(candidates))
                else:
                    candidates = [r for r in flat_list if cls.categorize_recipe(r) == category]
                    max_to_add = min(deficit, len(candidates))

                if not candidates or max_to_add <= 0:
                    continue

                selected = random.sample(candidates, max_to_add)
                menu[category].extend(selected)
                used_ids.update(r.id for r in selected)
                deficit -= len(selected)

                if deficit <= 0:
                    break

        logger.debug(f"Menu after ensuring 27 dishes: {menu}")
        return menu
    
    @classmethod
    async def format_menu_text(cls, menu: Dict[str, List[RecipeDTO]]) -> str:
        LTR_MARK = "\u200E"
        lines = ["🍽️ *Here’s your personal food menu:*", ""]
        index = 1

        for category in cls.CATEGORY_ANSWER_ORDER:
            category_icon = cls.CATEGORY_IMAGES.get(category, "")
            lines.append(f"*{category}* {category_icon}")
            recipes = menu.get(category, [])
            if not recipes:
                lines.append(f"_{category} - didn't find any dishes based on your forbidden foods_")
            else:
                for recipe in recipes:
                    lines.append(f"{LTR_MARK}{index}. {recipe.name} {category_icon}")
                    index += 1
            lines.append("")

        return "\n".join(lines)

    @classmethod
    async def prepare_message_with_shopping_list(cls, shopping_list_result: List[tuple[int, RecipeDTO]], divide_messages: bool = False) -> tuple[str]:
        RTL_MARK = "\u200F"
        message_header = "*🛒 Your combined shopping list:*\n"
        combined_list = ""

        # Dictionary for combined ingredients
        aggregated_ingredients = {}

        for index, recipe in shopping_list_result:
            # Get the shopping list, which is a list of dictionaries
            shopping_list = recipe.shopping_list_final_json

            # Log the shopping list format
            logger.info(f"Shopping list for recipe {recipe.name}: type {type(shopping_list)}, data: {shopping_list}")

            # Iterate through each item in the shopping list
            for item in shopping_list:
                name = item["name"]
                quantity = item["quantity"]
                unit = item["unit"]
                
                # If ingredient already exists in the dictionary, update it
                if name in aggregated_ingredients:
                    logger.info(f"Ingredient {name} already exists in the dictionary")
                    aggregated_ingredients[name]["quantity"] += quantity
                    # Update the unit of measurement if necessary
                    aggregated_ingredients[name]["units"].append(unit)
                else:
                    # If ingredient is new, add it to the dictionary
                    aggregated_ingredients[name] = {
                        "quantity": quantity,
                        "units": [unit]
                    }
        LTR_MARK = "\u200E"
        # Now we collect the list with the combined ingredients and the most common unit of measurement
        for name, data in aggregated_ingredients.items():
            quantity = data["quantity"]
            units = data["units"]

            # Find the most common unit of measurement
            most_common_unit = Counter(units).most_common(1)[0][0]
            combined_list += f"{LTR_MARK}{name}: {LTR_MARK}{quantity} - {LTR_MARK}{most_common_unit}\n"

        # Form the final message
        final_message = message_header + combined_list.strip()
        logger.info(f"Shopping list message:\n{final_message}")
        # return final_message

        # If dividing messages is needed
        if divide_messages:
            # Split the combined list by lines (each ingredient is on its own line)
            lines = combined_list.strip().split('\n')

            # Determine the number of parts based on the length of lines
            num_lines = len(lines)
            if num_lines <= 10:
                return (final_message,)  # No need to divide
            elif num_lines <= 20:
                # Divide into 2 parts
                part1 = "\n".join(lines[:num_lines // 2])
                part2 = "\n".join(lines[num_lines // 2:])
                return (message_header + part1, message_header + part2)
            else:
                # Divide into 3 parts
                third = num_lines // 3
                part1 = "\n".join(lines[:third])
                part2 = "\n".join(lines[third: 2 * third])
                part3 = "\n".join(lines[2 * third:])
                return (message_header + part1, part2, part3)

        return (final_message,)

    @classmethod
    async def menu_to_dto(cls, user_id: int, menu: Dict[str, List[RecipeDTO]]) -> CreatePersonalFoodMenuDTO:
        result = CreatePersonalFoodMenuDTO(
            user_id=user_id,
            starters_ids=[r.id for r in menu.get("Starters", [])],
            salad_sides_ids=[r.id for r in menu.get("Salads & Sides", [])],
            main_dishes_ids=[r.id for r in menu.get("Main Dishes", [])],
            soups_bowls_ids=[r.id for r in menu.get("Soups & Bowls", [])],
            desserts_snacks_ids=[r.id for r in menu.get("Desserts & Snacks", [])],
        )
        logger.info(f"Menu after menu_to_dto: {result}")
        return result

    @classmethod
    async def dto_to_menu(cls, dto: CreatePersonalFoodMenuDTO) -> Dict[str, List[int]]:
        
        result = {
            "Starters": [i for i in dto.starters_ids or []],
            "Salads & Sides": [i for i in dto.salad_sides_ids or []],
            "Main Dishes": [i for i in dto.main_dishes_ids or []],
            "Soups & Bowls": [i for i in dto.soups_bowls_ids or []],
            "Desserts & Snacks": [i for i in dto.desserts_snacks_ids or []],
        }
        
        logger.info(f"Menu after dto_to_menu: {result}")
        return result
