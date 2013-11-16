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
    def post(self, url, params):
        r = requests.post(url, params)
        if r.status_code == 500:
            raise InternalServerError(url)

    @interrupt
    def get(self, url):
        r = requests.get(url)
        if r.status_code == 500:
            raise InternalServerError(url)
        return r.json()


class MetadataClient(RestClient):

    def __init__(self, settings):
        self.settings = settings
        self.base_url = "http://{0}/cbmonitor".format(
            settings.cbmonitor_host_port)

    def add_cluster(self):
        logger.info("Adding cluster: {0}".format(self.settings.cluster))

        url = self.base_url + "/add_cluster/"
        params = {"name": self.settings.cluster,
                  "rest_username": self.settings.rest_username,
                  "rest_password": self.settings.rest_password}
        self.post(url, params)

    def add_server(self, address):
        logger.info("Adding server: {0}".format(address))

        url = self.base_url + "/add_server/"
        params = {"address": address,
                  "cluster": self.settings.cluster,
                  "ssh_username": self.settings.ssh_username,
                  "ssh_password": self.settings.ssh_password}
        self.post(url, params)

    def add_bucket(self, name):
        logger.info("Adding bucket: {0}".format(name))

        url = self.base_url + "/add_bucket/"
        params = {"name": name, "type": "Couchbase",
                  "cluster": self.settings.cluster}
        self.post(url, params)

    def add_metric(self, name, bucket=None, server=None, unit=None,
                   description=None, collector=None):
        logger.debug("Adding metric: {0}".format(name))

        url = self.base_url + "/add_metric_or_event/"
        params = {"name": name, "type": "metric",
                  "cluster": self.settings.cluster}
        for extra_param in ("bucket", "server", "unit", "description",
                            "collector"):
            if eval(extra_param) is not None:
                params[extra_param] = eval(extra_param)
        self.post(url, params)

    def add_snapshot(self, name, ts_from, ts_to):
        logger.info("Adding snapshot: {0}".format(name))

        url = self.base_url + "/add_snapshot/"
        params = {"cluster": self.settings.cluster, "name": name,
                  "ts_from": ts_from, "ts_to": ts_to}
        self.post(url, params)
