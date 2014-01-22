import sys
from optparse import OptionParser

from cbagent.collectors.active_tasks import ActiveTasks
from cbagent.collectors.iostat import IO
from cbagent.collectors.latency import Latency
from cbagent.collectors.observe import ObserveLatency
from cbagent.collectors.net import Net
from cbagent.collectors.ns_server import NSServer
from cbagent.collectors.ps import PS
from cbagent.collectors.sync_gateway import SyncGateway
from cbagent.collectors.xdcr_lag import XdcrLag
from cbagent.settings import Settings


def main():
    parser = OptionParser(prog="cbagent")

    parser.add_option("--at", action="store_true", dest="active_tasks",
                      help="Active tasks")
    parser.add_option("--io", action="store_true", dest="iostat",
                      help="iostat")
    parser.add_option("--l", action="store_true", dest="latency",
                      help="Latency")
    parser.add_option("--o", action="store_true", dest="observe",
                      help="Observe latency")
    parser.add_option("--n", action="store_true", dest="net",
                      help="Net")
    parser.add_option("--ns", action="store_true", dest="ns_server",
                      help="ns_server")
    parser.add_option("--ps", action="store_true", dest="ps",
                      help="ps CPU, RSS and VSIZE")
    parser.add_option("--sg", action="store_true", dest="sync_gateway",
                      help="Sync Gateway")
    parser.add_option("--x", action="store_true", dest="xdcr_lag",
                      help="XDCR lag")

    options, args = parser.parse_args()

    if not args:
        sys.exit("No configuration provided")

    if options.active_tasks:
        collector = ActiveTasks
    elif options.iostat:
        collector = IO
    elif options.latency:
        collector = Latency
    elif options.observe:
        collector = ObserveLatency
    elif options.net:
        collector = Net
    elif options.ns_server:
        collector = NSServer
    elif options.ps:
        collector = PS
    elif options.sync_gateway:
        collector = SyncGateway
    elif options.xdcr_lag:
        collector = XdcrLag
    else:
        sys.exit("No collector selected")

    settings = Settings()
    settings.read_cfg(args[0])

    collector = collector(settings)
    collector.update_metadata()
    collector.collect()

if __name__ == '__main__':
    main()
