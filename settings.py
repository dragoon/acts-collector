# -*- coding: utf-8 -*-
"""Application configuration.
Most configuration is set via environment variables.
For local development, use a .env file to set
environment variables.
"""
import logging.config
import json

from environs import Env


def configure_logging(symbol: str):
    with open('logging.json', 'r') as f:
        config_dict = json.load(f)
        log_file_name = f"data_{symbol}.log"
        config_dict['handlers']['rotateFileHandler']['filename'] = log_file_name
    logging.config.dictConfig(config_dict)


env = Env()
env.read_env()

MONGO_URI = env.str("MONGO_URI")
