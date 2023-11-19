import decimal
from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal

from bson.decimal128 import create_decimal128_context, Decimal128


@dataclass(frozen=True)
class AssetDataEntry:
    mid_price: Decimal
    best_bid: Decimal
    best_ask: Decimal
    total_ask: int
    total_bid: int
    total_ask_1: int
    total_ask_4: int
    total_bid_1: int
    total_bid_4: int
    book_bias_1: float
    book_bias_4: float
    last_book_update: datetime
    current_time: datetime

    def to_dict(self) -> dict:
        # Convert the data class to a dictionary
        data = asdict(self)

        # Convert Decimal fields to MongoDB's Decimal128
        for field in ['mid_price', 'best_bid', 'best_ask']:
            if field in data:
                decimal128_ctx = create_decimal128_context()
                with decimal.localcontext(decimal128_ctx) as ctx:
                    data[field] = Decimal128(ctx.create_decimal(data[field]))

        return data
