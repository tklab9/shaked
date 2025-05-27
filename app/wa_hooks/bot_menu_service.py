import asyncio

from app.wa_hooks.message_hooks import MessageClient
from app.api.dtos.recipes_dtos import RecipeDTO
from app.api.dtos.ask_recipe_dtos import AskRecipeAnswerDTO
from app.api.dtos.shopping_list_dtos import ShoppingListDTO
from app.config.logger_settings import get_logger


logger = get_logger("bot_menu_service")

class BotMenuService:
    def __init__(self, message_client: MessageClient, language: str = 'en'):
        self.message_client = message_client
        self.language = language # en or he
    
    @staticmethod
    async def __format_grouped_foods_with_group(grouped_foods: list[dict[str, list[str]]]) -> str:
        lines = []
        for group in grouped_foods:
            line = f"{group['food_group_name']}:  {', '.join(group['foods'])}"
            lines.append(line)

        return "\n".join(lines)
    
    @staticmethod
    async def __format_grouped_foods(grouped_foods: list[dict[str, list[str]]]) -> str:
        lines = []
        foods = []
        for group in grouped_foods:
            foods.extend(group['foods'])
        
        for food in foods:
            line = f"{food}"
            lines.append(line)

        return "\n".join(lines)
    
    async def send_first_message(self, whatsapp_number: str):
        """
        First message for V3 bot
        """
        if self.language == 'en':
            await self.message_client.send_message(whatsapp_number, "Please enter your Client ID to verify your identity.")
        else:
            await self.message_client.send_message(whatsapp_number, "הכנס את מספר הלקוח שלך כדי להזין את זה במערכת.")

    async def send_message(self, whatsapp_number: str, body_text: str):
        await self.message_client.send_message(whatsapp_number, body_text)

    async def send_you_verified_message(self, whatsapp_number: str):
        await self.message_client.send_message(whatsapp_number, "✅ Your ID has been verified!")
    
    async def send_invalid_client_id_message(self, whatsapp_number: str):
        """
        Invalid client id message for V3 bot 'Msg2-Error'
        """
        if self.language == 'en':
            await self.message_client.send_message(whatsapp_number, "Please try again or contact support.")
        else:
            await self.message_client.send_message(whatsapp_number, "הכנס את מספר הלקוח שלך כדי להזין את זה במערכת.")

    async def send_first_income_message(self, whatsapp_number: str, username: str):
        """
        First income message for V3 bot 'Msg1'
        """
        if self.language == 'en':
            menu_text = (
                f"*Hi {username}, 👋, I'm Shaked*\n"
                "*Welcome to your personal nutrition assistant.*\n"
                "*Let's get started!*\n"
            )

        # Hebrew version
        else:
            menu_text = (
                f"*היי {username}, 👋, אני שבדק*\n"
                "*ברוכים הבאים לassi̇טננטה הוראה אישית שלך.*\n"
                "*בוא נתחיל!*\n"
            )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_message_about_test_prepared(self, whastapp_number: str):
        if self.language == 'en':
            menu_text = (
                "Thanks! Your test has been identified.\n"
                "Let's personalize your menu.\n\n"
            )
        else:
            menu_text = (
                "תודה! בדיקה זו זמינה.\n"
                "בוא ניצור לך תפריט אישי.\n\n"
            )
        await self.message_client.send_message(whastapp_number, menu_text)

    async def send_select_dietary_preferences_menu(self, whastapp_number: str):
        """
        Select dietary preferences menu for V3 bot 'Msg2B'
        """
        if self.language == 'en':
            menu_text = (
                "*Great, lets Pick your diet:*\n\n"
                "1️⃣ Vegetarian 🥕\n"
                "2️⃣ Vegan 🌱\n"
                "3️⃣ No preference\n\n"
            )
        # Hebrew version
        else:
            menu_text = (
                "*Great, lets Pick your diet:*\n\n"
                "1️⃣ Vegetarian 🥕\n"
                "2️⃣ Vegan 🌱\n"
                "3️⃣ No preference\n\n"
            )
        await self.message_client.send_message(whastapp_number, menu_text)
    
    async def send_error_select_dietary_preferences(self, whastapp_number: str):
        """
        Error select dietary preferences menu for V3 bot 'Msg2B-Error'
        """
        if self.language == 'en':
            menu_text = (
                "Oops! Please reply with *1*, *2*, or *3* to pick your diet:\n\n"
                "1️⃣ Vegetarian 🥕\n"
                "2️⃣ Vegan 🌱\n"
                "3️⃣ No preference\n\n"
            )

        # Hebrew version
        else:
            menu_text = (
                "Oops! Please reply with *1*, *2*, or *3* to pick your diet:\n\n"
                "1️⃣ Vegetarian 🥕\n"
                "2️⃣ Vegan 🌱\n"
                "3️⃣ No preference\n\n"
            )
        await self.message_client.send_message(whastapp_number, menu_text)
    
    async def send_verify_dietary_preferences_menu(self, whastapp_number: str, dietary_name: str):
        """
        Verify dietary preferences menu for V3 bot 'Msg2B1'
        """

        if self.language == 'en':
            menu_text = (
                f"*You selected {dietary_name}.*\n"
                f"*This will build you a menu with only {dietary_name} dishes.*\n\n"
                "1️⃣ Yes, I'm sure\n"
                "2️⃣ I want to change\n"
            )
        else:
            menu_text = (
                f"*You selected {dietary_name}.\n"
                f"This will build you a menu with only {dietary_name} dishes.*\n\n"
                "1️⃣ Yes, I'm sure\n"
                "2️⃣ I want to change\n"
            )
        await self.message_client.send_message(whastapp_number, menu_text)

    async def send_select_notification_menu(self, whastapp_number: str):
        """
        Select notification menu for V3 bot 'Msg2B2'
        """

        if self.language == 'en':
            menu_text = (
                "*We've prepared daily tips to help you succeed with your new food plan 📝*\n"
                "*Would you like to receive one tip per day?*\n\n"
                "1️⃣ Yes\n"
                "2️⃣ No\n"
            )

        # Hebrew version
        else:
            menu_text = (
                "*We've prepared daily tips to help you succeed with your new food plan 📝*\n"
                "*Would you like to receive one tip per day?*\n\n"
                "1️⃣ Yes\n"
                "2️⃣ No\n"
            )
        await self.message_client.send_message(whastapp_number, menu_text)

    async def send_preparing_dishes_menu(self, whatsapp_number: str, dietary_name: str):
        """
        Preparing dishes menu for V3 bot 'Msg2C'
        """

        if self.language == 'en':
            menu_text = (
                f"*Awesome! Your {dietary_name} menu is preparing...*\n\n"
            )

        # Hebrew version
        else:
            menu_text = (
                f"*נוצר לך תפריט {dietary_name}...*\n\n"
            )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_main_menu_with_dishes(self, whatsapp_number: str):
        """
        Main menu for v3 bot 'Msg2D:'
        """
        if self.language == 'en':
            menu_text = (
                "*Enjoy your IgG-friendly menu!*\n"
                "*You can do things like review specific dish or create*\n"
                "*shopping list everything is personalized based on your test results.*\n\n"
                "1️⃣ View your IgG test results (PDF link) 📋\n"
                "2️⃣ See red & orange list 🔎\n"
                "3️⃣ Check your personal menu 📖\n"
                "4️⃣ Shopping list 🛒\n"
                "5️⃣ Feedback 💬\n\n"
            )
        # Hebrew version
        else:
            menu_text = (
                "*Enjoy your IgG-friendly menu! *\n"
                "*You can do things like review specific dish or create*\n"
                "*shopping list everything is personalized based on your test results.*\n\n"
                "1️⃣ View your IgG test results (PDF link) 📋\n"
                "2️⃣ See red & orange list 🔎\n"
                "3️⃣ Check your personal menu 📖\n"
                "4️⃣ Shopping list 🛒\n"
                "5️⃣ Feedback 💬\n\n"

            )
        await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_new_my_restrictions_menu(self, whatsapp_number: str, high_sensitivity: list = None, low_sensitivity: list = None):
        """
        Restrictions menu V3 bot 'Msg2A'
        """

        LTR_MARK = "\u200E"
        high_sensitivity_lines = [f"{LTR_MARK}🔴 {item}" for item in high_sensitivity]
        low_sensitivity_lines = [f"{LTR_MARK}🟠 {item}" for item in low_sensitivity]
        high_sensitivity_info = "\n".join(high_sensitivity_lines)
        low_sensitivity_info = "\n".join(low_sensitivity_lines)

        if self.language == 'en':
            menu_text = (
                f"*Based on your IgG food intolerance test results you are sensitive*\n"
                f"*for the following foods: (red high sensitivity, orange moderate sensitivity)*\n\n"
                f"{high_sensitivity_info}\n\n"
                f"{low_sensitivity_info}\n\n"
            )

        # Hebrew version
        else:
            menu_text = (
                f"*Based on your IgG food intolerance test results you are sensitive*\n"
                f"*for the following foods: (red high sensitivity, orange moderate sensitivity)*\n\n"
                f"{high_sensitivity_info}\n\n"
                f"{low_sensitivity_info}\n\n"
            )

        await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_message_about_plan_dishes(self, whatsapp_number: str):
        """
        Message about plan dishes V3 bot 'Msg2A1'
        """

        if self.language == 'en':
            menu_text = (
                "*Based on your food intolerance results, we’ll build your personal restaurant-style menu 🍽️*\n"
                "*Your menu will include 27 dishes – a variety of starters, mains, and desserts – just like*\n"
                "*having your own private chef 👨‍🍳*\n"
                "Reply *1* when you're ready to begin!\n\n"
            )

        # Hebrew version
        else:
            menu_text = (
                "*Based on your food intolerance results, we’ll build your personal restaurant-style menu 🍽️*\n"
                "*Your menu will include 27 dishes – a variety of starters, mains, and desserts – just like*\n"
                "*having your own private chef 👨‍🍳*\n"
                "Reply *1* when you're ready to begin!\n\n"
            )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_asc_support_topic(self, whatsapp_number: str):
        """
        ASC support topic V3 bot 'Msg2D5'
        """

        if self.language == 'en':
            menu_text = (
                "*💬 We'd love your feedback!*\n"
                "Please choose the topic:\n\n"
                "1️⃣ Nutrition team\n"
                "2️⃣ Technical team\n"
                "3️⃣ General feedback\n\n"
                "↩️ Type *0* to return to the main menu\n\n"

            )

        # Hebrew version
        else:
            menu_text = (
                "*💬 אנחנו שמחים לשמוע מה שברור לך!*\n"
                "*אנא בחר את הנושא:*\n\n"
                "1️⃣ צוות אוכל\n"
                "2️⃣ צוות טכניקי\n"
                "3️⃣ כללי\n\n"
                "↩️ Type *0* to return to the main menu\n\n"

            )
        await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_after_support_message(self, whatsapp_number: str):
        if self.language == 'en':
            menu_text = (
                "*🙏 Thank you for your feedback!*\n"
                # "Type *0* to go back to the main menu.\n\n"
            )
        else:
            menu_text = (
                "*🙏 תודה על ההודעה שלך! צוות תמיכה שלנו יחזור אליך בהקדם האפשרי.*\n\n"
                # "Type *0* to go back to the main menu.\n\n"
            )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_select_view_dish(self, whastapp_number: str):
        """
        Send select view dish menu for V3 bot 'Msg2D3'
        """

        if self.language == 'en':
            menu_text = (
                "*👀 Want to view a specific dish?*.\n"
                "Type the dish number (e.g., *1* for <dish 01>)\n\n"
                "↩️ Or type *0* to return to the main menu\n\n"
            )

        # Hebrew language
        else:
            menu_text = (
                "*👀 רוצה לראות תפריט ספציפי?*.\n"
                "Type the dish number (e.g., *1* for <dish 01>)\n\n"
                "↩️ Or type *0* to return to the main menu\n\n"
            )
        await self.message_client.send_message(whastapp_number, menu_text)

    async def send_want_check_another_dish(self, whatsapp_number: str):
        if self.language == 'en':
            menu_text = (
                "*🔁 Want to see another dish?*\n"
                "Type the dish number\n\n"
                "↩️ Or type *0* to return to the main menu\n\n"
            )
        else:
            menu_text = (
                "*🔁 רוצה לראות תפריט אחר?*\n"
                "Type the dish number (e.g., *1* for <dish 01>)\n\n"
                "↩️ Or type *0* to return to the main menu\n\n"
            )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_shopping_list_menu(self, whatsapp_number: str):
        """
        Send shopping list menu for V3 bot 'Msg2D4'
        """

        if self.language == 'en':
            menu_text = (
                "*🛒 Let’s build your shopping list!*\n"
                "Which dishes would you like to include?\n\n"
                "Type the dish numbers (e.g., *1,3,5*)\n\n"
                "↩️ Or type *0* to return to the main menu\n\n"
            )

        # Hebrew language
        else:
            menu_text = (
                "*🛒 Let’s build your shopping list!*\n"
                "Which dishes would you like to include?\n\n"
                "Type the dish numbers (e.g., *1,3,5*)\n\n"
                "↩️ Or type *0* to return to the main menu\n\n"
            )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_shopping_list_info(self, whatsapp_number: str, shopping_list_id: list[int]):
        """
        Send shopping list info for V3 bot 'Msg2D4-1'
        """
        if self.language == 'en':
            menu_text = (
                "*✅ Got it!*\n"
                f"Here’s your shopping list for dishes: *{', '.join(map(str, shopping_list_id))}*\n"
            )

        # Hebrew language
        else:
            menu_text = (
                "*✅ Got it!*\n"
                f"Here’s your shopping list for dishes: *{', '.join(map(str, shopping_list_id))}*\n"
            )
        await self.message_client.send_message(whatsapp_number, menu_text)















# Old menu for bot V1 and V2 -------------------------------------------------------

    async def send_select_recipe_type_menu(self, whastapp_number: str):
        menu_text = (
            "*Select Recipe Type:*\n\n"
            "1️⃣ Quick & Easy\n"
            "2️⃣ Medium (up to 20 min)\n"
            "3️⃣ No preference\n"
        )
        await self.message_client.send_message(whastapp_number, menu_text)

    async def send_next_choice_menu(self, whastapp_number: str):
        menu_text = (
            "*What would you like to do next?*\n"
            "*Please type or tap one of the options below:*\n\n"
            "1️⃣ View a recipe from the meal plan\n"
            "2️⃣ Get the full weekly shopping list\n"
            "3️⃣ Talk to our support team\n"
            "4️⃣ Get helpful tips\n"
            "5️⃣ See my food restriction list\n"
            "6️⃣ Plan a new week\n\n"
        )
        await self.message_client.send_message(whastapp_number, menu_text)

    async def send_view_recipe_from_meal_plan_menu(self, whastapp_number: str):
        menu_text = (
            "Great!\n"
            "Please type the number of the meal you'd like to view *(1-28)*.\n"
            "For example:\n\n"
            "2 to view Monday Lunch\n\n"
        )
        await self.message_client.send_message(whastapp_number, menu_text)

    async def send_asc_message_for_support(self, whatsapp_number: str):
        """
        ASC message for support V3 bot 'Msg2D5-1'
        """
        menu_text = (
            "*Please enter your feedback, we will review your message and get back with an answer:*\n"
            "↩️ Type 0 to return to the main menu\n\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_my_results_menu(self, whatsapp_number: str, result_link: str):
        """
        Send my results menu for V3 bot
        """
        if self.language == 'en':
            menu_text = (
                f"Here is your test result PDF:\n{result_link}\n\n"
            )

        # Hebrew
        else:
            menu_text = (
                f"Here is your test result PDF:\n{result_link}\n\n"
            )
        await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_my_restrictions_menu(self, whatsapp_number: str, high_sensitivity: list = None, low_sensitivity: list = None):
        if not high_sensitivity and not low_sensitivity:
            menu_text = (
                f"*See My Restrictions*\n\n"
                "No restrictions found for this user, please contact support.\n"
                # "0️⃣ 🔝 Main Menu"
            )
            await self.message_client.send_message(whatsapp_number, menu_text)
        
        else:
            high_sensitivity_info = ", ".join([f"{r}" for r in high_sensitivity])
            low_sensitivity_info = ", ".join([f"{r}" for r in low_sensitivity])
            menu_text = (
                f"*See My Restrictions*\n\n"
                "🚫 Based on your IgG test, here are the foods you should avoid:\n"
                f"_High Sensitivity_:\n{high_sensitivity_info}\n\n"
                f"_Low Sensitivity_:\n{low_sensitivity_info}\n\n"
                # "0️⃣ 🔝 Main Menu"
            )
            await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_personalized_recipes_rag_menu(self, whatsapp_number: str, personalized_recipe: str = None):
        menu_text = (
            f"{personalized_recipe}\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_info_for_debug(self, whatsapp_number: str, final_answer_recipe: AskRecipeAnswerDTO):
        menu_text = (
            "*Info for analyse work LLM and RAG*\n\n"
            f"*- Recipes ID after search in RAG:*\n{final_answer_recipe.recipes_id_from_rag}\n\n"
            f"*- Filtered recipes ID after check Disliked user recipes:*\n{final_answer_recipe.filtered_disliked_recipes_id}\n\n"
            f"*- Filtered recipes ID after check Restrictions user recipes:*\n{final_answer_recipe.filtered_restrictions_recipes_id}\n\n"
            f"*- Recipes for analyse with LLM:*\nCount: {len(final_answer_recipe.recipes_id_after_filter)}\nRecipes ID: {final_answer_recipe.recipes_id_after_filter}\n\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_promt_with_txt_file(self, whatsapp_number: str, link: str):
        menu_text = (
            "*Link to promt for LLM in this request*\n\n"
            f"{link}"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_asc_quality_result_recipes_menu_without_3(self, whatsapp_number: str):
            """
            Send message to user about select Like or Dislike recipe
            """

            menu_text = (
                "*What would you like to do?*\n\n"
                "1️⃣ Like Recipe\n"
                "2️⃣ Dislike Recipe\n"
                "0️⃣ Back to main menu\n"
            )
            await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_asc_quality_result_recipes_menu(self, whatsapp_number: str):
        """
        Send message to user about select Like or Dislike recipe
        """

        menu_text = (
            "*What would you like to do?*\n\n"
            "1️⃣ Like Recipe\n"
            "2️⃣ Dislike Recipe\n"
            "3️⃣ Generate new recipe\n"
            "0️⃣ Back to main menu\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_shopping_list_choice_recipes(self, whatsapp_number: str, recipes: list[ShoppingListDTO]):
        menu_text = "*\u200ESelect Liked recipe for get Shopping List*\n\n"
        for index, recipe in enumerate(recipes, 1):
            menu_text += f"*\u200E[{index}]* - {recipe.recipe_name}\n"
        
        menu_text += f"*\u200E[{len(recipes) + 1}]* - Show all recipes\n"
        menu_text += "0️⃣ Back to main menu\n"
        await self.message_client.send_message(whatsapp_number, menu_text)

    #         menu_text = (
    #             f"*Personalized Recipes*\n"
    #             "No personalized recipes found for this user, please contact support.\n"
    #             "0️⃣ 🔝 Main Menu"
    #         )
    #         await self.message_client.send_message(whatsapp_number, menu_text)
        
    #     else:
    #         # menu_text = (
    #         #     f"*Personalized Recipes*\n"
    #         #     f"{', '.join(recipes)}\n\n"
    #         #     "0️⃣ 🔝 Main Menu"
    #         # )
    #         menu_text = "*Personalized Recipes*\n"
    #         if len(recipes) > 0:

    #             for index, recipe in enumerate(recipes, 1):
    #                 menu_text += f"{index}. {recipe.name}\n"
    #                 if recipe.sub_title:
    #                     menu_text += f"{recipe.sub_title}\n\n"
    #                 else:
    #                     menu_text += "\n"
    #         else:
    #             menu_text += "No personalized recipes found!\n"

    #         menu_text += "0️⃣ 🔝 Main Menu"
    #         await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_personal_nutrition_assistant_menu(self, whatsapp_number: str):
        menu_text = (
            "🛠 Personal Nutrition Assistant - In development...\n"
            "0️⃣ 🔝 Main Menu"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_choice_meal_type_menu(self, whatsapp_number: str):
        # TODO maybe change on dynamic menu with 'meal_type' table
        menu_text = (
            "*What type of meal are you looking for?*\n\n"
            "1️⃣ Breakfast\n"
            "2️⃣ Lunch\n"
            "3️⃣ Dinner\n"
            "4️⃣ Snack\n"
            "5️⃣ Side Dish\n"
            "6️⃣ Salads\n"
            "7️⃣ Desserts\n"
            "8️⃣ Soups\n\n"
            "0️⃣ 🔝 Main Menu\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def ask_user_whant_get_recipes_menu(self, whatsapp_number: str):
        menu_text = (
            "*Would you like to get recipe suggestions based on your results?*\n\n"
            "1️⃣ Yes, show me recipes\n"
            "0️⃣ 🔝 No, return to Main Menu\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def ask_user_dietary_preference_menu(self, whatsapp_number: str):
        menu_text = (
            "*Do you have any dietary preferences for this meal*\n\n"
            "1️⃣ Vegetarian\n"
            "2️⃣ Vegan\n"
            "3️⃣ High Protein\n"
            "4️⃣ Low Carb\n"
            "5️⃣ No preference\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def ask_user_include_ingredients_menu(self, whatsapp_number: str):
        menu_text = (
            "*Would you like to include any ingredients you already have at home?*\n"
            "_(Example: rice, spinach, tuna)_\n"
            "Reply with a list of ingredients, or reply *'0' to skip.*\n\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_user_message_about_waiting_result(self, whatsapp_number: str):
        """
        Send message to user about waiting for result and preparing recipes
        """

        menu_text = (
            "Thank you for your clarifications!\n"
            "Please wait a little while, we are preparing suitable recipes...\n\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_wait_message(self, whatsapp_number: str):
        """
        Send message to user about waiting for long answer results
        """

        menu_text = (
            "Please wait a little while, we are preparing results...\n\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_question_why_dislike(self, whatsapp_number: str):
        menu_text = (
            "Thanks for your review!\n"
            "Could you please describe why you disliked this recipe so that we can pick\n"
            "the most appropriate ones for you in the future\n\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    
    async def send_menu_liked_recipe(self, whatsapp_number: str):
        menu_text = (
            "*Thanks for your review!*\n"
            "*What would you like to do?*\n\n"
            "1️⃣ Generate Shopping List for Recipe\n"
            "0️⃣ 🔝 Back to Main Menu\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_shopping_list_recipe_after_like(self, whatsapp_number: str, recipe_ingredients: str, recipe_name: str):
        recipe_ingredients = await self.__format_grouped_foods(recipe_ingredients)
        menu_text = (
            f"🛒Here’s your shopping list for *{recipe_name}*\n\n"
            f"{recipe_ingredients}\n\n"
            # "0️⃣ 🔝 Back to Main Menu\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)
