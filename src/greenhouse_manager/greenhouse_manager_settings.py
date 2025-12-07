"""
Greenhouse Manager Settings

Pydantic models for validating and managing greenhouse configuration settings.
"""

from datetime import time
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TemperatureControl(BaseModel):
    """Temperature control settings for the greenhouse."""

    target_temp_celsius: float = Field(
        ...,
        ge=0,
        le=50,
        description="Target temperature in Celsius"
    )
    temp_tolerance_celsius: float = Field(
        default=2.0,
        ge=0,
        le=10,
        description="Temperature tolerance in Celsius before activating heater/vent"
    )
    heater_enabled: bool = Field(
        default=True,
        description="Enable/disable automatic heater control"
    )
    vent_fan_enabled: bool = Field(
        default=True,
        description="Enable/disable automatic vent fan control"
    )


class HumidityControl(BaseModel):
    """Humidity control settings for the greenhouse."""

    target_humidity_percent: float = Field(
        ...,
        ge=0,
        le=100,
        description="Target humidity percentage"
    )
    humidity_tolerance_percent: float = Field(
        default=10.0,
        ge=0,
        le=50,
        description="Humidity tolerance before activating controls"
    )


class TimeSchedule(BaseModel):
    """Time-based schedule for device activation."""

    enabled: bool = Field(
        default=True,
        description="Enable/disable this schedule"
    )
    start_time: time = Field(
        ...,
        description="Start time for device activation (24hr format)"
    )
    end_time: time = Field(
        ...,
        description="End time for device deactivation (24hr format)"
    )

    @field_validator('end_time')
    @classmethod
    def validate_time_range(cls, v, info):
        """Validate that end_time is different from start_time."""
        if 'start_time' in info.data and v == info.data['start_time']:
            raise ValueError('end_time must be different from start_time')
        return v


class CameraSchedule(BaseModel):
    """Camera capture schedule settings."""

    enabled: bool = Field(
        default=True,
        description="Enable/disable automatic camera captures"
    )
    interval_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Interval between camera captures in minutes"
    )
    active_hours_start: time = Field(
        default=time(6, 0),
        description="Start time for camera captures (24hr format)"
    )
    active_hours_end: time = Field(
        default=time(20, 0),
        description="End time for camera captures (24hr format)"
    )


class DataLogging(BaseModel):
    """Data logging settings."""

    enabled: bool = Field(
        default=True,
        description="Enable/disable data logging"
    )
    log_interval_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Interval between log entries in seconds"
    )
    log_format: str = Field(
        default="parquet",
        pattern="^(parquet|feather)$",
        description="Log file format (parquet or feather)"
    )
    max_log_days: int = Field(
        default=365,
        ge=1,
        description="Maximum number of days to keep log files"
    )


class DeviceConfig(BaseModel):
    """Configuration for a controllable device."""

    name: str = Field(..., description="Device name")
    rf_on_code: int = Field(..., description="RF code to turn device on")
    rf_off_code: int = Field(..., description="RF code to turn device off")
    led_gpio_pin: int = Field(..., ge=0, le=27, description="GPIO pin for LED indicator")
    button_gpio_pin: Optional[int] = Field(
        default=None,
        ge=0,
        le=27,
        description="GPIO pin for manual button control"
    )


class SensorConfig(BaseModel):
    """BME280 sensor configuration."""

    i2c_bus: int = Field(default=1, ge=0, description="I2C bus number")
    i2c_address: int = Field(default=0x76, description="I2C device address")
    read_interval_seconds: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Interval between sensor readings in seconds"
    )


class GreenhouseManagerSettings(BaseModel):
    """Main greenhouse manager settings configuration."""

    # General settings
    mock_mode: bool = Field(
        default=False,
        description="Run in mock hardware mode for testing"
    )

    # Sensor configuration
    sensor: SensorConfig = Field(
        default_factory=SensorConfig,
        description="BME280 sensor configuration"
    )

    # Temperature and humidity control
    temperature_control: TemperatureControl = Field(
        ...,
        description="Temperature control settings"
    )
    humidity_control: HumidityControl = Field(
        ...,
        description="Humidity control settings"
    )

    # Device configurations
    heater: DeviceConfig = Field(..., description="Heater device configuration")
    vent_fan: DeviceConfig = Field(..., description="Vent fan device configuration")
    grow_lights: DeviceConfig = Field(..., description="Grow lights device configuration")
    stand_fan: DeviceConfig = Field(..., description="Stand fan device configuration")

    # Time-based schedules
    grow_lights_schedule: TimeSchedule = Field(
        ...,
        description="Schedule for grow lights operation"
    )
    stand_fan_schedule: TimeSchedule = Field(
        ...,
        description="Schedule for stand fan operation"
    )
    camera_schedule: CameraSchedule = Field(
        default_factory=CameraSchedule,
        description="Camera capture schedule"
    )

    # Data logging
    data_logging: DataLogging = Field(
        default_factory=DataLogging,
        description="Data logging configuration"
    )

    # File paths
    config_file_path: str = Field(
        default="config/greenhouse_manager_settings.json",
        description="Path to the configuration file"
    )
    rf_keys_path: str = Field(
        default="config/rf_keys.yaml",
        description="Path to RF keys configuration"
    )
    log_directory: str = Field(
        default="data/logs",
        description="Directory for log files"
    )
    image_directory: str = Field(
        default="data/images",
        description="Directory for camera images"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "mock_mode": False,
                "temperature_control": {
                    "target_temp_celsius": 24.0,
                    "temp_tolerance_celsius": 2.0,
                    "heater_enabled": True,
                    "vent_fan_enabled": True
                },
                "humidity_control": {
                    "target_humidity_percent": 65.0,
                    "humidity_tolerance_percent": 10.0
                },
                "heater": {
                    "name": "Heater",
                    "rf_on_code": 123456,
                    "rf_off_code": 123457,
                    "led_gpio_pin": 17
                },
                "grow_lights_schedule": {
                    "enabled": True,
                    "start_time": "06:00:00",
                    "end_time": "20:00:00"
                }
            }
        }
