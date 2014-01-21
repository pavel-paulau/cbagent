import json
import os
from argparse import ArgumentParser

from logger import logger


class Settings(object):

    DEFAULT = {
        "cbmonitor_host_port": "127.0.0.1:8000",
        "seriesly_host": "127.0.0.1",

        "interval": 10,

        "cluster": "default",
        "master_node": "127.0.0.1",
        "dest_master_node": "127.0.0.1",
        "rest_username": "Administrator",
        "rest_password": "password",
        "ssh_username": "root",
        "ssh_password": "couchbase",
        "partitions": {},

        "buckets": None,
        "hostnames": None
    }

    def __init__(self, options={}):
        for option, value in dict(self.DEFAULT, **options).items():
            setattr(self, option, value)

    def read_cfg(self):
        parser = ArgumentParser()
        parser.add_argument("config", help="name of configuration file")
        args = parser.parse_args()

        if not os.path.isfile(args.config):
            logger.interrupt("File doesn\'t exist: {}".format(args.config))

        logger.info("Reading configuration file: {}".format(args.config))
        with open(args.config) as fh:
            try:
                for option, value in json.load(fh).items():
                    setattr(self, option, value)
            except ValueError as e:
                logger.interrupt("Error reading config: {}".format(e))
            else:
                logger.info("Configuration file successfully parsed")
