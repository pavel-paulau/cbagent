import requests
from decorator import decorator
from logger import logger


class InternalServerError(Exception):

    def __init__(self, url):
        self.url = url

    def __str__(self):
        return "Internal server error: {0}".format(self.url)


@decorator
def interrupt(request, *args, **kargs):
    try:
        return request(*args, **kargs)
    except (requests.ConnectionError, InternalServerError) as e:
        logger.interrupt(e)


class RestClient(object):

    @interrupt
    def post(self, url, data):
        r = requests.post(url=url, data=data)
        if r.status_code == 500:
            raise InternalServerError(url)

    @interrupt
    def get(self, url, params):
        r = requests.get(url=url, params=params)
        if r.status_code == 500:
            raise InternalServerError(url)
        return r.json()


class MetadataClient(RestClient):

    def __init__(self, settings):
        self.settings = settings
        self.base_url = "http://{0}/cbmonitor".format(
            settings.cbmonitor_host_port)

    def get_clusters(self):
        url = self.base_url + "/get_clusters/"
        return self.get(url, {})

    def get_servers(self):
        url = self.base_url + "/get_servers/"
        params = {"cluster": self.settings.cluster}
        return self.get(url, params)

    def get_buckets(self):
        url = self.base_url + "/get_buckets/"
        params = {"cluster": self.settings.cluster}
        return self.get(url, params)

    def add_cluster(self):
        if self.settings.cluster in self.get_clusters():
            return

        url = self.base_url + "/add_cluster/"
        data = {"name": self.settings.cluster,
                "rest_username": self.settings.rest_username,
                "rest_password": self.settings.rest_password}

        logger.info("Adding cluster: {0}".format(self.settings.cluster))
        self.post(url, data)

    def add_server(self, address):
        if address in self.get_servers():
            return

        url = self.base_url + "/add_server/"
        data = {"address": address,
                "cluster": self.settings.cluster,
                "ssh_username": self.settings.ssh_username,
                "ssh_password": self.settings.ssh_password}

        logger.info("Adding server: {0}".format(address))
        self.post(url, data)

    def add_bucket(self, name):
        if name in self.get_buckets():
            return

        logger.info("Adding bucket: {0}".format(name))

        url = self.base_url + "/add_bucket/"
        data = {"name": name, "type": "Couchbase",
                "cluster": self.settings.cluster}
        self.post(url, data)

    def add_metric(self, name, bucket=None, server=None, unit=None,
                   description=None, collector=None):
        logger.debug("Adding metric: {0}".format(name))

        url = self.base_url + "/add_metric_or_event/"
        data = {"name": name, "type": "metric",
                "cluster": self.settings.cluster}
        for extra_param in ("bucket", "server", "unit", "description",
                            "collector"):
            if eval(extra_param) is not None:
                data[extra_param] = eval(extra_param)
        self.post(url, data)

    def add_snapshot(self, name, ts_from, ts_to):
        logger.info("Adding snapshot: {0}".format(name))

        url = self.base_url + "/add_snapshot/"
        data = {"cluster": self.settings.cluster, "name": name,
                "ts_from": ts_from, "ts_to": ts_to}
        self.post(url, data)
