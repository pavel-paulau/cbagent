import socket
import sys
import time

import requests
from logger import logger

from cbagent.stores import SerieslyStore
from cbagent.metadata_client import MetadataClient


class Collector(object):

    def __init__(self, settings):
        self.cluster = settings.cluster
        self.master_node = settings.master_node
        self.auth = (settings.rest_username, settings.rest_password)
        self.nodes = list(self._get_nodes())

        self.interval = settings.interval

        self.store = SerieslyStore(settings.seriesly_host)
        self.mc = MetadataClient(settings)

    def _get(self, path, server=None, port=8091):
        """HTTP GET request to Couchbase server with basic authentication"""
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
        for node in self.nodes:
            if self._check_node(node):
                self.master_mode = node
                self.nodes = list(self._get_nodes())
                break
        else:
            logger.interrupt("Failed to find at least one node")
        return self._get(*arg, **kwargs)

    def _check_node(self, node):
        try:
            s = socket.socket()
            s.connect((node, 8091))
        except socket.error:
            return False
        else:
            if not self._get(path="/pools", server=node).get("pools"):
                return False
        return True

    def _get_buckets(self):
        """Yield bucket names"""
        buckets = self._get("/pools/default/buckets")
        for bucket in buckets:
            yield bucket["name"]

    def _get_nodes(self):
        """Yield name of nodes in cluster"""
        pool = self._get("/pools/default")
        for node in pool["nodes"]:
            yield node["hostname"].split(":")[0]

    def update_metadata(self):
        raise NotImplementedError

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
