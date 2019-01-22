import pigpio
import sys
import time
import threading

from winsen_ch2o import WinsenCH2O
from winsen_co2 import WinsenCO2
from winsen_dust import WinsenDust

def main():
    pi = pigpio.pi()

    co2 = WinsenCO2(pi)
    co2.start()

    dust = WinsenDust(pi)
    dust.start()

    ch2o = WinsenCH2O(pi)
    ch2o.start()

    while True:
        time.sleep(1)
            
if __name__ == "__main__":
    main()
