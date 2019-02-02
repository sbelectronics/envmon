import pigpio
import sys
import threading
import time

FAN_PWM_PIN=4
FAN_RPM_PIN=20

class Fan(object):
    def __init__(self, pi, pin=FAN_PWM_PIN, pin_rpm=FAN_RPM_PIN, weighting=0.1):
        self.pi = pi
        self.pin = pin
        self.pin_rpm = pin_rpm
        self.pi.set_mode(self.pin, pigpio.OUTPUT)
        self.pi.set_PWM_frequency(self.pin, 20000)
        readback_f = self.pi.get_PWM_frequency(self.pin)
        if (readback_f != 20000):
            print "WARNING: Tried to set pwm freq of 20000 but received %d" % readback_f
        self.pwm = 0
        self._stretcher = None
        if (self.pin_rpm):
            self.pulses_per_rev = 4
            self._stretcher = PulseStretcher(self)
            self._new = 1.0 - weighting
            self._old = weighting
            self._high_tick = None
            self._period = None
            self._watchdog = 200
            self._rpm_callback_enabled = False
            self.pi.set_mode(self.pin_rpm, pigpio.INPUT)

            self._stretcher.start()

        self.set_pwm(255)

    def _set_pwm(self,v):
        self.pi.set_PWM_dutycycle(self.pin,v)

    def set_pwm(self,v):
        self._set_pwm(v)
        self.pwm = v

    def _rpm_callback_handler(self, pin, level, tick):
        if not self._rpm_callback_enabled:
            return

        if level == 1:  # Rising edge.
            if self._high_tick is not None:
                t = pigpio.tickDiff(self._high_tick, tick)

                if t>0:
                    # compute an rpm for bounds checking
                    t_rpm = 60000000.0 / (t * self.pulses_per_rev)
                else:
                    t_rpm = 0

                if (t_rpm > 9500) or (t_rpm < 100):
                    # abnormal reading, discard
                    pass
                else:
                    if self._period is not None:
                        self._period = (self._old * self._period) + (self._new * t)
                    else:
                        self._period = t

            self._high_tick = tick

        elif level == 2:  # Watchdog timeout.
            if self._period is not None:
                if self._period < 2000000000:
                    self._period += (self._watchdog * 1000)

    def enable_rpm(self):
        self._high_tick = None
        self._rpm_callback = self.pi.callback(self.pin_rpm, pigpio.RISING_EDGE, self._rpm_callback_handler)
        self._rpm_callback_enabled = True

    def disable_rpm(self):
        if self._rpm_callback:
            self._rpm_callback_enabled = False
            self._rpm_callback.cancel()
            self._rpm_callback = None

    def get_fan_rpm(self):
        if self._period is not None:
            return 60000000.0 / (self._period * self.pulses_per_rev)
        else:
            return 0

    def get_rpm(self):
        if self._stretcher:
            return self._stretcher.get_rpm()
        else:
            return 0

    def report(self, rpm):
        pass

class PulseStretcher(threading.Thread):
    """ D'oh! You can't easily read the tach on a fan the you're PWMing...

        Why didn't I think of this when designing the circuit???

        A workaround is to occasionally stretch the PWM to 100% when we want to take a measurement.
    """

    def __init__(self, fan):
        super(PulseStretcher, self).__init__()
        self.fan = fan
        self.rpm = 0
        self.daemon = True

    def run(self):
        while True:
            self.fan._set_pwm(255)
            # give it a little bit of settling time
            time.sleep(0.002)
            self.fan.enable_rpm()
            # 6ms sampling period
            time.sleep(0.006)
            self.rpm = self.fan.get_fan_rpm()
            self.fan.disable_rpm()
            self.fan._set_pwm(self.fan.pwm)
            self.fan.report(self.rpm)

            # perform a sampling every second
            time.sleep(1)

    def get_rpm(self):
        return self.rpm


def main():
    import time

    pi = pigpio.pi()

    fan = Fan(pi)

    if len(sys.argv)>1:
        fan.set_pwm(int(sys.argv[1]))

    while True:
        print "rpm", int(fan.get_rpm())
        time.sleep(1)


if __name__ == "__main__":
    main()
