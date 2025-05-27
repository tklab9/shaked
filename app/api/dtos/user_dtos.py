from typing import Optional
from datetime import datetime

from app.lib.dto.base_dto import Base


class UserDTO(Base):
    id: int
    client_id: int
    phone: str
    user_name: Optional[str] = None
    verified: bool
    menu_verified: Optional[bool] = False
    notification: Optional[bool] = False
    dietary_preference: Optional[str] = None
    pdf_result_link: Optional[str] = None
    ascii_result_link: Optional[str] = None
    restrictions: Optional[list[int]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __repr__(self):
        return (
            f"UserDTO(id={self.id}, client_id={self.client_id!r},"
            f"phone={self.phone!r}, user_name={self.user_name!r},"
        )
