"""
Greenhouse Hardware Collection

Module containing classes for different pieces of hardware used in the greenhouse:
- BME280Sensor: Temperature, humidity, and pressure sensor
- RFOutlet: RF-controlled power outlet for devices
- Button: GPIO button for manual device control

Supports mock mode for testing without actual hardware.
"""

import os
import subprocess
import time
import random
from typing import Callable, Optional, Dict, Any

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
            PUD_DOWN = 21
            FALLING = 31
            RISING = 32
            BOTH = 33
            HIGH = 1
            LOW = 0

            def setmode(self, mode):
                print("GPIO: Setting mode (mock)")

            def setup(self, pin, mode, pull_up_down=None):
                print(f"GPIO: Setting up pin {pin} as {mode} (mock)")

            def output(self, pin, value):
                print(f"GPIO: Setting pin {pin} to {value} (mock)")

            def input(self, pin):
                print(f"GPIO: Reading pin {pin} (mock)")
                return self.LOW

            def add_event_detect(self, pin, edge, callback=None, bouncetime=None):
                print(f"GPIO: Adding event detect on pin {pin} (mock)")

            def remove_event_detect(self, pin):
                print(f"GPIO: Removing event detect on pin {pin} (mock)")

            def cleanup(self, pin=None):
                if pin:
                    print(f"GPIO: Cleaning up pin {pin} (mock)")
                else:
                    print("GPIO: Cleaning up all pins (mock)")

        GPIO = MockGPIO()

        class MockBME280:
            def load_calibration_params(self, bus, address):
                print("BME280: Loading calibration params (mock)")
                return "mock_calibration_params"

            def sample(self, bus, address, params):
                print("BME280: Sampling data (mock)")
                # Return dummy data for mock mode
                class MockData:
                    def __init__(self):
                        self.id = 0
                        self.timestamp = time.time()
                        self.temperature = random.uniform(20, 30)
                        self.pressure = random.uniform(900, 1100)
                        self.humidity = random.uniform(50, 90)

                return MockData()

        bme280 = MockBME280()

        class MockSMBus:
            def __init__(self, bus_number):
                print(f"SMBus: Initializing mock bus {bus_number}")

            def close(self):
                print("SMBus: Closing mock bus")

        smbus2 = type('MockSMBus2Module', (), {'SMBus': MockSMBus})

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
        PUD_DOWN = 21
        FALLING = 31
        RISING = 32
        BOTH = 33
        HIGH = 1
        LOW = 0

        def setmode(self, mode):
            pass

        def setup(self, pin, mode, pull_up_down=None):
            pass

        def output(self, pin, value):
            pass

        def input(self, pin):
            return self.LOW

        def add_event_detect(self, pin, edge, callback=None, bouncetime=None):
            pass

        def remove_event_detect(self, pin):
            pass

        def cleanup(self, pin=None):
            pass

    GPIO = MockGPIO()

    class MockBME280:
        def load_calibration_params(self, bus, address):
            return "mock_calibration_params"

        def sample(self, bus, address, params):
            class MockData:
                def __init__(self):
                    self.id = 0
                    self.timestamp = time.time()
                    self.temperature = random.uniform(20, 30)
                    self.pressure = random.uniform(900, 1100)
                    self.humidity = random.uniform(50, 90)

            return MockData()

    bme280 = MockBME280()

    class MockSMBus:
        def __init__(self, bus_number):
            pass

        def close(self):
            pass

    smbus2 = type('MockSMBus2Module', (), {'SMBus': MockSMBus})


class RFOutlet:
    """
    RF-controlled power outlet for controlling greenhouse devices.

    Attributes:
        name: Human-readable device name
        send_on_code: RF code to turn device on
        send_off_code: RF code to turn device off
        led_gpio_pin: GPIO pin number for LED indicator
        mock_mode: If True, simulates hardware without actual GPIO operations
    """

    def __init__(
        self,
        name: str,
        send_on_code: int,
        send_off_code: int,
        led_gpio_pin: int,
        mock_mode: bool = False
    ):
        self.name = name
        self.send_on_code = send_on_code
        self.send_off_code = send_off_code
        self.led_gpio_pin = led_gpio_pin
        self.mock_mode = mock_mode
        self._state = False  # Track device state

        if not self.mock_mode:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.led_gpio_pin, GPIO.OUT)
            GPIO.output(self.led_gpio_pin, GPIO.LOW)  # Ensure LED is off initially

    def _execute_rf_command(self, code: int):
        """Execute RF command to control the outlet."""
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
        """Turn on the RF outlet and illuminate the LED."""
        print(f"Turning ON {self.name}")
        self._execute_rf_command(self.send_on_code)
        self._state = True
        if not self.mock_mode:
            GPIO.output(self.led_gpio_pin, GPIO.HIGH)

    def turn_off(self):
        """Turn off the RF outlet and turn off the LED."""
        print(f"Turning OFF {self.name}")
        self._execute_rf_command(self.send_off_code)
        self._state = False
        if not self.mock_mode:
            GPIO.output(self.led_gpio_pin, GPIO.LOW)

    def toggle(self):
        """Toggle the current state of the outlet."""
        if self._state:
            self.turn_off()
        else:
            self.turn_on()

    def get_state(self) -> bool:
        """Get the current state of the outlet."""
        return self._state

    def cleanup(self):
        """Clean up GPIO resources."""
        if not self.mock_mode:
            GPIO.cleanup(self.led_gpio_pin)


class BME280Sensor:
    """
    BME280 temperature, humidity, and pressure sensor.

    Attributes:
        i2c_bus_number: I2C bus number (typically 1 on Raspberry Pi)
        i2c_address: I2C device address (typically 0x76 or 0x77)
        mock_mode: If True, returns simulated sensor data
    """

    def __init__(
        self,
        i2c_bus_number: int = 1,
        i2c_address: int = 0x76,
        mock_mode: bool = False
    ):
        self.i2c_bus_number = i2c_bus_number
        self.i2c_address = i2c_address
        self.mock_mode = mock_mode
        self.calibration_params = None

        if not self.mock_mode:
            self.bus = smbus2.SMBus(self.i2c_bus_number)
            self.calibration_params = bme280.load_calibration_params(self.bus, self.i2c_address)
            print(f"BME280 Sensor initialized on bus {i2c_bus_number}, address {hex(i2c_address)}")
        else:
            print("MOCK: BME280 Sensor initialized in mock mode.")

    def read_data(self) -> Optional[Dict[str, float]]:
        """
        Read temperature, humidity, and pressure data from the sensor.

        Returns:
            Dictionary with 'temperature' (°C), 'pressure' (hPa), and 'humidity' (%)
            or None if reading fails.
        """
        if self.mock_mode:
            # Return dummy data for mock mode with some variation
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
        """Close the I2C bus connection."""
        if not self.mock_mode and hasattr(self, 'bus'):
            self.bus.close()
            print("BME280 Sensor bus closed.")


class Button:
    """
    GPIO button for manual control of greenhouse devices.

    Attributes:
        name: Human-readable button name
        gpio_pin: GPIO pin number for the button input
        callback: Function to call when button is pressed
        mock_mode: If True, simulates button without actual GPIO operations
    """

    def __init__(
        self,
        name: str,
        gpio_pin: int,
        callback: Optional[Callable] = None,
        mock_mode: bool = False,
        bouncetime: int = 300
    ):
        self.name = name
        self.gpio_pin = gpio_pin
        self.callback = callback
        self.mock_mode = mock_mode
        self.bouncetime = bouncetime

        if not self.mock_mode:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            if self.callback:
                # Button press is detected on falling edge (when pulled to ground)
                GPIO.add_event_detect(
                    self.gpio_pin,
                    GPIO.FALLING,
                    callback=self._handle_button_press,
                    bouncetime=self.bouncetime
                )
        else:
            print(f"MOCK: Button '{self.name}' initialized on GPIO pin {self.gpio_pin}")

    def _handle_button_press(self, channel):
        """Internal callback handler for button press events."""
        print(f"Button '{self.name}' pressed on GPIO pin {channel}")
        if self.callback:
            self.callback()

    def set_callback(self, callback: Callable):
        """Set or update the callback function for button presses."""
        self.callback = callback
        if not self.mock_mode:
            GPIO.remove_event_detect(self.gpio_pin)
            GPIO.add_event_detect(
                self.gpio_pin,
                GPIO.FALLING,
                callback=self._handle_button_press,
                bouncetime=self.bouncetime
            )

    def is_pressed(self) -> bool:
        """Check if button is currently pressed (for polling mode)."""
        if self.mock_mode:
            return False
        return GPIO.input(self.gpio_pin) == GPIO.LOW

    def cleanup(self):
        """Clean up GPIO resources."""
        if not self.mock_mode:
            GPIO.remove_event_detect(self.gpio_pin)
            GPIO.cleanup(self.gpio_pin)
            print(f"Button '{self.name}' GPIO cleaned up")
