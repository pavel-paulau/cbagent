from collections import defaultdict

from fabric.api import run

from cbagent.collectors.libstats.remotestats import (RemoteStats,
                                                     multi_node_task,
                                                     single_node_task)


class NetStat(RemoteStats):

    def __init__(self, *args, **kwargs):
        super(NetStat, self).__init__(*args, **kwargs)
        self.iface = self.detect_iface()

    @single_node_task
    def detect_iface(self):
        for iface in ("eth0", "em1"):
            result = run("grep {} /proc/net/dev".format(iface),
                         warn_only=True, quiet=True)
            if not result.return_code:
                return iface

    def get_dev_stats(self):
        cmd = "grep {} /proc/net/dev".format(self.iface)
        stdout = run("{0}; sleep 1; {0}".format(cmd))
        s1, s2 = stdout.split('\n')
        s1 = [int(v.split(":")[-1]) for v in s1.split() if v.split(":")[-1]]
        s2 = [int(v.split(":")[-1]) for v in s2.split() if v.split(":")[-1]]
        return {
            "in_bytes_per_sec": s2[0] - s1[0],
            "out_bytes_per_sec": s2[8] - s1[8],
            "in_packets_per_sec": s2[1] - s1[1],
            "out_packets_per_sec": s2[9] - s1[9],
        }

    @staticmethod
    def get_tcp_stats():
        stdout = run("cat /proc/net/tcp")
        raw_data = defaultdict(int)
        for conn in stdout.split("\n"):
            state = conn.split()[3]
            raw_data[state] += 1
        return {
            "ESTABLISHED": raw_data["01"],
            "TIME_WAIT": raw_data["06"],
        }

    @multi_node_task
    def get_samples(self):
        dev_stats = self.get_dev_stats()
        tcp_stats = self.get_tcp_stats()
        return dict(dev_stats, **tcp_stats)
