cbagent
-------

**cbagent** is stats collectors package for Couchbase Server monitoring. It does
not require installation on server side and could be used as CLI tool or embeded
in any 3rd party Python application.

**cbagent** is a key component of cbmonitor project - web application for stats
visualization and report generation.

Prerequisites
-------------

* Python 2.6 or 2.7
* pip or equivalent
* libcouchbase

Packages required for development are listed in requirements.txt.

Installation
------------

    $ pip install cbagent

Project structure
-----------------

Top-level project components:

* core **cbagent** package
* list for requirements for development
* unit tests
* setup script
* sample configuration file(s)

**cbagent** package itself includes:

* settings objects
* store objects
* metadata client for interaction with cbmonitor
* sub-package with collectors
* sub-package with CLI wrappers

Settings
--------

Regardless implementation any collector instance is initialized with settings
object. It could be any arbitrary Python object with a set of predefined
attributes. They include cbmonitor address:

    cbmonitor_host_port  # e.g., "127.0.0.1:8000"

seriesly database address:

    seriesly_host  # e.g., "127.0.0.1"

Polling interval:

    interval  # e.g., 10

Cluster specification:

    cluster = "default"
    master_node = "127.0.0.1"
    rest_username = "Administrator"
    rest_password = "password"

Notice that master_node parameter is dynamic, most collectors update it during
stats collection.

Some collectors like atop collector require additional parameters, for instance:

    ssh_username  # e.g., "root"
    ssh_password  # e.g., "couchbase"

CLI wrappers read all these parameters from configuration files. See
``sample.cfg`` for details.

Metadata client
---------------

Metadata client is a basic collection of POST requests that covers cbmonitor
REST API for adding:

* Clusters
* Servers
* Buckets
* Metrics
* Snapshots

cbmonitor uses metadata to extract actual stats from seriesly database. Usually
it's only invoked when collector starts. However some collectors implement
dynamic hooks for cases when new items (like servers or metrics) appear in the
middle of stats collection (e.g., after rebalance).

Snapshots is a cbmonitor concept of named time frames. They mainly used for
report generation, none of collectors uses it directly. However their API was
added to metadata client for general cbmonitor integration.

Stores
------

Currently there is only **SerieslyStore** class which provides high level API
to seriesly database. It could be replaced with any other Store implementation,
only public method ``append()`` is required. Notice that cbmonitor plotter
supports only seriesly backend at the moment of writing.

Collectors
----------

**collectors** sub-package is a set of collector implementations. All of them
inherit base Collector class (``cbagent/collectors/collector.py``) and implement
simple interface:

* ``update_medadata()`` - adding information about new clusters, servers,
buckets and metrics to cbmonitor databases.
* ``sample()`` - one-time stats sampling.
* ``collect()`` - infinite sampling loop with given polling interval. This
method is implemented in base class.

Every collector instance embeds store and metadata client objects (see above).

There is a convention to list implemented collectors in __init__ module of the
package. It significantly simplifies imports in 3rd party applications.

CLI wrappers
------------

Let's consider wrapper for ns_server stats collection:

    from cbagent.collectors import NSServer
    from cbagent.settings import Settings

    def main():
        settings = Settings()
        settings.read_cfg()

        collector = NSServer(settings)
        collector.update_metadata()
        collector.collect()

    if __name__ == '__main__':
        main()


It reflects general workflow of any stats collector. Creating settings object
followed by collector initialization, optional metadata updates and infinite
stats collection loop (until KeyboardInterrupt raised, see collector module for
details).

CLI wrappers must be specified in setup.py script as entry moint. Otherwise it
won't be added to environment PATH after **cbagent** installation.

Running CLI wrappers in development mode
----------------------------------------

First of all create vitrual environment:

    $ virtualenv env

Activate it:

    $ source env/bin/activate

Install required packages:

    $ pip -r requirements.txt

Now you can run CLI wrappers:

    $ python -m cbagent.cli_wrappers.ns_collector sample.cfg

alternatively:

    $ python setup.py install
    $ ns_collector sample.cfg

Integrating cbagent
-------------------

CLI wrappers is a great example of **cbagent** integration. Any Python
application can easily utilize this pattern. For instance, perfrunner project
(performance test framework) has a
[helper](https://github.com/pavel-paulau/perfrunner/blob/master/perfrunner/helpers/cbmonitor.py)
for stats collection using cbagent.

Running tests
-------------

    $ make test
