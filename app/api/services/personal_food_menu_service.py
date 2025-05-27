from app.config.logger_settings import get_logger
from app.utils.unitofwork import IUnitOfWork
from app.api.dtos.personal_food_menu_dtos import PersonalFoodMenuDTO, CreatePersonalFoodMenuDTO
from app.api.services.service_exceptions import PersonalFoodMenuServiceException


logger = get_logger(__name__)


class PersonalFoodMenuService:
    @staticmethod
    async def create_personal_food_menu(uow: IUnitOfWork, personal_food_menu: CreatePersonalFoodMenuDTO) -> PersonalFoodMenuDTO:
        try:
            async with uow:
                personal_food_menu = await uow.personal_food_menu_repository.create_personal_food_menu(personal_food_menu)
                return personal_food_menu

        except Exception as e:
            raise PersonalFoodMenuServiceException(e)
    
    @staticmethod
    async def get_personal_food_menu_by_user_id(uow: IUnitOfWork, user_id: int) -> list[PersonalFoodMenuDTO]:
        try:
            async with uow:
                personal_food_menu = await uow.personal_food_menu_repository.get_personal_food_menu_by_user_id(user_id)
                return personal_food_menu

        except Exception as e:
            raise PersonalFoodMenuServiceException(e)
