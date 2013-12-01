from cbagent.collectors import Collector


class ActiveTasks(Collector):

    COLLECTOR = "active_tasks"

    def update_metadata(self):
        self.mc.add_cluster()
        for bucket in self.get_buckets():
            self.mc.add_bucket(bucket)

    def _get_tasks(self):
        tasks = {
            "bucket_compaction_progress": (0, None),
            "rebalance_progress": (0, None)
        }
        for task in self.get_http(path="/pools/default/tasks"):
            _task = "{0}_progress".format(task["type"])
            tasks[_task] = (task.get("progress", 0), task.get("bucket", None))
        for task, (progress, bucket) in tasks.items():
            yield task, progress, bucket

    def sample(self):
        for task, progress, bucket in self._get_tasks():
            self._update_metric_metadata(metric=task, bucket=bucket)
            self.store.append(data={task: progress},
                              cluster=self.cluster, bucket=bucket,
                              collector=self.COLLECTOR)
