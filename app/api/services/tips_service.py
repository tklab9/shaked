from app.config.logger_settings import get_logger
from app.utils.unitofwork import IUnitOfWork
from app.api.dtos.tips_dtos import TipsDTO
from app.api.services.service_exceptions import TipsServiceException
from datetime import datetime, time as dt_time


logger = get_logger(__name__)


class TipsService:
    @staticmethod
    async def get_tips_for_time_range(uow: IUnitOfWork, time_from: dt_time, time_to: dt_time) -> list[TipsDTO]:
        try:
            async with uow:
                tips = await uow.tips_repository.get_tips_for_time_range(time_from, time_to)
                return tips

        except Exception as e:
            raise TipsServiceException(e)
