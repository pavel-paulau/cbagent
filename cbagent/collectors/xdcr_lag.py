import sys
from time import time, sleep
from threading import Thread
from uuid import uuid4

from couchbase.user_constants import OBS_PERSISTED
from logger import logger

from cbagent.collectors import Latency
from cbagent.collectors.libstats.pool import Pool

uhex = lambda: uuid4().hex


class XdcrLag(Latency):

    COLLECTOR = "xdcr_lag"

    METRICS = ("xdcr_lag", "xdcr_persistence_time", "xdcr_diff")

    NUM_THREADS = 10

    def __init__(self, settings):
        super(Latency, self).__init__(settings)

        self.pools = []
        for bucket in self.get_buckets():
            src_pool = Pool(
                bucket=bucket,
                host=settings.master_node,
                username=bucket,
                password=settings.rest_password,
                quiet=True,
            )
            dst_pool = Pool(
                bucket=bucket,
                host=settings.dest_master_node,
                username=bucket,
                password=settings.rest_password,
                quiet=True,
                unlock_gil=False,
            )
            self.pools.append((bucket, src_pool, dst_pool))

    @staticmethod
    def _measure_lags(src_pool, dst_pool):
        src_client = src_pool.get_client()
        dst_client = dst_pool.get_client()

        key = "xdcr_track_{}".format(uhex())

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

        src_pool.release_client(src_client)
        dst_pool.release_client(dst_client)

        return {
            "xdcr_lag": (t2 - t0) * 1000,
            "xdcr_persistence_time": (t1 - t0) * 1000,
            "xdcr_diff": (t2 - t1) * 1000,
        }

    def sample(self):
        while True:
            try:
                for bucket, src_pool, dst_pool in self.pools:
                    lags = self._measure_lags(src_pool, dst_pool)
                    self.store.append(lags,
                                      cluster=self.cluster,
                                      bucket=bucket,
                                      collector=self.COLLECTOR)
            except Exception as e:
                logger.warn(e)

    def collect(self):
        threads = [Thread(target=self.sample) for x in range(self.NUM_THREADS)]
        map(lambda t: t.start(), threads)
        map(lambda t: t.join(), threads)
