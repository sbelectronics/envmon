import os
import pigpio
import time

from winsen_ch2o import WinsenCH2O
from winsen_co2 import WinsenCO2
from winsen_dust import WinsenDust
from bme680_thb import BME680_TempHumidBarom

class ReportingWinsenCO2(WinsenCO2):
    def __init__(self, pi, reporter):
        super(ReportingWinsenCO2, self).__init__(pi)
        self.reporter = reporter

    def handle_good_packet(self):
        self.reporter.report("CO2", {"co2_conc": self.conc})

class ReportingWinsenCH2O(WinsenCH2O):
    def __init__(self, pi, reporter):
        super(ReportingWinsenCH2O, self).__init__(pi)
        self.reporter = reporter

    def handle_good_packet(self):
        self.reporter.report("CH2O", {"ch2o_conc": self.conc, "co2_full_range": self.full_range})

class ReportingWinsenDust(WinsenDust):
    def __init__(self, pi, reporter):
        super(ReportingWinsenDust, self).__init__(pi)
        self.reporter = reporter

    def handle_good_packet(self):
        self.reporter.report("DUST", {"pm1.0": self.pm1p0, "pm2.5": self.pm2p5, "pm10": self.pm10})

class ReportingBME680_TempHumidBarom(BME680_TempHumidBarom):
    def __init__(self, reporter):
        super(ReportingBME680_TempHumidBarom, self).__init__()
        self.reporter = reporter

    def handle_good_packet(self):
        self.reporter.report("BME680", {"temp": self.temperature, "pres": self.pressure, "humid": self.humidity})

class Reporter_Base(object):
    def __init__(self, station="envmon"):
        self.station = station
        self.current_result = {}

    def report(self, sensor, values):
        for (k,v) in values.items():
            self.current_result[k] = v

        if "temp" in values.keys():
            self.dump_result()
            self.current_result = {}

    def dump_result(self):
        pass

class Reporter_Print(Reporter_Base):
    def __init__(self, *args, **kwargs):
        super(Reporter_Print, self).__init__(*args, **kwargs)

    def dump_result(self):
        print time.time()
        for (k, v) in self.current_result.items():
            print "  ", k, v

class Reporter_RRD(Reporter_Base):
    def __init__(self, *args, **kwargs):
        super(Reporter_RRD, self).__init__(*args, **kwargs)

        import rrdtool
        self.rrdtool = rrdtool
        self.period = 10
        self.filename = "%s.rrd" % self.station

        self.keys = ["temp",
                     "humid",
                     "pres",
                     "gas",
                     "ch2o_conc",
                     "ch2o_full_range",
                     "co2_conc",
                     "pm1.0",
                     "pm2.5",
                     "pm10"]

        self.create_rrd()

    def create_rrd(self):
        if os.path.exists(self.filename):
            return

        heartbeat = 30
        hoursamps = 60*60/self.period
        oneweek = 7 * 24 * 60 * 60 / self.period
        hourly_oneyear = 365 * 24 * 60 * 60 / (60*60)

        rrd_def = """
  --step {period}
  DS:temp:GAUGE:{heartbeat}:-40:85
  DS:humid:GAUGE:{heartbeat}:10:90
  DS:pres:GAUGE:{heartbeat}:300:1100
  DS:gas:GAUGE:{heartbeat}:0:500
  DS:ch2o_conc:GAUGE:{heartbeat}:0:5000
  DS:ch2o_full_range:GAUGE:{heartbeat}:2000:5000
  DS:co2_conc:GAUGE:{heartbeat}:0:5000
  DS:pm1p0:GAUGE:{heartbeat}:0:1000
  DS:pm2p5:GAUGE:{heartbeat}:0:1000
  DS:pm10:GAUGE:{heartbeat}:0:1000
  RRA:AVERAGE:0.5:1:{oneweek}
  RRA:MIN:0.5:{hoursamps}:{hourly_oneyear} 
  RRA:MAX:0.5:{hoursamps}:{hourly_oneyear}
  RRA:AVERAGE:0.5:{hoursamps}:{hourly_oneyear}
""".format(period=self.period, heartbeat=heartbeat, hoursamps=hoursamps, oneweek=oneweek, hourly_oneyear=hourly_oneyear)

        rrd_expanded = []
        for line in rrd_def.split("\n"):
            line = line.strip()
            if not line:
                continue
            if " " in line:
                rrd_expanded = rrd_expanded + line.split(" ")
            else:
                rrd_expanded.append(line)

        print rrd_expanded
        self.rrdtool.create([self.filename] + rrd_expanded)

    def dump_result(self):
        update = "N"
        for k in self.keys:
            if k in self.current_result:
                update = update + ":%0.2f" % self.current_result[k]
            else:
                update = update + ":U"
        print update
        self.rrdtool.update(self.filename, update)

def main():
    pi = pigpio.pi()

    reporter = Reporter_Print()

    co2 = ReportingWinsenCO2(pi, reporter)
    co2.start()

    dust = ReportingWinsenDust(pi, reporter)
    dust.start()

    ch2o = ReportingWinsenCH2O(pi, reporter)
    ch2o.start()

    bme = ReportingBME680_TempHumidBarom(reporter)
    bme.start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
