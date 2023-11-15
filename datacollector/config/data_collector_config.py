from datetime import datetime

from pymongo import MongoClient
from pymongo.server_api import ServerApi

from datacollector.config import MONGO_URI
from datacollector.repositories.data_repository import DataRepository
from datacollector.services.collector_service import DataCollectorService, BookManager
from datacollector.services.data_process_service import DataProcessService
from datacollector.services.datetime_service import DateTimeService


def get_data_collector_service(asset_symbol: str, dt: datetime | None) -> DataCollectorService:
    dt_service = DateTimeService(dt)
    mongo_client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    db = mongo_client["faraway_finance"]
    data_repo = DataRepository(db, asset_symbol)
    data_service = DataProcessService(data_repo, dt_service)
    book_manager = BookManager(asset_symbol)

    collector_service = DataCollectorService(data_service, symbol=asset_symbol, book_manager=book_manager)
    return collector_service
