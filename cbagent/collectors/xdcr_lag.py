import sys
from Queue import Queue, Empty
from time import time, sleep
from threading import Thread
from uuid import uuid4

from couchbase import Couchbase
from couchbase.user_constants import OBS_PERSISTED
from logger import logger

from cbagent.collectors import Latency

uhex = lambda: uuid4().hex


class XdcrLag(Latency):

    COLLECTOR = "xdcr_lag"

    METRICS = ("xdcr_lag", "xdcr_persistence_time", "xdcr_diff")

    NUM_THREADS = 10

    def __init__(self, settings):
        super(Latency, self).__init__(settings)

        self.clients = []
        for bucket in self.get_buckets():
            src_client = Couchbase.connect(
                bucket=bucket,
                host=settings.master_node,
                username=bucket,
                password=settings.rest_password,
                quiet=True,
            )
            dst_client = Couchbase.connect(
                bucket=bucket,
                host=settings.dest_master_node,
                username=bucket,
                password=settings.rest_password,
                quiet=True,
            )
            self.clients.append((src_client, dst_client))

    def _measure_lags(self, src_client, dst_client):
        key = "xdcr_track_{0}".format(uhex())

        t0 = time()
        src_client.set(key, key)
        while True:
            r = src_client.observe(key)
            if r.value[0].flags == OBS_PERSISTED:
                break
            else:
                sleep(0.05)
        t1 = time()
        while True:
            r = dst_client.get(key)
            if r.value:
                break
            else:
                sleep(0.05)
        t2 = time()

        src_client.delete(key)

        return {
            "xdcr_lag": (t2 - t0) * 1000,
            "xdcr_persistence_time": (t1 - t0) * 1000,
            "xdcr_diff": (t2 - t1) * 1000,
        }

    def sample(self):
        for src_client, dst_client in self.clients:
            lags = self._measure_lags(src_client, dst_client)
            self.store.append(lags, cluster=self.cluster,
                              bucket=src_client.bucket,
                              collector=self.COLLECTOR)

    def _collect(self):
        while True:
            try:
                self.sample()
            except Exception as e:
                logger.warn(e)
            try:
                self.queue.get(timeout=1)
            except Empty:
                return

    def collect(self):
        self.queue = Queue(maxsize=self.NUM_THREADS)
        map(lambda _: self.queue.put(None), range(self.NUM_THREADS))

        for _ in range(self.NUM_THREADS):
            Thread(target=self._collect).start()

        while True:
            try:
                if not self.queue.full():
                    self.queue.put(None, block=True)
            except KeyboardInterrupt:
                sys.exit()
