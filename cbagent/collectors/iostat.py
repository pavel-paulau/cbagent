from cbagent.collectors.libstats.iostat import IOstat
from cbagent.collectors import Collector


class IO(Collector):

    COLLECTOR = "iostat"

    def __init__(self, settings):
        super(IO, self).__init__(settings)
        self.ssh_username = settings.ssh_username
        self.ssh_password = settings.ssh_password
        self.nodes = list(self.get_nodes())
        self.io = IOstat(hosts=self.nodes,
                         user=settings.ssh_username,
                         password=settings.ssh_password)
        self.partitions = settings.partitions

    def update_metadata(self):
        self.mc.add_cluster()
        for node in self.nodes:
            self.mc.add_server(node)

    def sample(self):
        for node, stats in self.io.get_samples(self.partitions).items():
            if stats:
                self.update_metric_metadata(stats.keys(), server=node)
                self.store.append(stats,
                                  cluster=self.cluster, server=node,
                                  collector=self.COLLECTOR)
