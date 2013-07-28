from time import time, sleep
from uuid import uuid4

from couchbase import Couchbase
from couchbase.user_constants import OBS_PERSISTED


from cbagent.collectors import Latency

uhex = lambda: uuid4().hex


class XdcrLag(Latency):

    COLLECTOR = "xdcr_lag"

    METRICS = ("xdcr_lag", "xdcr_persistence_time", "xdcr_diff")

    def __init__(self, settings):
        super(Latency, self).__init__(settings)
        self.clients = []
        for bucket in self.get_buckets():
            src_client = Couchbase.connect(
                bucket=bucket,
                host=settings.master_node,
                username=settings.rest_username,
                password=settings.rest_password,
                quiet=True,
            )
            dst_client = Couchbase.connect(
                bucket=bucket,
                host=settings.dest_master_node,
                username=settings.rest_username,
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
