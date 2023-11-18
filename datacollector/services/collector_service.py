import asyncio
import logging

from binance import DepthCacheManager, AsyncClient, Client

from datacollector.services.data_process_service import DataProcessService
from datacollector.services.datetime_service import DateTimeService


class BookManager:
    asset_symbol: str
    client: Client
    dcm: DepthCacheManager

    def __init__(self, asset_symbol):
        self.asset_symbol = asset_symbol

    async def get_data(self):
        try:
            self.client = await AsyncClient.create()
            self.dcm = DepthCacheManager(self.client, symbol=f'{self.asset_symbol.upper()}USDT',
                                         limit=5000,
                                         refresh_interval=0,
                                         ws_interval=100)
            async with self.dcm as dcm_socket:
                while True:
                    data = await dcm_socket.recv()
                    yield data
        finally:
            if self.client:
                await self.client.close_connection()


class DataCollectorService:
    logger: logging.Logger
    dt_service: DateTimeService
    asset_symbol: str
    max_retries: int
    retry_delay: int
    last_stored_minute: int = None

    def __init__(self, data_service: DataProcessService, dt_service: DateTimeService, book_manager: BookManager,
                 symbol: str, max_retries=5, retry_delay=1):
        self.data_service = data_service
        self.dt_service = dt_service
        self.asset_symbol = symbol
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
        self.book_manager = book_manager

    async def collect_data(self):
        retry_count = 0
        while True:
            try:
                self.logger.info(f"Starting order book collection for {self.asset_symbol}-USDT")

                async for data in self.book_manager.get_data():
                    await self._process_depth_cache(data)
                    retry_count = 0
                # in production the data will always continue
                break

            except asyncio.TimeoutError as e:
                self.logger.error(f"Network error: {e}. Reconnecting...")
                await asyncio.sleep(self.retry_delay)

            except Exception as e:
                self.logger.exception(f"An unexpected error occurred: {e}")
                retry_count += 1
                if retry_count > self.max_retries:
                    self.logger.error("Max retries exceeded. Exiting...")
                    break

                # Exponential backoff
                wait = self.retry_delay * 2 ** min(retry_count, self.max_retries)
                self.logger.info(f"Attempting to reconnect in {wait} seconds...")
                await asyncio.sleep(wait)

    async def _process_depth_cache(self, ob):
        current_time = self.dt_service.get_datetime()
        current_minute = current_time.minute
        if current_minute != self.last_stored_minute:
            data_entry = self.data_service.compute_data_entry(ob, current_time)
            self.data_service.insert_one(data_entry)
            self.last_stored_minute = current_minute
