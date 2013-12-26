from fabric.api import run

from cbagent.collectors.libstats.remotestats import (
    RemoteStats, multi_node_task)


class PSStats(RemoteStats):

    METRICS = (
        ("rss", 1024),    # kB -> B
        ("vsize", 1024),
    )

    def __init__(self, hosts, user, password):
        super(PSStats, self).__init__(hosts, user, password)
        self.ps_cmd = "ps -eo pid,rss,vsize,cmd | " \
                      "grep {} | grep -v grep | sort -n -k 2 | tail -n 1"
        self.top_cmd = "top -bn2d1 -p {} | grep {}"

    @multi_node_task
    def get_samples(self, process):
        samples = {}
        stdout = run(self.ps_cmd.format(process))
        if stdout:
            for i, value in enumerate(stdout.split()[1:1+len(self.METRICS)]):
                metric, multiplier = self.METRICS[i]
                title = "{}_{}".format(process, metric)
                samples[title] = float(value) * multiplier
            pid = stdout.split()[0]
        else:
            return samples
        stdout = run(self.top_cmd.format(pid, process))
        if stdout:
            title = "{}_cpu".format(process)
            samples[title] = float(stdout.split()[8])
        return samples
