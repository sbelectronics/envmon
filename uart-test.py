import pigpio
import sys

DUST_DEVICE_RX=18
DUST_DEVICE_TX=27

def dust_tx_write(pi, data):
    pi.wave_add_serial(DUST_TX, 9600, data, bb_bits=8)
    wid = pi.wave_create()
    pi.wave_send_once(wid)
    pi.wave_delete(wid)

def main():
    pi = pigpio.pi()
#    pi.set_mode(DUST_DEVICE_RX, pigpio.OUTPUT)
    pi.set_mode(DUST_DEVICE_TX, pigpio.INPUT)
    
    pi.bb_serial_read_open(DUST_DEVICE_TX, 9600)

#    dust_tx_write("foo")

    try:
        while True:
            (count, data) = pi.bb_serial_read(DUST_DEVICE_TX)
            for b in data:
                print "%02X" % b,

            sys.stdout.flush()
    except:
        pi.bb_serial_read_close(DUST_DEVICE_TX)
                
if __name__ == "__main__":
    main()
