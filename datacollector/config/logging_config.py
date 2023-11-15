# -*- coding: utf-8 -*-
import logging.config
import json


def setup_logging(symbol: str):
    with open('logging.json', 'r') as f:
        dict_config = json.load(f)
        dict_config['handlers']['file']['filename'] = f"data_{symbol}.log"
    logging.config.dictConfig(dict_config)
