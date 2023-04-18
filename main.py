import asyncio
import time

from binance import DepthCacheManager, AsyncClient


async def main():
    client = await AsyncClient.create()
    dcm = DepthCacheManager(client, 'BTCUSDT', refresh_interval=60*60, ws_interval=100)

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
                max_price = mid_price * 1.04
                min_price = mid_price * 0.96
                total_ask_quantity = sum(ask[1] for ask in asks if max_price >= ask[0] >= min_price)
                total_bid_quantity = sum(bid[1] for bid in bids if max_price >= bid[0] >= min_price)

                # Compute the book bias
                book_bias = (total_bid_quantity - total_ask_quantity) / (total_bid_quantity + total_ask_quantity)
                print("book bias:", book_bias)
                print("last update time {}".format(ob.update_time))

                # Reset the start time
                start_time = current_time

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    asyncio.run(main())
