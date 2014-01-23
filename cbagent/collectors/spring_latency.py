from time import time

from spring.docgen import ExistingKey, NewDocument
from spring.querygen import NewQuery
from spring.cbgen import CBGen

from cbagent.collectors import Latency


class SpringLatency(Latency):

    COLLECTOR = "spring_latency"

    METRICS = ("latency_set", "latency_get")

    def __init__(self, settings, workload, prefix=None):
        super(Latency, self).__init__(settings)
        self.clients = []
        for bucket in self.get_buckets():
            client = CBGen(bucket=bucket, host=settings.master_node,
                           username=bucket, password=settings.rest_password)
            self.clients.append((bucket, client))

        self.existing_keys = ExistingKey(workload.working_set,
                                         workload.working_set_access,
                                         prefix=prefix)
        self.new_docs = NewDocument(workload.size)
        self.items = workload.items

    def measure(self, client, metric):
        key = self.existing_keys.next(curr_items=self.items, curr_deletes=0)
        doc = self.new_docs.next(key)

        t0 = time()
        if metric == "latency_set":
            client.create(key, doc)
        else:
            client.read(key)
        return 1000 * (time() - t0)  # Latency in ms

    def sample(self):
        for bucket, client in self.clients:
            samples = {}
            for metric in self.METRICS:
                samples[metric] = self.measure(client, metric)
            self.store.append(samples, cluster=self.cluster,
                              bucket=bucket, collector=self.COLLECTOR)


class SpringQueryLatency(SpringLatency):

    COLLECTOR = "spring_query_latency"

    METRICS = ("latency_query", )

    def __init__(self, settings, workload, ddocs, params, prefix=None):
        super(SpringQueryLatency, self).__init__(settings, workload, prefix)
        self.new_queries = NewQuery(ddocs, params)

    def measure(self, client, metric):
        key = self.existing_keys.next(curr_items=self.items, curr_deletes=0)
        doc = self.new_docs.next(key)
        ddoc_name, view_name, query = self.new_queries.next(doc)

        t0 = time()
        client.query(ddoc_name, view_name, query=query)
        return 1000 * (time() - t0)
