import asyncio
import logging
from contextlib import asynccontextmanager

from binance import DepthCacheManager, AsyncClient, Client

from datacollector.services.data_process_service import DataProcessService


class BookManager:
    asset_symbol: str
    client: Client
    dcm: DepthCacheManager

    def __init__(self, asset_symbol):
        self.asset_symbol = asset_symbol

    async def connect(self):
        self.client = await AsyncClient.create()
        self.dcm = DepthCacheManager(self.client, symbol=f'{self.asset_symbol.upper()}USDT',
                                     limit=5000,  # initial number of order from the order book
                                     refresh_interval=0,  # disable cache refresh
                                     ws_interval=100  # update interval on websocket, ms
                                     )

    @asynccontextmanager
    async def get_dcm_socket(self):
        async with self.dcm as dcm_socket:
            yield dcm_socket

    async def close(self):
        if self.client:
            await self.client.close_connection()


class DataCollectorService:
    logger: logging.Logger
    asset_symbol: str
    max_retries: int
    retry_delay: int

    def __init__(self, data_service: DataProcessService, book_manager, symbol, max_retries=5, retry_delay=1):
        self.data_service = data_service
        self.asset_symbol = symbol
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
        self.book_manager = book_manager

    async def collect_data(self):
        retry_count = 0
        while True:
            try:
                await self.book_manager.connect()
                self.logger.info(f"Starting order book collection for {self.asset_symbol}-USDT")

                async with self.book_manager.get_dcm_socket() as dcm_socket:
                    await self._process_depth_cache(dcm_socket)
                    retry_count = 0

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
                continue  # Continue the while loop to retry connection

            finally:
                await self.book_manager.close()

    async def _process_depth_cache(self, dcm_socket):
        last_stored_minute = None
        while True:
            ob = await dcm_socket.recv()
            current_time = self.data_service.dt_service.get_datetime()
            current_minute = current_time.minute
            if current_minute != last_stored_minute:
                data_entry = self.data_service.compute_data_entry(ob, current_time)
                self.data_service.insert_one(data_entry)
                last_stored_minute = current_minute
