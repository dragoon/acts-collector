import logging
from datetime import datetime
from decimal import Decimal
from functools import partial

from binance.depthcache import DepthCache

from datacollector.domain import AssetDataEntry
from datacollector.repositories.date_repository import DataRepository
from datacollector.services.datetime_service import DateTimeService


def compute_bb(asks: list, bids: list, mid_price: Decimal, percent: float) -> tuple[int, int, float]:
    max_price = float(mid_price) * (1 + percent)
    min_price = float(mid_price) * (1 - percent)
    total_ask_quantity = sum(ask[1] for ask in asks if max_price >= ask[0] >= min_price)
    total_bid_quantity = sum(bid[1] for bid in bids if max_price >= bid[0] >= min_price)

    # Compute the book bias
    book_bias = (total_bid_quantity - total_ask_quantity) / (total_bid_quantity + total_ask_quantity)
    return int(total_ask_quantity), int(total_bid_quantity), book_bias


compute_bb1 = partial(compute_bb, percent=0.01)
compute_bb4 = partial(compute_bb, percent=0.04)


class DataProcessService:
    repository: DataRepository
    dt_service: DateTimeService
    logger: logging.Logger

    def __init__(self, data_repo: DataRepository, dt_service: DateTimeService):
        self.repository = data_repo
        self.dt_service = dt_service
        self.logger = logging.getLogger(__name__)

    def insert_one(self, entry: AssetDataEntry) -> None:
        self.repository.insert_one(entry)

    def compute_data_entry(self, ob: DepthCache, current_time: datetime) -> AssetDataEntry:
        # Get the asks and bids
        asks = ob.get_asks()
        bids = ob.get_bids()
        best_bid = Decimal(bids[0][0])
        best_ask = Decimal(asks[0][0])
        mid_price = (best_bid + best_ask)/2

        ask_d1, bid_d1, bb1 = compute_bb1(asks, bids, mid_price)
        ask_d4, bid_d4, bb4 = compute_bb4(asks, bids, mid_price)
        self.logger.info(f"BB4 at {current_time}: {bb4:.2f}")
        self.logger.info(f"Total asks: {len(asks)}")
        self.logger.info(f"Total bids: {len(bids)}")

        data_entry = AssetDataEntry(
            mid_price=mid_price,
            best_bid=best_bid,
            best_ask=best_ask,
            total_ask_1=ask_d1,
            total_ask_4=ask_d4,
            total_bid_1=bid_d1,
            total_bid_4=bid_d4,
            book_bias_1=bb1,
            book_bias_4=bb4,
            last_book_update=datetime.fromtimestamp(ob.update_time / 1000),
            current_time=current_time
        )

        return data_entry
