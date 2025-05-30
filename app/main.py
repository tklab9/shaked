import time
import uvicorn
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from functools import partial
from contextlib import asynccontextmanager

from app.routes import get_apps_router
from app.utils.unitofwork import IUnitOfWork, UnitOfWork
from app.utils.cache.ttl_cache import InMemoryUserCache
# from app.utils.cache.user_session import UserSession, UserStates
from app.services.google_upload_file_service import GoogleDriveService
from app.services.recipe_finder import RecipeFinder
from app.api.services.fuzzy_ingredients_recipes_service import FuzzyIngredientsRecipesService
from app.api.services.user_service import UserService
from app.api.services.tips_service import TipsService
from app.api.services.user_notification_service import UserNotificationService

from app.wa_hooks.message_hooks import MessageClient
from app.wa_hooks.bot_menu_service import BotMenuService
from app.config.logger_settings import get_logger
from app.config.project_config import project_settings
from app.database.db import get_supabase_client
from app.services.rag_service import AskRagForRecipe


logger = get_logger("main")


# async def create_recipe_finder(uow: IUnitOfWork) -> RecipeFinder:
#     logger.info(f"Creating [RecipeFinder]...")
#     ingredients = await FuzzyIngredientsRecipesService().get_list_ingridients_he_en(uow) 
#     return RecipeFinder(ingredients)


def create_google_driver_service() -> GoogleDriveService:
    logger.info(f"Creating [GoogleDriveService]...")
    google_drive_service = GoogleDriveService()
    return google_drive_service


def create_rag_service(supabase_client) -> AskRagForRecipe:
    logger.info("Creating [RagService]...")
    openai_key = project_settings.OPENAI_API_KEY
    return AskRagForRecipe(openai_key, supabase_client, project_settings.recipes_rag_csv_path)


def create_uow_client(supabase_client) -> IUnitOfWork:
    logger.info("Creating [UnitOfWork]...")
    return UnitOfWork(supabase_client)


def get_bot_menu_service() -> BotMenuService:
    logger.info("Creating [BotMenuService]...")
    message_client = MessageClient(
        account_sid=project_settings.account_sid,
        auth_token=project_settings.auth_token,
        twilio_number=project_settings.twilio_number
    )
    return BotMenuService(message_client=message_client, language=project_settings.BOT_LANGUAGE)

def get_user_states() -> dict:
    logger.info("Creating [UserStates]...")
    user_states = {}
    return user_states

def get_user_cache() -> dict:
    logger.info("Creating [UserCache]...")
    # user_cache = {}
    user_cache = InMemoryUserCache(ttl=project_settings.USER_CACHE_TTL)
    return user_cache


TIME_WINDOW_MINUTES = 5
SCHEDULLER_REPEAT_MINUTES = 5

async def notify_users(uow: IUnitOfWork, bot_menu_service: BotMenuService):
    now = datetime.now(ZoneInfo("Asia/Jerusalem"))
    logger.info(f"Current time: {now}")

    # Set time window
    time_from = (now - timedelta(minutes=TIME_WINDOW_MINUTES)).time()
    time_to = (now + timedelta(minutes=TIME_WINDOW_MINUTES)).time()
    logger.info(f"Time from: {time_from}, time to: {time_to}")

    # Get users with notifications enabled
    users = await UserService.get_users_with_notifications_enabled(uow)
    logger.info(f"Users with notifications enabled: {users}")

    if not users:
        return None

    # Get all tips for today that fall within the time window
    tips = await TipsService().get_tips_for_time_range(uow, time_from, time_to)
    logger.info(f"Tips for time range: {tips}")

    if not tips:
        return None

    for user in users:
        last_tip_day = await UserNotificationService().get_last_tip_day(uow, user.id)
        next_day = last_tip_day + 1

        # Filter tips by user last_tip_day + 1 == tip.day
        tip_to_send = next((tip for tip in tips if tip.day == next_day), None)
        logger.info(f"For user: {user.phone} we found next tip to send: {tip_to_send}")

        if tip_to_send:
            tip_sent_today = await UserNotificationService().was_tip_sent_today(uow, user.id, now.date())
            if tip_sent_today:
                logger.info(f"Tip was already sent to user: {user.phone} today!")
                continue  # Already sent tip today

            try:
                message = f"*Tip for day {tip_to_send.day}:*\n\n{tip_to_send.tip}"
                logger.info(f"Sending TIP to user {user.phone}: {message}")
                await bot_menu_service.send_message(user.phone, message)
                await UserNotificationService().update_user_last_tip_day(uow, user.id, tip_to_send.day, now.date())
            except Exception as e:
                logger.error(f"Failed to send tip to user {user.phone}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start APP"""

    logger.info(f"Starting app ...")
    supabase_client = await get_supabase_client()
    app.state.bot_menu_service = get_bot_menu_service()
    app.state.user_states = get_user_states()
    app.state.user_cache = get_user_cache()
    app.state.uow = create_uow_client(supabase_client)
    sup_client = await supabase_client.get_client()
    app.state.rag_service = create_rag_service(sup_client)
    app.state.google_drive_service = create_google_driver_service()
    # app.state.recipe_finder = await create_recipe_finder(app.state.uow)

    scheduler = AsyncIOScheduler()
    job_func = partial(notify_users, app.state.uow, app.state.bot_menu_service)

    scheduler.add_job(job_func, trigger=IntervalTrigger(minutes=SCHEDULLER_REPEAT_MINUTES))
    scheduler.start()
    logger.info("Scheduler started")

    yield

    # Code for finish app (shutdown)
    app.state.uow = None
    app.state.rag_service = None
    logger.info("Shutting down app...")


def get_application() -> FastAPI:
    application = FastAPI(
        title="WhatsApp Chat Bot",
        debug=project_settings.DEBUG,
        lifespan=lifespan,
    )

    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = round((time.time() - start_time) * 1000, 4)
        logger.info(f"PATH: {request.url.path}, METHOD: {request.method}, STATUS: {response.status_code}, "
                    f"DURATION: {process_time}ms")

        return response

    application.include_router(get_apps_router())
    return application


app = get_application()


if __name__ == "__main__":
    uvicorn.run(app="app.main:app", reload=True)
# uvicorn app.main:app --reload
