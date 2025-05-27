from datetime import datetime

from app.database.supabase_client import SupabaseClient
from app.api.dtos.user_notification_dtos import UserNotificationDTO
from app.config.logger_settings import get_logger


logger = get_logger(__name__)

class UserNotificationRepository:
    def __init__(self, supabase_client: SupabaseClient):
        self.client = supabase_client
        self.table = "user_notifications"

    async def get_user_notification_by_user_id(self, user_id: int) -> UserNotificationDTO:
        result = await self.client.read(table=self.table, query={"user_id": user_id})
        return UserNotificationDTO(**result[0])

    async def update_user_notification(self, user_id: int, day: int, date: datetime.date):
        result = await self.client.update(
            table=self.table,
            query={"user_id": user_id},
            data={"last_tip_day": day, "last_tip_sent_date": date.isoformat()}
        )
        return result

    async def create_user_notification(self, user_id: int):
        result = await self.client.create(table=self.table, data={"user_id": user_id})
        return result
