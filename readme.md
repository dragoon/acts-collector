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

[Order book structure description placeholder]

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

Let's define some requirements for our data collection pipeline
that will help us to focus on the right points during implementation (I'm mixing both technical and business
requirements here as there are not many):

- **Resilience**: Crypto exchanges work non-stop, so we want our system to
  run 24/7 and be resilient for any sort of errors (network, binance api errors, etc.).
- **Multi-assets**: The system should easily handle multiple assets and allow to add new assets easily.
- **Data Frequency**: We are going to collect our data points every minute.

One key point I'm not addressing here is data center / hardware resilience, e.g.,
what to do if the servers running your data collection pipeline are failing.
Is it okay to lose some data in case of such events? I leave this out of the scope,
but if any data loss is not acceptable,
a copy of the system needs to be setup in another region and
you need some sort of failover/event merging mechanism.

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

I leave deployment process out of scope here,
nonetheless I believe the process should be fully automated with CI/CD pipeline
setup to deploy updates to DEV/TEST/PROD environments according to the defined process.
I have seen people copy local builds to production for a live trading system.
**Do not ever do this!**
I usually setup my pipeline to deploy automatically to DEV and TEST, and then manual release to PROD.
