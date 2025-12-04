import os
import subprocess
import time
import random

# Attempt to import RPi.GPIO and bme280, smbus2.
# If not on a Raspberry Pi or in mock mode, these imports will be skipped or mocked.
try:
    # Check if GPIOZERO_PIN_FACTORY is set to mock, indicating a non-RPi environment
    if os.environ.get("GPIOZERO_PIN_FACTORY") == "mock":
        # Create dummy classes for RPi.GPIO and bme280 in mock mode
        class MockGPIO:
            BCM = 11
            OUT = 0
IN = 1
            PUD_UP = 20
            FALLING = 31

            def setmode(self, mode):
                print("GPIO: Setting mode (mock)")

            def setup(self, pin, mode, pull_up_down=None):
                print(f"GPIO: Setting up pin {pin} as {mode} (mock)")

            def output(self, pin, value):
                print(f"GPIO: Setting pin {pin} to {value} (mock)")

            def add_event_detect(self, pin, edge, callback, bouncetime):
                print(f"GPIO: Adding event detect on pin {pin} (mock)")

            def cleanup(self):
                print("GPIO: Cleaning up (mock)")

        GPIO = MockGPIO()

        class MockBME280:
            def load_calibration_params(self, bus, address):
                print("BME280: Loading calibration params (mock)")
                return "mock_calibration_params"

            def sample(self, bus, address, params):
                print("BME280: Sampling data (mock)")
                # Return dummy data for mock mode
                return {
                    "id": 0,
                    "timestamp": time.time(),
                    "temperature": random.uniform(20, 30),
                    "pressure": random.uniform(900, 1100),
                    "humidity": random.uniform(50, 90),
                }

        bme280 = MockBME280()

        class MockSMBus:
            def __init__(self, bus_number):
                print(f"SMBus: Initializing mock bus {bus_number}")

            def close(self):
                print("SMBus: Closing mock bus")

        smbus2 = MockSMBus

    else:
        import RPi.GPIO as GPIO
        import bme280
        import smbus2

except ImportError:
    # Fallback for non-Raspberry Pi environments without GPIOZERO_PIN_FACTORY set
    print("RPi.GPIO, bme280, or smbus2 not found. Running in mock hardware mode.")

    class MockGPIO:
        BCM = 11
        OUT = 0
        IN = 1
        PUD_UP = 20
        FALLING = 31

        def setmode(self, mode):
            pass

        def setup(self, pin, mode, pull_up_down=None):
            pass

        def output(self, pin, value):
            pass

        def add_event_detect(self, pin, edge, callback, bouncetime):
            pass

        def cleanup(self):
            pass

    GPIO = MockGPIO()

    class MockBME280:
        def load_calibration_params(self, bus, address):
            return "mock_calibration_params"

        def sample(self, bus, address, params):
            return {
                "id": 0,
                "timestamp": time.time(),
                "temperature": random.uniform(20, 30),
                "pressure": random.uniform(900, 1100),
                "humidity": random.uniform(50, 90),
            }

    bme280 = MockBME280()

    class MockSMBus:
        def __init__(self, bus_number):
            pass

        def close(self):
            pass

    smbus2 = MockSMBus


class RFOutlet:
    def __init__(self, name: str, send_on_code: int, send_off_code: int, led_gpio_pin: int, mock_mode: bool = False):
        self.name = name
        self.send_on_code = send_on_code
        self.send_off_code = send_off_code
        self.led_gpio_pin = led_gpio_pin
        self.mock_mode = mock_mode

        if not self.mock_mode:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.led_gpio_pin, GPIO.OUT)
            GPIO.output(self.led_gpio_pin, GPIO.LOW)  # Ensure LED is off initially

    def _execute_rf_command(self, code: int):
        if self.mock_mode:
            print(f"MOCK: RFOutlet '{self.name}' executing codesend {code}")
        else:
            # Using subprocess.run for better control and security than os.system
            try:
                # Assuming codesend is in a known path relative to the script or in PATH
                # Adjust path as necessary for your deployment
                command = ["../../rfoutlet/codesend", str(code)]
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                print(f"RFOutlet '{self.name}' command output: {result.stdout.strip()}")
            except FileNotFoundError:
                print(f"Error: 'codesend' command not found. Make sure it's installed and in your PATH. (Attempted to run: {' '.join(command)})")
            except subprocess.CalledProcessError as e:
                print(f"Error executing RF command for '{self.name}': {e.stderr.strip()}")
            except Exception as e:
                print(f"An unexpected error occurred while executing RF command for '{self.name}': {e}")

    def turn_on(self):
        print(f"Turning ON {self.name}")
        self._execute_rf_command(self.send_on_code)
        if not self.mock_mode:
            GPIO.output(self.led_gpio_pin, GPIO.HIGH)

    def turn_off(self):
        print(f"Turning OFF {self.name}")
        self._execute_rf_command(self.send_off_code)
        if not self.mock_mode:
            GPIO.output(self.led_gpio_pin, GPIO.LOW)


class BME280Sensor:
    def __init__(self, i2c_bus_number: int = 1, i2c_address: int = 0x76, mock_mode: bool = False):
        self.i2c_bus_number = i2c_bus_number
        self.i2c_address = i2c_address
        self.mock_mode = mock_mode
        self.calibration_params = None

        if not self.mock_mode:
            self.bus = smbus2.SMBus(self.i2c_bus_number)
            self.calibration_params = bme280.load_calibration_params(self.bus, self.i2c_address)
            print(f"BME280 Sensor initialized on bus {i2c_bus_number}, address {i2c_address}")
        else:
            print("MOCK: BME280 Sensor initialized in mock mode.")

    def read_data(self):
        if self.mock_mode:
            # Return dummy data for mock mode
            return {
                "temperature": random.uniform(18.0, 35.0),
                "pressure": random.uniform(950.0, 1050.0),
                "humidity": random.uniform(40.0, 99.0),
            }
        else:
            try:
                data = bme280.sample(self.bus, self.i2c_address, self.calibration_params)
                return {
                    "temperature": data.temperature,
                    "pressure": data.pressure,
                    "humidity": data.humidity,
                }
            except Exception as e:
                print(f"Error reading BME280 data: {e}")
                return None

    def cleanup(self):
        if not self.mock_mode and hasattr(self, 'bus'):
            self.bus.close()
            print("BME280 Sensor bus closed.")
