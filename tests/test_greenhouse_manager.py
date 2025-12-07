"""
Tests for greenhouse_manager module.

Tests manager settings and configuration.
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import time

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from greenhouse_manager.greenhouse_manager_settings import (
    GreenhouseManagerSettings,
    TemperatureControl,
    HumidityControl,
    TimeSchedule,
    CameraSchedule,
    DataLogging,
    DeviceConfig,
    SensorConfig
)


class TestTemperatureControl:
    """Test cases for TemperatureControl model."""

    def test_valid_temperature_control(self):
        """Test valid temperature control settings."""
        temp_control = TemperatureControl(
            target_temp_celsius=24.0,
            temp_tolerance_celsius=2.0,
            heater_enabled=True,
            vent_fan_enabled=True
        )

        assert temp_control.target_temp_celsius == 24.0
        assert temp_control.temp_tolerance_celsius == 2.0
        assert temp_control.heater_enabled is True

    def test_temperature_bounds(self):
        """Test temperature validation bounds."""
        with pytest.raises(Exception):
            TemperatureControl(
                target_temp_celsius=-10.0,  # Below minimum
                temp_tolerance_celsius=2.0
            )

        with pytest.raises(Exception):
            TemperatureControl(
                target_temp_celsius=60.0,  # Above maximum
                temp_tolerance_celsius=2.0
            )


class TestHumidityControl:
    """Test cases for HumidityControl model."""

    def test_valid_humidity_control(self):
        """Test valid humidity control settings."""
        humidity_control = HumidityControl(
            target_humidity_percent=65.0,
            humidity_tolerance_percent=10.0
        )

        assert humidity_control.target_humidity_percent == 65.0
        assert humidity_control.humidity_tolerance_percent == 10.0

    def test_humidity_bounds(self):
        """Test humidity validation bounds."""
        with pytest.raises(Exception):
            HumidityControl(
                target_humidity_percent=150.0,  # Above maximum
                humidity_tolerance_percent=10.0
            )


class TestTimeSchedule:
    """Test cases for TimeSchedule model."""

    def test_valid_time_schedule(self):
        """Test valid time schedule."""
        schedule = TimeSchedule(
            enabled=True,
            start_time=time(6, 0),
            end_time=time(20, 0)
        )

        assert schedule.enabled is True
        assert schedule.start_time == time(6, 0)
        assert schedule.end_time == time(20, 0)

    def test_same_start_end_time_invalid(self):
        """Test that start and end time cannot be the same."""
        with pytest.raises(Exception):
            TimeSchedule(
                enabled=True,
                start_time=time(12, 0),
                end_time=time(12, 0)  # Same as start
            )

    def test_schedule_disabled(self):
        """Test disabled schedule."""
        schedule = TimeSchedule(
            enabled=False,
            start_time=time(6, 0),
            end_time=time(20, 0)
        )

        assert schedule.enabled is False


class TestCameraSchedule:
    """Test cases for CameraSchedule model."""

    def test_valid_camera_schedule(self):
        """Test valid camera schedule."""
        camera = CameraSchedule(
            enabled=True,
            interval_minutes=30,
            active_hours_start=time(6, 0),
            active_hours_end=time(20, 0)
        )

        assert camera.enabled is True
        assert camera.interval_minutes == 30

    def test_camera_interval_bounds(self):
        """Test camera interval validation."""
        with pytest.raises(Exception):
            CameraSchedule(interval_minutes=0)  # Below minimum

        with pytest.raises(Exception):
            CameraSchedule(interval_minutes=2000)  # Above maximum


class TestDataLogging:
    """Test cases for DataLogging model."""

    def test_valid_data_logging(self):
        """Test valid data logging settings."""
        logging = DataLogging(
            enabled=True,
            log_interval_seconds=60,
            log_format="parquet",
            max_log_days=365
        )

        assert logging.enabled is True
        assert logging.log_interval_seconds == 60
        assert logging.log_format == "parquet"

    def test_invalid_log_format(self):
        """Test invalid log format rejection."""
        with pytest.raises(Exception):
            DataLogging(log_format="csv")  # Invalid format

    def test_valid_feather_format(self):
        """Test feather format is accepted."""
        logging = DataLogging(log_format="feather")
        assert logging.log_format == "feather"


class TestDeviceConfig:
    """Test cases for DeviceConfig model."""

    def test_valid_device_config(self):
        """Test valid device configuration."""
        device = DeviceConfig(
            name="Heater",
            rf_on_code=123456,
            rf_off_code=123457,
            led_gpio_pin=17,
            button_gpio_pin=23
        )

        assert device.name == "Heater"
        assert device.rf_on_code == 123456
        assert device.led_gpio_pin == 17
        assert device.button_gpio_pin == 23

    def test_device_without_button(self):
        """Test device config without button pin."""
        device = DeviceConfig(
            name="Heater",
            rf_on_code=123456,
            rf_off_code=123457,
            led_gpio_pin=17
        )

        assert device.button_gpio_pin is None

    def test_gpio_pin_bounds(self):
        """Test GPIO pin validation."""
        with pytest.raises(Exception):
            DeviceConfig(
                name="Test",
                rf_on_code=111,
                rf_off_code=222,
                led_gpio_pin=50  # Above maximum GPIO pin
            )


class TestSensorConfig:
    """Test cases for SensorConfig model."""

    def test_default_sensor_config(self):
        """Test default sensor configuration."""
        sensor = SensorConfig()

        assert sensor.i2c_bus == 1
        assert sensor.i2c_address == 0x76
        assert sensor.read_interval_seconds == 5

    def test_custom_sensor_config(self):
        """Test custom sensor configuration."""
        sensor = SensorConfig(
            i2c_bus=2,
            i2c_address=0x77,
            read_interval_seconds=10
        )

        assert sensor.i2c_bus == 2
        assert sensor.i2c_address == 0x77
        assert sensor.read_interval_seconds == 10


class TestGreenhouseManagerSettings:
    """Test cases for complete GreenhouseManagerSettings."""

    def test_minimal_valid_settings(self):
        """Test minimal valid settings configuration."""
        settings = GreenhouseManagerSettings(
            mock_mode=True,
            temperature_control=TemperatureControl(
                target_temp_celsius=24.0,
                temp_tolerance_celsius=2.0
            ),
            humidity_control=HumidityControl(
                target_humidity_percent=65.0,
                humidity_tolerance_percent=10.0
            ),
            heater=DeviceConfig(
                name="Heater",
                rf_on_code=123456,
                rf_off_code=123457,
                led_gpio_pin=17
            ),
            vent_fan=DeviceConfig(
                name="Vent Fan",
                rf_on_code=223456,
                rf_off_code=223457,
                led_gpio_pin=18
            ),
            grow_lights=DeviceConfig(
                name="Grow Lights",
                rf_on_code=323456,
                rf_off_code=323457,
                led_gpio_pin=19
            ),
            stand_fan=DeviceConfig(
                name="Stand Fan",
                rf_on_code=423456,
                rf_off_code=423457,
                led_gpio_pin=20
            ),
            grow_lights_schedule=TimeSchedule(
                enabled=True,
                start_time=time(6, 0),
                end_time=time(20, 0)
            ),
            stand_fan_schedule=TimeSchedule(
                enabled=True,
                start_time=time(8, 0),
                end_time=time(22, 0)
            )
        )

        assert settings.mock_mode is True
        assert settings.temperature_control.target_temp_celsius == 24.0
        assert settings.heater.name == "Heater"

    def test_settings_with_defaults(self):
        """Test that default values are applied correctly."""
        settings = GreenhouseManagerSettings(
            temperature_control=TemperatureControl(
                target_temp_celsius=24.0,
                temp_tolerance_celsius=2.0
            ),
            humidity_control=HumidityControl(
                target_humidity_percent=65.0
            ),
            heater=DeviceConfig(name="Heater", rf_on_code=111, rf_off_code=222, led_gpio_pin=17),
            vent_fan=DeviceConfig(name="Vent", rf_on_code=111, rf_off_code=222, led_gpio_pin=18),
            grow_lights=DeviceConfig(name="Lights", rf_on_code=111, rf_off_code=222, led_gpio_pin=19),
            stand_fan=DeviceConfig(name="Fan", rf_on_code=111, rf_off_code=222, led_gpio_pin=20),
            grow_lights_schedule=TimeSchedule(enabled=True, start_time=time(6, 0), end_time=time(20, 0)),
            stand_fan_schedule=TimeSchedule(enabled=True, start_time=time(8, 0), end_time=time(22, 0))
        )

        assert settings.mock_mode is False  # Default
        assert settings.log_directory == "data/logs"  # Default
        assert settings.data_logging.log_format == "parquet"  # Default
