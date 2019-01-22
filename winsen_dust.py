import pigpio
import sys
import time
import threading

DUST_DEVICE_TX=27

class WinsenDust(threading.Thread):
    def __init__(self, pi, dust_device_tx = DUST_DEVICE_TX):
        super(WinsenDust, self).__init__()
        self.daemon = True
        self.pi = pi
        self.dust_device_tx = dust_device_tx
        
        self.pi.set_mode(self.dust_device_tx, pigpio.INPUT)

        try:
            self.pi.bb_serial_read_close(self.dust_device_tx)
        except:
            pass
        self.pi.bb_serial_read_open(self.dust_device_tx, 9600)

        self.byte=0
        self.pm1p0 = 0
        self.pm2p5 = 0
        self.pm10 = 0
        self.calc_check = 0
        self.check = 0
        
    def handle_packet(self):
        if self.check!=self.calc_check:
            print "mismatch:", self.check, self.calc_check
        else:
            print "pm1.0=%d, pm2.5=%d, pm10=%d" % (self.pm1p0, self.pm2p5, self.pm10)
        
    def process_byte(self, b):
        if (self.byte == 0):
            if (b==0x42):
                self.byte = 1
                self.calc_check = 0
        elif (self.byte == 1):
            if (b==0x4D):
                self.byte = 2
            else:
                self.byte = 0
        elif (self.byte==2):
            if (b==00):
                self.byte = 3
            else:
                self.byte = 0
        elif (self.byte==3):
            if (b==0x14):
                self.byte = 4
                self.framelen = b
            else:
                self.byte = 0
        elif (self.byte==4):
            self.byte=5
        elif (self.byte==5):
            self.byte=6
        elif (self.byte==6):
            self.byte=7
        elif (self.byte==7):
            self.byte=8
        elif (self.byte==8):
            self.byte=9
        elif (self.byte==9):
            self.byte=10
        elif (self.byte==10):
            self.pm1p0_high = b
            self.byte=11
        elif (self.byte==11):
            self.pm1p0 = self.pm1p0_high<<8 | b
            self.byte=12
        elif (self.byte==12):
            self.pm2p5_high = b
            self.byte=13
        elif (self.byte==13):
            self.pm2p5 = self.pm2p5_high<< 8 | b
            self.byte=14
        elif (self.byte==14):
            self.pm10_high = b
            self.byte=15
        elif (self.byte==15):
            self.pm10 = self.pm10_high << 8 | b
            self.byte=16
        elif (self.byte==16):
            self.byte=17
        elif (self.byte==17):
            self.byte=18
        elif (self.byte==18):
            self.byte=19
        elif (self.byte==19):
            self.byte=20
        elif (self.byte==20):
            self.byte=21
        elif (self.byte==21):
            self.byte=22
        elif (self.byte==22):
            self.check_high = b
            self.byte=23
        elif (self.byte==23):
            self.check = self.check_high << 8 | b
            self.handle_packet()
            self.byte = 0
            
        if self.byte <= 22:
            self.calc_check = self.calc_check + b


    def run_once(self):
        (count, data) = self.pi.bb_serial_read(self.dust_device_tx)
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
            self.pi.bb_serial_read_close(self.dust_device_tx)                

def stress(pi):
    # pretend the CO2 and CH20 sensors also exist
    pi.set_mode(23, pigpio.INPUT)
    pi.set_mode(6, pigpio.INPUT)
    try:
        pi.bb_serial_read_close(23)
    except:
        pass
    try:
        pi.bb_serial_read_close(6)
    except:
        pass
    pi.bb_serial_read_open(23, 9600)
    pi.bb_serial_read_open(6, 9600)
    
            
def main():
    pi = pigpio.pi()
    stress(pi)
    
    dust = WinsenDust(pi)
    dust.start()

    while True:
        time.sleep(1)
            
if __name__ == "__main__":
    main()
