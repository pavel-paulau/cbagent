from fabric.api import run

from cbagent.collectors.libstats.remotestats import (
    RemoteStats, multi_node_task)


class PSStats(RemoteStats):

    METRICS = (
        ("rss", 1024),    # kB -> B
        ("vsize", 1024),  # kB -> B
        ("cpu", 1)
    )

    def __init__(self, hosts, user, password):
        super(PSStats, self).__init__(hosts, user, password)
        self.cmd = "ps -eo rss,vsize,pcpu,cmd | " \
                   "grep {0} | grep -v grep | sort -n | tail -n 1"

    @multi_node_task
    def get_samples(self, process):
        samples = {}
        cmd = self.cmd.format(process)
        stdout = run(cmd)
        if stdout:
            for i, value in enumerate(stdout.split()[:len(self.METRICS)]):
                metric, multiplier = self.METRICS[i]
                title = "{0}_{1}".format(process, metric)
                samples[title] = float(value) * multiplier
        return samples
