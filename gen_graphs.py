import argparse
import os
import rrdtool

MEAS = {"temp": {"name": "Temperature", "transform": "CDEF:tempf=9,5,/,temp,*,32,+", "mappedvar": "tempf"},
        "humid": {"name": "Humidity"},
        "pres": {"name": "Pressure"},
        "gas": {"name": "Gas"},
        "ch2o_conc": {"name": "CH2O"},
        "ch2o_full_range": {"name": "CH2O_range"},
        "co2_conc": {"name": "CO2"},
        "pm1.0": {"name": "pm1.0", "var": "pm1p0"},
        "pm2.5": {"name": "pm2.5", "var": "pm1p0"},
        "pm10": {"name": "pm10"}}

def parse_args():
    parser = argparse.ArgumentParser()

    defs = {}

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

def split_args(cmd):
    args = []
    cmd = cmd.split("\n")
    cmd = [x.strip() for x in cmd]
    cmd = [x for x in cmd if x]
    for line in cmd:
        if " " in line:
            args = args + ([x for x in line.split(" ") if x])
        else:
            args.append(line)
    return args

def gen_graph(station):
    graph_dir = "graphs"

    html_24h_f = open(os.path.join(graph_dir, "24h.html"), "w")
    html_24h_f.write("<html><head></head><body>\n")
    html_1h_f = open(os.path.join(graph_dir, "1h.html"), "w")
    html_1h_f.write("<html><head></head><body>\n")
    html_30d_max_f = open(os.path.join(graph_dir, "30d_max.html"), "w")
    html_30d_max_f.write("<html><head></head><body>\n")

    transforms = {"temp": ("tempf", "CDEF:tempf=9,5,/,temp,*,32,+")}
    vmap = {"pm1.0": "pm1p0",
            "pm2.5": "pm2p5"}

    for (k, v) in MEAS.items():
        kwargs = {"graph_base_fn": k+"_24h.png",
                  "graph_fn": os.path.join(graph_dir, k+"_24h.png"),
                  "rrd_fn": "%s.rrd" % station,
                  "var": v.get("var", k),
                  "transform": v.get("transform", ""),
                  "mappedv": v.get("mappedvar", v.get("var", k)),
                  "name": v["name"]}
        cmd = """{graph_fn}
                 --start now-24h
                 --end now 
                 -w 1024 
                 -h 400 
                 DEF:{var}={rrd_fn}:{var}:AVERAGE
                 {transform}
                 LINE1:{mappedv}#FF0000:{name}""".format(**kwargs)
        cmd = split_args(cmd)
        rrdtool.graph(*cmd)
        html_24h_f.write('<img src="{graph_base_fn}">\n'.format(**kwargs))

        kwargs["graph_base_fn"] = k+"_1h.png"
        kwargs["graph_fn"] = os.path.join(graph_dir, k+"_1h.png")
        cmd = """{graph_fn}
                 --start now-1h
                 --end now 
                 -w 1024 
                 -h 400 
                 DEF:{var}={rrd_fn}:{var}:MAX
                 {transform}
                 LINE1:{mappedv}#FF0000:{name}""".format(**kwargs)
        cmd = split_args(cmd)
        rrdtool.graph(*cmd)
        html_1h_f.write('<img src="{graph_base_fn}">\n'.format(**kwargs))

        kwargs["graph_base_fn"] = k+"_30d_max.png"
        kwargs["graph_fn"] = os.path.join(graph_dir, k+"_30d_max.png")
        cmd = """{graph_fn}
                 --start now-30d
                 --end now 
                 -w 1024 
                 -h 400 
                 DEF:{var}={rrd_fn}:{var}:MAX
                 {transform}
                 LINE1:{mappedv}#FF0000:{name}""".format(**kwargs)
        cmd = split_args(cmd)
        rrdtool.graph(*cmd)
        html_30d_max_f.write('<img src="{graph_base_fn}">\n'.format(**kwargs))

    html_24h_f.write("</body></html>\n")
    html_1h_f.write("</body></html>\n")
    html_30d_max_f.write("</body></html>\n")


def main():
    args = parse_args()
    verbosity = args.verbose - args.quiet
    
    stations = []
    for fn in os.listdir("."):
        if fn.endswith(".rrd"):
            stations.append(fn[:-4])
            
    for station in stations:
        gen_graph(station)

if __name__ == "__main__":
    main()