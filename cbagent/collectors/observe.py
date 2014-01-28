from time import time, sleep
from threading import Thread
from uuid import uuid4

from couchbase.user_constants import OBS_PERSISTED
from logger import logger

from cbagent.collectors import Latency
from cbagent.collectors.libstats.pool import Pool

uhex = lambda: uuid4().hex


class ObserveLatency(Latency):

    COLLECTOR = "observe"

    METRICS = ("latency_observe", )

    NUM_THREADS = 10

    MAX_POLLING_INTERVAL = 1

    INITIAL_REQUEST_INTERVAL = 0.01

    MAX_REQUEST_INTERVAL = 2

    def __init__(self, settings):
        super(Latency, self).__init__(settings)

        self.pools = []
        for bucket in self.get_buckets():
            pool = Pool(
                bucket=bucket,
                host=settings.master_node,
                username=bucket,
                password=settings.rest_password,
                quiet=True,
            )
            self.pools.append((bucket, pool))

    def _measure_lags(self, pool):
        client = pool.get_client()

        key = uhex()

        req_interval = self.INITIAL_REQUEST_INTERVAL
        client.set(key, key)
        t0 = time()
        while True:
            r = client.observe(key)
            if r.value[0].flags == OBS_PERSISTED:
                break
            else:
                sleep(req_interval)
            req_interval = min(req_interval * 2, self.MAX_REQUEST_INTERVAL)
        t1 = time()
        latency = (t1 - t0) * 1000  # s -> ms
        sleep_time = max(0, self.MAX_POLLING_INTERVAL - (t1 - t0))

        client.delete(key)
        pool.release_client(client)
        return {"latency_observe": latency}, sleep_time

    def sample(self):
        while True:
            try:
                for bucket, pool in self.pools:
                    stats, sleep_time = self._measure_lags(pool)
                    self.store.append(stats,
                                      cluster=self.cluster,
                                      bucket=bucket,
                                      collector=self.COLLECTOR)
                    sleep(sleep_time)
            except Exception as e:
                logger.warn(e)

    def collect(self):
        threads = [Thread(target=self.sample) for _ in range(self.NUM_THREADS)]
        map(lambda t: t.start(), threads)
        map(lambda t: t.join(), threads)
