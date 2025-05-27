from app.lib.dto.base_dto import Base
from datetime import date
from typing import Optional


class UserNotificationDTO(Base):
    user_id: int
    last_tip_day: int
    last_tip_sent_date: Optional[date] = None
