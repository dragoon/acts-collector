import argparse
import asyncio
import logging
from datetime import datetime
from functools import partial

from binance import DepthCacheManager, AsyncClient
from pymongo import MongoClient
from pymongo.server_api import ServerApi

from settings import MONGO_URI, configure_logging


parser = argparse.ArgumentParser(description="Binance order book collector")
parser.add_argument("-s", "--symbol", required=True, help="Instrument code to collect data for, must be USDT pair")
args = parser.parse_args()

symbol = args.symbol.lower()
configure_logging(symbol)

mongo_client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = mongo_client["faraway_finance"]
book_bias_collection = db[f"{symbol}_data"]

logger = logging.getLogger(__name__)


def compute_bb(asks: list, bids: list, mid_price: float, percent: int):
    max_price = mid_price * (1 + percent)
    min_price = mid_price * (1 - percent)
    total_ask_quantity = sum(ask[1] for ask in asks if max_price >= ask[0] >= min_price)
    total_bid_quantity = sum(bid[1] for bid in bids if max_price >= bid[0] >= min_price)

    # Compute the book bias
    book_bias = (total_bid_quantity - total_ask_quantity) / (total_bid_quantity + total_ask_quantity)
    return total_ask_quantity, total_bid_quantity, book_bias


compute_bb05 = partial(compute_bb, percent=0.005)
compute_bb1 = partial(compute_bb, percent=0.01)
compute_bb2 = partial(compute_bb, percent=0.02)
compute_bb4 = partial(compute_bb, percent=0.04)


async def main():
    client = await AsyncClient.create()
    dcm = DepthCacheManager(client, limit=5000, symbol=f'{symbol.upper()}USDT', refresh_interval=None, ws_interval=100)
    logger.info(f"Starting order book collection for {symbol}-USDT")

    async with dcm as dcm_socket:
        last_stored_minute = None
        while True:
            ob = await dcm_socket.recv()
            current_time = datetime.utcnow()

            current_minute = current_time.minute
            if current_minute != last_stored_minute:
                # Get the asks and bids
                asks = ob.get_asks()
                bids = ob.get_bids()
                mid_price = (asks[0][0] + bids[0][0]) / 2

                ask_d05, bid_d05, bb05 = compute_bb05(asks, bids, mid_price)
                ask_d1, bid_d1, bb1 = compute_bb1(asks, bids, mid_price)
                ask_d2, bid_d2, bb2 = compute_bb2(asks, bids, mid_price)
                ask_d4, bid_d4, bb4 = compute_bb4(asks, bids, mid_price)
                logger.info(f"BB4 at {current_time}: {bb4:.2f}")
                logger.info(f"Total asks: {len(asks)}")
                logger.info(f"Total bids: {len(bids)}")

                # Insert the book biases and mid-price into MongoDB
                book_bias_data = {
                    "mid_price": mid_price,
                    "best_bid": bids[0][0],
                    "best_ask": asks[0][0],
                    "total_ask_05": ask_d05,
                    "total_ask_1": ask_d1,
                    "total_ask_2": ask_d2,
                    "total_ask_4": ask_d4,
                    "total_bid_05": bid_d05,
                    "total_bid_1": bid_d1,
                    "total_bid_2": bid_d2,
                    "total_bid_4": bid_d4,
                    "book_bias_05": bb05,
                    "book_bias_1": bb1,
                    "book_bias_2": bb2,
                    "book_bias_4": bb4,
                    "last_book_update": datetime.fromtimestamp(ob.update_time/1000),
                    "current_time": current_time
                }
                book_bias_collection.insert_one(book_bias_data)

                # Update the last stored minute
                last_stored_minute = current_minute

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    asyncio.run(main())
