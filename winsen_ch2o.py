import pigpio
import sys
import time
import threading

CH2O_DEVICE_TX=23

class WinsenCH2O(threading.Thread):
    def __init__(self, pi, device_tx = CH2O_DEVICE_TX):
        super(WinsenCH2O, self).__init__()
        self.daemon = True
        self.pi = pi
        self.device_tx = device_tx
        
        self.pi.set_mode(self.device_tx, pigpio.INPUT)

        try:
            self.pi.bb_serial_read_close(self.device_tx)
        except:
            pass
        self.pi.bb_serial_read_open(self.device_tx, 9600)

        self.byte=0
        self.calc_check = 0
        self.check = 0
        self.full_range = 0
        self.conc = 0
        
    def handle_packet(self):
        calc_check = (~self.calc_check) & 0xFF
        calc_check = calc_check + 1
        calc_check = calc_check & 0xFF

        if self.check!=calc_check:
            print "ch2o mismatch:", self.check, calc_check
        else:
            self.handle_good_packet()

    def handle_good_packet(self):
            print "CH2O conc=%d, full_range=%d" % (self.conc, self.full_range)

    def process_byte(self, b):
        sys.stdout.flush()
        if (self.byte == 0):
            if (b==0xFF):
                self.byte = 1
                self.calc_check = 0
        elif (self.byte == 1):
            if (b==0x17): # gas name ch2o
                self.byte = 2
            else:
                self.byte = 0
        elif (self.byte==2):
            if (b==0x04): # unit ppb
                self.byte = 3
            else:
                self.byte = 0
        elif (self.byte==3):
            if (b==0x00): # no decimal
                self.byte = 4
                self.framelen = b
            else:
                self.byte = 0
        elif (self.byte==4):
            self.conc_high = b
            self.byte=5
        elif (self.byte==5):
            self.conc = self.conc_high << 8 | b
            self.byte=6
        elif (self.byte==6):
            self.full_range_high = b
            self.byte=7
        elif (self.byte==7):
            self.full_range = self.full_range_high << 8 | b
            self.byte=8
        elif (self.byte==8):
            self.check = b
            self.handle_packet()
            self.byte = 0
            
        if (self.byte>=2) and (self.byte <= 8):
            self.calc_check = self.calc_check + b

    def run_once(self):
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

    dust = WinsenCH2O(pi)
    dust.start()

    while True:
        time.sleep(1)
            
if __name__ == "__main__":
    main()
