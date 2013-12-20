from cbagent.collectors.libstats.psstats import PSStats
from cbagent.collectors import Collector


class PS(Collector):

    COLLECTOR = "atop"  # Legacy

    KNOWN_PROCESSES = ("beam.smp", "memcached", "sync_gateway")

    def __init__(self, settings):
        super(PS, self).__init__(settings)
        self.ssh_username = settings.ssh_username
        self.ssh_password = settings.ssh_password
        self.nodes = list(self.get_nodes())
        if hasattr(settings, "sync_gateway_nodes") and settings.sync_gateway_nodes:
            self.nodes += settings.sync_gateway_nodes
        self.ps = PSStats(hosts=self.nodes,
                          user=settings.ssh_username,
                          password=settings.ssh_password)

    def update_metadata(self):
        self.mc.add_cluster()
        for node in self.nodes:
            self.mc.add_server(node)

    def sample(self):
        for process in self.KNOWN_PROCESSES:
            for node, stats in self.ps.get_samples(process).items():
                if stats:
                    self.update_metric_metadata(stats.keys(), server=node)
                    self.store.append(stats,
                                      cluster=self.cluster, server=node,
                                      collector=self.COLLECTOR)
