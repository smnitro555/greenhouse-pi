"""
Greenhouse Manager

Main script for managing greenhouse operations including:
- Continuous monitoring of temperature and humidity
- Automatic control of heater and vent fan
- Time-based scheduling of grow lights and stand fan
- Scheduled camera captures
- Data logging
- Manual button control via GPIO interrupts
"""

import os
import sys
import json
import time
import signal
import subprocess
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Dict, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from greenhouse_manager_settings import GreenhouseManagerSettings, DeviceConfig, TimeSchedule
from greenhouse_hardware_collection import BME280Sensor, RFOutlet, Button
from greenhouse_data_logger import GreenhouseDataLogger


class ConfigFileHandler(FileSystemEventHandler):
    """Monitors configuration file for changes."""

    def __init__(self, config_path: str, callback):
        self.config_path = Path(config_path).resolve()
        self.callback = callback

    def on_modified(self, event):
        if Path(event.src_path).resolve() == self.config_path:
            print(f"Configuration file modified: {event.src_path}")
            self.callback()


class GreenhouseManager:
    """
    Main greenhouse management system.

    Handles sensor monitoring, device control, scheduling, and data logging.
    """

    def __init__(self, config_path: str = "config/greenhouse_manager_settings.json"):
        """
        Initialize the greenhouse manager.

        Args:
            config_path: Path to the JSON configuration file
        """
        self.config_path = config_path
        self.settings: Optional[GreenhouseManagerSettings] = None
        self.running = False

        # Hardware components
        self.sensor: Optional[BME280Sensor] = None
        self.heater: Optional[RFOutlet] = None
        self.vent_fan: Optional[RFOutlet] = None
        self.grow_lights: Optional[RFOutlet] = None
        self.stand_fan: Optional[RFOutlet] = None

        # Buttons for manual control
        self.heater_button: Optional[Button] = None
        self.vent_fan_button: Optional[Button] = None
        self.grow_lights_button: Optional[Button] = None
        self.stand_fan_button: Optional[Button] = None

        # Data logger
        self.data_logger: Optional[GreenhouseDataLogger] = None

        # Timing tracking
        self.last_sensor_read = 0
        self.last_log_write = 0
        self.last_camera_capture = 0
        self.last_log_cleanup = 0

        # Config file monitoring
        self.config_observer: Optional[Observer] = None

        # Load initial configuration
        self.load_configuration()
        self.initialize_hardware()
        self.setup_config_monitoring()

    def load_configuration(self):
        """Load and validate configuration from JSON file."""
        try:
            print(f"Loading configuration from: {self.config_path}")
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)

            # Validate with Pydantic model
            self.settings = GreenhouseManagerSettings(**config_data)
            print("Configuration loaded and validated successfully")

        except FileNotFoundError:
            print(f"ERROR: Configuration file not found: {self.config_path}")
            print("Please create a configuration file based on the template")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in configuration file: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Configuration validation failed: {e}")
            sys.exit(1)

    def initialize_hardware(self):
        """Initialize all hardware components based on configuration."""
        print("Initializing hardware components...")

        mock_mode = self.settings.mock_mode

        # Initialize sensor
        self.sensor = BME280Sensor(
            i2c_bus_number=self.settings.sensor.i2c_bus,
            i2c_address=self.settings.sensor.i2c_address,
            mock_mode=mock_mode
        )

        # Initialize devices
        self.heater = RFOutlet(
            name=self.settings.heater.name,
            send_on_code=self.settings.heater.rf_on_code,
            send_off_code=self.settings.heater.rf_off_code,
            led_gpio_pin=self.settings.heater.led_gpio_pin,
            mock_mode=mock_mode
        )

        self.vent_fan = RFOutlet(
            name=self.settings.vent_fan.name,
            send_on_code=self.settings.vent_fan.rf_on_code,
            send_off_code=self.settings.vent_fan.rf_off_code,
            led_gpio_pin=self.settings.vent_fan.led_gpio_pin,
            mock_mode=mock_mode
        )

        self.grow_lights = RFOutlet(
            name=self.settings.grow_lights.name,
            send_on_code=self.settings.grow_lights.rf_on_code,
            send_off_code=self.settings.grow_lights.rf_off_code,
            led_gpio_pin=self.settings.grow_lights.led_gpio_pin,
            mock_mode=mock_mode
        )

        self.stand_fan = RFOutlet(
            name=self.settings.stand_fan.name,
            send_on_code=self.settings.stand_fan.rf_on_code,
            send_off_code=self.settings.stand_fan.rf_off_code,
            led_gpio_pin=self.settings.stand_fan.led_gpio_pin,
            mock_mode=mock_mode
        )

        # Initialize buttons if configured
        if self.settings.heater.button_gpio_pin is not None:
            self.heater_button = Button(
                name=f"{self.settings.heater.name} Button",
                gpio_pin=self.settings.heater.button_gpio_pin,
                callback=lambda: self.heater.toggle(),
                mock_mode=mock_mode
            )

        if self.settings.vent_fan.button_gpio_pin is not None:
            self.vent_fan_button = Button(
                name=f"{self.settings.vent_fan.name} Button",
                gpio_pin=self.settings.vent_fan.button_gpio_pin,
                callback=lambda: self.vent_fan.toggle(),
                mock_mode=mock_mode
            )

        if self.settings.grow_lights.button_gpio_pin is not None:
            self.grow_lights_button = Button(
                name=f"{self.settings.grow_lights.name} Button",
                gpio_pin=self.settings.grow_lights.button_gpio_pin,
                callback=lambda: self.grow_lights.toggle(),
                mock_mode=mock_mode
            )

        if self.settings.stand_fan.button_gpio_pin is not None:
            self.stand_fan_button = Button(
                name=f"{self.settings.stand_fan.name} Button",
                gpio_pin=self.settings.stand_fan.button_gpio_pin,
                callback=lambda: self.stand_fan.toggle(),
                mock_mode=mock_mode
            )

        # Initialize data logger
        self.data_logger = GreenhouseDataLogger(
            log_directory=self.settings.log_directory,
            log_format=self.settings.data_logging.log_format,
            max_log_days=self.settings.data_logging.max_log_days
        )

        print("Hardware initialization complete")

    def setup_config_monitoring(self):
        """Set up file system monitoring for configuration changes."""
        config_dir = Path(self.config_path).parent
        event_handler = ConfigFileHandler(self.config_path, self.on_config_changed)

        self.config_observer = Observer()
        self.config_observer.schedule(event_handler, str(config_dir), recursive=False)
        self.config_observer.start()
        print("Configuration file monitoring started")

    def on_config_changed(self):
        """Callback when configuration file is modified."""
        print("Reloading configuration...")
        try:
            self.load_configuration()
            print("Configuration reloaded successfully")
            # Note: Hardware reinitialization would require cleanup and restart
            # For now, only settings that don't require hardware changes will take effect
        except Exception as e:
            print(f"Error reloading configuration: {e}")

    def is_time_in_schedule(self, schedule: TimeSchedule) -> bool:
        """
        Check if current time falls within a schedule.

        Args:
            schedule: TimeSchedule object to check

        Returns:
            True if current time is within the schedule
        """
        if not schedule.enabled:
            return False

        current_time = datetime.now().time()
        start = schedule.start_time
        end = schedule.end_time

        # Handle schedules that cross midnight
        if start <= end:
            return start <= current_time <= end
        else:
            return current_time >= start or current_time <= end

    def control_temperature(self, temperature: float):
        """
        Control heater and vent fan based on temperature.

        Args:
            temperature: Current temperature in Celsius
        """
        target = self.settings.temperature_control.target_temp_celsius
        tolerance = self.settings.temperature_control.temp_tolerance_celsius

        # Control heater
        if self.settings.temperature_control.heater_enabled:
            if temperature < (target - tolerance):
                if not self.heater.get_state():
                    print(f"Temperature {temperature:.1f}°C below target, turning ON heater")
                    self.heater.turn_on()
            elif temperature > target:
                if self.heater.get_state():
                    print(f"Temperature {temperature:.1f}°C at target, turning OFF heater")
                    self.heater.turn_off()

        # Control vent fan
        if self.settings.temperature_control.vent_fan_enabled:
            if temperature > (target + tolerance):
                if not self.vent_fan.get_state():
                    print(f"Temperature {temperature:.1f}°C above target, turning ON vent fan")
                    self.vent_fan.turn_on()
            elif temperature < target:
                if self.vent_fan.get_state():
                    print(f"Temperature {temperature:.1f}°C at target, turning OFF vent fan")
                    self.vent_fan.turn_off()

    def control_scheduled_devices(self):
        """Control grow lights and stand fan based on time schedules."""
        # Control grow lights
        if self.is_time_in_schedule(self.settings.grow_lights_schedule):
            if not self.grow_lights.get_state():
                print("Grow lights schedule active, turning ON")
                self.grow_lights.turn_on()
        else:
            if self.grow_lights.get_state():
                print("Grow lights schedule inactive, turning OFF")
                self.grow_lights.turn_off()

        # Control stand fan
        if self.is_time_in_schedule(self.settings.stand_fan_schedule):
            if not self.stand_fan.get_state():
                print("Stand fan schedule active, turning ON")
                self.stand_fan.turn_on()
        else:
            if self.stand_fan.get_state():
                print("Stand fan schedule inactive, turning OFF")
                self.stand_fan.turn_off()

    def capture_image(self):
        """Capture an image using the camera."""
        if not self.settings.camera_schedule.enabled:
            return

        # Check if we're within active hours
        current_time = datetime.now().time()
        if not (self.settings.camera_schedule.active_hours_start <= current_time <=
                self.settings.camera_schedule.active_hours_end):
            return

        # Ensure image directory exists
        image_dir = Path(self.settings.image_directory)
        image_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = image_dir / f"greenhouse_{timestamp}.jpg"

        try:
            # Use raspistill for Raspberry Pi camera
            # Adjust command based on your camera setup
            if not self.settings.mock_mode:
                cmd = [
                    "raspistill",
                    "-o", str(image_path),
                    "-w", "1920",
                    "-h", "1080",
                    "-q", "85",
                    "-t", "1000"  # 1 second timeout
                ]
                subprocess.run(cmd, check=True)
                print(f"Image captured: {image_path}")
            else:
                print(f"MOCK: Would capture image to {image_path}")

        except subprocess.CalledProcessError as e:
            print(f"Error capturing image: {e}")
        except FileNotFoundError:
            print("raspistill not found. Ensure camera is enabled and raspistill is installed.")

    def run_control_loop(self):
        """Main control loop for greenhouse management."""
        current_time = time.time()

        # Read sensor data
        if current_time - self.last_sensor_read >= self.settings.sensor.read_interval_seconds:
            sensor_data = self.sensor.read_data()

            if sensor_data:
                temperature = sensor_data['temperature']
                humidity = sensor_data['humidity']
                pressure = sensor_data['pressure']

                print(f"Sensor: {temperature:.1f}°C, {humidity:.1f}%, {pressure:.1f}hPa")

                # Control temperature
                self.control_temperature(temperature)

                # Control scheduled devices
                self.control_scheduled_devices()

                # Log data
                if (self.settings.data_logging.enabled and
                    current_time - self.last_log_write >= self.settings.data_logging.log_interval_seconds):

                    self.data_logger.log_data(
                        temperature=temperature,
                        humidity=humidity,
                        pressure=pressure,
                        heater_state=self.heater.get_state(),
                        vent_fan_state=self.vent_fan.get_state(),
                        grow_lights_state=self.grow_lights.get_state(),
                        stand_fan_state=self.stand_fan.get_state()
                    )
                    self.last_log_write = current_time

            self.last_sensor_read = current_time

        # Capture images on schedule
        if (self.settings.camera_schedule.enabled and
            current_time - self.last_camera_capture >= self.settings.camera_schedule.interval_minutes * 60):
            self.capture_image()
            self.last_camera_capture = current_time

        # Cleanup old logs (once per day)
        if current_time - self.last_log_cleanup >= 86400:  # 24 hours
            self.data_logger.cleanup_old_logs()
            self.last_log_cleanup = current_time

    def run(self):
        """Start the greenhouse manager main loop."""
        print("Starting Greenhouse Manager...")
        self.running = True

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        try:
            while self.running:
                self.run_control_loop()
                time.sleep(0.1)  # Small delay to prevent CPU spinning

        except Exception as e:
            print(f"Error in main loop: {e}")
            raise
        finally:
            self.shutdown()

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False

    def shutdown(self):
        """Clean up resources and shut down gracefully."""
        print("Shutting down Greenhouse Manager...")

        # Flush data logger
        if self.data_logger:
            self.data_logger.flush()

        # Clean up hardware
        if self.sensor:
            self.sensor.cleanup()
        if self.heater:
            self.heater.cleanup()
        if self.vent_fan:
            self.vent_fan.cleanup()
        if self.grow_lights:
            self.grow_lights.cleanup()
        if self.stand_fan:
            self.stand_fan.cleanup()

        # Clean up buttons
        if self.heater_button:
            self.heater_button.cleanup()
        if self.vent_fan_button:
            self.vent_fan_button.cleanup()
        if self.grow_lights_button:
            self.grow_lights_button.cleanup()
        if self.stand_fan_button:
            self.stand_fan_button.cleanup()

        # Stop config monitoring
        if self.config_observer:
            self.config_observer.stop()
            self.config_observer.join()

        print("Shutdown complete")


def main():
    """Main entry point for the greenhouse manager."""
    # Get config path from command line or use default
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/greenhouse_manager_settings.json"

    # Create and run the manager
    manager = GreenhouseManager(config_path=config_path)
    manager.run()


if __name__ == "__main__":
    main()
