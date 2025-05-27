from app.database.supabase_client import SupabaseClient
from app.api.dtos.personal_food_menu_dtos import PersonalFoodMenuDTO, CreatePersonalFoodMenuDTO
from app.config.logger_settings import get_logger

logger = get_logger(__name__)

class PersonalFoodMenuRepository:
    def __init__(self, supabase_client: SupabaseClient):
        self.client = supabase_client
        self.table = "personal_food_menu"

    async def create_personal_food_menu(self, personal_food_menu: CreatePersonalFoodMenuDTO) -> PersonalFoodMenuDTO:
        data = personal_food_menu.model_dump()
        logger.info(f"Data for create personal food menu: {data}")
        result = await self.client.create(self.table, data)
        logger.info(f"Result of create personal food menu: {result}")
        return PersonalFoodMenuDTO(**result)

    async def get_personal_food_menu_by_user_id(self, user_id: int) -> PersonalFoodMenuDTO or None:
        result = await self.client.read(self.table, {"user_id": user_id})
        logger.info(f"TYPE: {type(result)}")
        if not result:
            return None
        logger.info(f"Result of get personal food menu by user id: {result}")
        result = PersonalFoodMenuDTO(**result[0])
        return result
