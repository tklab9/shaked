
import datetime
from typing import List
from app.database.supabase_client import SupabaseClient
from app.api.dtos.tips_dtos import TipsDTO
from app.config.logger_settings import get_logger

logger = get_logger(__name__)

class TipsRepository:
    def __init__(self, supabase_client: SupabaseClient):
        self.client = supabase_client
        self.table = "tips"

    async def get_tips_by_day(self, day: int) -> TipsDTO:
        result = await self.client.read(table=self.table, query={"day": day})
        return TipsDTO(**result[0])

    async def get_tips_for_time_range(self, time_from: datetime.time, time_to: datetime.time) -> List[TipsDTO]:
        """
        Returns a list of tips where the time is between time_from and time_to.
        It is assumed that the 'time' field is stored as a string, e.g. '9AM', '2PM', etc.
        """
        result = await self.client.read(table=self.table, query={})

        tips_in_window = []
        for record in result:
            try:
                tip_time = datetime.datetime.strptime(record["time"], "%H:%M:%S").time()
                if time_from <= tip_time <= time_to:
                    tips_in_window.append(TipsDTO(**record))
            except Exception as e:
                logger.error(f"Error processing time for tip: {record} | {e}")
        
        return tips_in_window
