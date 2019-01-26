import bme680
import time
import threading

BME680_ADDR = 0x77

class BME680_TempHumidBarom(threading.Thread):
    def __init__(self):
        super(BME680_TempHumidBarom, self).__init__()

        self.sensor = bme680.BME680(i2c_addr=BME680_ADDR)

        self.sensor.set_humidity_oversample(bme680.OS_2X)
        self.sensor.set_pressure_oversample(bme680.OS_4X)
        self.sensor.set_temperature_oversample(bme680.OS_8X)
        self.sensor.set_filter(bme680.FILTER_SIZE_3)

        self.sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
        self.sensor.set_gas_heater_temperature(320)
        self.sensor.set_gas_heater_duration(150)
        self.sensor.select_gas_heater_profile(0)

        self.daemon = True

    def handle_packet(self):
        self.handle_good_packet()

    def handle_good_packet(self):
        output = "{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH".format(self.temperature, self.pressure, self.humidity)
        print "BME", output
        
    def run(self):
        while True:
            if self.sensor.get_sensor_data():
                self.temperature = self.sensor.data.temperature
                self.pressure = self.sensor.data.pressure
                self.humidity = self.sensor.data.humidity
                self.handle_packet()
            time.sleep(10)
            
        
def main():
  thb = BME680_TempHumidBarom()
  thb.start()
  
  while True:
      time.sleep(1)

if __name__ == "__main__":
    main()
