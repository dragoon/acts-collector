import argparse
import asyncio
import logging

from datacollector.config.data_collector_config import get_data_collector_service
from datacollector.config.logging_config import setup_logging
from datacollector.services.collector_service import DataCollectorService


async def main(service: DataCollectorService):
    try:
        await service.collect_data()
    except asyncio.CancelledError:
        logger.info("Shutdown signal received, closing client and exiting...")
    except KeyboardInterrupt:
        logger.info("Program stopped by user.")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Binance asset data collector")
    parser.add_argument("-s", "--symbol", required=True, help="Instrument code to collect data for, must be USDT pair")
    args = parser.parse_args()

    symbol = args.symbol.lower()
    setup_logging(symbol)
    logger = logging.getLogger(__name__)
    s = get_data_collector_service(asset_symbol=symbol, dt=None)

    try:
        asyncio.run(main(s))
    except KeyboardInterrupt:
        logger.info("Program stopped by user.")
