from datetime import datetime
from app.config.logger_settings import get_logger
from app.utils.unitofwork import IUnitOfWork
from app.api.dtos.user_notification_dtos import UserNotificationDTO
from app.api.services.service_exceptions import UserNotificationServiceException


logger = get_logger(__name__)


class UserNotificationService:
    @staticmethod
    async def get_last_tip_day(uow: IUnitOfWork, user_id: int) -> int:
        try:
            async with uow:
                tip = await uow.user_notification_repository.get_user_notification_by_user_id(user_id)
                return tip.last_tip_day

        except Exception as e:
            raise UserNotificationServiceException(e)

    @staticmethod
    async def update_user_last_tip_day(uow: IUnitOfWork, user_id: int, day: int, date: datetime.date):
        try:
            async with uow:
                await uow.user_notification_repository.update_user_notification(user_id, day, date)

        except Exception as e:
            raise UserNotificationServiceException(e)

    @staticmethod
    async def create_user_notification(uow: IUnitOfWork, user_id: int):
        try:
            async with uow:
                await uow.user_notification_repository.create_user_notification(user_id)

        except Exception as e:
            raise UserNotificationServiceException(e)

    @staticmethod
    async def was_tip_sent_today(uow: IUnitOfWork, user_id: int, date_now: datetime.date) -> bool:
        """
        Check if the user got tip today.
        """
        record = await uow.user_notification_repository.get_user_notification_by_user_id(user_id)
        if record is None:
            return False

        logger.info(f"user_last_tip_sent_date: {record.last_tip_sent_date} == now date:{date_now}")
        compare_two = record.last_tip_sent_date == date_now
        logger.info(f"Compare dates: {compare_two}")
        return compare_two
