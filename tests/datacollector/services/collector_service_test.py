import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from datacollector.services.data_process_service import DataProcessService
from datacollector.services.collector_service import DataCollectorService, BookManager
from tests.datacollector.util import string_to_date
from datacollector.services.datetime_service import DateTimeService


async def async_generator(mock_data):
    for item in mock_data:
        yield item


class TestDataCollectorService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.data_service = Mock(spec=DataProcessService)
        self.book_manager = AsyncMock(spec=BookManager)
        self.dt_service = DateTimeService(dt=string_to_date("2023-12-12"))  # fix the time
        self.collector_service = DataCollectorService(self.data_service, self.dt_service, self.book_manager, "BTC")

    @patch('datacollector.services.collector_service.asyncio.sleep', new_callable=AsyncMock)
    async def test_collect_data_normal(self, mock_sleep):
        self.book_manager.get_data.side_effect = lambda: async_generator([{}, {}])

        # Test collect_data under normal conditions
        await self.collector_service.collect_data()
        # will be one because the minute didn't change
        self.assertEqual(1, self.data_service.insert_one.call_count)

    @patch('datacollector.services.collector_service.asyncio.sleep', new_callable=AsyncMock)
    async def test_collect_data_timeout_error(self, mock_sleep):
        self.book_manager.get_data.side_effect = [asyncio.TimeoutError("Timeout"), Exception("Error")]
        await self.collector_service.collect_data()
        # 1 timeout error + max_retries
        self.assertEqual(self.collector_service.max_retries + 1, mock_sleep.call_count)

    @patch('datacollector.services.collector_service.asyncio.sleep', new_callable=AsyncMock)
    async def test_collect_data_generic_exception(self, mock_sleep):
        # Test collect_data handling generic exception
        self.book_manager.get_data.side_effect = Exception("Error")
        await self.collector_service.collect_data()
        self.assertEqual(self.collector_service.max_retries, mock_sleep.call_count)

    # You can add more tests for different scenarios and exception handling


if __name__ == '__main__':
    unittest.main()
