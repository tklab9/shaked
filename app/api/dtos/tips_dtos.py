from typing import Optional
from datetime import time as dt_time

from app.lib.dto.base_dto import Base


class TipsDTO(Base):
    id: int
    day: int
    time: Optional[dt_time] = None
    tip: str

    def __repr__(self):
        return (
            f"TipsDTO(id={self.id}, day={self.day!r},"
            f"time={self.time!r}"
        )
