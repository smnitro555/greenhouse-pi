import plotly
import os

# Set environment variable for GPIOZERO to use a mock library for development
# on non-Raspberry Pi machines. This must be done before importing RPi.GPIO.
if os.name != 'posix':
    os.environ['GPIOZERO_PIN_FACTORY'] = 'mock'

import RPi.GPIO as GPIO  # https://pypi.org/project/RPi.GPIO/
import bme280  # https://pypi.org/project/RPi.bme280/

# https://pypi.org/project/RPi.bme280/
import time
import pandas
import smbus2
import yaml

from datetime import datetime

DESIRED_HUMIDITY = 80
HUMIDITY_MARGIN = 5
DESIRED_TEMP = 66
TEMP_MARGIN = 4

NIGHTLIGHT_ON = 'time'
NIGHTLIGHT_OFF = 'time'
CIRC_FAN_MINS_PER_HOUR = 5
AVERAGE_INTERVAL = 5  # Minutes
SWITCH_TIMEOUT = 5 * 60  # Minutes * Seconds/Min
SLEEP_DELAY = 50


class Greenhouse:

    def __init__(self):
        self.now = datetime.now()
        self.start_time = time.time()
        self.current_temp = None
        self.current_humidity = None
        self.average_temp = None
        self.average_humidity = None
        self.switch_status = {'VentFan': None,
                              'Heater': None,
                              'GrowLight': None,
                              'StandFan': None}
        self.light_range = [NIGHTLIGHT_OFF, NIGHTLIGHT_ON]
        # Load the RF Keys
        if os.path.isfile('rf_keys.yaml'):
            with open('rf_keys.yaml', 'r') as rf_keys_file:
                self.rf_transmit_keys = yaml.load(rf_keys_file)
        else:
            raise FileNotFoundError('Cannot find rf_keys.yaml file')

    def vent_fan_callback(self, channel):
        print('Vent Fan Button Press Detected')
        if self.switch_status['VentFan'] is False:
            print('Engaging Vent Fan')
            self.switch_on('VentFan')
        else:
            print('Powering Down Vent Fan')
            self.switch_off('VentFan')

    def heater_callback(self, channel):
        print('Heater Button Press Detected')
        if self.switch_status['Heater'] is False:
            print('Engaging Heater')
            self.switch_on('Heater')
        else:
            print('Powering Down Heater')
            self.switch_off('Heater')

    def grow_light_callback(self, channel):
        print('Grow Light Button Press Detected')
        if self.switch_status['GrowLight'] is False:
            print('Engaging Grow Light')
            self.switch_on('GrowLight')
        else:
            print('Powering Down GrowLight')
            self.switch_off('GrowLight')

    def stand_fan_callback(self, channel):
        print('Stand Fan Button Press Detected')
        if self.switch_status['StandFan'] is False:
            print('Engaging Stand Fan')
            self.switch_on('StandFan')
        else:
            print('Powering Down Stand Fan')
            self.switch_off('StandFan')

    def initialize(self):
        # Turn Everything off
        for key in self.rf_transmit_keys.keys():
            self.switch_off(key)
        # Initialize Buttons
        for key in self.rf_transmit_keys.keys():
            # Setup Button
            GPIO.setup(self.rf_transmit_keys[key]['ButtonGPIO'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # Setup LED
            GPIO.setup(self.rf_transmit_keys[key]['LEDGPIO'], GPIO.OUT)
            GPIO.output(self.rf_transmit_keys[key]['LEDGPIO'], GPIO.HIGH)
            GPIO.output(self.rf_transmit_keys[key]['LEDGPIO'], GPIO.LOW)
        # Set Interrupts for Button Presses
        GPIO.add_event_detect(self.rf_transmit_keys['VentFan']['ButtonGPIO'], GPIO.FALLING,
                              callback=self.vent_fan_callback, bouncetime=300)
        GPIO.add_event_detect(self.rf_transmit_keys['Heater']['ButtonGPIO'], GPIO.FALLING,
                              callback=self.heater_callback, bouncetime=300)
        GPIO.add_event_detect(self.rf_transmit_keys['GrowLight']['ButtonGPIO'], GPIO.FALLING,
                              callback=self.grow_light_callback, bouncetime=300)
        GPIO.add_event_detect(self.rf_transmit_keys['StandFan']['ButtonGPIO'], GPIO.FALLING,
                              callback=self.stand_fan_callback, bouncetime=300)

    def switch_off(self, device_name):
        os.system('../../rfoutlet/codesend %i' % self.rf_transmit_keys[device_name]['SendOff'])
        self.switch_status[device_name] = False
        GPIO.output(self.rf_transmit_keys[device_name]['LEDGPIO'], GPIO.LOW)

    def switch_on(self, device_name, update_val=time.time()):
        os.system('../../rfoutlet/codesend %i' % self.rf_transmit_keys[device_name]['SendOn'])
        # Log the time the device is switched on
        self.switch_status[device_name] = update_val
        GPIO.output(self.rf_transmit_keys[device_name]['LEDGPIO'], GPIO.HIGH)

    def log_conditions(self):
        a = 1

    @staticmethod
    def get_condition_filename(date):
        return 'test'

    def update_switches(self):
        a = 1

    def generate_plotly_plot(self):
        a = 1

    def write_html(self):
        with open('../index.html', 'w') as html_file:
            html_file.write(
                '<h1 style="text-align: center;"><span style="text-decoration: underline;">Greenhouse Dashboard</span></h1>')
            html_file.write('<p>Date Last Updated: %s</p>' % self.now.strftime("%H:%M:%S"))
            html_file.write(self.generate_plotly_plot)

    def main(self):
        self.initialize()
        while True:
            # Log Temperature
            # Read Switch Over-ride for Heater
            if (self.switch_status['Heater'] is not False) and (self.switch_status['Heater'] > 0) and (
                    time.time() - self.switch_status['Heater'] > SWITCH_TIMEOUT):
                self.switch_off('Heater')
            if (self.switch_status['VentFan'] is not False) and (self.switch_status['VentFan'] > 0) and (
                    time.time() - self.switch_status['VentFan'] > SWITCH_TIMEOUT):
                self.switch_off('VentFan')

            if self.average_temp < (DESIRED_TEMP + TEMP_MARGIN):
                self.switch_on('Heater', update_val=-1)
            elif (self.average_temp > (DESIRED_TEMP + TEMP_MARGIN)) or (
                    self.average_humidity > (DESIRED_HUMIDITY - HUMIDITY_MARGIN)):
                self.switch_on('VentFan', update_val=-1)
            else:
                # Switch VentFan or Heater Off
                if self.switch_status['Heater'] is not False:
                    self.switch_off('Heater')
                if self.switch_status['VentFan'] is not False:
                    self.switch_off('VentFan')

            # Append data to dataframe
            # Generate temperature plot
            # generate switch plot
            time.sleep(SLEEP_DELAY)


if __name__ == '__main__':
    GREENHOUSE = Greenhouse()
    GREENHOUSE.main()
