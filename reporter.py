import os
import time

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
