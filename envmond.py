import os
import pigpio
import time

from winsen_ch2o import WinsenCH2O
from winsen_co2 import WinsenCO2
from winsen_dust import WinsenDust
from bme680_thb import BME680_TempHumidBarom
from reporter import Reporter_Print, Reporter_RRD

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
