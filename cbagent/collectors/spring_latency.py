from time import time

from spring.docgen import ExistingKey, NewDocument, NewNestedDocument
from spring.querygen import NewQuery, NewQueryNG, NewN1QLQuery
from spring.cbgen import CBGen, N1QLGen

from cbagent.collectors import Latency


class SpringLatency(Latency):

    COLLECTOR = "spring_latency"

    METRICS = ("latency_set", "latency_get")

    def __init__(self, settings, workload, prefix=None):
        super(Latency, self).__init__(settings)
        self.clients = []
        for bucket in self.get_buckets():
            client = CBGen(bucket=bucket, host=settings.master_node,
                           username=bucket, password=settings.bucket_password)
            self.clients.append((bucket, client))

        self.existing_keys = ExistingKey(workload.working_set,
                                         workload.working_set_access,
                                         prefix=prefix)
        if not hasattr(workload, 'doc_gen') or workload.doc_gen == 'old':
            self.new_docs = NewDocument(workload.size)
        else:
            self.new_docs = NewNestedDocument(workload.size)
        self.items = workload.items

    def measure(self, client, metric):
        key = self.existing_keys.next(curr_items=self.items, curr_deletes=0)
        doc = self.new_docs.next(key)

        t0 = time()
        if metric == "latency_set":
            client.create(key, doc)
        elif metric == "latency_get":
            client.read(key)
        elif metric == "latency_cas":
            client.cas(key, doc)
        return 1000 * (time() - t0)  # Latency in ms

    def sample(self):
        for bucket, client in self.clients:
            samples = {}
            for metric in self.METRICS:
                samples[metric] = self.measure(client, metric)
            self.store.append(samples, cluster=self.cluster,
                              bucket=bucket, collector=self.COLLECTOR)


class SpringCasLatency(SpringLatency):

    METRICS = ("latency_set", "latency_get", "latency_cas")


class SpringQueryLatency(SpringLatency):

    COLLECTOR = "spring_query_latency"

    METRICS = ("latency_query", )

    def __init__(self, settings, workload, ddocs, params, index_type,
                 prefix=None):
        super(SpringQueryLatency, self).__init__(settings, workload, prefix)
        if index_type is None:
            self.new_queries = NewQuery(ddocs, params)
        else:
            self.new_queries = NewQueryNG(index_type, params)

    def measure(self, client, metric):
        key = self.existing_keys.next(curr_items=self.items, curr_deletes=0)
        doc = self.new_docs.next(key)
        ddoc_name, view_name, query = self.new_queries.next(doc)

        _, latency = client.query(ddoc_name, view_name, query=query)
        return 1000 * latency  # s -> ms


class SpringN1QLQueryLatency(SpringQueryLatency):

    def __init__(self, settings, workload, index_type, prefix=None):
        super(SpringQueryLatency, self).__init__(settings, workload, prefix)
        self.clients = []
        for bucket in self.get_buckets():
            client = N1QLGen(bucket=bucket, host=settings.master_node,
                             username=bucket, password=settings.bucket_password)
            self.clients.append((bucket, client))

        self.new_queries = NewN1QLQuery(index_type)
