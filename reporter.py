import cPickle
import os
import socket
import time

class Reporter_Base(object):
    def __init__(self, verbosity, station="envmon"):
        self.verbosity=verbosity
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

""" Some simple rrdtool graphs:
    rrdtool graph temp_graph1.png --start now-24h --end now -w 1024 -h 768 DEF:temp=envmon.rrd:temp:AVERAGE CDEF:tempf=9,5,/,temp,*,32,+ LINE1:tempf#FF0000:"Temperature"
    rrdtool graph humid_graph1.png --start now-24h --end now -w 1024 -h 768 DEF:humid=envmon.rrd:humid:AVERAGE LINE1:humid#FF0000:"Humidity"
    rrdtool graph co2_graph1.png --start now-24h --end now -w 1024 -h 768 DEF:co2_conc=envmon.rrd:co2_conc:AVERAGE LINE1:co2_conc#FF0000:"CO2"
    rrdtool graph pm10_graph1.png --start now-24h --end now -w 1024 -h 768 DEF:pm10=envmon.rrd:pm10:MAX LINE1:pm10#FF0000:"pm10"
"""

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
  DS:gas:GAUGE:{heartbeat}:0:500000
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

        if self.verbosity>=1:
            print rrd_expanded
        self.rrdtool.create([self.filename] + rrd_expanded)

    def dump_result(self):
        update = "N"
        for k in self.keys:
            if k in self.current_result:
                update = update + ":%0.2f" % self.current_result[k]
            else:
                update = update + ":U"
        if self.verbosity>=1:
            print update
        self.rrdtool.update(self.filename, update)

class Reporter_UDP(Reporter_Base):
    def __init__(self, *args, **kwargs):
        dest_addr = kwargs.pop("dest_addr")
        super(Reporter_UDP, self).__init__(*args, **kwargs)

        (dest_host, dest_port) = dest_addr.split(":")
        self.dest_addr = (dest_host, int(dest_port))
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def dump_result(self):
        message = {"station": self.station,
                   "result": self.current_result}
        if self.verbosity>=1:
            print message
        self.sock.sendto(cPickle.dumps(message), self.dest_addr)

class Reporter_Prometheus(Reporter_Base):
    def __init__(self, *args, **kwargs):
        super(Reporter_Prometheus, self).__init__(*args, **kwargs)

        from prometheus_client import Gauge

        self.Gauge = Gauge
        self.gauges = {}

    def dump_result(self):
        remap = {"pm1.0": "pm1p0", "pm2.5": "pm2p5"}
        for (k,v) in self.current_result.items():
            if not k in self.gauges:
                self.gauges[k] = self.Gauge(remap.get(k, k), k)
            self.gauges[k].set(v)

        
