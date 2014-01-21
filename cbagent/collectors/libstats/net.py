from collections import defaultdict

from fabric.api import run

from cbagent.collectors.libstats.remotestats import (RemoteStats,
                                                     multi_node_task)


class NetStat(RemoteStats):

    @staticmethod
    def get_dev_stats():
        cmd = "grep eth0 /proc/net/dev"
        stdout = run("{0}; sleep 1; {0}".format(cmd))
        s1, s2 = stdout.split('\n')
        s1 = [int(v.split(":")[-1]) for v in s1.split()]
        s2 = [int(v.split(":")[-1]) for v in s2.split()]
        return {
            "total_bytes_per_sec": s2[1] + s2[9] - s1[1] - s1[9],
            "total_packets_per_sec": s2[2] + s2[10] - s1[2] - s1[10],
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
