import asyncio
import time
from functools import partial

from binance import DepthCacheManager, AsyncClient


def compute_bb(asks: list, bids: list, mid_price: float, percent: int):
    max_price = mid_price * (1 + percent)
    min_price = mid_price * (1 - percent)
    total_ask_quantity = sum(ask[1] for ask in asks if max_price >= ask[0] >= min_price)
    total_bid_quantity = sum(bid[1] for bid in bids if max_price >= bid[0] >= min_price)

    # Compute the book bias
    book_bias = (total_bid_quantity - total_ask_quantity) / (total_bid_quantity + total_ask_quantity)
    return book_bias


compute_bb05 = partial(compute_bb, percent=0.005)
compute_bb1 = partial(compute_bb, percent=0.01)
compute_bb2 = partial(compute_bb, percent=0.02)
compute_bb4 = partial(compute_bb, percent=0.04)


async def main():
    client = await AsyncClient.create()
    dcm = DepthCacheManager(client, limit=5000, symbol='BTCUSDT', refresh_interval=60*60, ws_interval=100)

    async with dcm as dcm_socket:
        start_time = time.time()
        while True:
            ob = await dcm_socket.recv()
            current_time = time.time()

            if current_time - start_time >= 1 * 60:
                # Get the asks and bids
                asks = ob.get_asks()
                bids = ob.get_bids()
                mid_price = (asks[0][0] + bids[0][0]) / 2

                print("book bias 05:", compute_bb05(asks, bids, mid_price))
                print("book bias 1:", compute_bb1(asks, bids, mid_price))
                print("book bias 2:", compute_bb2(asks, bids, mid_price))
                print("book bias 4:", compute_bb4(asks, bids, mid_price))
                print("last update time {}".format(ob.update_time))

                # Reset the start time
                start_time = current_time

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    asyncio.run(main())
