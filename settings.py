# -*- coding: utf-8 -*-
"""Application configuration.
Most configuration is set via environment variables.
For local development, use a .env file to set
environment variables.
"""
import logging.config
import json

from environs import Env

with open('logging.json', 'r') as f:
    config_dict = json.load(f)
logging.config.dictConfig(config_dict)

env = Env()
env.read_env()

MONGO_URI = env.str("MONGO_URI")
