import unittest
from datetime import datetime
from decimal import Decimal
from unittest import TestCase

import pymongo
from bson import Decimal128
from pymongo import MongoClient

from datacollector.repositories.data_repository import DataRepository
from datacollector.domain import AssetDataEntry


class DataRepositoryTest(TestCase):
    repo: DataRepository
    client: MongoClient
    TEST_DB = "test"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.client = pymongo.MongoClient("mongodb://localhost:27017")

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.client.close()

    def setUp(self) -> None:
        super().setUp()
        self.repo = DataRepository(self.client[self.TEST_DB], asset_name="TEST")

    def tearDown(self) -> None:
        super().tearDown()
        self.client.drop_database(self.TEST_DB)

    def test_insert_one(self):
        # Arrange: Create an AssetDataEntry object
        entry = AssetDataEntry(
            mid_price=Decimal("100.0"),
            best_bid=Decimal("99.5"),
            best_ask=Decimal("100.5"),
            total_ask_1=50.0,
            total_ask_4=200.0,
            total_bid_1=45.0,
            total_bid_4=180.0,
            book_bias_1=0.1,
            book_bias_4=0.2,
            last_book_update=datetime.now(),
            current_time=datetime.now()
        )

        # Act: Insert the entry into the database
        self.repo.insert_one(entry)

        # Assert: Verify that the entry is correctly inserted
        inserted_entry = self.repo.col.find_one({"_id": entry.to_dict()["_id"]})
        self.assertIsNotNone(inserted_entry)
        self.assertEqual(Decimal128(entry.mid_price), inserted_entry["mid_price"])


if __name__ == '__main__':
    unittest.main()
