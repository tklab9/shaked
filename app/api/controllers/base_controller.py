import asyncio
from fastapi import APIRouter, Depends, HTTPException, Form, Request

from app.utils.cache.user_session import UserSession, UserStates
from app.services.ascii_service import ASCIIService
from app.services.google_upload_file_service import GoogleDriveService
from app.dependencies import (
    BotMenuServiceDep,
    UserStatesDep,
    UOWDep,
    UserCacheDep,
    AskRagForRecipeDep,
    GoogleDriveServiceDep,
    # RecipeFinderDep,
)
from app.api.dtos.recipe_user_preferences_dto import RecipeUserPreferencesDTO
from app.api.dtos.user_dtos import UserDTO
from app.api.dtos.food_dtos import FoodDTO
from app.api.dtos.recipe_ratings_dtos import CreateRecipeRatingDTO
from app.api.dtos.shopping_list_dtos import CreateShoppingListDTO, ShoppingListDTO
from app.api.dtos.recipes_view_data_dtos import RecipesViewDataDTO
from app.api.dtos.personal_food_menu_dtos import CreatePersonalFoodMenuDTO

from app.api.services.user_service import UserService
from app.api.services.recipes_service import RecipesService
from app.api.services.food_service import FoodService
from app.api.services.shopping_list_service import ShoppingListService
from app.api.services.recipe_ratings_service import RecipeRatingsService
from app.api.services.fuzzy_ingredients_recipes_service import FuzzyIngredientsRecipesService
from app.api.services.recipes_view_data_service import RecipesViewDataService
from app.api.services.user_notification_service import UserNotificationService

from app.services.dishes_algorytm_service import PreparingDishes
from app.config.logger_settings import get_logger
from app.api.services.personal_food_menu_service import PersonalFoodMenuService


logger = get_logger("base_controller")

router = APIRouter(tags=["Base"])


@router.post("/message", response_model=None)
async def reply(
    request: Request,
    uow: UOWDep,
    # recipe_finder: RecipeFinderDep,
    bot_menu_service: BotMenuServiceDep,
    user_cache: UserCacheDep,
    rag_service: AskRagForRecipeDep,
    google_drive_service: GoogleDriveServiceDep,
    Body: str = Form()
):
    form_data = await request.form()
    whatsapp_number = form_data['From'].split("whatsapp:")[-1]
    user_message = Body.strip()

    user_session = UserSession(user_cache, whatsapp_number)

    if not await user_session.exists():
        logger.info(f"User {whatsapp_number} not in cache. Checking DB verification status.")
        try:
            user = await UserService().get_user_by_phone(uow, whatsapp_number)
            if user is None:
                logger.info(f"Failed to get user by phone {whatsapp_number}: {e}")
                await bot_menu_service.send_message(whatsapp_number, "Your number is not in the system, contact support at @support email")
                return ""

        except Exception as e:
            logger.warning(f"Failed to get user by phone {whatsapp_number}: {e}")
            await bot_menu_service.send_message(whatsapp_number, "Your number is not in the system, contact support at @support email")
            return ""

        if user.verified and user.menu_verified:
            logger.info(f"User {whatsapp_number} is already verified in DB.")
            await user_session.set_user(user)
            await user_session.set_state(UserStates.USER_WAITING_ANSWER)

            # Add to cache personal menu
            personal_menu = await PersonalFoodMenuService().get_personal_food_menu_by_user_id(uow, user.id)
            dto_for_menu = await PreparingDishes.dto_to_menu(personal_menu)
            logger.info(f"DTO for menu USER: {user.id}:\n{dto_for_menu}")
            for category, recipe_ids in dto_for_menu.items():
                recipes = await RecipesService.get_recipes_by_ids(uow, recipe_ids)
                # Sort recipes in order recipe_ids
                id_to_recipe = {recipe.id: recipe for recipe in recipes}
                dto_for_menu[category] = [id_to_recipe[recipe_id] for recipe_id in recipe_ids if recipe_id in id_to_recipe]
                # dto_for_menu[category] = await RecipesService.get_recipes_by_ids(uow, recipe_ids)

            # logger.info(f"2 DTO for menu USER: {user.id}:\n{dto_for_menu}")
            index_to_recipe = {}
            current_index = 1
            for category, recipes in dto_for_menu.items():
                for recipe in recipes:
                    index_to_recipe[current_index] = recipe.id
                    current_index += 1

            logger.info(f"Index to recipe for save to cache: {index_to_recipe}")
            await user_session.set_personal_food_menu(dto_for_menu)
            await user_session.set_index_to_personal_food_recipes(index_to_recipe)
            
            await user_session.set_state(UserStates.MAIN_MENU)
            await bot_menu_service.send_main_menu_with_dishes(whatsapp_number)
            return ""
        
        if user.verified and not user.menu_verified:
            # If user verified and long waiting (cache reload) before select dietary preferences
            logger.info(f"User {whatsapp_number} is verified in DB but not verified in menu.")
            await user_session.set_user(user)
            await user_session.set_state(UserStates.USER_WAITING_ANSWER)

            # Check restrictions
            ascii_result_link = user.ascii_result_link
            # TODO create util for work with getting restrictions info
            file_id = ascii_result_link.split("/d/")[1].split("/view")[0]
            logger.info(f"File ID: {file_id}")
            high_sensitivity_foods_codes, low_sensitivity_foods_codes = await ASCIIService.process_csv(file_id)
            await user_session.set_restrictions_lab_codes(high_sensitivity_foods_codes + low_sensitivity_foods_codes)
            # TODO create one request instead of two, and filter results on hight and low foods
            high_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, high_sensitivity_foods_codes)
            low_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, low_sensitivity_foods_codes)
            await user_session.set_high_sensitivity_foods(high_sensitivity_foods)
            await user_session.set_low_sensitivity_foods(low_sensitivity_foods)
            await user_session.set_all_restriction_products(high_sensitivity_foods + low_sensitivity_foods)

            high_sensitivity_foods_names = [food.name for food in high_sensitivity_foods]
            low_sensitivity_foods_names = [food.name for food in low_sensitivity_foods]
            logger.info(f"High sensitivity foods: {high_sensitivity_foods_names}")
            logger.info(f"Low sensitivity foods: {low_sensitivity_foods_names}")
            # Finish preparing restrictions

            await bot_menu_service.send_new_my_restrictions_menu(whatsapp_number, high_sensitivity_foods_names, low_sensitivity_foods_names)
            await asyncio.sleep(1.5)
            await bot_menu_service.send_message_about_plan_dishes(whatsapp_number)
            await user_session.set_state(UserStates.ASC_SELECT_DIETARY_PREFERENCES)
            return ""

        else:
            logger.info(f"User {whatsapp_number} is not verified. Sending first message.")
            await user_session.set_user(user)
            await user_session.set_state(UserStates.AWAITING_VERIFICATION)
            await bot_menu_service.send_first_message(whatsapp_number)
            return ""

    state = await user_session.get_state()
    logger.info(f"USER STATE: {state}")
    user: UserDTO = await user_session.get_user()
    logger.info(f"USER: {user}")

    if state == UserStates.AWAITING_VERIFICATION:
        try:
            logger.info(f"Trying to verify {whatsapp_number} with Client ID: {user_message}")
            verified_user = await UserService().get_user_by_phone_and_client_id(uow, whatsapp_number, int(user_message))
            if verified_user is None:
                raise Exception("Verification failed")
        except Exception as e:
            logger.warning(f"Verification error for {whatsapp_number}: {e}")
            await bot_menu_service.send_invalid_client_id_message(whatsapp_number)
            return ""

        logger.info(f"User {whatsapp_number} verified successfully.")
        updated_user = await UserService().verify_user(uow, verified_user.id)
        await user_session.set_user(updated_user)
        await user_session.set_state(UserStates.USER_WAITING_ANSWER)
        await bot_menu_service.send_first_income_message(whatsapp_number, updated_user.user_name)
        await asyncio.sleep(1.5)

        # Check restrictions
        ascii_result_link = updated_user.ascii_result_link
        # TODO create util for work with getting restrictions info
        file_id = ascii_result_link.split("/d/")[1].split("/view")[0]
        logger.info(f"File ID: {file_id}")
        high_sensitivity_foods_codes, low_sensitivity_foods_codes = await ASCIIService.process_csv(file_id)
        await user_session.set_restrictions_lab_codes(high_sensitivity_foods_codes + low_sensitivity_foods_codes)
        # TODO create one request instead of two, and filter results on hight and low foods
        high_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, high_sensitivity_foods_codes)
        low_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, low_sensitivity_foods_codes)
        await user_session.set_high_sensitivity_foods(high_sensitivity_foods)
        await user_session.set_low_sensitivity_foods(low_sensitivity_foods)
        await user_session.set_all_restriction_products(high_sensitivity_foods + low_sensitivity_foods)

        high_sensitivity_foods_names = [food.name for food in high_sensitivity_foods]
        low_sensitivity_foods_names = [food.name for food in low_sensitivity_foods]
        logger.info(f"High sensitivity foods: {high_sensitivity_foods_names}")
        logger.info(f"Low sensitivity foods: {low_sensitivity_foods_names}")
        # Finish preparing restrictions

        await bot_menu_service.send_new_my_restrictions_menu(whatsapp_number, high_sensitivity_foods_names, low_sensitivity_foods_names)
        await asyncio.sleep(2)
        await bot_menu_service.send_message_about_plan_dishes(whatsapp_number)
        await user_session.set_state(UserStates.ASC_SELECT_DIETARY_PREFERENCES)
        return ""


    # Menu for verified user
    match state:
        case UserStates.ASC_SELECT_DIETARY_PREFERENCES:
            match user_message:
                case "1":
                    await bot_menu_service.send_select_dietary_preferences_menu(whatsapp_number)
                    await user_session.set_state(UserStates.SELECT_DIETARY_PREFERENCES)

                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Please choose *1* to continue:"
                    )
                    await asyncio.sleep(1.5)

        case UserStates.SELECT_DIETARY_PREFERENCES:
            match user_message:
                case "1" | "2" | "3":
                    if user_message == "1":
                        dietary_preference = "Vegetarian"
                        await user_session.set_vegetarian(True)

                    elif user_message == "2":
                        dietary_preference = "Vegan"
                        await user_session.set_vegan(True)

                    elif user_message == "3":
                        dietary_preference = "No preference"

                    await user_session.set_dietary_preference(dietary_preference)
                    logger.info(f"Catch dietary preference: {dietary_preference}")
                    await bot_menu_service.send_verify_dietary_preferences_menu(whatsapp_number, dietary_preference)
                    await user_session.set_state(UserStates.VERIFY_DIETARY_PREFERENCES)
                
                case _:
                    await bot_menu_service.send_error_select_dietary_preferences(whatsapp_number)
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_select_dietary_preferences_menu(whatsapp_number)
        
        case UserStates.VERIFY_DIETARY_PREFERENCES:
            match user_message:
                case "1":
                    await bot_menu_service.send_select_notification_menu(whatsapp_number)
                    await user_session.set_state(UserStates.SELECT_NOTIFICATION)

                case "2":
                    await bot_menu_service.send_select_dietary_preferences_menu(whatsapp_number)
                    await user_session.set_state(UserStates.SELECT_DIETARY_PREFERENCES)

                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Please choose from *1* to *2*"
                    )
                    await asyncio.sleep(1.5)
                    dietary_preference = await user_session.get_dietary_preference()
                    await bot_menu_service.send_verify_dietary_preferences_menu(whatsapp_number, dietary_preference)

        case UserStates.SELECT_NOTIFICATION:
            match user_message:
                case "1" | "2":
                    await user_session.set_state(UserStates.USER_WAITING_ANSWER)
                    try:
                        notification = True if user_message == "1" else False
                        dietary_preference = await user_session.get_dietary_preference()
                        
                        await bot_menu_service.send_preparing_dishes_menu(whatsapp_number, dietary_preference)
                        await asyncio.sleep(0.5)
                        # await user_session.set_state(UserStates.USER_WAITING_ANSWER)

                        # Preparing dishes with user dietary preference
                        all_restriction_products = await user_session.get_all_restriction_products()
                        id_restriction_products = [p.id for p in all_restriction_products]

                        # Add user restrictions to DB
                        await UserService().update_user_restrictions(uow, user.id, id_restriction_products)
                        
                        vegan_pref = await user_session.get_vegan()
                        vegetarian_pref = await user_session.get_vegetarian()
                        recipes = await RecipesService().get_recipes_with_selected_settings(
                            uow,
                            id_restriction_products,
                            vegan=vegan_pref,
                            vegetarian=vegetarian_pref
                        )

                        # logger.info(f"Recipes: {recipes}")
                        for key, value in recipes.items():
                            logger.info(f"{key}: Count: {len(value)}, Value: {value}")
                        
                        # Save personal food menu to DB
                        dto_for_db = await PreparingDishes.menu_to_dto(user.id, recipes)
                        logger.info(f"DTO for PreparingDishes DB USER: {user.id}:\n{dto_for_db}")
                        await PersonalFoodMenuService().create_personal_food_menu(uow, dto_for_db)

                        # Save to cash personal food menu
                        dto_for_menu = await PreparingDishes.dto_to_menu(dto_for_db)
                        logger.info(f"DTO for menu USER: {user.id}:\n{dto_for_menu}")
                        for category, recipe_ids in dto_for_menu.items():
                            recipes = await RecipesService.get_recipes_by_ids(uow, recipe_ids)
                            # Sort recipes in order recipe_ids
                            id_to_recipe = {recipe.id: recipe for recipe in recipes}
                            dto_for_menu[category] = [id_to_recipe[recipe_id] for recipe_id in recipe_ids if recipe_id in id_to_recipe]
                            # dto_for_menu[category] = await RecipesService.get_recipes_by_ids(uow, recipe_ids)
                        
                        index_to_recipe = {}
                        current_index = 1
                        for category, recipes in dto_for_menu.items():
                            for recipe in recipes:
                                index_to_recipe[current_index] = recipe.id
                                current_index += 1

                        logger.info(f"Index to recipe for save to cache: {index_to_recipe}")
                        await user_session.set_personal_food_menu(dto_for_menu)
                        await user_session.set_index_to_personal_food_recipes(index_to_recipe)
                        
                        personal_menu = await user_session.get_personal_food_menu()
                        menu_text = await PreparingDishes.format_menu_text(personal_menu)
                        await bot_menu_service.send_message(whatsapp_number, menu_text)
                        await asyncio.sleep(1)

                        # Update user info
                        updated_user_info = await UserService().update_user_preferences(uow, user.id, notification, dietary_preference)
                        await UserNotificationService().create_user_notification(uow, user.id)
                        await user_session.set_user(updated_user_info)

                        await bot_menu_service.send_main_menu_with_dishes(whatsapp_number)
                        await user_session.set_state(UserStates.MAIN_MENU)

                    except Exception as e:
                        logger.error(f"Error in select notification: {e}")
                        await bot_menu_service.send_select_notification_menu(whatsapp_number)
                        await user_session.set_state(UserStates.SELECT_NOTIFICATION)

                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Please choose from *1* to *2*"
                    )
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_select_notification_menu(whatsapp_number)
        
        case UserStates.MAIN_MENU:
            match user_message:
                case "1":
                    await bot_menu_service.send_my_results_menu(whatsapp_number, user.pdf_result_link)
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_main_menu_with_dishes(whatsapp_number)
                    return ""

                case "2":
                    await user_session.set_state(UserStates.USER_WAITING_ANSWER)
                    ascii_result_link = user.ascii_result_link

                    high_sensitivity_foods = await user_session.get_high_sensitivity_foods()
                    low_sensitivity_foods = await user_session.get_low_sensitivity_foods()

                    if high_sensitivity_foods is not None and low_sensitivity_foods is not None:
                        logger.info(f" === Find Restrictions in User cache! ===")
                        high_sensitivity_foods_names = [food.name for food in high_sensitivity_foods]
                        low_sensitivity_foods_names = [food.name for food in low_sensitivity_foods]
                        await bot_menu_service.send_new_my_restrictions_menu(whatsapp_number, high_sensitivity_foods_names, low_sensitivity_foods_names)
                        await user_session.set_state(UserStates.MAIN_MENU)
                        await asyncio.sleep(1.5)
                        await bot_menu_service.send_main_menu_with_dishes(whatsapp_number)

                    elif ascii_result_link:
                        # TODO create util for work with getting restrictions info
                        file_id = ascii_result_link.split("/d/")[1].split("/view")[0]
                        logger.info(f"File ID: {file_id}")
                        high_sensitivity_foods_codes, low_sensitivity_foods_codes = await ASCIIService.process_csv(file_id)

                        await user_session.set_restrictions_lab_codes(high_sensitivity_foods_codes + low_sensitivity_foods_codes)
                        # TODO create one request instead of two, and filter results on hight and low foods
                        high_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, high_sensitivity_foods_codes)
                        low_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, low_sensitivity_foods_codes)
                        await user_session.set_high_sensitivity_foods(high_sensitivity_foods)
                        await user_session.set_low_sensitivity_foods(low_sensitivity_foods)
                        await user_session.set_all_restriction_products(high_sensitivity_foods + low_sensitivity_foods)

                        # user_cache[whatsapp_number]["restrictions_foods_id"] = [food.id for food in high_sensitivity_foods + low_sensitivity_foods]
                        high_sensitivity_foods_names = [food.name for food in high_sensitivity_foods]
                        low_sensitivity_foods_names = [food.name for food in low_sensitivity_foods]
                        logger.info(f"High sensitivity foods: {high_sensitivity_foods_names}")
                        logger.info(f"Low sensitivity foods: {low_sensitivity_foods_names}")
                        await bot_menu_service.send_new_my_restrictions_menu(whatsapp_number, high_sensitivity_foods_names, low_sensitivity_foods_names)
                        await user_session.set_state(UserStates.MAIN_MENU)
                        await asyncio.sleep(1.5)
                        await bot_menu_service.send_main_menu_with_dishes(whatsapp_number)

                    else:
                        await bot_menu_service.send_new_my_restrictions_menu(whatsapp_number)
                        await user_session.set_state(UserStates.MAIN_MENU)
                        await asyncio.sleep(1.5)
                        await bot_menu_service.send_main_menu_with_dishes(whatsapp_number)

                case "3":
                    await user_session.set_state(UserStates.USER_WAITING_ANSWER)
                    personal_menu = await user_session.get_personal_food_menu()
                    menu_text = await PreparingDishes.format_menu_text(personal_menu)
                    await bot_menu_service.send_message(whatsapp_number, menu_text)
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_select_view_dish(whatsapp_number)
                    await user_session.set_state(UserStates.SELECT_VIEW_DISH)

                case "4":
                    await user_session.set_state(UserStates.SELECT_SHOPPING_LIST_MENU)
                    await bot_menu_service.send_shopping_list_menu(whatsapp_number)

                case "5":
                    await bot_menu_service.send_asc_support_topic(whatsapp_number)
                    await user_session.set_state(UserStates.ASK_TOPIC_SUPPORT)

                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Please choose from *1* to *5* to select an option from the menu."
                    )
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_main_menu_with_dishes(whatsapp_number)
        
        case UserStates.SELECT_SHOPPING_LIST_MENU:
            user_input = user_message.strip()

            if user_input == "0":
                await user_session.set_state(UserStates.MAIN_MENU)
                await bot_menu_service.send_main_menu_with_dishes(whatsapp_number)
            
            # elif user_input == "28":
            #     await user_session.set_state(UserStates.USER_WAITING_ANSWER)
            #     try:
            #         indexes_to_personal_food_recipes = await user_session.get_index_to_personal_food_recipes()
            #         recipe_to_index = {v: k for k, v in indexes_to_personal_food_recipes.items()}

            #         user_shopping_list = await ShoppingListService.get_user_shopping_lists(uow, user.id)
            #         shopping_list_ids = [recipe.recipe_id for recipe in user_shopping_list]

            #         new_recipe_ids = [
            #             recipe_id
            #             for index, recipe_id in indexes_to_personal_food_recipes.items()
            #             if recipe_id not in shopping_list_ids
            #         ]

            #         for recipe_id in new_recipe_ids:
            #             dto = CreateShoppingListDTO(user_id=user.id, recipe_id=recipe_id)
            #             await ShoppingListService.create_shopping_list(uow, dto)
            #             shopping_list_ids.append(recipe_id)

            #         logger.info(f"Added all missing recipes to shopping list: {new_recipe_ids}")

            #         shopping_list_dto = await RecipesService().get_recipes_by_ids(uow, shopping_list_ids)
            #         recipe_to_index = {v: k for k, v in indexes_to_personal_food_recipes.items()}
            #         shopping_list_result = [
            #             (recipe_to_index.get(recipe.id), recipe)
            #             for recipe in shopping_list_dto
            #             if recipe.id in recipe_to_index
            #         ]

            #         await bot_menu_service.send_shopping_list_info(whatsapp_number, [i for i, _ in shopping_list_result])
            #         await asyncio.sleep(1.5)

            #         # Prepare message with shopping list
            #         shopping_list_message = await PreparingDishes.prepare_message_with_shopping_list(shopping_list_result=shopping_list_result, divide_messages=True)
            #         for message in shopping_list_message:
            #             await bot_menu_service.send_message(whatsapp_number, message)
            #             await asyncio.sleep(1.5)

            #         await bot_menu_service.send_shopping_list_menu(whatsapp_number)
            #         await user_session.set_state(UserStates.SELECT_SHOPPING_LIST_MENU)

            #     except Exception as e:
            #         logger.error(f"Error in SELECT_SHOPPING_LIST_MENU (28): {e}")
            #         await bot_menu_service.send_shopping_list_menu(whatsapp_number)
            #         await user_session.set_state(UserStates.SELECT_SHOPPING_LIST_MENU)

            else:
                try:
                    indexes_to_personal_food_recipes = await user_session.get_index_to_personal_food_recipes()
                    valid_indexes = set(indexes_to_personal_food_recipes.keys())
                    logger.info(f"Valid indexes: {valid_indexes}")

                    input_indexes = [int(part.strip()) for part in user_input.split(",")]
                    logger.info(f"Input indexes: {input_indexes}")

                    if any(index < 1 or index > 27 for index in input_indexes):
                        raise ValueError("Invalid index in selection")

                    await user_session.set_state(UserStates.USER_WAITING_ANSWER)

                    recipe_to_index = {v: k for k, v in indexes_to_personal_food_recipes.items()}
                    user_shopping_list = await ShoppingListService.get_user_shopping_lists(uow, user.id)
                    shopping_list_ids = [recipe.recipe_id for recipe in user_shopping_list]

                    for index in input_indexes:
                        recipe_id = indexes_to_personal_food_recipes.get(index)
                        if recipe_id and recipe_id not in shopping_list_ids:
                            dto = CreateShoppingListDTO(user_id=user.id, recipe_id=recipe_id)
                            await ShoppingListService.create_shopping_list(uow, dto)
                            shopping_list_ids.append(recipe_id)

                    shopping_list_dto = await RecipesService().get_recipes_by_ids(uow, shopping_list_ids)
                    shopping_list_result = [
                        (recipe_to_index.get(recipe.id), recipe)
                        for recipe in shopping_list_dto
                        if recipe.id in recipe_to_index
                    ]

                    await bot_menu_service.send_shopping_list_info(whatsapp_number, [i for i, _ in shopping_list_result])
                    await asyncio.sleep(1.5)

                    # Prepare message with shopping list
                    shopping_list_message = await PreparingDishes.prepare_message_with_shopping_list(shopping_list_result=shopping_list_result, divide_messages=True)
                    for message in shopping_list_message:
                        await bot_menu_service.send_message(whatsapp_number, message)
                        await asyncio.sleep(1.5)

                    await bot_menu_service.send_shopping_list_menu(whatsapp_number)
                    await user_session.set_state(UserStates.SELECT_SHOPPING_LIST_MENU)

                except Exception as e:
                    logger.error(f"Error in SELECT_SHOPPING_LIST_MENU (multi): {e}")
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid input. Please type dish numbers like *1,3,5* or *0* to return."
                    )
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_shopping_list_menu(whatsapp_number)
                    await user_session.set_state(UserStates.SELECT_SHOPPING_LIST_MENU)

        case UserStates.ASK_TOPIC_SUPPORT:
            match user_message:

                case "1" | "2" | "3":
                    await user_session.set_state(UserStates.USER_WAITING_ANSWER)
                    try:
                        topics = {
                            "1": "Nutrition team",
                            "2": "Technical team",
                            "3": "General feedback"
                        }
                        topic = topics[user_message]
                        await user_session.set_support_topic(topic)
                        await bot_menu_service.send_asc_message_for_support(whatsapp_number)
                        await user_session.set_state(UserStates.ASK_SUPPORT)

                    except Exception as e:
                        logger.error(f"Error in ASK_TOPIC_SUPPORT: {e}")
                        await bot_menu_service.send_asc_support_topic(whatsapp_number)
                        await user_session.set_state(UserStates.ASK_TOPIC_SUPPORT)
                    
                case "0":
                    await user_session.set_state(UserStates.MAIN_MENU)
                    await bot_menu_service.send_main_menu_with_dishes(whatsapp_number)
                
                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Please choose from *1* to *3* to select an option or *0* to return to the menu."
                    )
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_asc_support_topic(whatsapp_number)

        case UserStates.SELECT_VIEW_DISH:
            match user_message:
                case "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "11" | "12" | "13" | "14" | "15" | "16" | "17" | "18" | "19" | "20" | "21" | "22" | "23" | "24" | "25" | "26" | "27":
                    await user_session.set_state(UserStates.USER_WAITING_ANSWER)
                    index_recipe = int(user_message)
                    indexes_to_personal_food_recipes = await user_session.get_index_to_personal_food_recipes()
                    logger.info(f"Indexes to personal food recipes: {indexes_to_personal_food_recipes}")
                    recipe_id = indexes_to_personal_food_recipes[index_recipe]
                    logger.info(f"Recipe id for view: {recipe_id}")
                    recipe_object = await RecipesViewDataService().get_recipes_view_data_by_list_id(uow, [recipe_id])
                    recipe_object = recipe_object[0].model_dump()
                    recipe_view = await rag_service.get_recipe_info_message(recipe_object)
                    await bot_menu_service.send_message(whatsapp_number, recipe_view)
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_want_check_another_dish(whatsapp_number)
                    await user_session.set_state(UserStates.SELECT_VIEW_DISH)
                
                case "0":
                    await user_session.set_state(UserStates.MAIN_MENU)
                    await bot_menu_service.send_main_menu_with_dishes(whatsapp_number)
                
                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Please choose from *1* to *27* to select an option or *0* to return to the menu."
                    )
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_select_view_dish(whatsapp_number)

        case UserStates.ASK_SUPPORT:
            match user_message:
                case "0":
                    await user_session.set_state(UserStates.MAIN_MENU)
                    await bot_menu_service.send_main_menu_with_dishes(whatsapp_number)

                case _:
                    topic = await user_session.get_support_topic()
                    await google_drive_service.append_row_to_sheet(
                        user_id=user.id,
                        phone=user.phone,
                        topic=topic,
                        message=user_message,
                    )
                    await bot_menu_service.send_after_support_message(whatsapp_number)
                    await user_session.set_state(UserStates.MAIN_MENU)
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_main_menu_with_dishes(whatsapp_number)
   
        case UserStates.USER_WAITING_ANSWER:
            # For block user message during work our logic
            match user_message:
                case _:
                    logger.debug(f" #### User {whatsapp_number} sent message: {user_message} during waiting answer !")
                    await bot_menu_service.send_message(
                        whatsapp_number, "Please wait while we are preparing your answer!"
                    )

    return ""
