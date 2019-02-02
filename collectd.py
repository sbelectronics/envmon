"""
    Make sure to open a UDP port, for example:
       sudo iptables -A INPUT -p udp --dport 1234 -j ACCEPT
"""

import argparse
import cPickle
import socket
import threading
import time
import traceback

from reporter import Reporter_Print, Reporter_RRD, Reporter_UDP

def parse_args():
    parser = argparse.ArgumentParser()

    defs = {"udp": None,
            "console": False,
            "rrd": False,
            "prometheus": None}

    _help = 'Report to UDP (default: %s)' % defs['udp']
    parser.add_argument(
        '-U', '--udp', dest='udp', action='store',
        default=defs['udp'],
        help=_help)

    _help = 'Report to console (default: %s)' % defs['console']
    parser.add_argument(
        '-C', '--ccnsole', dest='console', action='store_true',
        default=defs['console'],
        help=_help)

    _help = 'Report to RRD (default: %s)' % defs['rrd']
    parser.add_argument(
        '-R', '--rrd', dest='rrd', action='store_true',
        default=defs['rrd'],
        help=_help)

    _help = 'Report to Prometheus on port (default: %s)' % defs['rrd']
    parser.add_argument(
        '-P', '--prometheus', dest='prometheus', action='store', type=int,
        default=defs['prometheus'],
        help=_help)

    _help = "suppress debug and info logs"
    parser.add_argument('-q', '--quiet',
                        dest='quiet',
                        action='count',
                        default=0,
                        help=_help)

    _help = 'enable verbose logging'
    parser.add_argument('-v', '--verbose',
                        dest='verbose',
                        action='count',
                        default=0,
                        help=_help)

    args = parser.parse_args()

    return args

class UDPCollector(threading.Thread):
    def __init__(self, port=1234, verbosity=0, reporters={}):
        super(UDPCollector, self).__init__()
        self.port = port
        self.verbosity = verbosity
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM )
        self.sock.bind( ('', self.port) )
        self.daemon = True
        self.desired_reporters = reporters
        self.reporters = {}

    def receive_once(self):
        (data, address) = self.sock.recvfrom(4096)
        if not data:
            return 0

        message = cPickle.loads(data)
        station = message["station"]
        result =  message["result"]

        if self.verbosity>=1:
            print "RECV", station, result

        for (r_name, r_class, r_args) in self.desired_reporters:
            key = "%s:%s" % (station, r_name)
            if not key in self.reporters:
                self.reporters[key] = r_class(station=station, **r_args)
            self.reporters[key].report("collector", result)

        return 1

    def run(self):
        while True:
            try:
                if not self.receive_once():
                    time.sleep(0.1)
            except:
                traceback.print_exc()

def main():
    args = parse_args()

    if (not args.udp) and (not args.console) and (not args.rrd):
        args.console = True

    verbosity = args.verbose-args.quiet

    reporters = []
    if args.console:
        reporters.append(("print", Reporter_Print, {"verbosity": verbosity}))
    if args.rrd:
        reporters.append(("rrd", Reporter_RRD, {"verbosity": verbosity}))
    if args.udp:
        reporters.append(("udp", Reporter_UDP, {"verbosity": verbosity, "dest_addr": args.udp}))
    if args.prometheus:
        from prometheus_client import start_http_server
        # TODO: finish me

    collector = UDPCollector(verbosity = verbosity, reporters = reporters)
    collector.start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
