"""
Tests for greenhouse_hardware_collection module.

Tests hardware classes with mock mode enabled.
"""

import pytest
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from greenhouse_manager.greenhouse_hardware_collection import BME280Sensor, RFOutlet, Button


class TestBME280Sensor:
    """Test cases for BME280Sensor class."""

    def test_sensor_init_mock_mode(self):
        """Test sensor initialization in mock mode."""
        sensor = BME280Sensor(mock_mode=True)
        assert sensor.mock_mode is True
        assert sensor.i2c_bus_number == 1
        assert sensor.i2c_address == 0x76

    def test_sensor_read_data_mock_mode(self):
        """Test reading sensor data in mock mode."""
        sensor = BME280Sensor(mock_mode=True)
        data = sensor.read_data()

        assert data is not None
        assert 'temperature' in data
        assert 'humidity' in data
        assert 'pressure' in data

        # Check reasonable ranges for mock data
        assert 18.0 <= data['temperature'] <= 35.0
        assert 40.0 <= data['humidity'] <= 99.0
        assert 950.0 <= data['pressure'] <= 1050.0

    def test_sensor_cleanup(self):
        """Test sensor cleanup in mock mode."""
        sensor = BME280Sensor(mock_mode=True)
        # Should not raise any errors
        sensor.cleanup()

    def test_sensor_custom_config(self):
        """Test sensor with custom I2C configuration."""
        sensor = BME280Sensor(i2c_bus_number=2, i2c_address=0x77, mock_mode=True)
        assert sensor.i2c_bus_number == 2
        assert sensor.i2c_address == 0x77


class TestRFOutlet:
    """Test cases for RFOutlet class."""

    def test_outlet_init_mock_mode(self):
        """Test RF outlet initialization in mock mode."""
        outlet = RFOutlet(
            name="Test Heater",
            send_on_code=123456,
            send_off_code=123457,
            led_gpio_pin=17,
            mock_mode=True
        )

        assert outlet.name == "Test Heater"
        assert outlet.send_on_code == 123456
        assert outlet.send_off_code == 123457
        assert outlet.led_gpio_pin == 17
        assert outlet.mock_mode is True
        assert outlet.get_state() is False

    def test_outlet_turn_on(self):
        """Test turning on RF outlet."""
        outlet = RFOutlet(
            name="Test Device",
            send_on_code=111,
            send_off_code=222,
            led_gpio_pin=18,
            mock_mode=True
        )

        outlet.turn_on()
        assert outlet.get_state() is True

    def test_outlet_turn_off(self):
        """Test turning off RF outlet."""
        outlet = RFOutlet(
            name="Test Device",
            send_on_code=111,
            send_off_code=222,
            led_gpio_pin=18,
            mock_mode=True
        )

        outlet.turn_on()
        assert outlet.get_state() is True

        outlet.turn_off()
        assert outlet.get_state() is False

    def test_outlet_toggle(self):
        """Test toggling RF outlet state."""
        outlet = RFOutlet(
            name="Test Device",
            send_on_code=111,
            send_off_code=222,
            led_gpio_pin=18,
            mock_mode=True
        )

        initial_state = outlet.get_state()
        outlet.toggle()
        assert outlet.get_state() != initial_state

        outlet.toggle()
        assert outlet.get_state() == initial_state

    def test_outlet_cleanup(self):
        """Test outlet cleanup in mock mode."""
        outlet = RFOutlet(
            name="Test Device",
            send_on_code=111,
            send_off_code=222,
            led_gpio_pin=18,
            mock_mode=True
        )
        # Should not raise any errors
        outlet.cleanup()


class TestButton:
    """Test cases for Button class."""

    def test_button_init_mock_mode(self):
        """Test button initialization in mock mode."""
        button = Button(
            name="Test Button",
            gpio_pin=23,
            mock_mode=True
        )

        assert button.name == "Test Button"
        assert button.gpio_pin == 23
        assert button.mock_mode is True

    def test_button_with_callback(self):
        """Test button with callback function."""
        callback_executed = []

        def test_callback():
            callback_executed.append(True)

        button = Button(
            name="Test Button",
            gpio_pin=23,
            callback=test_callback,
            mock_mode=True
        )

        assert button.callback is not None

    def test_button_set_callback(self):
        """Test setting callback after initialization."""
        new_callback_executed = []

        def new_callback():
            new_callback_executed.append(True)

        button = Button(
            name="Test Button",
            gpio_pin=23,
            mock_mode=True
        )

        button.set_callback(new_callback)
        assert button.callback is not None

    def test_button_is_pressed_mock(self):
        """Test checking if button is pressed in mock mode."""
        button = Button(
            name="Test Button",
            gpio_pin=23,
            mock_mode=True
        )

        # In mock mode, button should always return False
        assert button.is_pressed() is False

    def test_button_cleanup(self):
        """Test button cleanup in mock mode."""
        button = Button(
            name="Test Button",
            gpio_pin=23,
            mock_mode=True
        )
        # Should not raise any errors
        button.cleanup()


class TestHardwareIntegration:
    """Integration tests for hardware components."""

    def test_multiple_outlets(self):
        """Test managing multiple RF outlets."""
        heater = RFOutlet("Heater", 111, 112, 17, mock_mode=True)
        fan = RFOutlet("Fan", 211, 212, 18, mock_mode=True)
        lights = RFOutlet("Lights", 311, 312, 19, mock_mode=True)

        heater.turn_on()
        fan.turn_off()
        lights.turn_on()

        assert heater.get_state() is True
        assert fan.get_state() is False
        assert lights.get_state() is True

    def test_sensor_with_outlets(self):
        """Test coordinating sensor readings with outlet control."""
        sensor = BME280Sensor(mock_mode=True)
        heater = RFOutlet("Heater", 111, 112, 17, mock_mode=True)

        data = sensor.read_data()
        assert data is not None

        # Simulate temperature control logic
        if data['temperature'] < 20:
            heater.turn_on()
        else:
            heater.turn_off()

        # Just verify it doesn't crash
        assert True
