from typing import Optional
from datetime import datetime

from app.lib.dto.base_dto import Base


class PersonalFoodMenuDTO(Base):
    id: int
    user_id: int
    starters_ids: Optional[list[int]] = None
    main_dishes_ids: Optional[list[int]] = None
    salad_sides_ids: Optional[list[int]] = None
    soups_bowls_ids: Optional[list[int]] = None
    desserts_snacks_ids: Optional[list[int]] = None
    created_at: Optional[datetime] = None


class CreatePersonalFoodMenuDTO(Base):
    user_id: int
    starters_ids: Optional[list[int]] = None
    main_dishes_ids: Optional[list[int]] = None
    salad_sides_ids: Optional[list[int]] = None
    soups_bowls_ids: Optional[list[int]] = None
    desserts_snacks_ids: Optional[list[int]] = None

