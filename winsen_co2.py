import pigpio
import sys
import time
import threading

CO2_DEVICE_RX=5 # pin the sensor receives data from pi
CO2_DEVICE_TX=6 # pin the sensor transmits data to the pi

class WinsenCO2(threading.Thread):
    def __init__(self, pi, device_tx = CO2_DEVICE_TX, device_rx = CO2_DEVICE_RX):
        super(WinsenCO2, self).__init__()
        self.daemon = True
        self.pi = pi
        self.device_tx = device_tx
        self.device_rx = device_rx
        
        self.pi.set_mode(self.device_tx, pigpio.INPUT)
        self.pi.set_mode(self.device_rx, pigpio.OUTPUT)

        try:
            self.pi.bb_serial_read_close(self.device_tx)
        except:
            pass
        self.pi.bb_serial_read_open(self.device_tx, 9600)

        request = (0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79)
        self.pi.wave_clear()
        self.pi.wave_add_serial(self.device_rx, 9600, request, 0, 8, 2)
        self.request_wid = self.pi.wave_create()
        self.last_send_time = 0

        self.byte=0
        self.calc_check = 0
        self.check = 0
        self.conc = 0

        self.request_period = 1

    def handle_packet(self):
        calc_check = (~self.calc_check) & 0xFF
        calc_check = calc_check + 1
        calc_check = calc_check & 0xFF

        if self.check!=calc_check:
            print "co2 mismatch:", self.check, calc_check
        else:
            self.handle_good_packet()

    def handle_good_packet(self):
            print "CO2 conc=%d" % (self.conc,)

    def process_byte(self, b):
        sys.stdout.flush()
        if (self.byte == 0):
            if (b==0xFF):
                self.byte = 1
                self.calc_check = 0
        elif (self.byte == 1):
            if (b==0x86): # sensor number
                self.byte = 2
            else:
                self.byte = 0
        elif (self.byte==2):
            self.conc_high = b
            self.byte = 3
        elif (self.byte==3):
            self.conc = self.conc_high << 8 | b
            self.byte = 4
        elif (self.byte==4):
            self.byte=5
        elif (self.byte==5):
            self.byte=6
        elif (self.byte==6):
            self.byte=7
        elif (self.byte==7):
            self.byte=8
        elif (self.byte==8):
            self.check = b
            self.handle_packet()
            self.byte = 0
            
        if (self.byte>=2) and (self.byte <= 8):
            self.calc_check = self.calc_check + b

    def run_once(self):
        # if it's time to send a request, then send one
        if (time.time() - self.last_send_time) > self.request_period:
            self.pi.wave_send_once(self.request_wid)
            self.last_send_time=time.time()

        (count, data) = self.pi.bb_serial_read(self.device_tx)
        for b in data:
            self.process_byte(b)
        return count
            
    def run(self):
        try:
            while True:
                count = self.run_once()
                if (count == 0):
                    time.sleep(0.1)
        finally:
            self.pi.bb_serial_read_close(self.device_tx)

def main():
    pi = pigpio.pi()

    dust = WinsenCO2(pi)
    dust.start()

    while True:
        time.sleep(1)
            
if __name__ == "__main__":
    main()
