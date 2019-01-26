import argparse
import os
import pigpio
import time

from winsen_ch2o import WinsenCH2O
from winsen_co2 import WinsenCO2
from winsen_dust import WinsenDust
from bme680_thb import BME680_TempHumidBarom
from reporter import Reporter_Print, Reporter_RRD, Reporter_UDP

class ReportingWinsenCO2(WinsenCO2):
    def __init__(self, pi, reporters):
        super(ReportingWinsenCO2, self).__init__(pi)
        self.reporters = reporters

    def handle_good_packet(self):
        for reporter in self.reporters:
            reporter.report("CO2", {"co2_conc": self.conc})

class ReportingWinsenCH2O(WinsenCH2O):
    def __init__(self, pi, reporters):
        super(ReportingWinsenCH2O, self).__init__(pi)
        self.reporters = reporters

    def handle_good_packet(self):
        for reporter in self.reporters:
            reporter.report("CH2O", {"ch2o_conc": self.conc, "co2_full_range": self.full_range})

class ReportingWinsenDust(WinsenDust):
    def __init__(self, pi, reporters):
        super(ReportingWinsenDust, self).__init__(pi)
        self.reporters = reporters

    def handle_good_packet(self):
        for reporter in self.reporters:
            reporter.report("DUST", {"pm1.0": self.pm1p0, "pm2.5": self.pm2p5, "pm10": self.pm10})

class ReportingBME680_TempHumidBarom(BME680_TempHumidBarom):
    def __init__(self, reporters):
        super(ReportingBME680_TempHumidBarom, self).__init__()
        self.reporters = reporters

    def handle_good_packet(self):
        for reporter in self.reporters:
            reporter.report("BME680", {"temp": self.temperature, "pres": self.pressure, "humid": self.humidity})


def parse_args():
    parser = argparse.ArgumentParser()

    defs = {"station": "envmon",
            "udp": None,
            "console": False,
            "rrd": False}

    _help = 'Name of station (default: %s)' % defs['station']
    parser.add_argument(
        '-S', '--station', dest='station', action='store',
        default=defs['station'],
        help=_help)

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

def main():
    pi = pigpio.pi()

    args = parse_args()

    if (not args.udp) and (not args.console) and (not args.rrd):
        args.console = True

    verbosity = args.verbose-args.quiet

    reporters = []
    if args.console:
        reporters.append(Reporter_Print(station=args.station, verbosity=verbosity))
    if args.rrd:
        reporters.append(Reporter_RRD(station=args.station, verbosity=verbosity))
    if args.udp:
        reporters.append(Reporter_UDP(station=args.station, dest_addr=args.udp, verbosity=verbosity))

    co2 = ReportingWinsenCO2(pi, reporters)
    co2.start()

    dust = ReportingWinsenDust(pi, reporters)
    dust.start()

    ch2o = ReportingWinsenCH2O(pi, reporters)
    ch2o.start()

    bme = ReportingBME680_TempHumidBarom(reporters)
    bme.start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
