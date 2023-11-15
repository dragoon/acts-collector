from decimal import Decimal
from unittest import TestCase
from unittest.mock import Mock

from binance.depthcache import DepthCache

from datacollector.domain import AssetDataEntry
from datacollector.repositories.data_repository import DataRepository
from datacollector.services.data_process_service import DataProcessService
from datacollector.services.datetime_service import DateTimeService
from tests.datacollector.util import string_to_date


class DataProcessServiceTest(TestCase):
    repo: DataRepository
    dt_service: DateTimeService

    def setUp(self):
        super().setUp()
        self.dt_service = DateTimeService(dt=string_to_date("2023-12-12"))  # fix the time
        self.repo = Mock(spec=DataRepository)
        self.service = DataProcessService(data_repo=self.repo, dt_service=self.dt_service)

    def test_insert_one(self):
        mock_entry = Mock(spec=AssetDataEntry)
        self.service.insert_one(mock_entry)
        self.repo.insert_one.assert_called_with(mock_entry)

    def test_compute_data_entry(self):
        mock_depth_cache = Mock(spec=DepthCache)
        mock_depth_cache.get_asks.return_value = [(Decimal(100), 1), (Decimal(101), 2)]
        mock_depth_cache.get_bids.return_value = [(Decimal(99), 1), (Decimal(98), 2)]
        mock_depth_cache.update_time = self.dt_service.get_datetime().timestamp()*1000

        result = self.service.compute_data_entry(mock_depth_cache, self.dt_service.get_datetime())
        correct_result = AssetDataEntry(mid_price=Decimal(99.5), best_ask=Decimal(100), best_bid=Decimal(99),
                                        book_bias_1=0.0, book_bias_4=0.0,
                                        total_ask_1=1, total_bid_1=1, total_ask_4=3, total_bid_4=3,
                                        current_time=self.dt_service.get_datetime(), last_book_update=self.dt_service.get_datetime())

        self.assertEqual(result, correct_result)
