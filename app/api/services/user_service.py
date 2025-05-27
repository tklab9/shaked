from app.config.logger_settings import get_logger
from app.utils.unitofwork import IUnitOfWork
from app.api.dtos.user_dtos import UserDTO
from app.api.services.service_exceptions import UserServiceException


logger = get_logger("user_service")


class UserService:
    @staticmethod
    async def get_user_by_phone_and_client_id(uow: IUnitOfWork, phone_number: str, client_id: int) -> UserDTO | None:
        try:
            async with uow:
                user = await uow.user_repository.get_user({"phone": phone_number, "client_id": client_id})
                return user

        except Exception as e:
            raise UserServiceException(e)

    @staticmethod
    async def verify_user(uow: IUnitOfWork, user_id: int) -> UserDTO:
        try:
            async with uow:
                user = await uow.user_repository.update_user({"id": user_id}, {"verified": True})
                return user

        except Exception as e:
            raise UserServiceException(e)

    @staticmethod
    async def get_user_by_phone(uow: IUnitOfWork, phone_number: str) -> UserDTO | None:
        try:
            async with uow:
                user = await uow.user_repository.get_user({"phone": phone_number})
                return user

        except Exception as e:
            raise UserServiceException(e)
    
    @staticmethod
    async def update_user_preferences(uow: IUnitOfWork, user_id: int, notification: bool, dietary_preference: str) -> UserDTO:
        """
        Update user preferences in DB after user select notification and dietary preferences
        """
        try:
            async with uow:
                user = await uow.user_repository.update_user(
                    {"id": user_id},
                    {
                        "notification": notification,
                        "dietary_preference": dietary_preference,
                        "menu_verified": True
                    }
                )
                return user

        except Exception as e:
            raise UserServiceException(e)

    @staticmethod
    async def get_users_with_notifications_enabled(uow: IUnitOfWork) -> list[UserDTO]:
        try:
            async with uow:
                users = await uow.user_repository.get_users_with_notifications_enabled()

                if users is None:
                    return []
                return users

        except Exception as e:
            raise UserServiceException(e)

    @staticmethod
    async def update_user_restrictions(uow: IUnitOfWork, user_id: int, restrictions: list[int]) -> UserDTO:
        try:
            async with uow:
                user = await uow.user_repository.update_user(
                    {"id": user_id},
                    {"restrictions": restrictions}
                )
                return user

        except Exception as e:
            raise UserServiceException(e)
