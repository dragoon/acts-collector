# Automated Crypto Trading System (ACTS)

In the last couple of years, I have built and maintained an automated trading system for a hedge fund that traded
Futures contracts on major stock exchanges around the world. While I can’t share the details of this trading system
publicly, I would like to use these series of article to demonstrate how to build an automated trading system from
scratch for crypto assets.

Here is a high-level overview of what we are going to cover:

1. Data Collection platform
2. Signal generation
3. Backtesting & reporting
4. Unit and integration testing
5. Live trading

## Data collection platform

We are going to setup data collection platform from a single exchange,
in real system you probably would like to collect data from multiple exchanges
and merge/aggregate them somehow depending on the trading strategy you are implementing.

In these series, I am going to collect data from the [Binance exchange](https://www.binance.com/en),
as it is the largest global crypto exchange, and offers excellent data collection APIs.

### Order book

An order book is a fundamental concept in financial trading,
representing a list of buy and sell orders for a specific financial instrument,
like a stock, currency, or cryptocurrency.

The key components of an order book are bids and asks.
A "bid" is an offer to buy a financial instrument at a specific price.
It represents the highest price a buyer is willing to pay.
For example, if someone wants to buy Bitcoin, they place a bid at the price they're willing to pay.
On the other side, an "ask" is an offer to sell at a specific price.
It represents the lowest price a seller is willing to accept.
So, if someone wants to sell their Bitcoin, they place an ask at their desired price.

The difference between the highest bid and the lowest ask is known as the "spread."
A smaller spread often indicates a more liquid market, meaning there are many buyers and sellers,
and it's easier to execute a trade at a price close to the market value.
The order book provides valuable insight into the supply and demand
at different price levels and helps traders make informed decisions.
For instance, a large number of bids at a particular price level might indicate strong support for that price, while a significant number of asks might suggest a resistance level.

### Data types

Now let’s define the data we would like to collect:

- **Prices**. Any sort of strategy would probably need actual asset prices, so we need to collect at least best bid (
  highest buy) and best ask (lowest sell) prices
- **Order book (derivatives)**. This data type largely depends on a specific trading
  strategy, but a lot of advanced strategies use values like
  the **order book bias** at different levels, **amount of bid/asks**, etc. So this is what we are also going to
  collect.
- If you have a lot of resources, you might even want to replicate the complete
  order book and store all events, so that you can compute
  any order book feature you didn't think of initially.

### Requirements.

Let's define requirements for our data collection pipeline
that will guide our implementation:

- **Multi-assets**: The system should easily handle multiple assets and allow to add new assets easily.
- **Resilience**: Crypto exchanges work non-stop, so we want our system to
  run 24/7 and be resilient for any sort of errors (network, binance api errors, etc.).
- **Data Frequency**: We are going to collect data in minute intervals.
- **Testability**: We want our code to be testable with unit tests.

Out of scope:
- **Data center resilience**: what to do if the server(s) running your data collection pipelines failed.
There are a lot of possible solutions to this topic, the simplest would be to have multiple systems
write to different databases and merge data when needed. In any case, these solutions do not require code modifications, so I leave it out of scope.

### Technology Stack.

- **Implementation language**: I am going to use _Python_ for its simplicity and ubiquity.
  I think it’s also okay to use Python in production for data collection parts of the system when the volume if not too
  large.
- **Data storage**: I will use MongoDB here for the same reasons -- simplicity and ubiquity. For production, I would
  also consider specialized Time Series databases like _InfluxDB_, _TimescaleDB_ (Postgres extension), or even
  _ClickHouse_ for large volumes, especially if you are going to store all order book events.
- **Data APIs**: Binance
  offers [websocket-based APIs](https://developers.binance.com/docs/binance-trading-api/websocket_api) that can be used
  to replicate order book and maintain your own copy in memory.
  I will additionally use a python wrapper library [python-binance](https://github.com/sammchardy/python-binance) to
  access order book data as it already implements high-level interface to access the order book.

Out of scope:
- **Deployment**: I leave the deployment process out of scope here,
nonetheless the process should obviously be fully automated with CI/CD pipeline
pushing updates to DEV/TEST/PROD environments according to a defined process.

### Initial implementation

I wrote the initial implementation of data collection pipeline in
under a couple of hours. Here is a condensed version:
```python
import asyncio
from datetime import datetime

from binance import DepthCacheManager, AsyncClient

async def main(symbol):
    client = await AsyncClient.create()
    dcm = DepthCacheManager(client, limit=5000, symbol=f'{symbol.upper()}USDT',
                            refresh_interval=None, ws_interval=100)

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

                # Insert the book biases and mid-price into MongoDB
                book_bias_data = {
                    "mid_price": mid_price,
                    "best_bid": bids[0][0],
                    "best_ask": asks[0][0],
                    "last_book_update": datetime.fromtimestamp(ob.update_time/1000),
                    "current_time": current_time
                }
                data_collection.insert_one(book_bias_data)

                # Update the last stored minute
                last_stored_minute = current_minute

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    asyncio.run(main("BTC"))

```
Full initial version is available with tag https://github.com/FarawayTech/faraway-finance/tree/v0.1.0-beta
This very is super short, fits into a single python file, but lacks one important requirement that we defined: this code is completely untestable.

To make it testable, we need to split the implementation in several modules for business logic, data access, etc.,
that we can unit test independently, and mock in higher-level services.
This is a typical domain-driven design (DDD) that I have used successfully in many other projects.

### Testable implementation

Here is our new structure