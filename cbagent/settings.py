from argparse import ArgumentParser
from ConfigParser import ConfigParser, NoOptionError

from logger import logger


class DefaultSettings(dict):

    def __init__(self):
        self.cbmonitor_host_port = "127.0.0.1:8000"

        self.interval = 10
        self.seriesly_host = "127.0.0.1"

        self.cluster = "default"
        self.master_node = "127.0.0.1"
        self.dest_master_node = None
        self.sync_gateway_nodes = None
        self.rest_username = "Administrator"
        self.rest_password = "password"
        self.ssh_username = "root"
        self.ssh_password = "couchbase"
        self.partitions = {}


class Settings(DefaultSettings):

    def __init__(self, options={}):
        super(Settings, self).__init__()
        for option, value in options.iteritems():
            setattr(self, option, value)

    def read_cfg(self):
        parser = ArgumentParser()
        parser.add_argument("config", help="name of configuration file")
        args = parser.parse_args()

        config = ConfigParser()
        try:
            logger.info("Reading configuration file: {}".format(args.config))
            config.read(args.config)
            logger.info("Configuration file successfully parsed")
        except Exception as e:
            logger.interrupt("Failed to parse config file: {}".format(e))
        try:
            self.cbmonitor_host_port = config.get("cbmonitor", "host_port")

            self.interval = config.getint("store", "interval")
            self.seriesly_host = config.get("store", "host")

            self.cluster = config.get("target", "cluster")
            self.master_node = config.get("target", "master_node")
            self.rest_username = config.get("target", "rest_username")
            self.rest_password = config.get("target", "rest_password")
            self.ssh_username = config.get("target", "ssh_username")
            self.ssh_password = config.get("target", "ssh_password")
        except NoOptionError as e:
            logger.interrupt("Failed to get option from config: {}".format(e))
        try:
            self.dest_master_node = config.get("target", "dest_master_node")
        except NoOptionError:
            pass
        try:
            self.sync_gateway_nodes = config.get("target",
                                                 "sync_gateway_nodes").split()
        except NoOptionError:
            pass

        logger.info("Configuration file successfully applied")

    def __getitem__(self, item):
        return getattr(self, item, None)
