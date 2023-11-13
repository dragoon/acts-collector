import asyncio
import logging
from datetime import datetime

from binance import DepthCacheManager, AsyncClient

from datacollector.services.data_service import DataProcessService


class DataCollectorService:
    logger: logging.Logger
    asset_symbol: str
    max_retries: int
    retry_delay: int

    def __init__(self, data_service: DataProcessService, symbol, max_retries=5, retry_delay=1):
        self.data_service = data_service
        self.asset_symbol = symbol
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)

    async def collect_data(self):
        retry_count = 0
        while True:
            client = None
            try:
                client = await AsyncClient.create()
                dcm = DepthCacheManager(client, symbol=f'{self.asset_symbol.upper()}USDT',
                                        limit=5000, refresh_interval=0, ws_interval=100)
                self.logger.info(f"Starting order book collection for {self.asset_symbol}-USDT")

                async with dcm as dcm_socket:
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
                if client is not None:
                    await client.close_connection()

    async def _process_depth_cache(self, dcm_socket):
        last_stored_minute = None
        while True:
            ob = await dcm_socket.recv()
            current_time = datetime.utcnow()
            current_minute = current_time.minute
            if current_minute != last_stored_minute:
                data_entry = self.data_service.compute_data_entry(ob, current_time)
                self.data_service.insert_one(data_entry)
                last_stored_minute = current_minute
