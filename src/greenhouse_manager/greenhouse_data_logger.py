"""
Greenhouse Data Logger

Class for managing greenhouse sensor and state data logging.
Stores data in space-efficient binary formats (Parquet or Feather).
Creates one log file per day.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd


class GreenhouseDataLogger:
    """
    Manages logging of greenhouse sensor readings and device states.

    Attributes:
        log_directory: Directory path for storing log files
        log_format: Format for log files ('parquet' or 'feather')
        max_log_days: Maximum number of days to retain log files
    """

    def __init__(
        self,
        log_directory: str = "data/logs",
        log_format: str = "parquet",
        max_log_days: int = 365
    ):
        """
        Initialize the data logger.

        Args:
            log_directory: Directory for storing log files
            log_format: File format ('parquet' or 'feather')
            max_log_days: Days to keep old log files before cleanup
        """
        self.log_directory = Path(log_directory)
        self.log_format = log_format.lower()
        self.max_log_days = max_log_days

        # Validate log format
        if self.log_format not in ["parquet", "feather"]:
            raise ValueError(f"Invalid log format: {log_format}. Must be 'parquet' or 'feather'")

        # Create log directory if it doesn't exist
        self.log_directory.mkdir(parents=True, exist_ok=True)

        # Cache for current day's data
        self._current_date: Optional[datetime] = None
        self._current_dataframe: Optional[pd.DataFrame] = None

        print(f"GreenhouseDataLogger initialized: {self.log_directory} (format: {self.log_format})")

    def _get_log_filename(self, date: datetime) -> Path:
        """
        Generate the log filename for a given date.

        Args:
            date: Date for the log file

        Returns:
            Path object for the log file
        """
        date_str = date.strftime("%Y-%m-%d")
        extension = self.log_format
        return self.log_directory / f"greenhouse_log_{date_str}.{extension}"

    def _load_daily_log(self, date: datetime) -> pd.DataFrame:
        """
        Load existing log file for a specific date.

        Args:
            date: Date of the log file to load

        Returns:
            DataFrame with existing data, or empty DataFrame if file doesn't exist
        """
        log_file = self._get_log_filename(date)

        if log_file.exists():
            try:
                if self.log_format == "parquet":
                    df = pd.read_parquet(log_file)
                else:  # feather
                    df = pd.read_feather(log_file)

                print(f"Loaded existing log file: {log_file} ({len(df)} records)")
                return df
            except Exception as e:
                print(f"Error loading log file {log_file}: {e}")
                return pd.DataFrame()
        else:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=self._get_column_names())

    def _save_daily_log(self, df: pd.DataFrame, date: datetime):
        """
        Save DataFrame to log file for a specific date.

        Args:
            df: DataFrame to save
            date: Date for the log file
        """
        log_file = self._get_log_filename(date)

        try:
            if self.log_format == "parquet":
                df.to_parquet(log_file, index=False, compression='snappy')
            else:  # feather
                df.to_feather(log_file)

            print(f"Saved log file: {log_file} ({len(df)} records)")
        except Exception as e:
            print(f"Error saving log file {log_file}: {e}")

    def _get_column_names(self) -> List[str]:
        """
        Get the standard column names for log data.

        Returns:
            List of column names
        """
        return [
            "timestamp",
            "date",
            "time_24hr",
            "temperature_celsius",
            "humidity_percent",
            "pressure_hpa",
            "heater_state",
            "vent_fan_state",
            "grow_lights_state",
            "stand_fan_state"
        ]

    def log_data(
        self,
        temperature: float,
        humidity: float,
        pressure: float,
        heater_state: bool,
        vent_fan_state: bool,
        grow_lights_state: bool,
        stand_fan_state: bool,
        timestamp: Optional[datetime] = None
    ):
        """
        Log greenhouse sensor readings and device states.

        Args:
            temperature: Temperature in Celsius
            humidity: Humidity percentage
            pressure: Atmospheric pressure in hPa
            heater_state: True if heater is on
            vent_fan_state: True if vent fan is on
            grow_lights_state: True if grow lights are on
            stand_fan_state: True if stand fan is on
            timestamp: Optional timestamp (defaults to current time)
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Create data record
        record = {
            "timestamp": timestamp,
            "date": timestamp.strftime("%Y-%m-%d"),
            "time_24hr": timestamp.strftime("%H:%M:%S"),
            "temperature_celsius": temperature,
            "humidity_percent": humidity,
            "pressure_hpa": pressure,
            "heater_state": heater_state,
            "vent_fan_state": vent_fan_state,
            "grow_lights_state": grow_lights_state,
            "stand_fan_state": stand_fan_state
        }

        # Check if we need to start a new day's log
        current_date = timestamp.date()
        if self._current_date is None or self._current_date != current_date:
            # Save previous day's data if exists
            if self._current_dataframe is not None and not self._current_dataframe.empty:
                self._save_daily_log(self._current_dataframe, datetime.combine(self._current_date, datetime.min.time()))

            # Load or create new day's DataFrame
            self._current_date = current_date
            self._current_dataframe = self._load_daily_log(timestamp)

        # Append new record to current DataFrame
        new_row = pd.DataFrame([record])
        self._current_dataframe = pd.concat([self._current_dataframe, new_row], ignore_index=True)

        # Periodically save to disk (every 10 records to balance performance and data safety)
        if len(self._current_dataframe) % 10 == 0:
            self._save_daily_log(self._current_dataframe, timestamp)

    def flush(self):
        """
        Force save of current data to disk.
        """
        if self._current_dataframe is not None and not self._current_dataframe.empty:
            timestamp = datetime.combine(self._current_date, datetime.min.time())
            self._save_daily_log(self._current_dataframe, timestamp)
            print("Data logger flushed to disk")

    def get_data_for_date(self, date: datetime) -> Optional[pd.DataFrame]:
        """
        Retrieve log data for a specific date.

        Args:
            date: Date to retrieve data for

        Returns:
            DataFrame with data for the specified date, or None if not found
        """
        log_file = self._get_log_filename(date)

        if log_file.exists():
            try:
                if self.log_format == "parquet":
                    return pd.read_parquet(log_file)
                else:  # feather
                    return pd.read_feather(log_file)
            except Exception as e:
                print(f"Error loading data for {date.strftime('%Y-%m-%d')}: {e}")
                return None
        else:
            print(f"No log file found for {date.strftime('%Y-%m-%d')}")
            return None

    def get_latest_reading(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent sensor reading from the current day's log.

        Returns:
            Dictionary with latest reading, or None if no data available
        """
        if self._current_dataframe is None or self._current_dataframe.empty:
            return None

        latest_row = self._current_dataframe.iloc[-1]
        return latest_row.to_dict()

    def cleanup_old_logs(self):
        """
        Remove log files older than max_log_days.
        """
        cutoff_date = datetime.now() - timedelta(days=self.max_log_days)
        removed_count = 0

        # Iterate through log files
        pattern = f"greenhouse_log_*.{self.log_format}"
        for log_file in self.log_directory.glob(pattern):
            try:
                # Extract date from filename (format: greenhouse_log_YYYY-MM-DD.ext)
                date_str = log_file.stem.split('_')[-1]
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff_date:
                    log_file.unlink()
                    removed_count += 1
                    print(f"Removed old log file: {log_file}")

            except Exception as e:
                print(f"Error processing log file {log_file}: {e}")

        if removed_count > 0:
            print(f"Cleanup complete: {removed_count} old log file(s) removed")
        else:
            print("No old log files to remove")

    def get_date_range_data(self, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Retrieve log data for a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Combined DataFrame with data for the date range, or None if no data
        """
        all_data = []
        current_date = start_date

        while current_date <= end_date:
            daily_data = self.get_data_for_date(current_date)
            if daily_data is not None and not daily_data.empty:
                all_data.append(daily_data)
            current_date += timedelta(days=1)

        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            return combined_df
        else:
            return None

    def get_statistics(self, date: datetime) -> Optional[Dict[str, Any]]:
        """
        Calculate statistics for a specific date.

        Args:
            date: Date to calculate statistics for

        Returns:
            Dictionary with statistics (min, max, mean, etc.)
        """
        data = self.get_data_for_date(date)

        if data is None or data.empty:
            return None

        stats = {
            "date": date.strftime("%Y-%m-%d"),
            "record_count": len(data),
            "temperature": {
                "min": data["temperature_celsius"].min(),
                "max": data["temperature_celsius"].max(),
                "mean": data["temperature_celsius"].mean(),
                "std": data["temperature_celsius"].std()
            },
            "humidity": {
                "min": data["humidity_percent"].min(),
                "max": data["humidity_percent"].max(),
                "mean": data["humidity_percent"].mean(),
                "std": data["humidity_percent"].std()
            },
            "pressure": {
                "min": data["pressure_hpa"].min(),
                "max": data["pressure_hpa"].max(),
                "mean": data["pressure_hpa"].mean(),
                "std": data["pressure_hpa"].std()
            },
            "device_uptime": {
                "heater_percent": (data["heater_state"].sum() / len(data)) * 100,
                "vent_fan_percent": (data["vent_fan_state"].sum() / len(data)) * 100,
                "grow_lights_percent": (data["grow_lights_state"].sum() / len(data)) * 100,
                "stand_fan_percent": (data["stand_fan_state"].sum() / len(data)) * 100
            }
        }

        return stats
