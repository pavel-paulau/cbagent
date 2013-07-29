import socket
import sys
import time

import requests
from logger import logger

from cbagent.stores import SerieslyStore
from cbagent.metadata_client import MetadataClient


class Collector(object):

    def __init__(self, settings):
        self.interval = settings.interval

        self.cluster = settings.cluster
        self.master_node = settings.master_node
        self.auth = (settings.rest_username, settings.rest_password)
        self.nodes = list(self.get_nodes())

        self.store = SerieslyStore(settings.seriesly_host)
        self.mc = MetadataClient(settings)

    def get_http(self, path, server=None, port=8091):
        url = "http://{0}:{1}{2}".format(server or self.master_node, port, path)
        try:
            r = requests.get(url=url, auth=self.auth)
            if r.status_code in (200, 201, 202):
                return r.json()
            else:
                return self.retry(path, server, port)
        except requests.exceptions.ConnectionError:
            return self.retry(path, server, port)

    def retry(self, *arg, **kwargs):
        time.sleep(self.interval)
        for node in self.nodes:
            if self._check_node(node):
                self.master_node = node
                self.nodes = list(self.get_nodes())
                break
        else:
            logger.interrupt("Failed to find at least one node")
        return self.get_http(*arg, **kwargs)

    def _check_node(self, node):
        try:
            s = socket.socket()
            s.connect((node, 8091))
        except socket.error:
            return False
        else:
            if not self.get_http(path="/pools", server=node).get("pools"):
                return False
        return True

    def get_buckets(self, with_stats=False):
        buckets = self.get_http(path="/pools/default/buckets")
        if not buckets:
            buckets = self.retry(path="/pools/default/buckets")
        for bucket in buckets:
            if with_stats:
                yield bucket["name"], bucket["stats"]
            else:
                yield bucket["name"]

    def get_nodes(self):
        pool = self.get_http(path="/pools/default")
        for node in pool["nodes"]:
            yield node["hostname"].split(":")[0]

    def sample(self):
        raise NotImplementedError

    def collect(self):
        while True:
            try:
                self.sample()
                time.sleep(self.interval)
            except KeyboardInterrupt:
                sys.exit()
            except Exception as e:
                logger.warn(e)
